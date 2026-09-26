from datetime import datetime
from typing import Optional

from ..models import Application, ApplicationLog


class AuditService:
    """Tracks every meaningful change to an application."""

    def log_change(
        self,
        application: Application,
        field_name: str,
        old_value: Optional[str],
        new_value: Optional[str],
        actor: str = "applicant",
        ip_address: Optional[str] = None,
    ) -> ApplicationLog:
        return ApplicationLog.objects.create(
            application=application,
            field_name=field_name,
            old_value=str(old_value) if old_value is not None else None,
            new_value=str(new_value) if new_value is not None else None,
            actor=actor,
            ip_address=ip_address,
        )

    def get_logs(self, application: Application, limit: int = 50) -> list[ApplicationLog]:
        return list(ApplicationLog.objects.filter(application=application)[:limit])

    def get_recent_activity(self, applicant, limit: int = 20) -> list[ApplicationLog]:
        return list(
            ApplicationLog.objects.filter(application__applicant=applicant)
            .select_related("application")[:limit]
        )
