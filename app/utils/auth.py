from __future__ import annotations

from datetime import datetime, timedelta, timezone
from functools import wraps
import re
import secrets

import bcrypt
import jwt
from flask import current_app, g, jsonify, redirect, render_template, request, session, url_for


PASSWORD_MIN_LENGTH = 12
PASSWORD_RULES = {
    "uppercase": re.compile(r"[A-Z]"),
    "lowercase": re.compile(r"[a-z]"),
    "digit": re.compile(r"\d"),
    "special": re.compile(r"[^A-Za-z0-9]"),
}

ROLE_ALIASES = {
    "administrator": "administrator",
    "admin": "administrator",
    "doctor": "doctor",
    "clinician": "doctor",
    "nurse": "nurse",
    "receptionist": "receptionist",
}

ROLE_LABELS = {
    "administrator": "Administrator",
    "doctor": "Doctor",
    "nurse": "Nurse",
    "receptionist": "Receptionist",
}


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def hash_password(password: str) -> tuple[str, str]:
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8"), salt.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def validate_password(password: str, username: str = "") -> list[str]:
    errors: list[str] = []
    if len(password) < PASSWORD_MIN_LENGTH:
        errors.append(f"Password must be at least {PASSWORD_MIN_LENGTH} characters long.")
    if username and username.lower() in password.lower():
        errors.append("Password must not contain the username.")
    for label, pattern in PASSWORD_RULES.items():
        if not pattern.search(password):
            errors.append(f"Password must include at least one {label} character.")
    return errors


def normalize_role_key(role_name: str | None) -> str:
    if not role_name:
        return ""
    return ROLE_ALIASES.get(role_name.strip().lower(), role_name.strip().lower())


def role_label(role_key: str) -> str:
    return ROLE_LABELS.get(normalize_role_key(role_key), role_key.title())


def create_access_token(*, user_id: int, username: str, role_name: str, jti: str, expires_in_minutes: int, secret_key: str, issuer: str, audience: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role_name,
        "jti": jti,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_in_minutes)).timestamp()),
        "iss": issuer,
        "aud": audience,
    }
    return jwt.encode(payload, secret_key, algorithm="HS256")


def decode_access_token(token: str, *, secret_key: str, issuer: str, audience: str) -> dict:
    return jwt.decode(
        token,
        secret_key,
        algorithms=["HS256"],
        issuer=issuer,
        audience=audience,
        options={"require": ["exp", "iat", "nbf", "sub", "jti"]},
    )


def extract_bearer_token() -> str | None:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip()
    return request.cookies.get(current_app.config["AUTH_COOKIE_NAME"])


def wants_json_response() -> bool:
    return request.is_json or "application/json" in request.headers.get("Accept", "")


def access_denied_response(status_code: int, message: str, *, required_roles: list[str] | None = None):
    if wants_json_response():
        payload = {"error": message}
        if required_roles:
            payload["required_roles"] = required_roles
        return jsonify(payload), status_code

    template = "errors/401.html" if status_code == 401 else "errors/403.html"
    return render_template(template, message=message, required_roles=required_roles), status_code


def role_required(*roles):
    allowed_roles = {normalize_role_key(role) for role in roles if role}

    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            from app.extensions import get_auth_service

            token = extract_bearer_token()
            if not token:
                return access_denied_response(401, "Authentication required.")

            service = get_auth_service()
            result = service.authenticate_token(token, request.remote_addr or "", request.headers.get("User-Agent", ""))
            if not result:
                return access_denied_response(401, "Authentication required.")

            g.current_user = result["user"]
            g.current_session = result["session"]
            g.current_token = token
            g.current_role_key = result["user"]["role_key"]

            if allowed_roles and g.current_role_key not in allowed_roles:
                return access_denied_response(
                    403,
                    "You do not have permission to access this resource.",
                    required_roles=[role_label(role) for role in sorted(allowed_roles)],
                )

            return view(*args, **kwargs)

        return wrapped

    return decorator


def auth_required(view):
    return role_required()(view)
