from __future__ import annotations

from typing import Any

from app.db.oracle import get_connection
from app.repositories.base_repository import BaseRepository


def _row_to_dict(row) -> dict[str, Any] | None:
    if row is None:
        return None
    return {key.lower(): row[key] for key in row.keys()}


class PatientRepository(BaseRepository):
    def list_patients(self, search: str = "", active_only: bool = True):
        sql = """
            SELECT
                p.patient_id,
                p.mrn,
                p.first_name,
                p.last_name,
                p.date_of_birth,
                p.sex,
                p.phone_number,
                p.email,
                p.address_line1,
                p.address_line2,
                p.city,
                p.region,
                p.country,
                p.is_active,
                p.created_at,
                p.updated_at,
                COUNT(DISTINCT mr.record_id) AS record_count,
                COUNT(DISTINCT a.appointment_id) AS appointment_count
            FROM patients p
            LEFT JOIN medical_records mr ON mr.patient_id = p.patient_id
            LEFT JOIN appointments a ON a.patient_id = p.patient_id
            WHERE (
                :search IS NULL
                OR LOWER(p.mrn) LIKE LOWER(:search_like)
                OR LOWER(p.first_name) LIKE LOWER(:search_like)
                OR LOWER(p.last_name) LIKE LOWER(:search_like)
                OR LOWER(p.email) LIKE LOWER(:search_like)
                OR LOWER(p.phone_number) LIKE LOWER(:search_like)
            )
            AND (:active_only = 0 OR p.is_active = 'Y')
            GROUP BY
                p.patient_id,
                p.mrn,
                p.first_name,
                p.last_name,
                p.date_of_birth,
                p.sex,
                p.phone_number,
                p.email,
                p.address_line1,
                p.address_line2,
                p.city,
                p.region,
                p.country,
                p.is_active,
                p.created_at,
                p.updated_at
            ORDER BY p.last_name, p.first_name
        """
        search_like = f"%{search.strip()}%" if search.strip() else None
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    sql,
                    {
                        "search": search.strip() or None,
                        "search_like": search_like,
                        "active_only": 1 if active_only else 0,
                    },
                )
                return [_row_to_dict(row) for row in cursor.fetchall()]

    def get_patient_by_id(self, patient_id: int):
        sql = """
            SELECT
                p.patient_id,
                p.mrn,
                p.first_name,
                p.last_name,
                p.date_of_birth,
                p.sex,
                p.phone_number,
                p.email,
                p.address_line1,
                p.address_line2,
                p.city,
                p.region,
                p.country,
                p.is_active,
                p.created_at,
                p.updated_at,
                COUNT(DISTINCT mr.record_id) AS record_count,
                COUNT(DISTINCT a.appointment_id) AS appointment_count
            FROM patients p
            LEFT JOIN medical_records mr ON mr.patient_id = p.patient_id
            LEFT JOIN appointments a ON a.patient_id = p.patient_id
            WHERE p.patient_id = :patient_id
            GROUP BY
                p.patient_id,
                p.mrn,
                p.first_name,
                p.last_name,
                p.date_of_birth,
                p.sex,
                p.phone_number,
                p.email,
                p.address_line1,
                p.address_line2,
                p.city,
                p.region,
                p.country,
                p.is_active,
                p.created_at,
                p.updated_at
        """
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, {"patient_id": patient_id})
                return _row_to_dict(cursor.fetchone())

    def create_patient(
        self,
        *,
        mrn: str,
        first_name: str,
        last_name: str,
        date_of_birth,
        sex: str,
        phone_number: str | None,
        email: str | None,
        address_line1: str | None,
        address_line2: str | None,
        city: str | None,
        region: str | None,
        country: str,
    ) -> int:
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                patient_id_var = cursor.var(int)
                cursor.execute(
                    """
                    INSERT INTO patients (
                        mrn, first_name, last_name, date_of_birth, sex, phone_number, email,
                        address_line1, address_line2, city, region, country, is_active, created_at, updated_at
                    ) VALUES (
                        :mrn, :first_name, :last_name, :date_of_birth, :sex, :phone_number, :email,
                        :address_line1, :address_line2, :city, :region, :country, 'Y', SYSTIMESTAMP, SYSTIMESTAMP
                    )
                    RETURNING patient_id INTO :patient_id
                    """,
                    {
                        "mrn": mrn,
                        "first_name": first_name,
                        "last_name": last_name,
                        "date_of_birth": date_of_birth,
                        "sex": sex,
                        "phone_number": phone_number,
                        "email": email,
                        "address_line1": address_line1,
                        "address_line2": address_line2,
                        "city": city,
                        "region": region,
                        "country": country,
                        "patient_id": patient_id_var,
                    },
                )
                value = patient_id_var.getvalue()
                return int(value[0] if isinstance(value, list) else value)

    def update_patient(
        self,
        *,
        patient_id: int,
        mrn: str,
        first_name: str,
        last_name: str,
        date_of_birth,
        sex: str,
        phone_number: str | None,
        email: str | None,
        address_line1: str | None,
        address_line2: str | None,
        city: str | None,
        region: str | None,
        country: str,
        is_active: str,
    ) -> None:
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE patients
                    SET
                        mrn = :mrn,
                        first_name = :first_name,
                        last_name = :last_name,
                        date_of_birth = :date_of_birth,
                        sex = :sex,
                        phone_number = :phone_number,
                        email = :email,
                        address_line1 = :address_line1,
                        address_line2 = :address_line2,
                        city = :city,
                        region = :region,
                        country = :country,
                        is_active = :is_active,
                        updated_at = SYSTIMESTAMP
                    WHERE patient_id = :patient_id
                    """,
                    {
                        "patient_id": patient_id,
                        "mrn": mrn,
                        "first_name": first_name,
                        "last_name": last_name,
                        "date_of_birth": date_of_birth,
                        "sex": sex,
                        "phone_number": phone_number,
                        "email": email,
                        "address_line1": address_line1,
                        "address_line2": address_line2,
                        "city": city,
                        "region": region,
                        "country": country,
                        "is_active": is_active,
                    },
                )

    def deactivate_patient(self, patient_id: int) -> None:
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE patients SET is_active = 'N', updated_at = SYSTIMESTAMP WHERE patient_id = :patient_id",
                    {"patient_id": patient_id},
                )

    def patient_exists(self, mrn: str, exclude_patient_id: int | None = None) -> bool:
        sql = "SELECT 1 FROM patients WHERE mrn = :mrn"
        params = {"mrn": mrn}
        if exclude_patient_id is not None:
            sql += " AND patient_id != :exclude_patient_id"
            params["exclude_patient_id"] = exclude_patient_id
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                return cursor.fetchone() is not None
