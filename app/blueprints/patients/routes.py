from __future__ import annotations

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for, g, session

from app.extensions import get_audit_service, get_patient_service
from app.services.patient_service import PatientError
from app.utils.auth import role_required, wants_json_response

patients_bp = Blueprint("patients", __name__)


def _ensure_csrf() -> str:
    token = session.get("csrf_token")
    if not token:
        from app.utils.auth import generate_csrf_token

        token = generate_csrf_token()
        session["csrf_token"] = token
    return token


def _validate_csrf() -> bool:
    return request.form.get("csrf_token", "") == session.get("csrf_token", "")


def _payload_from_request() -> dict:
    if request.is_json:
        return request.get_json(force=True) or {}
    return request.form.to_dict(flat=True)


def _audit(action_type: str, entity_id: str, details: str) -> None:
    get_audit_service().log(
        user_id=int(g.current_user["user_id"]) if getattr(g, "current_user", None) else None,
        action_type=action_type,
        entity_name="patients",
        entity_id=entity_id,
        details=details,
        ip_address=request.remote_addr or "unknown",
    )


def _patient_or_404(patient_id: int):
    return get_patient_service().get_patient(patient_id)


def _form_template(patient=None, action="Create", submit_label="Save"):
    return render_template(
        "patients/form.html",
        patient=patient,
        action=action,
        submit_label=submit_label,
        csrf_token=_ensure_csrf(),
    )


@patients_bp.route("/")
@role_required("administrator", "doctor", "nurse", "receptionist")
def index():
    search = request.args.get("q", "").strip()
    include_inactive = request.args.get("include_inactive") == "1"
    patients = get_patient_service().list_patients(search=search, active_only=not include_inactive)
    return render_template(
        "patients/index.html",
        patients=patients,
        search=search,
        include_inactive=include_inactive,
        csrf_token=_ensure_csrf(),
    )


@patients_bp.route("/new", methods=["GET", "POST"])
@role_required("administrator", "doctor", "receptionist")
def new_patient():
    if request.method == "POST":
        if not request.is_json and not _validate_csrf():
            flash("Invalid form token. Please try again.", "danger")
            if wants_json_response():
                return jsonify({"error": "Invalid form token."}), 400
            return _form_template(action="Add Patient", submit_label="Create"), 400
        try:
            patient_id = get_patient_service().create_patient(_payload_from_request())
        except PatientError as exc:
            flash(str(exc), "danger")
            if wants_json_response():
                return jsonify({"error": str(exc)}), 400
            return _form_template(action="Add Patient", submit_label="Create"), 400

        patient = _patient_or_404(patient_id)
        _audit("CREATE", str(patient_id), f"Created patient {patient['mrn']}.")
        if wants_json_response():
            return jsonify({"message": "Patient created successfully.", "patient": patient}), 201
        flash("Patient created successfully.", "success")
        return redirect(url_for("patients.profile", patient_id=patient_id))

    return _form_template(action="Add Patient", submit_label="Create")


@patients_bp.route("/<int:patient_id>")
@role_required("administrator", "doctor", "nurse", "receptionist")
def profile(patient_id: int):
    patient = _patient_or_404(patient_id)
    if not patient:
        if wants_json_response():
            return jsonify({"error": "Patient not found."}), 404
        flash("Patient not found.", "danger")
        return redirect(url_for("patients.index"))
    return render_template("patients/profile.html", patient=patient)


@patients_bp.route("/<int:patient_id>/edit", methods=["GET", "POST"])
@role_required("administrator", "doctor", "receptionist")
def edit_patient(patient_id: int):
    patient = _patient_or_404(patient_id)
    if not patient:
        if wants_json_response():
            return jsonify({"error": "Patient not found."}), 404
        flash("Patient not found.", "danger")
        return redirect(url_for("patients.index"))

    if request.method == "POST":
        if not request.is_json and not _validate_csrf():
            flash("Invalid form token. Please try again.", "danger")
            if wants_json_response():
                return jsonify({"error": "Invalid form token."}), 400
            return _form_template(patient=patient, action="Edit Patient", submit_label="Update"), 400
        try:
            get_patient_service().update_patient(
                patient_id,
                _payload_from_request(),
                current_is_active=patient["is_active"],
                allow_status_change=g.current_role_key == "administrator",
            )
        except PatientError as exc:
            flash(str(exc), "danger")
            if wants_json_response():
                return jsonify({"error": str(exc)}), 400
            return _form_template(patient=patient, action="Edit Patient", submit_label="Update"), 400

        patient = _patient_or_404(patient_id)
        _audit("UPDATE", str(patient_id), f"Updated patient {patient['mrn']}.")
        if wants_json_response():
            return jsonify({"message": "Patient updated successfully.", "patient": patient})
        flash("Patient updated successfully.", "success")
        return redirect(url_for("patients.profile", patient_id=patient_id))

    return _form_template(patient=patient, action="Edit Patient", submit_label="Update")


@patients_bp.route("/<int:patient_id>/delete", methods=["POST"])
@role_required("administrator")
def delete_patient(patient_id: int):
    patient = _patient_or_404(patient_id)
    if not patient:
        if wants_json_response():
            return jsonify({"error": "Patient not found."}), 404
        flash("Patient not found.", "danger")
        return redirect(url_for("patients.index"))

    if not request.is_json and not _validate_csrf():
        flash("Invalid form token. Please try again.", "danger")
        if wants_json_response():
            return jsonify({"error": "Invalid form token."}), 400
        return redirect(url_for("patients.profile", patient_id=patient_id))

    get_patient_service().delete_patient(patient_id)
    _audit("DELETE", str(patient_id), f"Deactivated patient {patient['mrn']}.")
    if wants_json_response():
        return jsonify({"message": "Patient deactivated successfully.", "patient_id": patient_id})
    flash("Patient deactivated successfully.", "success")
    return redirect(url_for("patients.index"))


@patients_bp.route("/api", methods=["GET", "POST"])
@role_required("administrator", "doctor", "nurse", "receptionist")
def api_patients():
    if request.method == "GET":
        patients = get_patient_service().list_patients(
            search=request.args.get("q", ""),
            active_only=request.args.get("include_inactive") != "1",
        )
        return jsonify({"patients": patients})

    if g.current_role_key not in {"administrator", "doctor", "receptionist"}:
        return jsonify({"error": "You do not have permission to create patients."}), 403

    if request.method == "POST" and request.is_json is False and request.form and not _validate_csrf():
        return jsonify({"error": "Invalid form token."}), 400

    try:
        patient_id = get_patient_service().create_patient(_payload_from_request())
    except PatientError as exc:
        return jsonify({"error": str(exc)}), 400
    _audit("CREATE", str(patient_id), "Created patient via API.")
    return jsonify({"message": "Patient created successfully.", "patient": _patient_or_404(patient_id)}), 201


@patients_bp.route("/api/<int:patient_id>", methods=["GET", "PUT", "PATCH", "DELETE"])
@role_required("administrator", "doctor", "nurse", "receptionist")
def api_patient_detail(patient_id: int):
    patient = _patient_or_404(patient_id)
    if not patient:
        return jsonify({"error": "Patient not found."}), 404

    if request.method == "GET":
        return jsonify({"patient": patient})

    if request.method in {"PUT", "PATCH"}:
        if g.current_role_key not in {"administrator", "doctor", "receptionist"}:
            return jsonify({"error": "You do not have permission to update patients."}), 403
        if request.is_json is False and request.form and not _validate_csrf():
            return jsonify({"error": "Invalid form token."}), 400
        try:
            get_patient_service().update_patient(
                patient_id,
                _payload_from_request(),
                current_is_active=patient["is_active"],
                allow_status_change=g.current_role_key == "administrator",
            )
        except PatientError as exc:
            return jsonify({"error": str(exc)}), 400
        _audit("UPDATE", str(patient_id), "Updated patient via API.")
        return jsonify({"message": "Patient updated successfully.", "patient": _patient_or_404(patient_id)})

    if request.method == "DELETE":
        if g.current_role_key != "administrator":
            return jsonify({"error": "You do not have permission to deactivate patients."}), 403
        if request.is_json is False and request.form and not _validate_csrf():
            return jsonify({"error": "Invalid form token."}), 400
        get_patient_service().delete_patient(patient_id)
        _audit("DELETE", str(patient_id), "Deactivated patient via API.")
        return jsonify({"message": "Patient deactivated successfully.", "patient_id": patient_id})

    return jsonify({"error": "Method not allowed."}), 405
