from __future__ import annotations

from datetime import datetime
import re

from app.repositories.medical_record_repository import MedicalRecordRepository
from app.repositories.patient_repository import PatientRepository
from app.utils.crypto import decrypt_mapping, encrypt_value


class MedicalRecordError(ValueError):
    pass


class MedicalRecordService:
    RECORD_TYPES = {"Encounter", "Diagnosis", "Medication", "Lab Result", "Imaging", "Procedure", "Note"}
    RECORD_STATUSES = {"ACTIVE", "AMENDED", "VOID"}
    DIAGNOSIS_STATUSES = {"ACTIVE", "RESOLVED", "RULE_OUT"}

    def __init__(self, record_repository: MedicalRecordRepository, patient_repository: PatientRepository) -> None:
        self.record_repository = record_repository
        self.patient_repository = patient_repository

    def _trim(self, value: str | None) -> str:
        return value.strip() if value else ""

    def _optional(self, value: str | None) -> str | None:
        value = self._trim(value)
        return value or None

    def _parse_datetime(self, value: str | None):
        if not value:
            return datetime.utcnow()
        value = value.strip()
        for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        raise MedicalRecordError("Date and time must be a valid ISO datetime value.")

    def _require_patient(self, patient_id: str | int):
        try:
            patient_id_int = int(patient_id)
        except (TypeError, ValueError) as exc:
            raise MedicalRecordError("A valid patient must be selected.") from exc
        patient = self.patient_repository.get_patient_by_id(patient_id_int)
        if not patient:
            raise MedicalRecordError("Selected patient does not exist.")
        if patient["is_active"] != "Y":
            raise MedicalRecordError("Selected patient is inactive.")
        return patient

    def _require_record(self, record_id: int):
        record = self.record_repository.get_record_by_id(record_id)
        if not record:
            raise MedicalRecordError("Medical record not found.")
        return record

    def _validate_record(
        self,
        *,
        patient_id,
        record_type: str,
        title: str,
        clinical_note: str,
        record_status: str,
        encounter_date: str | None,
    ):
        patient = self._require_patient(patient_id)
        record_type = self._trim(record_type)
        title = self._trim(title)
        clinical_note = self._trim(clinical_note)
        record_status = self._trim(record_status) or "ACTIVE"

        if record_type not in self.RECORD_TYPES:
            raise MedicalRecordError("Record type is not valid.")
        if not title:
            raise MedicalRecordError("Record title is required.")
        if len(title) > 150:
            raise MedicalRecordError("Record title cannot exceed 150 characters.")
        if not clinical_note:
            raise MedicalRecordError("Clinical note is required.")
        if len(clinical_note) > 10000:
            raise MedicalRecordError("Clinical note is too long.")
        if record_status not in self.RECORD_STATUSES:
            raise MedicalRecordError("Record status is not valid.")

        return {
            "patient_id": int(patient["patient_id"]),
            "record_type": record_type,
            "title": title,
            "clinical_note": clinical_note,
            "record_status": record_status,
            "encounter_date": self._parse_datetime(encounter_date),
        }

    def _validate_diagnosis(self, *, diagnosis_name: str, icd10_code: str | None, diagnosis_status: str, is_primary) -> dict:
        diagnosis_name = self._trim(diagnosis_name)
        icd10_code = self._optional(icd10_code)
        diagnosis_status = self._trim(diagnosis_status) or "ACTIVE"
        if not diagnosis_name:
            raise MedicalRecordError("Diagnosis name is required.")
        if len(diagnosis_name) > 255:
            raise MedicalRecordError("Diagnosis name cannot exceed 255 characters.")
        if icd10_code and not re.fullmatch(r"[A-Z0-9.]{1,12}", icd10_code.upper()):
            raise MedicalRecordError("ICD-10 code contains invalid characters.")
        if diagnosis_status not in self.DIAGNOSIS_STATUSES:
            raise MedicalRecordError("Diagnosis status is not valid.")
        return {
            "diagnosis_name": diagnosis_name,
            "icd10_code": icd10_code.upper() if icd10_code else None,
            "diagnosis_status": diagnosis_status,
            "is_primary": "Y" if str(is_primary).lower() in {"y", "yes", "1", "true", "on"} else "N",
        }

    def _validate_prescription(
        self,
        *,
        medication_name: str,
        dosage: str | None,
        frequency: str | None,
        route: str | None,
        duration_days: str | int | None,
        instructions: str | None,
    ) -> dict:
        medication_name = self._trim(medication_name)
        if not medication_name:
            raise MedicalRecordError("Medication name is required.")
        if len(medication_name) > 255:
            raise MedicalRecordError("Medication name cannot exceed 255 characters.")

        duration_value = None
        if duration_days not in (None, ""):
            try:
                duration_value = int(duration_days)
            except (TypeError, ValueError) as exc:
                raise MedicalRecordError("Duration must be a whole number of days.") from exc
            if duration_value <= 0:
                raise MedicalRecordError("Duration must be greater than zero.")

        return {
            "medication_name": medication_name,
            "dosage": self._optional(dosage),
            "frequency": self._optional(frequency),
            "route": self._optional(route),
            "duration_days": duration_value,
            "instructions": self._optional(instructions),
        }

    def _validate_treatment(self, *, treatment_name: str, treatment_description: str | None, treatment_date: str | None, outcome: str | None, notes: str | None) -> dict:
        treatment_name = self._trim(treatment_name)
        if not treatment_name:
            raise MedicalRecordError("Treatment name is required.")
        if len(treatment_name) > 255:
            raise MedicalRecordError("Treatment name cannot exceed 255 characters.")
        return {
            "treatment_name": treatment_name,
            "treatment_description": self._optional(treatment_description),
            "treatment_date": self._parse_datetime(treatment_date),
            "outcome": self._optional(outcome),
            "notes": self._optional(notes),
        }

    def list_patients(self):
        return self.record_repository.list_patients_for_selector(active_only=True)

    def list_records(self, search: str = "", patient_id: int | None = None, record_type: str | None = None, record_status: str | None = None):
        return self.record_repository.list_records(search=search, patient_id=patient_id, record_type=record_type, record_status=record_status)

    def get_record(self, record_id: int):
        return self.record_repository.get_record_by_id(record_id)

    def get_record_bundle(self, record_id: int, *, include_inactive: bool = False):
        record = self._require_record(record_id)
        return {
            "record": record,
            "diagnoses": [
                decrypt_mapping(row, ["diagnosis_name", "icd10_code"])
                for row in self.record_repository.list_diagnoses(record_id, include_inactive=include_inactive)
            ],
            "prescriptions": [
                decrypt_mapping(row, ["medication_name", "dosage", "frequency", "route", "instructions"])
                for row in self.record_repository.list_prescriptions(record_id, include_inactive=include_inactive)
            ],
            "treatments": [
                decrypt_mapping(row, ["treatment_name", "treatment_description", "outcome", "notes"])
                for row in self.record_repository.list_treatments(record_id, include_inactive=include_inactive)
            ],
        }

    def create_record(self, data: dict, *, created_by_user_id: int) -> int:
        validated = self._validate_record(
            patient_id=data.get("patient_id"),
            record_type=data.get("record_type", ""),
            title=data.get("title", ""),
            clinical_note=data.get("clinical_note", ""),
            record_status=data.get("record_status", "ACTIVE"),
            encounter_date=data.get("encounter_date"),
        )
        return self.record_repository.create_record(created_by_user_id=created_by_user_id, **validated)

    def update_record(self, record_id: int, data: dict) -> None:
        self._require_record(record_id)
        validated = self._validate_record(
            patient_id=data.get("patient_id"),
            record_type=data.get("record_type", ""),
            title=data.get("title", ""),
            clinical_note=data.get("clinical_note", ""),
            record_status=data.get("record_status", "ACTIVE"),
            encounter_date=data.get("encounter_date"),
        )
        self.record_repository.update_record(record_id=record_id, **{k: v for k, v in validated.items() if k != "patient_id"})

    def add_diagnosis(self, record_id: int, data: dict) -> int:
        self._require_record(record_id)
        validated = self._validate_diagnosis(
            diagnosis_name=data.get("diagnosis_name", ""),
            icd10_code=data.get("icd10_code"),
            diagnosis_status=data.get("diagnosis_status", "ACTIVE"),
            is_primary=data.get("is_primary"),
        )
        validated["diagnosis_name"] = encrypt_value(validated["diagnosis_name"])
        validated["icd10_code"] = encrypt_value(validated["icd10_code"])
        diagnosed_at = self._parse_datetime(data.get("diagnosed_at"))
        return self.record_repository.create_diagnosis(record_id=record_id, diagnosed_at=diagnosed_at, **validated)

    def update_diagnosis(self, record_id: int, diagnosis_id: int, data: dict) -> None:
        diagnosis = self.record_repository.get_diagnosis_by_id(diagnosis_id)
        if not diagnosis or int(diagnosis["record_id"]) != int(record_id):
            raise MedicalRecordError("Diagnosis not found.")
        validated = self._validate_diagnosis(
            diagnosis_name=data.get("diagnosis_name", ""),
            icd10_code=data.get("icd10_code"),
            diagnosis_status=data.get("diagnosis_status", diagnosis.get("diagnosis_status", "ACTIVE")),
            is_primary=data.get("is_primary"),
        )
        validated["diagnosis_name"] = encrypt_value(validated["diagnosis_name"])
        validated["icd10_code"] = encrypt_value(validated["icd10_code"])
        diagnosed_at = self._parse_datetime(data.get("diagnosed_at"))
        self.record_repository.update_diagnosis(diagnosis_id=diagnosis_id, diagnosed_at=diagnosed_at, **validated)

    def deactivate_diagnosis(self, record_id: int, diagnosis_id: int) -> None:
        diagnosis = self.record_repository.get_diagnosis_by_id(diagnosis_id)
        if not diagnosis or int(diagnosis["record_id"]) != int(record_id):
            raise MedicalRecordError("Diagnosis not found.")
        self.record_repository.deactivate_diagnosis(diagnosis_id)

    def add_prescription(self, record_id: int, data: dict) -> int:
        self._require_record(record_id)
        validated = self._validate_prescription(
            medication_name=data.get("medication_name", ""),
            dosage=data.get("dosage"),
            frequency=data.get("frequency"),
            route=data.get("route"),
            duration_days=data.get("duration_days"),
            instructions=data.get("instructions"),
        )
        for field in ["medication_name", "dosage", "frequency", "route", "instructions"]:
            validated[field] = encrypt_value(validated[field])
        prescribed_at = self._parse_datetime(data.get("prescribed_at"))
        return self.record_repository.create_prescription(record_id=record_id, prescribed_at=prescribed_at, **validated)

    def update_prescription(self, record_id: int, prescription_id: int, data: dict) -> None:
        prescription = self.record_repository.get_prescription_by_id(prescription_id)
        if not prescription or int(prescription["record_id"]) != int(record_id):
            raise MedicalRecordError("Prescription not found.")
        validated = self._validate_prescription(
            medication_name=data.get("medication_name", ""),
            dosage=data.get("dosage"),
            frequency=data.get("frequency"),
            route=data.get("route"),
            duration_days=data.get("duration_days"),
            instructions=data.get("instructions"),
        )
        for field in ["medication_name", "dosage", "frequency", "route", "instructions"]:
            validated[field] = encrypt_value(validated[field])
        prescribed_at = self._parse_datetime(data.get("prescribed_at"))
        self.record_repository.update_prescription(
            prescription_id=prescription_id,
            prescription_status=data.get("prescription_status", prescription.get("prescription_status", "ACTIVE")),
            prescribed_at=prescribed_at,
            **validated,
        )

    def deactivate_prescription(self, record_id: int, prescription_id: int) -> None:
        prescription = self.record_repository.get_prescription_by_id(prescription_id)
        if not prescription or int(prescription["record_id"]) != int(record_id):
            raise MedicalRecordError("Prescription not found.")
        self.record_repository.deactivate_prescription(prescription_id)

    def add_treatment(self, record_id: int, data: dict) -> int:
        self._require_record(record_id)
        validated = self._validate_treatment(
            treatment_name=data.get("treatment_name", ""),
            treatment_description=data.get("treatment_description"),
            treatment_date=data.get("treatment_date"),
            outcome=data.get("outcome"),
            notes=data.get("notes"),
        )
        for field in ["treatment_name", "treatment_description", "outcome", "notes"]:
            validated[field] = encrypt_value(validated[field])
        return self.record_repository.create_treatment(record_id=record_id, **validated)

    def update_treatment(self, record_id: int, treatment_id: int, data: dict) -> None:
        treatment = self.record_repository.get_treatment_by_id(treatment_id)
        if not treatment or int(treatment["record_id"]) != int(record_id):
            raise MedicalRecordError("Treatment not found.")
        validated = self._validate_treatment(
            treatment_name=data.get("treatment_name", ""),
            treatment_description=data.get("treatment_description"),
            treatment_date=data.get("treatment_date"),
            outcome=data.get("outcome"),
            notes=data.get("notes"),
        )
        for field in ["treatment_name", "treatment_description", "outcome", "notes"]:
            validated[field] = encrypt_value(validated[field])
        self.record_repository.update_treatment(treatment_id=treatment_id, **validated)

    def deactivate_treatment(self, record_id: int, treatment_id: int) -> None:
        treatment = self.record_repository.get_treatment_by_id(treatment_id)
        if not treatment or int(treatment["record_id"]) != int(record_id):
            raise MedicalRecordError("Treatment not found.")
        self.record_repository.deactivate_treatment(treatment_id)
