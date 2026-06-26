from __future__ import annotations

from typing import Any

from app.db.postgres import get_connection
from app.repositories.base_repository import BaseRepository


def _row_to_dict(row) -> dict[str, Any] | None:
    if row is None:
        return None
    return {key.lower(): row[key] for key in row.keys()}


class AuditRepository(BaseRepository):
    def create_log(
        self,
        *,
        user_id: int | None,
        action_type: str,
        entity_name: str,
        entity_id: str,
        details: str | None,
        ip_address: str | None,
    ) -> None:
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO audit_logs (
                        user_id, action_type, entity_name, entity_id, details, ip_address, created_at
                    ) VALUES (
                        :user_id, :action_type, :entity_name, :entity_id, :details, :ip_address, SYSTIMESTAMP
                    )
                    """,
                    {
                        "user_id": user_id,
                        "action_type": action_type,
                        "entity_name": entity_name[:60],
                        "entity_id": str(entity_id)[:60],
                        "details": details[:4000] if details else None,
                        "ip_address": ip_address[:45] if ip_address else None,
                    },
                )
                connection.commit()

    def list_logs(self, *, action_type: str | None = None, search: str = "", limit: int = 100):
        sql = """
            SELECT *
            FROM (
                SELECT
                    al.audit_log_id,
                    al.user_id,
                    al.action_type,
                    al.entity_name,
                    al.entity_id,
                    DBMS_LOB.SUBSTR(al.details, 4000, 1) AS details,
                    al.ip_address,
                    al.created_at,
                    u.username,
                    u.display_name,
                    r.role_name
                FROM audit_logs al
                LEFT JOIN users u ON u.user_id = al.user_id
                LEFT JOIN roles r ON r.role_id = u.role_id
                WHERE (:action_type IS NULL OR al.action_type = :action_type)
                  AND (
                    :search IS NULL
                    OR LOWER(al.action_type) LIKE LOWER(:search_like)
                    OR LOWER(al.entity_name) LIKE LOWER(:search_like)
                    OR LOWER(al.entity_id) LIKE LOWER(:search_like)
                    OR LOWER(NVL(DBMS_LOB.SUBSTR(al.details, 4000, 1), ' ')) LIKE LOWER(:search_like)
                    OR LOWER(NVL(u.display_name, ' ')) LIKE LOWER(:search_like)
                    OR LOWER(NVL(u.username, ' ')) LIKE LOWER(:search_like)
                    OR LOWER(NVL(al.ip_address, ' ')) LIKE LOWER(:search_like)
                  )
                ORDER BY al.created_at DESC
            )
            WHERE ROWNUM <= :limit
        """
        search_value = search.strip()
        search_like = f"%{search_value}%" if search_value else None
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    sql,
                    {
                        "action_type": action_type,
                        "search": search_value or None,
                        "search_like": search_like,
                        "limit": limit,
                    },
                )
                return [_row_to_dict(row) for row in cursor.fetchall()]

    def count_by_action(self, limit: int = 10):
        sql = """
            SELECT *
            FROM (
                SELECT action_type, COUNT(1) AS total
                FROM audit_logs
                GROUP BY action_type
                ORDER BY total DESC
            )
            WHERE ROWNUM <= :limit
        """
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, {"limit": limit})
                return [_row_to_dict(row) for row in cursor.fetchall()]

    def failed_login_count(self):
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(1) AS total FROM audit_logs WHERE action_type = 'LOGIN_FAILED'")
                return int(cursor.fetchone()["total"])

    def recent_security_events(self, limit: int = 50):
        sql = """
            SELECT *
            FROM (
                SELECT audit_log_id, user_id, action_type, entity_name, entity_id,
                       DBMS_LOB.SUBSTR(details, 4000, 1) AS details, ip_address, created_at
                FROM audit_logs
                WHERE action_type IN ('LOGIN_FAILED', 'LOCKOUT', 'MFA_FAILED', 'UNAUTHORIZED', 'LOGIN')
                ORDER BY created_at DESC
            )
            WHERE ROWNUM <= :limit
        """
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, {"limit": limit})
                return [_row_to_dict(row) for row in cursor.fetchall()]

    def locked_accounts(self):
        sql = """
            SELECT u.user_id, u.username, u.display_name, u.failed_login_count, u.locked_until, r.role_name
            FROM users u
            JOIN roles r ON r.role_id = u.role_id
            WHERE u.locked_until IS NOT NULL
              AND u.locked_until > SYSTIMESTAMP
            ORDER BY u.locked_until DESC
        """
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql)
                return [_row_to_dict(row) for row in cursor.fetchall()]
