from flask import current_app

from app.repositories.audit_repository import AuditRepository
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.dashboard_repository import DashboardRepository
from app.repositories.medical_record_repository import MedicalRecordRepository
from app.repositories.patient_repository import PatientRepository
from app.repositories.user_repository import UserRepository
from app.services.audit_service import AuditService
from app.services.appointment_service import AppointmentService
from app.services.auth_service import AuthService
from app.services.dashboard_service import DashboardService
from app.services.medical_record_service import MedicalRecordService
from app.services.patient_service import PatientService


class DatabaseExtension:
    def __init__(self) -> None:
        self.pool = None

    def init_app(self, app) -> None:
        from app.db.postgres import create_pool

        self.pool = create_pool(app.config["POSTGRES"])
        app.extensions["postgres_pool"] = self.pool


db = DatabaseExtension()


def get_pool():
    return current_app.extensions["postgres_pool"]


def get_user_repository() -> UserRepository:
    return UserRepository(get_pool())


def get_auth_service() -> AuthService:
    return AuthService(get_user_repository())


def get_audit_repository() -> AuditRepository:
    return AuditRepository(get_pool())


def get_audit_service() -> AuditService:
    return AuditService(get_audit_repository())


def get_dashboard_repository() -> DashboardRepository:
    return DashboardRepository(get_pool())


def get_dashboard_service() -> DashboardService:
    return DashboardService(get_dashboard_repository())


def get_patient_repository() -> PatientRepository:
    return PatientRepository(get_pool())


def get_patient_service() -> PatientService:
    return PatientService(get_patient_repository())


def get_medical_record_repository() -> MedicalRecordRepository:
    return MedicalRecordRepository(get_pool())


def get_medical_record_service() -> MedicalRecordService:
    return MedicalRecordService(get_medical_record_repository(), get_patient_repository())


def get_appointment_repository() -> AppointmentRepository:
    return AppointmentRepository(get_pool())


def get_appointment_service() -> AppointmentService:
    return AppointmentService(get_appointment_repository(), get_patient_repository())
