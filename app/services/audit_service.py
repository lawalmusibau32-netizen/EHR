from __future__ import annotations

from app.repositories.audit_repository import AuditRepository


class AuditService:
    def __init__(self, audit_repository: AuditRepository) -> None:
        self.audit_repository = audit_repository

    def log(self, *, user_id: int | None, action_type: str, entity_name: str, entity_id: str, details: str | None, ip_address: str | None) -> None:
        self.audit_repository.create_log(
            user_id=user_id,
            action_type=action_type,
            entity_name=entity_name,
            entity_id=entity_id,
            details=details,
            ip_address=ip_address,
        )

    def list_logs(self, *, action_type: str | None = None, search: str = ""):
        return self.audit_repository.list_logs(action_type=action_type, search=search)

    def action_summary(self):
        return self.audit_repository.count_by_action()

    def recent_security_events(self):
        return self.audit_repository.recent_security_events()

    def locked_accounts(self):
        return self.audit_repository.locked_accounts()
