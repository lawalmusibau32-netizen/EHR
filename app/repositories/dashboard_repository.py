from __future__ import annotations

from typing import Any

from app.db.oracle import get_connection
from app.repositories.base_repository import BaseRepository


def _row_to_dict(row) -> dict[str, Any] | None:
    if row is None:
        return None
    return {key.lower(): row[key] for key in row.keys()}


class DashboardRepository(BaseRepository):
    def scalar(self, sql: str, params: dict | None = None) -> int:
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, params or {})
                row = cursor.fetchone()
                return int(row[0] if row else 0)

    def recent_activity(self, limit: int = 6):
        sql = """
            SELECT *
            FROM (
                SELECT al.action_type, al.entity_name, al.entity_id,
                       DBMS_LOB.SUBSTR(al.details, 4000, 1) AS details,
                       al.created_at, u.display_name
                FROM audit_logs al
                LEFT JOIN users u ON u.user_id = al.user_id
                ORDER BY al.created_at DESC
            )
            WHERE ROWNUM <= :limit
        """
        with get_connection(self.pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, {"limit": limit})
                return [_row_to_dict(row) for row in cursor.fetchall()]

    def notifications(self, role_key: str):
        data = []
        cancelled = self.scalar("SELECT COUNT(1) FROM appointments WHERE status = 'CANCELLED'")
        failed = self.scalar("SELECT COUNT(1) FROM audit_logs WHERE action_type = 'LOGIN_FAILED'")
        if role_key == "administrator" and failed:
            data.append({"tone": "warning", "title": "Failed login activity", "message": f"{failed} failed login events need review."})
        if role_key in {"administrator", "receptionist"} and cancelled:
            data.append({"tone": "info", "title": "Cancelled appointments", "message": f"{cancelled} appointments are currently cancelled."})
        if not data:
            data.append({"tone": "success", "title": "Workspace stable", "message": "No urgent notifications right now."})
        return data

    def dashboard_stats(self, role_key: str):
        if role_key == "administrator":
            return [
                {"label": "Active Users", "value": self.scalar("SELECT COUNT(1) FROM users WHERE is_active = 'Y'"), "tone": "primary"},
                {"label": "Patients", "value": self.scalar("SELECT COUNT(1) FROM patients WHERE is_active = 'Y'"), "tone": "success"},
                {"label": "Audit Events", "value": self.scalar("SELECT COUNT(1) FROM audit_logs"), "tone": "info"},
                {"label": "Failed Logins", "value": self.scalar("SELECT COUNT(1) FROM audit_logs WHERE action_type = 'LOGIN_FAILED'"), "tone": "warning"},
            ]
        if role_key == "doctor":
            return [
                {"label": "Appointments", "value": self.scalar("SELECT COUNT(1) FROM appointments WHERE clinician_user_id IS NOT NULL AND status IN ('SCHEDULED','CHECKED_IN')"), "tone": "primary"},
                {"label": "Records", "value": self.scalar("SELECT COUNT(1) FROM medical_records"), "tone": "success"},
                {"label": "Active Patients", "value": self.scalar("SELECT COUNT(1) FROM patients WHERE is_active = 'Y'"), "tone": "info"},
                {"label": "Unsigned Notes", "value": self.scalar("SELECT COUNT(1) FROM medical_records WHERE record_status = 'ACTIVE'"), "tone": "warning"},
            ]
        if role_key == "nurse":
            return [
                {"label": "Checked In", "value": self.scalar("SELECT COUNT(1) FROM appointments WHERE status = 'CHECKED_IN'"), "tone": "success"},
                {"label": "Scheduled", "value": self.scalar("SELECT COUNT(1) FROM appointments WHERE status = 'SCHEDULED'"), "tone": "primary"},
                {"label": "Active Patients", "value": self.scalar("SELECT COUNT(1) FROM patients WHERE is_active = 'Y'"), "tone": "info"},
                {"label": "No Shows", "value": self.scalar("SELECT COUNT(1) FROM appointments WHERE status = 'NO_SHOW'"), "tone": "warning"},
            ]
        return [
            {"label": "Scheduled Visits", "value": self.scalar("SELECT COUNT(1) FROM appointments WHERE status = 'SCHEDULED'"), "tone": "primary"},
            {"label": "Checked In", "value": self.scalar("SELECT COUNT(1) FROM appointments WHERE status = 'CHECKED_IN'"), "tone": "success"},
            {"label": "Patients", "value": self.scalar("SELECT COUNT(1) FROM patients WHERE is_active = 'Y'"), "tone": "info"},
            {"label": "Cancelled", "value": self.scalar("SELECT COUNT(1) FROM appointments WHERE status = 'CANCELLED'"), "tone": "warning"},
        ]
