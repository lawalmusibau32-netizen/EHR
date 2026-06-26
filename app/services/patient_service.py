from __future__ import annotations

from datetime import date, datetime
import re

from app.repositories.patient_repository import PatientRepository
from app.utils.crypto import decrypt_mapping, encrypt_value


class PatientError(ValueError):
    pass


class PatientService:
    SEX_VALUES = {"Male", "Female", "Other"}

    def __init__(self, patient_repository: PatientRepository) -> None:
        self.patient_repository = patient_repository

    def _trim(self, value: str | None) -> str:
        return value.strip() if value else ""

    def _normalize_optional(self, value: str | None) -> str | None:
        value = self._trim(value)
        return value or None

    def _parse_date(self, value: str):
        if not value:
            raise PatientError("Date of birth is required.")
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError as exc:
            raise PatientError("Date of birth must be in YYYY-MM-DD format.") from exc

    def _validate(self, *, mrn: str, first_name: str, last_name: str, date_of_birth: str, sex: str, email: str | None, phone_number: str | None, exclude_patient_id: int | None = None):
        mrn = self._trim(mrn)
        first_name = self._trim(first_name)
        last_name = self._trim(last_name)
        sex = self._trim(sex)

        if not mrn:
            raise PatientError("MRN is required.")
        if len(mrn) > 30:
            raise PatientError("MRN cannot exceed 30 characters.")
        if not first_name:
            raise PatientError("First name is required.")
        if not last_name:
            raise PatientError("Last name is required.")
        if sex not in self.SEX_VALUES:
            raise PatientError("Sex must be Male, Female, or Other.")

        dob = self._parse_date(date_of_birth)
        if dob > date.today():
            raise PatientError("Date of birth cannot be in the future.")

        email_value = self._normalize_optional(email)
        if email_value and len(email_value) > 255:
            raise PatientError("Email cannot exceed 255 characters.")
        if email_value and "@" not in email_value:
            raise PatientError("Email must be a valid email address.")

        phone_value = self._normalize_optional(phone_number)
        if phone_value and len(phone_value) > 30:
            raise PatientError("Phone number cannot exceed 30 characters.")
        if phone_value and not re.fullmatch(r"[0-9+() \-]{6,30}", phone_value):
            raise PatientError("Phone number contains invalid characters.")

        if self.patient_repository.patient_exists(mrn, exclude_patient_id=exclude_patient_id):
            raise PatientError("That MRN already exists.")

        return {
            "mrn": mrn,
            "first_name": first_name,
            "last_name": last_name,
            "date_of_birth": dob,
            "sex": sex,
            "phone_number": phone_value,
            "email": email_value,
        }

    def list_patients(self, search: str = "", active_only: bool = True):
        return [
            decrypt_mapping(patient, ["phone_number", "email", "address_line1", "address_line2", "city", "region"])
            for patient in self.patient_repository.list_patients(search=search, active_only=active_only)
        ]

    def get_patient(self, patient_id: int):
        return decrypt_mapping(
            self.patient_repository.get_patient_by_id(patient_id),
            ["phone_number", "email", "address_line1", "address_line2", "city", "region"],
        )

    def create_patient(self, data: dict) -> int:
        validated = self._validate(
            mrn=data.get("mrn", ""),
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            date_of_birth=data.get("date_of_birth", ""),
            sex=data.get("sex", ""),
            email=data.get("email"),
            phone_number=data.get("phone_number"),
        )
        validated["phone_number"] = encrypt_value(validated["phone_number"])
        validated["email"] = encrypt_value(validated["email"])
        validated["address_line1"] = encrypt_value(self._normalize_optional(data.get("address_line1")))
        validated["address_line2"] = encrypt_value(self._normalize_optional(data.get("address_line2")))
        validated["city"] = encrypt_value(self._normalize_optional(data.get("city")))
        validated["region"] = encrypt_value(self._normalize_optional(data.get("region")))
        validated["country"] = self._trim(data.get("country")) or "Ghana"
        return self.patient_repository.create_patient(**validated)

    def update_patient(self, patient_id: int, data: dict, *, current_is_active: str = "Y", allow_status_change: bool = False) -> None:
        validated = self._validate(
            mrn=data.get("mrn", ""),
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            date_of_birth=data.get("date_of_birth", ""),
            sex=data.get("sex", ""),
            email=data.get("email"),
            phone_number=data.get("phone_number"),
            exclude_patient_id=patient_id,
        )
        validated["phone_number"] = encrypt_value(validated["phone_number"])
        validated["email"] = encrypt_value(validated["email"])
        validated["address_line1"] = encrypt_value(self._normalize_optional(data.get("address_line1")))
        validated["address_line2"] = encrypt_value(self._normalize_optional(data.get("address_line2")))
        validated["city"] = encrypt_value(self._normalize_optional(data.get("city")))
        validated["region"] = encrypt_value(self._normalize_optional(data.get("region")))
        validated["country"] = self._trim(data.get("country")) or "Ghana"
        if allow_status_change:
            validated["is_active"] = "Y" if data.get("is_active") in {"Y", "on", "1", True} else "N"
        else:
            validated["is_active"] = current_is_active if current_is_active in {"Y", "N"} else "Y"
        validated["patient_id"] = patient_id
        self.patient_repository.update_patient(**validated)

    def delete_patient(self, patient_id: int) -> None:
        self.patient_repository.deactivate_patient(patient_id)
