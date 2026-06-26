from __future__ import annotations

from typing import Any

from app.db.postgres import get_connection
from app.repositories.base_repository import BaseRepository


def _row_to_dict(row) -> dict[str, Any] | None:
    if row is None:
        return None
    return {key.lower(): row[key] for key in row.keys()}


class AppointmentRepository(BaseRepository):
    def list_appointments(self, *, search: str = "", status: str | None = None, patient_id: int | None = None):
        sql = """
            SELECT
                a.appointment_id,
                a.patient_id,
                a.scheduled_by_user_id,
                a.clinician_user_id,
                a.appointment_date,
                a.appointment_type,
                a.status,
                a.reason,
                a.location,
                DBMS_LOB.SUBSTR(a.notes, 4000, 1) AS notes,
                a.created_at,
                a.updated_at,
                p.mrn,
                p.first_name AS patient_first_name,
                p.last_name AS patient_last_name,
                p.phone_number AS patient_phone_number,
                scheduler.display_name AS scheduled_by_name,
                clinician.display_name AS clinician_name
            FROM appointments a
            JOIN patients p ON p.patient_id = a.patient_id
            JOIN users scheduler ON scheduler.user_id = a.scheduled_by_user_id
            LEFT JOIN users clinician ON clinician.user_id = a.clinician_user_id
            WHERE (:status IS NULL OR a.status = :status)
              AND (:patient_id IS NULL OR a.patient_id = :patient_id)
              AND (
                :search IS NULL
                OR LOWER(p.mrn) LIKE LOWER(:search_like)
                OR LOWER(p.first_name) LIKE LOWER(:search_like)
                OR LOWER(p.last_name) LIKE LOWER(:search_like)
                OR LOWER(a.appointment_type) LIKE LOWER(:search_like)
                OR LOWER(NVL(a.reason, ' ')) LIKE LOWER(:search_like)
                OR LOWER(NVL(a.location, ' ')) LIKE LOWER(:search_like)
                OR LOWER(NVL(clinician.display_name, ' ')) LIKE LOWER(:search_like)
              )
            ORDER BY a.appointment_date DESC, a.created_at DESC
        """
        search_value = search.strip()
        search_like = f"%{search_value}%" if search_value else None
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    sql,
                    {
                        "search": search_value or None,
                        "search_like": search_like,
                        "status": status,
                        "patient_id": patient_id,
                    },
                )
                return [_row_to_dict(row) for row in cursor.fetchall()]

    def get_appointment_by_id(self, appointment_id: int):
        sql = """
            SELECT
                a.appointment_id,
                a.patient_id,
                a.scheduled_by_user_id,
                a.clinician_user_id,
                a.appointment_date,
                a.appointment_type,
                a.status,
                a.reason,
                a.location,
                DBMS_LOB.SUBSTR(a.notes, 4000, 1) AS notes,
                a.created_at,
                a.updated_at,
                p.mrn,
                p.first_name AS patient_first_name,
                p.last_name AS patient_last_name,
                p.phone_number AS patient_phone_number,
                p.email AS patient_email,
                scheduler.display_name AS scheduled_by_name,
                clinician.display_name AS clinician_name
            FROM appointments a
            JOIN patients p ON p.patient_id = a.patient_id
            JOIN users scheduler ON scheduler.user_id = a.scheduled_by_user_id
            LEFT JOIN users clinician ON clinician.user_id = a.clinician_user_id
            WHERE a.appointment_id = :appointment_id
        """
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, {"appointment_id": appointment_id})
                return _row_to_dict(cursor.fetchone())

    def list_active_patients(self):
        sql = """
            SELECT patient_id, mrn, first_name, last_name
            FROM patients
            WHERE is_active = 'Y'
            ORDER BY last_name, first_name
        """
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql)
                return [_row_to_dict(row) for row in cursor.fetchall()]

    def list_clinicians(self):
        sql = """
            SELECT u.user_id, u.display_name, u.username, r.role_name
            FROM users u
            JOIN roles r ON r.role_id = u.role_id
            WHERE u.is_active = 'Y'
              AND LOWER(r.role_name) IN ('doctor', 'administrator')
            ORDER BY r.role_name, u.display_name
        """
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql)
                return [_row_to_dict(row) for row in cursor.fetchall()]

    def clinician_exists(self, user_id: int) -> bool:
        sql = """
            SELECT 1
            FROM users u
            JOIN roles r ON r.role_id = u.role_id
            WHERE u.user_id = :user_id
              AND u.is_active = 'Y'
              AND LOWER(r.role_name) IN ('doctor', 'administrator')
        """
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, {"user_id": user_id})
                return cursor.fetchone() is not None

    def create_appointment(
        self,
        *,
        patient_id: int,
        scheduled_by_user_id: int,
        clinician_user_id: int | None,
        appointment_date,
        appointment_type: str,
        status: str,
        reason: str | None,
        location: str | None,
        notes: str | None,
    ) -> int:
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO appointments (
                        patient_id, scheduled_by_user_id, clinician_user_id, appointment_date,
                        appointment_type, status, reason, location, notes, created_at, updated_at
                    ) VALUES (
                        :patient_id, :scheduled_by_user_id, :clinician_user_id, :appointment_date,
                        :appointment_type, :status, :reason, :location, :notes, SYSTIMESTAMP, SYSTIMESTAMP
                    )
                    RETURNING appointment_id
                    """,
                    {
                        "patient_id": patient_id,
                        "scheduled_by_user_id": scheduled_by_user_id,
                        "clinician_user_id": clinician_user_id,
                        "appointment_date": appointment_date,
                        "appointment_type": appointment_type,
                        "status": status,
                        "reason": reason,
                        "location": location,
                        "notes": notes,
                    },
                )
                row = cursor.fetchone()
                connection.commit()
                return int(row["appointment_id"])

    def update_appointment(
        self,
        *,
        appointment_id: int,
        patient_id: int,
        clinician_user_id: int | None,
        appointment_date,
        appointment_type: str,
        status: str,
        reason: str | None,
        location: str | None,
        notes: str | None,
    ) -> None:
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE appointments
                    SET patient_id = :patient_id,
                        clinician_user_id = :clinician_user_id,
                        appointment_date = :appointment_date,
                        appointment_type = :appointment_type,
                        status = :status,
                        reason = :reason,
                        location = :location,
                        notes = :notes,
                        updated_at = SYSTIMESTAMP
                    WHERE appointment_id = :appointment_id
                    """,
                    {
                        "appointment_id": appointment_id,
                        "patient_id": patient_id,
                        "clinician_user_id": clinician_user_id,
                        "appointment_date": appointment_date,
                        "appointment_type": appointment_type,
                        "status": status,
                        "reason": reason,
                        "location": location,
                        "notes": notes,
                    },
                )
                connection.commit()

    def cancel_appointment(self, appointment_id: int, notes: str | None = None) -> None:
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE appointments
                    SET status = 'CANCELLED',
                        notes = CASE
                            WHEN :notes IS NULL THEN notes
                            WHEN notes IS NULL THEN :notes
                            ELSE notes || CHR(10) || :notes
                        END,
                        updated_at = SYSTIMESTAMP
                    WHERE appointment_id = :appointment_id
                    """,
                    {"appointment_id": appointment_id, "notes": notes},
                )
                connection.commit()
