from datetime import datetime, timedelta

from flask import Flask, g, jsonify, redirect, render_template, request, session, url_for

from app.blueprints.appointments import appointments_bp
from app.blueprints.auth import auth_bp
from app.blueprints.main import main_bp
from app.blueprints.patients import patients_bp
from app.config import Config
from app.extensions import db
from app.utils.auth import wants_json_response


def create_app(config_class: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    @app.before_request
    def enforce_session_timeout():
        if request.blueprint == "auth":
            return None
        if "user_id" not in session:
            return None
        timeout = timedelta(minutes=int(app.config["SESSION_TIMEOUT_MINUTES"]))
        last_seen = session.get("last_seen_at")
        now = datetime.utcnow()
        if last_seen and now - datetime.fromisoformat(last_seen) > timeout:
            session.clear()
            if wants_json_response():
                return jsonify({"error": "Session timed out."}), 401
            return redirect(url_for("auth.login"))
        session["last_seen_at"] = now.isoformat()
        return None

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.headers.setdefault("Content-Security-Policy", "default-src 'self'; script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; img-src 'self' data:; font-src 'self' https://cdn.jsdelivr.net; connect-src 'self'; frame-ancestors 'none'")
        if app.config["SESSION_COOKIE_SECURE"]:
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response

    @app.context_processor
    def inject_auth_context():
        return {
            "current_user": getattr(g, "current_user", None),
            "csrf_token": session.get("csrf_token", ""),
            "current_role_key": getattr(g, "current_role_key", ""),
        }

    @app.errorhandler(401)
    def unauthorized_handler(error):
        if wants_json_response():
            return jsonify({"error": "Authentication required"}), 401
        return render_template("errors/401.html"), 401

    @app.errorhandler(403)
    def forbidden_handler(error):
        if wants_json_response():
            return jsonify({"error": "You do not have permission to access this resource."}), 403
        return render_template("errors/403.html"), 403

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(patients_bp, url_prefix="/patients")
    app.register_blueprint(appointments_bp, url_prefix="/appointments")

    return app
