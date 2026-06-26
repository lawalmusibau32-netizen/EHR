from __future__ import annotations

from datetime import datetime

from flask import Blueprint, current_app, flash, g, jsonify, make_response, redirect, render_template, request, session, url_for

from app.extensions import get_audit_service, get_auth_service, get_user_repository
from app.services.auth_service import AuthError
from app.utils.auth import auth_required, extract_bearer_token, generate_csrf_token, role_required, wants_json_response

auth_bp = Blueprint("auth", __name__)


def _ensure_csrf() -> str:
    token = session.get("csrf_token")
    if not token:
        token = generate_csrf_token()
        session["csrf_token"] = token
    return token


def _validate_csrf() -> bool:
    form_token = request.form.get("csrf_token", "")
    session_token = session.get("csrf_token", "")
    return bool(form_token and session_token and form_token == session_token)


def _set_auth_cookie(response, access_token: str):
    response.set_cookie(
        current_app.config["AUTH_COOKIE_NAME"],
        access_token,
        httponly=True,
        secure=current_app.config["SESSION_COOKIE_SECURE"],
        samesite=current_app.config["SESSION_COOKIE_SAMESITE"],
        max_age=current_app.config["JWT_ACCESS_TOKEN_MINUTES"] * 60,
        path="/",
    )
    return response


def _audit(user_id: int | None, action_type: str, entity_name: str, entity_id: str, details: str | None = None) -> None:
    get_audit_service().log(
        user_id=user_id,
        action_type=action_type,
        entity_name=entity_name,
        entity_id=entity_id,
        details=details,
        ip_address=request.remote_addr or "unknown",
    )


@auth_bp.route("/register", methods=["GET", "POST"])
@role_required("administrator")
def register():
    csrf_token = _ensure_csrf()
    roles = get_user_repository().list_roles()

    if request.method == "POST":
        if not _validate_csrf():
            flash("Invalid form token. Please try again.", "danger")
            if wants_json_response():
                return jsonify({"error": "Invalid form token."}), 400
        else:
            try:
                user = get_auth_service().register_user(
                    username=request.form.get("username", ""),
                    display_name=request.form.get("display_name", ""),
                    email=request.form.get("email", ""),
                    role_name=request.form.get("role_name", ""),
                    password=request.form.get("password", ""),
                )
                _audit(g.current_user["user_id"], "CREATE", "users", str(user["user_id"]), f"Registered user {user['username']}.")
                flash("User registered successfully.", "success")
                if wants_json_response():
                    return jsonify({"message": "User registered successfully.", "user": user}), 201
                return redirect(url_for("main.users"))
            except AuthError as exc:
                flash(str(exc), "danger")
                if wants_json_response():
                    return jsonify({"error": str(exc)}), 400

    if wants_json_response():
        return jsonify({"roles": roles, "csrf_token": csrf_token})
    return render_template("auth/register.html", roles=roles, csrf_token=csrf_token)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        token = extract_bearer_token()
        if token:
            result = get_auth_service().authenticate_token(
                token,
                request.remote_addr or "unknown",
                request.headers.get("User-Agent", "unknown"),
            )
            if result:
                g.current_user = result["user"]
                g.current_session = result["session"]
                return redirect(url_for("main.index"))
        csrf_token = _ensure_csrf()
        return render_template("auth/login.html", csrf_token=csrf_token)

    if not _validate_csrf():
        flash("Invalid form token. Please try again.", "danger")
        if wants_json_response():
            return jsonify({"error": "Invalid form token."}), 400
        return render_template("auth/login.html", csrf_token=_ensure_csrf()), 400

    try:
        result = get_auth_service().login(
            username=request.form.get("username", ""),
            password=request.form.get("password", ""),
            mfa_code=request.form.get("mfa_code", ""),
            ip_address=request.remote_addr or "unknown",
            user_agent=request.headers.get("User-Agent", "unknown"),
        )
    except AuthError as exc:
        attempted_user = get_user_repository().get_user_by_username(request.form.get("username", ""))
        _audit(
            attempted_user["user_id"] if attempted_user else None,
            "LOGIN_FAILED",
            "auth",
            request.form.get("username", "unknown"),
            str(exc),
        )
        flash(str(exc), "danger")
        if wants_json_response():
            return jsonify({"error": str(exc)}), 401
        return render_template("auth/login.html", csrf_token=_ensure_csrf()), 401

    session["user_id"] = result["user"]["user_id"]
    session["auth_jti"] = result["jti"]
    session["display_name"] = result["user"]["display_name"]
    session["role_name"] = result["user"]["role_name"]
    session["role_key"] = result["user"]["role_key"]
    session["csrf_token"] = result["csrf_token"]
    session["last_seen_at"] = datetime.utcnow().isoformat()
    _audit(result["user"]["user_id"], "LOGIN", "auth_sessions", str(result["session_id"]), "Interactive login succeeded.")

    if wants_json_response():
        response = jsonify(
            {
                "access_token": result["access_token"],
                "token_type": "Bearer",
                "user": {
                    "user_id": result["user"]["user_id"],
                    "username": result["user"]["username"],
                    "display_name": result["user"]["display_name"],
                    "role_name": result["user"]["role_name"],
                    "role_key": result["user"]["role_key"],
                    "email": result["user"]["email"],
                },
            }
        )
        return _set_auth_cookie(response, result["access_token"])

    response = make_response(redirect(url_for("main.index")))
    _set_auth_cookie(response, result["access_token"])
    flash("Signed in successfully.", "success")
    return response


@auth_bp.route("/logout", methods=["POST"])
def logout():
    if not _validate_csrf():
        flash("Invalid form token. Please try again.", "danger")
        if wants_json_response():
            return jsonify({"error": "Invalid form token."}), 400
        return redirect(url_for("main.index"))

    token = request.cookies.get(current_app.config["AUTH_COOKIE_NAME"], "")
    user_id = session.get("user_id")
    get_auth_service().logout(token)
    session.clear()
    _audit(user_id, "LOGOUT", "auth_sessions", "browser", "Interactive logout completed.")

    if wants_json_response():
        response = jsonify({"message": "Logged out successfully."})
        response.set_cookie(current_app.config["AUTH_COOKIE_NAME"], "", expires=0, path="/")
        return response

    response = make_response(redirect(url_for("auth.login")))
    response.set_cookie(current_app.config["AUTH_COOKIE_NAME"], "", expires=0, path="/")
    flash("Signed out successfully.", "success")
    return response


@auth_bp.route("/api/login", methods=["POST"])
def api_login():
    session["csrf_token"] = session.get("csrf_token") or generate_csrf_token()
    try:
        payload = request.get_json(force=True)
        result = get_auth_service().login(
            username=payload.get("username", ""),
            password=payload.get("password", ""),
            mfa_code=payload.get("mfa_code", ""),
            ip_address=request.remote_addr or "unknown",
            user_agent=request.headers.get("User-Agent", "unknown"),
        )
    except AuthError as exc:
        attempted_user = get_user_repository().get_user_by_username(payload.get("username", "") if "payload" in locals() else "")
        _audit(
            attempted_user["user_id"] if attempted_user else None,
            "LOGIN_FAILED",
            "auth",
            payload.get("username", "unknown") if "payload" in locals() else "unknown",
            str(exc),
        )
        return jsonify({"error": str(exc)}), 401
    _audit(result["user"]["user_id"], "LOGIN", "auth_sessions", str(result["session_id"]), "API login succeeded.")

    response = jsonify(
        {
            "access_token": result["access_token"],
            "token_type": "Bearer",
            "user": {
                "user_id": result["user"]["user_id"],
                "username": result["user"]["username"],
                "display_name": result["user"]["display_name"],
                "role_name": result["user"]["role_name"],
                "role_key": result["user"]["role_key"],
                "email": result["user"]["email"],
            },
        }
    )
    return _set_auth_cookie(response, result["access_token"])


@auth_bp.route("/api/register", methods=["POST"])
@role_required("administrator")
def api_register():
    session["csrf_token"] = session.get("csrf_token") or generate_csrf_token()
    try:
        payload = request.get_json(force=True)
        user = get_auth_service().register_user(
            username=payload.get("username", ""),
            display_name=payload.get("display_name", ""),
            email=payload.get("email", ""),
            role_name=payload.get("role_name", ""),
            password=payload.get("password", ""),
        )
    except AuthError as exc:
        return jsonify({"error": str(exc)}), 400
    _audit(g.current_user["user_id"], "CREATE", "users", str(user["user_id"]), f"Registered user {user['username']} via API.")
    return jsonify({"message": "User registered successfully.", "user": user}), 201


@auth_bp.route("/mfa/setup", methods=["POST"])
@auth_required
def setup_mfa():
    if not _validate_csrf():
        if wants_json_response():
            return jsonify({"error": "Invalid form token."}), 400
        flash("Invalid form token. Please try again.", "danger")
        return redirect(url_for("main.index"))
    secret = get_auth_service().enable_mfa(int(g.current_user["user_id"]))
    _audit(g.current_user["user_id"], "UPDATE", "users", str(g.current_user["user_id"]), "MFA enabled.")
    if wants_json_response():
        return jsonify({"message": "MFA enabled.", "secret": secret})
    flash(f"MFA enabled. Add this secret to your authenticator app: {secret}", "success")
    return redirect(url_for("main.index"))


@auth_bp.route("/api/me", methods=["GET"])
@auth_required
def api_me():
    return jsonify({"user": g.current_user, "session": g.current_session})


@auth_bp.route("/api/logout", methods=["POST"])
@auth_required
def api_logout():
    token = extract_bearer_token() or ""
    get_auth_service().logout(token)
    response = jsonify({"message": "Logged out successfully."})
    response.set_cookie(current_app.config["AUTH_COOKIE_NAME"], "", expires=0, path="/")
    return response
