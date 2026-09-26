from typing import Optional

from django.db.models import QuerySet

from ..models import (
    Applicant,
    Application,
    ApplicationTimeline,
    ApplicationStatusHistory,
)


class ApplicantRepository:
    """Data-access layer for the Applicant model."""

    def get_by_id(self, pk: int) -> Optional[Applicant]:
        try:
            return Applicant.objects.get(pk=pk)
        except Applicant.DoesNotExist:
            return None

    def get_by_email(self, email: str) -> Optional[Applicant]:
        try:
            return Applicant.objects.get(email=email)
        except Applicant.DoesNotExist:
            return None

    def create_applicant(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        **extra,
    ) -> Applicant:
        applicant = Applicant(
            email=email,
            first_name=first_name,
            last_name=last_name,
            **extra,
        )
        applicant.set_password(password)
        applicant.save()
        return applicant

    def verify_email(self, applicant: Applicant) -> None:
        applicant.email_verified = True
        applicant.save(update_fields=["email_verified"])


class ApplicationRepository:
    """Data-access layer for the Application model."""

    def get_by_id(self, pk: int) -> Optional[Application]:
        try:
            return Application.objects.select_related(
                "university", "degree_level", "program", "admission_cycle"
            ).get(pk=pk)
        except Application.DoesNotExist:
            return None

    def get_by_reference(self, ref: str) -> Optional[Application]:
        try:
            return Application.objects.get(Reference_id=ref)
        except Application.DoesNotExist:
            return None

    def get_applicant_applications(
        self,
        applicant: Applicant,
        status: Optional[str] = None,
    ) -> QuerySet:
        qs = Application.objects.filter(applicant=applicant).select_related(
            "university", "degree_level", "program", "admission_cycle"
        )
        if status:
            qs = qs.filter(status=status)
        return qs

    def create_application(
        self,
        applicant: Applicant,
        university,
        campus_name: str,
        degree_level,
        program,
        admission_cycle,
        applicant_type: str = "first_year",
        school=None,
        backup_program=None,
    ) -> Application:
        app = Application(
            applicant=applicant,
            university=university,
            campus_name=campus_name,
            degree_level=degree_level,
            program=program,
            backup_program=backup_program,
            admission_cycle=admission_cycle,
            applicant_type=applicant_type or "first_year",
            school=school,
            status="in_progress",
        )
        app.save()

        ApplicationStatusHistory.objects.create(
            application=app,
            from_status="",
            to_status="in_progress",
            changed_by="system",
            note="Application created",
        )

        ApplicationTimeline.objects.create(
            application=app,
            event_type="created",
            title="Application Created",
            description=f"Application {app.Reference_id} was created",
            event_date=app.created_date,
            is_automated=True,
        )

        return app

    def update_status(
        self,
        application: Application,
        status: str,
        actor: str = "system",
        note: str = "",
    ) -> None:
        old_status = application.status
        application.status = status
        application.save(update_fields=["status", "updated_date"])

        ApplicationStatusHistory.objects.create(
            application=application,
            from_status=old_status,
            to_status=status,
            changed_by=actor,
            note=note,
        )

        ApplicationTimeline.objects.create(
            application=application,
            event_type="status_change",
            title=f"Status changed to {status}",
            description=note or f"Status changed from {old_status} to {status}",
            event_date=application.updated_date,
            is_automated=True,
        )

    def submit(self, application: Application) -> None:
        from django.utils import timezone

        old_status = application.status
        application.status = "submitted"
        application.submitted_date = timezone.now()
        application.progress_pct = 100
        application.save(
            update_fields=[
                "status",
                "submitted_date",
                "progress_pct",
                "signature",
                "updated_date",
            ]
        )

        ApplicationStatusHistory.objects.create(
            application=application,
            from_status=old_status,
            to_status="submitted",
            changed_by="applicant",
            note="Application submitted by applicant",
        )

        ApplicationTimeline.objects.create(
            application=application,
            event_type="submitted",
            title="Application Submitted",
            description=f"Application {application.Reference_id} was submitted",
            event_date=application.submitted_date,
            is_automated=True,
        )
