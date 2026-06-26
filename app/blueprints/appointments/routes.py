from __future__ import annotations

from flask import Blueprint, flash, g, jsonify, redirect, render_template, request, session, url_for

from app.extensions import get_appointment_service, get_audit_service
from app.services.appointment_service import AppointmentError
from app.utils.auth import generate_csrf_token, role_required, wants_json_response


appointments_bp = Blueprint("appointments", __name__)


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


def _payload_from_request() -> dict:
    if request.is_json:
        return request.get_json(force=True) or {}
    return request.form.to_dict(flat=True)


def _audit(action_type: str, entity_id: str, details: str) -> None:
    get_audit_service().log(
        user_id=int(g.current_user["user_id"]) if getattr(g, "current_user", None) else None,
        action_type=action_type,
        entity_name="appointments",
        entity_id=entity_id,
        details=details,
        ip_address=request.remote_addr or "unknown",
    )


def _form_template(appointment=None, action="Schedule Appointment", submit_label="Schedule"):
    options = get_appointment_service().get_form_options()
    return render_template(
        "appointments/form.html",
        appointment=appointment,
        action=action,
        submit_label=submit_label,
        csrf_token=_ensure_csrf(),
        **options,
    )


@appointments_bp.route("/")
@role_required("administrator", "doctor", "nurse", "receptionist")
def index():
    service = get_appointment_service()
    search = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip() or None
    patient_id = request.args.get("patient_id", "").strip()
    try:
        patient_id_value = int(patient_id) if patient_id else None
        appointments = service.list_appointments(search=search, status=status, patient_id=patient_id_value)
    except (AppointmentError, ValueError) as exc:
        flash(str(exc), "danger")
        appointments = []
    return render_template(
        "appointments/index.html",
        appointments=appointments,
        search=search,
        selected_status=status or "",
        selected_patient_id=patient_id,
        csrf_token=_ensure_csrf(),
        **service.get_form_options(),
    )


@appointments_bp.route("/new", methods=["GET", "POST"])
@role_required("administrator", "doctor", "nurse", "receptionist")
def new_appointment():
    if request.method == "POST":
        if not request.is_json and not _validate_csrf():
            flash("Invalid form token. Please try again.", "danger")
            if wants_json_response():
                return jsonify({"error": "Invalid form token."}), 400
            return _form_template(), 400
        try:
            appointment_id = get_appointment_service().schedule_appointment(
                _payload_from_request(),
                scheduled_by_user_id=int(g.current_user["user_id"]),
            )
        except AppointmentError as exc:
            flash(str(exc), "danger")
            if wants_json_response():
                return jsonify({"error": str(exc)}), 400
            return _form_template(), 400
        appointment = get_appointment_service().get_appointment(appointment_id)
        _audit("CREATE", str(appointment_id), f"Scheduled appointment for MRN {appointment['mrn']}.")
        if wants_json_response():
            return jsonify({"message": "Appointment scheduled successfully.", "appointment": appointment}), 201
        flash("Appointment scheduled successfully.", "success")
        return redirect(url_for("appointments.detail", appointment_id=appointment_id))

    return _form_template()


@appointments_bp.route("/<int:appointment_id>")
@role_required("administrator", "doctor", "nurse", "receptionist")
def detail(appointment_id: int):
    appointment = get_appointment_service().get_appointment(appointment_id)
    if not appointment:
        if wants_json_response():
            return jsonify({"error": "Appointment not found."}), 404
        flash("Appointment not found.", "danger")
        return redirect(url_for("appointments.index"))
    return render_template("appointments/detail.html", appointment=appointment, csrf_token=_ensure_csrf())


@appointments_bp.route("/<int:appointment_id>/reschedule", methods=["GET", "POST"])
@role_required("administrator", "doctor", "nurse", "receptionist")
def reschedule(appointment_id: int):
    appointment = get_appointment_service().get_appointment(appointment_id)
    if not appointment:
        if wants_json_response():
            return jsonify({"error": "Appointment not found."}), 404
        flash("Appointment not found.", "danger")
        return redirect(url_for("appointments.index"))

    if request.method == "POST":
        if not request.is_json and not _validate_csrf():
            flash("Invalid form token. Please try again.", "danger")
            if wants_json_response():
                return jsonify({"error": "Invalid form token."}), 400
            return _form_template(appointment=appointment, action="Reschedule Appointment", submit_label="Update"), 400
        try:
            get_appointment_service().reschedule_appointment(appointment_id, _payload_from_request())
        except AppointmentError as exc:
            flash(str(exc), "danger")
            if wants_json_response():
                return jsonify({"error": str(exc)}), 400
            return _form_template(appointment=appointment, action="Reschedule Appointment", submit_label="Update"), 400
        appointment = get_appointment_service().get_appointment(appointment_id)
        _audit("UPDATE", str(appointment_id), f"Updated appointment for MRN {appointment['mrn']}.")
        if wants_json_response():
            return jsonify({"message": "Appointment updated successfully.", "appointment": appointment})
        flash("Appointment updated successfully.", "success")
        return redirect(url_for("appointments.detail", appointment_id=appointment_id))

    return _form_template(appointment=appointment, action="Reschedule Appointment", submit_label="Update")


@appointments_bp.route("/<int:appointment_id>/cancel", methods=["POST"])
@role_required("administrator", "doctor", "nurse", "receptionist")
def cancel(appointment_id: int):
    if not request.is_json and not _validate_csrf():
        flash("Invalid form token. Please try again.", "danger")
        if wants_json_response():
            return jsonify({"error": "Invalid form token."}), 400
        return redirect(url_for("appointments.detail", appointment_id=appointment_id))
    try:
        get_appointment_service().cancel_appointment(appointment_id, _payload_from_request().get("cancel_note"))
    except AppointmentError as exc:
        flash(str(exc), "danger")
        if wants_json_response():
            return jsonify({"error": str(exc)}), 400
        return redirect(url_for("appointments.detail", appointment_id=appointment_id))
    _audit("DELETE", str(appointment_id), "Cancelled appointment.")
    if wants_json_response():
        return jsonify({"message": "Appointment cancelled successfully.", "appointment_id": appointment_id})
    flash("Appointment cancelled successfully.", "success")
    return redirect(url_for("appointments.detail", appointment_id=appointment_id))


@appointments_bp.route("/api", methods=["GET", "POST"])
@role_required("administrator", "doctor", "nurse", "receptionist")
def api_appointments():
    service = get_appointment_service()
    if request.method == "GET":
        try:
            patient_id = request.args.get("patient_id", "").strip()
            appointments = service.list_appointments(
                search=request.args.get("q", ""),
                status=request.args.get("status", "").strip() or None,
                patient_id=int(patient_id) if patient_id else None,
            )
        except (AppointmentError, ValueError) as exc:
            return jsonify({"error": str(exc)}), 400
        return jsonify({"appointments": appointments})

    try:
        appointment_id = service.schedule_appointment(_payload_from_request(), scheduled_by_user_id=int(g.current_user["user_id"]))
    except AppointmentError as exc:
        return jsonify({"error": str(exc)}), 400
    _audit("CREATE", str(appointment_id), "Scheduled appointment via API.")
    return jsonify({"message": "Appointment scheduled successfully.", "appointment": service.get_appointment(appointment_id)}), 201


@appointments_bp.route("/api/<int:appointment_id>", methods=["GET", "PUT", "PATCH", "DELETE"])
@role_required("administrator", "doctor", "nurse", "receptionist")
def api_appointment_detail(appointment_id: int):
    service = get_appointment_service()
    appointment = service.get_appointment(appointment_id)
    if not appointment:
        return jsonify({"error": "Appointment not found."}), 404
    if request.method == "GET":
        return jsonify({"appointment": appointment})
    if request.method in {"PUT", "PATCH"}:
        try:
            service.reschedule_appointment(appointment_id, _payload_from_request())
        except AppointmentError as exc:
            return jsonify({"error": str(exc)}), 400
        _audit("UPDATE", str(appointment_id), "Updated appointment via API.")
        return jsonify({"message": "Appointment updated successfully.", "appointment": service.get_appointment(appointment_id)})
    if request.method == "DELETE":
        try:
            service.cancel_appointment(appointment_id, _payload_from_request().get("cancel_note"))
        except AppointmentError as exc:
            return jsonify({"error": str(exc)}), 400
        _audit("DELETE", str(appointment_id), "Cancelled appointment via API.")
        return jsonify({"message": "Appointment cancelled successfully.", "appointment_id": appointment_id})
    return jsonify({"error": "Method not allowed."}), 405
