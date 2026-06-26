from __future__ import annotations

from flask import Blueprint, g, redirect, render_template, request, url_for

from app.extensions import get_audit_service, get_dashboard_service
from app.utils.auth import auth_required, role_required

main_bp = Blueprint("main", __name__)


def _dashboard_endpoint(role_key: str) -> str:
    return {
        "administrator": "main.dashboard_administrator",
        "doctor": "main.dashboard_doctor",
        "nurse": "main.dashboard_nurse",
        "receptionist": "main.dashboard_receptionist",
    }.get(role_key, "main.dashboard_doctor")


@main_bp.route("/")
@auth_required
def index():
    return redirect(url_for("main.dashboard"))


@main_bp.route("/dashboard")
@auth_required
def dashboard():
    return redirect(url_for(_dashboard_endpoint(g.current_user["role_key"])))


@main_bp.route("/dashboard/administrator")
@role_required("administrator")
def dashboard_administrator():
    return render_template("main/dashboard.html", dashboard_role="administrator", dashboard=get_dashboard_service().for_role("administrator"))


@main_bp.route("/dashboard/doctor")
@role_required("administrator", "doctor")
def dashboard_doctor():
    return render_template("main/dashboard.html", dashboard_role="doctor", dashboard=get_dashboard_service().for_role("doctor"))


@main_bp.route("/dashboard/nurse")
@role_required("administrator", "nurse")
def dashboard_nurse():
    return render_template("main/dashboard.html", dashboard_role="nurse", dashboard=get_dashboard_service().for_role("nurse"))


@main_bp.route("/dashboard/receptionist")
@role_required("administrator", "receptionist")
def dashboard_receptionist():
    return render_template("main/dashboard.html", dashboard_role="receptionist", dashboard=get_dashboard_service().for_role("receptionist"))


@main_bp.route("/medical-records")
@role_required("administrator", "doctor", "nurse")
def records():
    return render_template("main/records.html")


@main_bp.route("/users")
@role_required("administrator")
def users():
    return render_template("main/users.html")


@main_bp.route("/audit-logs")
@role_required("administrator")
def audit_logs():
    action_type = request.args.get("action_type", "").strip() or None
    search = request.args.get("q", "").strip()
    audit_service = get_audit_service()
    return render_template(
        "main/audit_logs.html",
        logs=audit_service.list_logs(action_type=action_type, search=search),
        action_summary=audit_service.action_summary(),
        selected_action=action_type or "",
        search=search,
    )


@main_bp.route("/security-monitoring")
@role_required("administrator")
def security_monitoring():
    audit_service = get_audit_service()
    action_summary = audit_service.action_summary()
    security_events = audit_service.recent_security_events()
    locked_accounts = audit_service.locked_accounts()
    return render_template(
        "main/security_monitoring.html",
        action_summary=action_summary,
        security_events=security_events,
        locked_accounts=locked_accounts,
        chart_labels=[row["action_type"] for row in action_summary],
        chart_values=[row["total"] for row in action_summary],
        failed_login_total=sum(row["total"] for row in action_summary if row["action_type"] == "LOGIN_FAILED"),
    )
