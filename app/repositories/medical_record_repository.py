from __future__ import annotations

from typing import Any

from app.db.oracle import get_connection
from app.repositories.base_repository import BaseRepository


def _row_to_dict(row) -> dict[str, Any] | None:
    if row is None:
        return None
    return {key.lower(): row[key] for key in row.keys()}


class MedicalRecordRepository(BaseRepository):
    def list_patients_for_selector(self, active_only: bool = True):
        sql = """
            SELECT patient_id, mrn, first_name, last_name, is_active
            FROM patients
            WHERE (:active_only = 0 OR is_active = 'Y')
            ORDER BY last_name, first_name
        """
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, {"active_only": 1 if active_only else 0})
                return [_row_to_dict(row) for row in cursor.fetchall()]

    def list_records(
        self,
        *,
        search: str = "",
        patient_id: int | None = None,
        record_type: str | None = None,
        record_status: str | None = None,
    ):
        sql = """
            SELECT
                mr.record_id,
                mr.patient_id,
                mr.created_by_user_id,
                mr.record_type,
                mr.title,
                mr.clinical_note,
                mr.record_status,
                mr.encounter_date,
                mr.created_at,
                mr.updated_at,
                p.mrn,
                p.first_name AS patient_first_name,
                p.last_name AS patient_last_name,
                p.sex AS patient_sex,
                p.date_of_birth AS patient_date_of_birth,
                u.display_name AS created_by_name,
                (
                    SELECT COUNT(1)
                    FROM record_diagnoses d
                    WHERE d.record_id = mr.record_id AND d.is_active = 'Y'
                ) AS diagnosis_count,
                (
                    SELECT COUNT(1)
                    FROM record_prescriptions pr
                    WHERE pr.record_id = mr.record_id AND pr.is_active = 'Y'
                ) AS prescription_count,
                (
                    SELECT COUNT(1)
                    FROM record_treatments t
                    WHERE t.record_id = mr.record_id AND t.is_active = 'Y'
                ) AS treatment_count
            FROM medical_records mr
            JOIN patients p ON p.patient_id = mr.patient_id
            JOIN users u ON u.user_id = mr.created_by_user_id
            WHERE (:patient_id IS NULL OR mr.patient_id = :patient_id)
              AND (:record_type IS NULL OR mr.record_type = :record_type)
              AND (:record_status IS NULL OR mr.record_status = :record_status)
              AND (
                  :search IS NULL
                  OR LOWER(p.mrn) LIKE LOWER(:search_like)
                  OR LOWER(p.first_name) LIKE LOWER(:search_like)
                  OR LOWER(p.last_name) LIKE LOWER(:search_like)
                  OR LOWER(mr.title) LIKE LOWER(:search_like)
                  OR LOWER(mr.record_type) LIKE LOWER(:search_like)
                  OR LOWER(DBMS_LOB.SUBSTR(mr.clinical_note, 4000, 1)) LIKE LOWER(:search_like)
                  OR EXISTS (
                      SELECT 1
                      FROM record_diagnoses d
                      WHERE d.record_id = mr.record_id
                        AND d.is_active = 'Y'
                        AND (
                            LOWER(d.diagnosis_name) LIKE LOWER(:search_like)
                            OR LOWER(NVL(d.icd10_code, ' ')) LIKE LOWER(:search_like)
                        )
                  )
                  OR EXISTS (
                      SELECT 1
                      FROM record_prescriptions pr
                      WHERE pr.record_id = mr.record_id
                        AND pr.is_active = 'Y'
                        AND (
                            LOWER(pr.medication_name) LIKE LOWER(:search_like)
                            OR LOWER(NVL(pr.instructions, ' ')) LIKE LOWER(:search_like)
                        )
                  )
                  OR EXISTS (
                      SELECT 1
                      FROM record_treatments t
                      WHERE t.record_id = mr.record_id
                        AND t.is_active = 'Y'
                        AND (
                            LOWER(t.treatment_name) LIKE LOWER(:search_like)
                            OR LOWER(NVL(t.outcome, ' ')) LIKE LOWER(:search_like)
                        )
                  )
              )
            ORDER BY mr.encounter_date DESC, mr.updated_at DESC
        """
        search_value = search.strip()
        search_like = f"%{search_value}%" if search_value else None
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    sql,
                    {
                        "patient_id": patient_id,
                        "record_type": record_type,
                        "record_status": record_status,
                        "search": search_value or None,
                        "search_like": search_like,
                    },
                )
                return [_row_to_dict(row) for row in cursor.fetchall()]

    def get_record_by_id(self, record_id: int):
        sql = """
            SELECT
                mr.record_id,
                mr.patient_id,
                mr.created_by_user_id,
                mr.record_type,
                mr.title,
                mr.clinical_note,
                mr.record_status,
                mr.encounter_date,
                mr.created_at,
                mr.updated_at,
                p.mrn,
                p.first_name AS patient_first_name,
                p.last_name AS patient_last_name,
                p.sex AS patient_sex,
                p.date_of_birth AS patient_date_of_birth,
                p.phone_number AS patient_phone_number,
                p.email AS patient_email,
                u.display_name AS created_by_name,
                (
                    SELECT COUNT(1)
                    FROM record_diagnoses d
                    WHERE d.record_id = mr.record_id AND d.is_active = 'Y'
                ) AS diagnosis_count,
                (
                    SELECT COUNT(1)
                    FROM record_prescriptions pr
                    WHERE pr.record_id = mr.record_id AND pr.is_active = 'Y'
                ) AS prescription_count,
                (
                    SELECT COUNT(1)
                    FROM record_treatments t
                    WHERE t.record_id = mr.record_id AND t.is_active = 'Y'
                ) AS treatment_count
            FROM medical_records mr
            JOIN patients p ON p.patient_id = mr.patient_id
            JOIN users u ON u.user_id = mr.created_by_user_id
            WHERE mr.record_id = :record_id
        """
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, {"record_id": record_id})
                return _row_to_dict(cursor.fetchone())

    def list_diagnoses(self, record_id: int, include_inactive: bool = False):
        sql = """
            SELECT diagnosis_id, record_id, diagnosis_name, icd10_code, diagnosis_status,
                   is_primary, is_active, diagnosed_at, created_at, updated_at
            FROM record_diagnoses
            WHERE record_id = :record_id
              AND (:include_inactive = 1 OR is_active = 'Y')
            ORDER BY CASE WHEN is_primary = 'Y' THEN 0 ELSE 1 END, diagnosed_at DESC, created_at DESC
        """
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, {"record_id": record_id, "include_inactive": 1 if include_inactive else 0})
                return [_row_to_dict(row) for row in cursor.fetchall()]

    def get_diagnosis_by_id(self, diagnosis_id: int):
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT diagnosis_id, record_id, diagnosis_name, icd10_code, diagnosis_status,
                           is_primary, is_active, diagnosed_at, created_at, updated_at
                    FROM record_diagnoses
                    WHERE diagnosis_id = :diagnosis_id
                    """,
                    {"diagnosis_id": diagnosis_id},
                )
                return _row_to_dict(cursor.fetchone())

    def list_prescriptions(self, record_id: int, include_inactive: bool = False):
        sql = """
            SELECT prescription_id, record_id, medication_name, dosage, frequency, route,
                   duration_days, instructions, prescription_status, is_active,
                   prescribed_at, created_at, updated_at
            FROM record_prescriptions
            WHERE record_id = :record_id
              AND (:include_inactive = 1 OR is_active = 'Y')
            ORDER BY prescribed_at DESC, created_at DESC
        """
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, {"record_id": record_id, "include_inactive": 1 if include_inactive else 0})
                return [_row_to_dict(row) for row in cursor.fetchall()]

    def get_prescription_by_id(self, prescription_id: int):
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT prescription_id, record_id, medication_name, dosage, frequency, route,
                           duration_days, instructions, prescription_status, is_active,
                           prescribed_at, created_at, updated_at
                    FROM record_prescriptions
                    WHERE prescription_id = :prescription_id
                    """,
                    {"prescription_id": prescription_id},
                )
                return _row_to_dict(cursor.fetchone())

    def list_treatments(self, record_id: int, include_inactive: bool = False):
        sql = """
            SELECT treatment_id, record_id, treatment_name, treatment_description,
                   treatment_date, outcome, notes, is_active, created_at, updated_at
            FROM record_treatments
            WHERE record_id = :record_id
              AND (:include_inactive = 1 OR is_active = 'Y')
            ORDER BY treatment_date DESC, created_at DESC
        """
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, {"record_id": record_id, "include_inactive": 1 if include_inactive else 0})
                return [_row_to_dict(row) for row in cursor.fetchall()]

    def get_treatment_by_id(self, treatment_id: int):
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT treatment_id, record_id, treatment_name, treatment_description,
                           treatment_date, outcome, notes, is_active, created_at, updated_at
                    FROM record_treatments
                    WHERE treatment_id = :treatment_id
                    """,
                    {"treatment_id": treatment_id},
                )
                return _row_to_dict(cursor.fetchone())

    def create_record(
        self,
        *,
        patient_id: int,
        created_by_user_id: int,
        record_type: str,
        title: str,
        clinical_note: str,
        record_status: str,
        encounter_date,
    ) -> int:
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                record_id_var = cursor.var(int)
                cursor.execute(
                    """
                    INSERT INTO medical_records (
                        patient_id, created_by_user_id, record_type, title, clinical_note,
                        record_status, encounter_date, created_at, updated_at
                    ) VALUES (
                        :patient_id, :created_by_user_id, :record_type, :title, :clinical_note,
                        :record_status, :encounter_date, SYSTIMESTAMP, SYSTIMESTAMP
                    )
                    RETURNING record_id INTO :record_id
                    """,
                    {
                        "patient_id": patient_id,
                        "created_by_user_id": created_by_user_id,
                        "record_type": record_type,
                        "title": title,
                        "clinical_note": clinical_note,
                        "record_status": record_status,
                        "encounter_date": encounter_date,
                        "record_id": record_id_var,
                    },
                )
                connection.commit()
                value = record_id_var.getvalue()
                return int(value[0] if isinstance(value, list) else value)

    def update_record(
        self,
        *,
        record_id: int,
        record_type: str,
        title: str,
        clinical_note: str,
        record_status: str,
        encounter_date,
    ) -> None:
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE medical_records
                    SET record_type = :record_type,
                        title = :title,
                        clinical_note = :clinical_note,
                        record_status = :record_status,
                        encounter_date = :encounter_date,
                        updated_at = SYSTIMESTAMP
                    WHERE record_id = :record_id
                    """,
                    {
                        "record_id": record_id,
                        "record_type": record_type,
                        "title": title,
                        "clinical_note": clinical_note,
                        "record_status": record_status,
                        "encounter_date": encounter_date,
                    },
                )
                connection.commit()

    def create_diagnosis(
        self,
        *,
        record_id: int,
        diagnosis_name: str,
        icd10_code: str | None,
        diagnosis_status: str,
        is_primary: str,
        diagnosed_at,
    ) -> int:
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                diagnosis_id_var = cursor.var(int)
                cursor.execute(
                    """
                    INSERT INTO record_diagnoses (
                        record_id, diagnosis_name, icd10_code, diagnosis_status, is_primary,
                        is_active, diagnosed_at, created_at, updated_at
                    ) VALUES (
                        :record_id, :diagnosis_name, :icd10_code, :diagnosis_status, :is_primary,
                        'Y', :diagnosed_at, SYSTIMESTAMP, SYSTIMESTAMP
                    )
                    RETURNING diagnosis_id INTO :diagnosis_id
                    """,
                    {
                        "record_id": record_id,
                        "diagnosis_name": diagnosis_name,
                        "icd10_code": icd10_code,
                        "diagnosis_status": diagnosis_status,
                        "is_primary": is_primary,
                        "diagnosed_at": diagnosed_at,
                        "diagnosis_id": diagnosis_id_var,
                    },
                )
                connection.commit()
                value = diagnosis_id_var.getvalue()
                return int(value[0] if isinstance(value, list) else value)

    def update_diagnosis(
        self,
        *,
        diagnosis_id: int,
        diagnosis_name: str,
        icd10_code: str | None,
        diagnosis_status: str,
        is_primary: str,
        diagnosed_at,
    ) -> None:
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE record_diagnoses
                    SET diagnosis_name = :diagnosis_name,
                        icd10_code = :icd10_code,
                        diagnosis_status = :diagnosis_status,
                        is_primary = :is_primary,
                        diagnosed_at = :diagnosed_at,
                        updated_at = SYSTIMESTAMP
                    WHERE diagnosis_id = :diagnosis_id
                    """,
                    {
                        "diagnosis_id": diagnosis_id,
                        "diagnosis_name": diagnosis_name,
                        "icd10_code": icd10_code,
                        "diagnosis_status": diagnosis_status,
                        "is_primary": is_primary,
                        "diagnosed_at": diagnosed_at,
                    },
                )
                connection.commit()

    def deactivate_diagnosis(self, diagnosis_id: int) -> None:
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE record_diagnoses SET is_active = 'N', updated_at = SYSTIMESTAMP WHERE diagnosis_id = :diagnosis_id",
                    {"diagnosis_id": diagnosis_id},
                )
                connection.commit()

    def create_prescription(
        self,
        *,
        record_id: int,
        medication_name: str,
        dosage: str | None,
        frequency: str | None,
        route: str | None,
        duration_days: int | None,
        instructions: str | None,
        prescribed_at,
    ) -> int:
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                prescription_id_var = cursor.var(int)
                cursor.execute(
                    """
                    INSERT INTO record_prescriptions (
                        record_id, medication_name, dosage, frequency, route, duration_days,
                        instructions, prescription_status, is_active, prescribed_at, created_at, updated_at
                    ) VALUES (
                        :record_id, :medication_name, :dosage, :frequency, :route, :duration_days,
                        :instructions, 'ACTIVE', 'Y', :prescribed_at, SYSTIMESTAMP, SYSTIMESTAMP
                    )
                    RETURNING prescription_id INTO :prescription_id
                    """,
                    {
                        "record_id": record_id,
                        "medication_name": medication_name,
                        "dosage": dosage,
                        "frequency": frequency,
                        "route": route,
                        "duration_days": duration_days,
                        "instructions": instructions,
                        "prescribed_at": prescribed_at,
                        "prescription_id": prescription_id_var,
                    },
                )
                connection.commit()
                value = prescription_id_var.getvalue()
                return int(value[0] if isinstance(value, list) else value)

    def update_prescription(
        self,
        *,
        prescription_id: int,
        medication_name: str,
        dosage: str | None,
        frequency: str | None,
        route: str | None,
        duration_days: int | None,
        instructions: str | None,
        prescription_status: str,
        prescribed_at,
    ) -> None:
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE record_prescriptions
                    SET medication_name = :medication_name,
                        dosage = :dosage,
                        frequency = :frequency,
                        route = :route,
                        duration_days = :duration_days,
                        instructions = :instructions,
                        prescription_status = :prescription_status,
                        prescribed_at = :prescribed_at,
                        updated_at = SYSTIMESTAMP
                    WHERE prescription_id = :prescription_id
                    """,
                    {
                        "prescription_id": prescription_id,
                        "medication_name": medication_name,
                        "dosage": dosage,
                        "frequency": frequency,
                        "route": route,
                        "duration_days": duration_days,
                        "instructions": instructions,
                        "prescription_status": prescription_status,
                        "prescribed_at": prescribed_at,
                    },
                )
                connection.commit()

    def deactivate_prescription(self, prescription_id: int) -> None:
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE record_prescriptions SET is_active = 'N', updated_at = SYSTIMESTAMP WHERE prescription_id = :prescription_id",
                    {"prescription_id": prescription_id},
                )
                connection.commit()

    def create_treatment(
        self,
        *,
        record_id: int,
        treatment_name: str,
        treatment_description: str | None,
        treatment_date,
        outcome: str | None,
        notes: str | None,
    ) -> int:
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                treatment_id_var = cursor.var(int)
                cursor.execute(
                    """
                    INSERT INTO record_treatments (
                        record_id, treatment_name, treatment_description, treatment_date,
                        outcome, notes, is_active, created_at, updated_at
                    ) VALUES (
                        :record_id, :treatment_name, :treatment_description, :treatment_date,
                        :outcome, :notes, 'Y', SYSTIMESTAMP, SYSTIMESTAMP
                    )
                    RETURNING treatment_id INTO :treatment_id
                    """,
                    {
                        "record_id": record_id,
                        "treatment_name": treatment_name,
                        "treatment_description": treatment_description,
                        "treatment_date": treatment_date,
                        "outcome": outcome,
                        "notes": notes,
                        "treatment_id": treatment_id_var,
                    },
                )
                connection.commit()
                value = treatment_id_var.getvalue()
                return int(value[0] if isinstance(value, list) else value)

    def update_treatment(
        self,
        *,
        treatment_id: int,
        treatment_name: str,
        treatment_description: str | None,
        treatment_date,
        outcome: str | None,
        notes: str | None,
    ) -> None:
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE record_treatments
                    SET treatment_name = :treatment_name,
                        treatment_description = :treatment_description,
                        treatment_date = :treatment_date,
                        outcome = :outcome,
                        notes = :notes,
                        updated_at = SYSTIMESTAMP
                    WHERE treatment_id = :treatment_id
                    """,
                    {
                        "treatment_id": treatment_id,
                        "treatment_name": treatment_name,
                        "treatment_description": treatment_description,
                        "treatment_date": treatment_date,
                        "outcome": outcome,
                        "notes": notes,
                    },
                )
                connection.commit()

    def deactivate_treatment(self, treatment_id: int) -> None:
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE record_treatments SET is_active = 'N', updated_at = SYSTIMESTAMP WHERE treatment_id = :treatment_id",
                    {"treatment_id": treatment_id},
                )
                connection.commit()
