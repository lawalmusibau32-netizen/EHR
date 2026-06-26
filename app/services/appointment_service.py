from __future__ import annotations

from datetime import datetime

from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.patient_repository import PatientRepository


class AppointmentError(ValueError):
    pass


class AppointmentService:
    APPOINTMENT_TYPES = {"Consultation", "Follow-up", "Procedure", "Telehealth", "Lab Review", "Referral"}
    STATUSES = {"SCHEDULED", "CHECKED_IN", "COMPLETED", "CANCELLED", "NO_SHOW"}

    def __init__(self, appointment_repository: AppointmentRepository, patient_repository: PatientRepository) -> None:
        self.appointment_repository = appointment_repository
        self.patient_repository = patient_repository

    def _trim(self, value: str | None) -> str:
        return value.strip() if value else ""

    def _optional(self, value: str | None) -> str | None:
        value = self._trim(value)
        return value or None

    def _parse_datetime(self, value: str | None):
        value = self._trim(value)
        if not value:
            raise AppointmentError("Appointment date and time are required.")
        for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        raise AppointmentError("Appointment date and time must be valid.")

    def _parse_optional_int(self, value) -> int | None:
        if value in (None, ""):
            return None
        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise AppointmentError("Selected clinician is not valid.") from exc

    def _require_patient(self, patient_id) -> int:
        try:
            patient_id_int = int(patient_id)
        except (TypeError, ValueError) as exc:
            raise AppointmentError("A valid patient must be selected.") from exc
        patient = self.patient_repository.get_patient_by_id(patient_id_int)
        if not patient:
            raise AppointmentError("Selected patient does not exist.")
        if patient["is_active"] != "Y":
            raise AppointmentError("Selected patient is inactive.")
        return patient_id_int

    def _validate(self, data: dict, *, default_status: str = "SCHEDULED") -> dict:
        patient_id = self._require_patient(data.get("patient_id"))
        appointment_type = self._trim(data.get("appointment_type"))
        status = self._trim(data.get("status")) or default_status
        reason = self._optional(data.get("reason"))
        location = self._optional(data.get("location"))
        notes = self._optional(data.get("notes"))

        if appointment_type not in self.APPOINTMENT_TYPES:
            raise AppointmentError("Appointment type is not valid.")
        if status not in self.STATUSES:
            raise AppointmentError("Appointment status is not valid.")
        if reason and len(reason) > 255:
            raise AppointmentError("Reason cannot exceed 255 characters.")
        if location and len(location) > 120:
            raise AppointmentError("Location cannot exceed 120 characters.")
        if notes and len(notes) > 4000:
            raise AppointmentError("Notes cannot exceed 4000 characters.")

        clinician_user_id = self._parse_optional_int(data.get("clinician_user_id"))
        if clinician_user_id is not None and not self.appointment_repository.clinician_exists(clinician_user_id):
            raise AppointmentError("Selected clinician is not available.")

        return {
            "patient_id": patient_id,
            "clinician_user_id": clinician_user_id,
            "appointment_date": self._parse_datetime(data.get("appointment_date")),
            "appointment_type": appointment_type,
            "status": status,
            "reason": reason,
            "location": location,
            "notes": notes,
        }

    def list_appointments(self, *, search: str = "", status: str | None = None, patient_id: int | None = None):
        status = self._trim(status) or None
        if status and status not in self.STATUSES:
            raise AppointmentError("Appointment status is not valid.")
        return self.appointment_repository.list_appointments(search=search, status=status, patient_id=patient_id)

    def get_appointment(self, appointment_id: int):
        return self.appointment_repository.get_appointment_by_id(appointment_id)

    def get_form_options(self):
        return {
            "patients": self.appointment_repository.list_active_patients(),
            "clinicians": self.appointment_repository.list_clinicians(),
            "appointment_types": sorted(self.APPOINTMENT_TYPES),
            "statuses": ["SCHEDULED", "CHECKED_IN", "COMPLETED", "NO_SHOW", "CANCELLED"],
        }

    def schedule_appointment(self, data: dict, *, scheduled_by_user_id: int) -> int:
        validated = self._validate(data, default_status="SCHEDULED")
        return self.appointment_repository.create_appointment(scheduled_by_user_id=scheduled_by_user_id, **validated)

    def reschedule_appointment(self, appointment_id: int, data: dict) -> None:
        current = self.get_appointment(appointment_id)
        if not current:
            raise AppointmentError("Appointment not found.")
        if current["status"] == "CANCELLED":
            raise AppointmentError("Cancelled appointments cannot be rescheduled.")
        validated = self._validate(data, default_status=current["status"])
        self.appointment_repository.update_appointment(appointment_id=appointment_id, **validated)

    def cancel_appointment(self, appointment_id: int, notes: str | None = None) -> None:
        current = self.get_appointment(appointment_id)
        if not current:
            raise AppointmentError("Appointment not found.")
        if current["status"] == "CANCELLED":
            raise AppointmentError("Appointment is already cancelled.")
        self.appointment_repository.cancel_appointment(appointment_id, self._optional(notes))
