from __future__ import annotations

from datetime import datetime
from typing import Any

from app.db.postgres import get_connection
from app.repositories.base_repository import BaseRepository


def _row_to_dict(row) -> dict[str, Any] | None:
    if row is None:
        return None
    return {key.lower(): row[key] for key in row.keys()}


class UserRepository(BaseRepository):
    def get_user_by_username(self, username: str):
        sql = """
            SELECT u.user_id, u.role_id, u.username, u.display_name, u.email, u.password_hash,
                   u.password_salt, u.is_active, u.failed_login_count, u.locked_until,
                   u.mfa_enabled, u.mfa_secret, u.last_login_at, u.created_at, u.updated_at,
                   r.role_name, r.description AS role_description
            FROM users u
            JOIN roles r ON r.role_id = u.role_id
            WHERE LOWER(u.username) = LOWER(:username)
        """
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, {"username": username})
                return _row_to_dict(cursor.fetchone())

    def get_user_by_id(self, user_id: int):
        sql = """
            SELECT u.user_id, u.role_id, u.username, u.display_name, u.email, u.password_hash,
                   u.password_salt, u.is_active, u.failed_login_count, u.locked_until,
                   u.mfa_enabled, u.mfa_secret, u.last_login_at, u.created_at, u.updated_at,
                   r.role_name, r.description AS role_description
            FROM users u
            JOIN roles r ON r.role_id = u.role_id
            WHERE u.user_id = :user_id
        """
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, {"user_id": user_id})
                return _row_to_dict(cursor.fetchone())

    def get_role_by_name(self, role_name: str):
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT role_id, role_name, description FROM roles WHERE LOWER(role_name) = LOWER(:role_name)",
                    {"role_name": role_name},
                )
                return _row_to_dict(cursor.fetchone())

    def list_roles(self):
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT role_id, role_name, description FROM roles ORDER BY role_name")
                return [_row_to_dict(row) for row in cursor.fetchall()]

    def create_user(self, *, role_id: int, username: str, display_name: str, email: str | None, password_hash: str, password_salt: str) -> int:
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO users (role_id, username, display_name, email, password_hash, password_salt, is_active, created_at, updated_at)
                    VALUES (:role_id, :username, :display_name, :email, :password_hash, :password_salt, 'Y', SYSTIMESTAMP, SYSTIMESTAMP)
                    RETURNING user_id
                    """,
                    {
                        "role_id": role_id,
                        "username": username,
                        "display_name": display_name,
                        "email": email,
                        "password_hash": password_hash,
                        "password_salt": password_salt,
                    },
                )
                row = cursor.fetchone()
                connection.commit()
                return int(row["user_id"])

    def update_last_login(self, user_id: int) -> None:
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE users
                    SET last_login_at = SYSTIMESTAMP,
                        failed_login_count = 0,
                        locked_until = NULL,
                        updated_at = SYSTIMESTAMP
                    WHERE user_id = :user_id
                    """,
                    {"user_id": user_id},
                )
                connection.commit()

    def record_failed_login(self, user_id: int, lock_after: int, lock_minutes: int) -> None:
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE users
                    SET failed_login_count = failed_login_count + 1,
                        locked_until = CASE
                            WHEN failed_login_count + 1 >= :lock_after
                            THEN SYSTIMESTAMP + NUMTODSINTERVAL(:lock_minutes, 'MINUTE')
                            ELSE locked_until
                        END,
                        updated_at = SYSTIMESTAMP
                    WHERE user_id = :user_id
                    """,
                    {"user_id": user_id, "lock_after": lock_after, "lock_minutes": lock_minutes},
                )
                connection.commit()

    def enable_mfa(self, user_id: int, secret: str) -> None:
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE users
                    SET mfa_enabled = 'Y',
                        mfa_secret = :secret,
                        updated_at = SYSTIMESTAMP
                    WHERE user_id = :user_id
                    """,
                    {"user_id": user_id, "secret": secret},
                )
                connection.commit()

    def create_auth_session(self, *, user_id: int, jti: str, expires_at: datetime, ip_address: str, user_agent: str) -> int:
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO auth_sessions (
                        user_id, jti, expires_at, revoked_at, created_at, last_seen_at, ip_address, user_agent
                    ) VALUES (
                        :user_id, :jti, :expires_at, NULL, SYSTIMESTAMP, SYSTIMESTAMP, :ip_address, :user_agent
                    )
                    RETURNING session_id
                    """,
                    {
                        "user_id": user_id,
                        "jti": jti,
                        "expires_at": expires_at,
                        "ip_address": ip_address,
                        "user_agent": user_agent[:255],
                    },
                )
                row = cursor.fetchone()
                connection.commit()
                return int(row["session_id"])

    def get_auth_session(self, jti: str):
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT session_id, user_id, jti, expires_at, revoked_at, created_at, last_seen_at, ip_address, user_agent
                    FROM auth_sessions
                    WHERE jti = :jti
                    """,
                    {"jti": jti},
                )
                return _row_to_dict(cursor.fetchone())

    def revoke_auth_session(self, jti: str) -> None:
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE auth_sessions SET revoked_at = SYSTIMESTAMP WHERE jti = :jti",
                    {"jti": jti},
                )

    def touch_auth_session(self, jti: str) -> None:
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE auth_sessions SET last_seen_at = SYSTIMESTAMP WHERE jti = :jti",
                    {"jti": jti},
                )
