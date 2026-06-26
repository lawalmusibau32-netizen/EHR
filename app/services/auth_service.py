from __future__ import annotations

from datetime import datetime, timedelta
import secrets

from flask import current_app

from app.repositories.user_repository import UserRepository
from app.utils.auth import (
    create_access_token,
    generate_csrf_token,
    hash_password,
    normalize_role_key,
    validate_password,
    verify_password,
    decode_access_token,
)
from app.utils.mfa import generate_mfa_secret, verify_totp


class AuthError(ValueError):
    pass


class AuthService:
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    def _public_session(self, session_row: dict | None) -> dict | None:
        if not session_row:
            return None
        return {
            "session_id": session_row["session_id"],
            "user_id": session_row["user_id"],
            "jti": session_row["jti"],
            "expires_at": session_row["expires_at"],
            "revoked_at": session_row["revoked_at"],
            "created_at": session_row["created_at"],
            "last_seen_at": session_row["last_seen_at"],
            "ip_address": session_row["ip_address"],
            "user_agent": session_row["user_agent"],
        }

    def _public_user(self, user: dict | None) -> dict | None:
        if not user:
            return None
        return {
            "user_id": user["user_id"],
            "role_id": user["role_id"],
            "username": user["username"],
            "display_name": user["display_name"],
            "email": user["email"],
            "is_active": user["is_active"],
            "mfa_enabled": user.get("mfa_enabled", "N"),
            "last_login_at": user["last_login_at"],
            "created_at": user["created_at"],
            "updated_at": user["updated_at"],
            "role_name": user["role_name"],
            "role_description": user["role_description"],
            "role_key": normalize_role_key(user["role_name"]),
        }

    def register_user(self, *, username: str, display_name: str, email: str | None, role_name: str, password: str) -> dict:
        username = username.strip()
        display_name = display_name.strip()
        email = email.strip() if email else None

        if not username:
            raise AuthError("Username is required.")
        if not display_name:
            raise AuthError("Display name is required.")
        if not role_name:
            raise AuthError("Role is required.")

        password_errors = validate_password(password, username=username)
        if password_errors:
            raise AuthError(" ".join(password_errors))

        if self.user_repository.get_user_by_username(username):
            raise AuthError("That username is already registered.")

        role = self.user_repository.get_role_by_name(role_name)
        if not role:
            raise AuthError("Selected role does not exist.")

        password_hash, password_salt = hash_password(password)
        user_id = self.user_repository.create_user(
            role_id=int(role["role_id"]),
            username=username,
            display_name=display_name,
            email=email,
            password_hash=password_hash,
            password_salt=password_salt,
        )
        return self._public_user(self.user_repository.get_user_by_id(user_id))

    def login(self, *, username: str, password: str, ip_address: str, user_agent: str, mfa_code: str | None = None) -> dict:
        user = self.user_repository.get_user_by_username(username)
        if not user or user["is_active"] != "Y":
            raise AuthError("Invalid username or password.")
        if user.get("locked_until") and user["locked_until"] > datetime.utcnow():
            raise AuthError("Account is temporarily locked. Please try again later.")
        if not verify_password(password, user["password_hash"]):
            self.user_repository.record_failed_login(
                int(user["user_id"]),
                int(current_app.config["ACCOUNT_LOCKOUT_ATTEMPTS"]),
                int(current_app.config["ACCOUNT_LOCKOUT_MINUTES"]),
            )
            raise AuthError("Invalid username or password.")
        if user.get("mfa_enabled") == "Y" and not verify_totp(user.get("mfa_secret"), mfa_code):
            self.user_repository.record_failed_login(
                int(user["user_id"]),
                int(current_app.config["ACCOUNT_LOCKOUT_ATTEMPTS"]),
                int(current_app.config["ACCOUNT_LOCKOUT_MINUTES"]),
            )
            raise AuthError("A valid MFA code is required.")

        jti = secrets.token_urlsafe(24)
        expires_minutes = int(current_app.config["JWT_ACCESS_TOKEN_MINUTES"])
        expires_at = datetime.utcnow() + timedelta(minutes=expires_minutes)
        session_id = self.user_repository.create_auth_session(
            user_id=int(user["user_id"]),
            jti=jti,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.user_repository.update_last_login(int(user["user_id"]))

        access_token = create_access_token(
            user_id=int(user["user_id"]),
            username=user["username"],
            role_name=user["role_name"],
            jti=jti,
            expires_in_minutes=expires_minutes,
            secret_key=current_app.config["JWT_SECRET_KEY"],
            issuer=current_app.config["JWT_ISSUER"],
            audience=current_app.config["JWT_AUDIENCE"],
        )

        return {
            "user": self._public_user(user),
            "access_token": access_token,
            "jti": jti,
            "session_id": session_id,
            "csrf_token": generate_csrf_token(),
            "expires_at": expires_at,
        }

    def enable_mfa(self, user_id: int) -> str:
        secret = generate_mfa_secret()
        self.user_repository.enable_mfa(user_id, secret)
        return secret

    def authenticate_token(self, token: str, ip_address: str, user_agent: str) -> dict | None:
        try:
            payload = decode_access_token(
                token,
                secret_key=current_app.config["JWT_SECRET_KEY"],
                issuer=current_app.config["JWT_ISSUER"],
                audience=current_app.config["JWT_AUDIENCE"],
            )
        except Exception:
            return None

        session_row = self.user_repository.get_auth_session(payload["jti"])
        if not session_row or session_row["revoked_at"] is not None:
            return None
        if session_row["expires_at"] < datetime.utcnow():
            return None

        user = self.user_repository.get_user_by_id(int(payload["sub"]))
        if not user or user["is_active"] != "Y":
            return None

        self.user_repository.touch_auth_session(payload["jti"])
        return {"user": self._public_user(user), "session": self._public_session(session_row), "payload": payload}

    def logout(self, token: str) -> None:
        try:
            payload = decode_access_token(
                token,
                secret_key=current_app.config["JWT_SECRET_KEY"],
                issuer=current_app.config["JWT_ISSUER"],
                audience=current_app.config["JWT_AUDIENCE"],
            )
        except Exception:
            return
        self.user_repository.revoke_auth_session(payload["jti"])
