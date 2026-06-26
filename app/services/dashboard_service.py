from __future__ import annotations

from app.repositories.dashboard_repository import DashboardRepository


class DashboardService:
    def __init__(self, dashboard_repository: DashboardRepository) -> None:
        self.dashboard_repository = dashboard_repository

    def for_role(self, role_key: str):
        return {
            "stats": self.dashboard_repository.dashboard_stats(role_key),
            "notifications": self.dashboard_repository.notifications(role_key),
            "recent_activity": self.dashboard_repository.recent_activity(),
        }
