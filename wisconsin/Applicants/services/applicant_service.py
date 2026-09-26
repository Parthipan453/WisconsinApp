from typing import Optional

from django.db import transaction
from django.db.models import Q
from datetime import date
from decimal import Decimal

from Admin.Colleges.models import University as CollegesUniversity
from Admin.Colleges.models import AcademicProgram, Degree

from ..models import (
    Applicant,
    Application,
    ApplicantProfile,
    AdmissionCycle,
    ProgramRequirement,
    ApplicationChecklistItem,
    ApplicationFee,
    FeePayment,
)
from ..repositories.applicant_repository import ApplicantRepository, ApplicationRepository
from .audit_service import AuditService
from .document_service import DocumentService
from .form_engine import DynamicFormEngine


DEFAULT_APP_FEES = {
    "UW-Madison": "80.00",
    "UW-La Crosse": "25.00",
}
FALLBACK_APP_FEE = "25.00"


class ApplicantService:

    def __init__(self) -> None:
        self.repo = ApplicantRepository()
        self.app_repo = ApplicationRepository()
        self.audit = AuditService()
        self.docs = DocumentService()


    @transaction.atomic
    def register(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        **extra,
    ) -> Optional[Applicant]:
        existing = self.repo.get_by_email(email)
        if existing:
            return None
        applicant = self.repo.create_applicant(
            email, password, first_name, last_name, **extra
        )
        ApplicantProfile.objects.create(applicant=applicant)
        return applicant

    def authenticate(self, email: str, password: str) -> Optional[Applicant]:
        applicant = self.repo.get_by_email(email)
        if applicant and applicant.check_password(password):
            return applicant
        return None

    def get_or_create_profile(self, applicant: Applicant) -> ApplicantProfile:
        profile, _ = ApplicantProfile.objects.get_or_create(applicant=applicant)
        return profile


    @transaction.atomic
    def create_application(
        self,
        applicant: Applicant,
        university_id: int,
        campus_name: str,
        degree_level_id: int,
        program_id: int,
        cycle_id: int,
        applicant_type: str = "first_year",
        backup_program_id: int = None,
    ) -> Application:
        dl = Degree.objects.get(pk=degree_level_id)
        program = AcademicProgram.objects.get(pk=program_id)
        school = program.department.school
        backup_program = None
        if backup_program_id:
            backup_program = AcademicProgram.objects.filter(pk=backup_program_id).first()
        app = self.app_repo.create_application(
            applicant=applicant,
            university=CollegesUniversity.objects.get(pk=university_id),
            campus_name=campus_name or "Main Campus",
            degree_level=dl,
            program=program,
            backup_program=backup_program,
            admission_cycle=AdmissionCycle.objects.get(pk=cycle_id),
            applicant_type=applicant_type,
            school=school,
        )
        self._populate_taxonomy(app, dl, applicant_type)
        self._capture_config_snapshot(app)
        self.audit.log_change(app, "status", None, "in_progress")
        return app

    def _populate_taxonomy(
        self,
        app: Application,
        degree_level: Degree,
        applicant_type: str,
    ) -> None:
        LEVEL_MAP = {
            "UG": "ug",
            "GR": "masters",
            "PG": "masters",
            "PHD": "phd",
        }
        app.admission_level = LEVEL_MAP.get(degree_level.level, "")

        CAT_MAP = {
            "first_year": "first_year",
            "transfer": "transfer",
            "returning": "returning",
            "reentry": "reentry",
            "dual_enrollment": "dual_enrollment",
            "non_degree": "non_degree",
            "international_first_year": "first_year",
            "international_transfer": "transfer",
        }
        app.applicant_category = CAT_MAP.get(applicant_type, "")

        IMM_MAP = {
            "international_first_year": "f1",
            "international_transfer": "f1",
            "f1": "f1",
            "j1": "j1",
            "permanent_resident": "permanent_resident",
            "refugee": "refugee",
            "asylum": "refugee",
            "daca": "daca",
        }
        app.immigration_status = IMM_MAP.get(applicant_type, "us_citizen")
        app.save(
            update_fields=[
                "admission_level",
                "applicant_category",
                "immigration_status",
            ]
        )

    def _capture_config_snapshot(self, app: Application) -> None:
        fe = DynamicFormEngine()
        snapshot = fe.build_snapshot(app)
        if snapshot:
            app.config_snapshot = snapshot
            app.save(update_fields=["config_snapshot"])

    def get_applicant_applications(self, applicant: Applicant) -> list[Application]:
        return self.app_repo.get_applicant_applications(applicant)

    def get_in_progress(self, applicant: Applicant) -> list[Application]:
        return self.app_repo.get_applicant_applications(applicant).filter(
            status__in=["in_progress", "draft"], is_archived=False
        )

    def get_submitted(self, applicant: Applicant) -> list[Application]:
        return (
            self.app_repo.get_applicant_applications(applicant)
            .filter(is_archived=False)
            .exclude(status__in=["in_progress", "draft", "archived"])
        )


    def validate_submission(self, application: Application) -> list[str]:
        errors = []
        deadline_error = self._check_deadline(application)
        if deadline_error:
            errors.append(deadline_error)
        transfer_error = self._check_transfer_credits(application)
        if transfer_error:
            errors.append(transfer_error)
        form_errors = self._check_missing_required_steps(application)
        errors.extend(form_errors)
        return errors

    @staticmethod
    def _check_deadline(application: Application) -> Optional[str]:
        cycle = application.admission_cycle
        if (
            cycle
            and cycle.application_deadline
            and date.today() > cycle.application_deadline
        ):
            return f"The application deadline ({cycle.application_deadline}) has passed."
        return None

    @staticmethod
    def _check_transfer_credits(application: Application) -> Optional[str]:
        if application.applicant_type not in ("transfer", "international_transfer"):
            return None
        try:
            credits = application.transfer_credits_earned
        except AttributeError:
            return None
        if credits is None:
            return "Transfer applicants must specify their transferable credits."
        if credits < 24:
            return (
                f"Transfer applicants need at least 24 transferable credits. "
                f"You have {credits}."
            )
        return None

    @staticmethod
    def _check_missing_required_steps(application: Application) -> list[str]:
        fe = DynamicFormEngine()
        errors = []
        steps = fe.get_active_workflow_steps(application)
        for step in steps:
            if step.is_required and not fe.is_step_complete(application, step.code):
                errors.append(f"Required section '{step.name}' is not complete.")
        return errors

    @transaction.atomic
    def submit_application(
        self,
        application: Application,
        signature: str = "",
        skip_form_check: bool = False,
    ) -> tuple[bool, list[str]]:
        errors = []
        if skip_form_check:
            deadline_error = self._check_deadline(application)
            if deadline_error:
                errors.append(deadline_error)
        else:
            errors = self.validate_submission(application)
        if errors:
            return False, errors
        old = application.status
        if signature:
            application.signature = signature
        fe = DynamicFormEngine()
        snapshot = fe.build_snapshot(application)
        if snapshot:
            application.config_snapshot = snapshot
        self.app_repo.submit(application)
        self._build_checklist(application)
        self.audit.log_change(application, "status", old, "submitted")
        return True, []

    def get_submission_readiness(self, application: Application) -> dict:
        sections_done = []
        sections_missing = []
        fe = DynamicFormEngine()
        steps = fe.get_active_workflow_steps(application)
        for step in steps:
            if step.step_type != "form":
                continue
            complete = fe.is_step_complete(application, step.code)
            if complete:
                sections_done.append(step.name)
            else:
                sections_missing.append(step.name)
        return {
            "sections_done": sections_done,
            "sections_missing": sections_missing,
            "ready": not sections_missing,
        }

    @staticmethod
    def _build_checklist(application: Application) -> None:
        items = []
        is_transfer = application.applicant_type in (
            "transfer",
            "international_transfer",
        )
        if is_transfer:
            items.append(("college_transcript", "College Transcript(s)"))
        else:
            items.append(("high_school_transcript", "High School Transcript"))
        items.append(("essay", "Personal Essay"))
        items.append(("test_scores", "Test Scores (if applicable)"))
        for code, label in items:
            ApplicationChecklistItem.objects.get_or_create(
                application=application,
                code=code,
                defaults={"label": label, "is_required": True},
            )


    def update_status(
        self,
        application: Application,
        new_status: str,
        actor: str = "system",
        note: str = "",
    ) -> None:
        old = application.status
        self.app_repo.update_status(application, new_status, actor, note)
        self.audit.log_change(application, "status", old, new_status)

    def archive_application(self, application: Application) -> None:
        old = application.status
        application.status = "archived"
        application.is_archived = True
        application.save(update_fields=["status", "is_archived", "updated_date"])
        self.audit.log_change(application, "status", old, "archived")

    def search_applications(
        self,
        applicant: Applicant,
        query: str,
    ) -> list[Application]:
        qs = self.get_applicant_applications(applicant).filter(is_archived=False)
        if query:
            qs = qs.filter(
                Q(Reference_id__icontains=query)
                | Q(university__university_name__icontains=query)
                | Q(program__program_name__icontains=query)
            )
        return list(qs)


    def get_active_universities(self) -> list[CollegesUniversity]:
        return list(CollegesUniversity.objects.filter(status="ACTIVE"))

    def get_active_cycles(self) -> list[AdmissionCycle]:
        return list(AdmissionCycle.objects.filter(is_active=True))

    def get_programs_for_university(
        self,
        university_id: int,
        degree_level_id: int = None,
        school_id: int = None,
    ) -> list[AcademicProgram]:
        qs = AcademicProgram.objects.filter(status="ACTIVE")
        if school_id:
            qs = qs.filter(department__school_id=school_id)
        else:
            qs = qs.filter(department__school__university_id=university_id)
        if degree_level_id:
            qs = qs.filter(
                degree__level__iexact=Degree.objects.get(pk=degree_level_id).level,
            )
        return list(qs)

    def get_program_requirements(
        self,
        program: AcademicProgram,
        degree_level: Degree,
    ) -> Optional[ProgramRequirement]:
        return ProgramRequirement.objects.filter(
            program=program, degree_level=degree_level, is_active=True
        ).first()

    def get_missing_items(self, application: Application) -> list:
        fe = DynamicFormEngine()
        missing = []
        steps = fe.get_active_workflow_steps(application)
        for step in steps:
            if step.is_required and not fe.is_step_complete(application, step.code):
                missing.append(step)
        return missing

    def get_dashboard_context(self, applicant: Applicant) -> dict:
        profile = self.get_or_create_profile(applicant)
        submitted = self.get_submitted(applicant)
        for app in submitted:
            app.fee_info = self.get_application_fee_info(app)
        return {
            "applicant": applicant,
            "profile": profile,
            "profile_completion": 100 if profile.profile_completed else 0,
            "in_progress": self.get_in_progress(applicant),
            "submitted": submitted,
            "recent_activity": self.audit.get_recent_activity(applicant, limit=5),
        }


    def get_application_fee_for(self, application: Application) -> Optional[Decimal]:
        """Return the application fee amount for an application's university.

        Fee is driven by the ApplicationFee model (editable in admin). Falls back
        to a default per-campus mapping, then to a flat default. A fee of 0.00
        means the university charges no application fee and returns None.
        """
        amount = self._resolve_fee_amount(application)
        if amount is None:
            return None
        return amount if amount > 0 else None

    def get_application_fee_info(self, application: Application) -> dict:
        """Fee info used by templates: amount, paid state, and human label."""
        amount = self.get_application_fee_for(application)
        paid = application.payments.filter(status="completed").exists()
        pending = application.payments.filter(status="pending").exists()
        return {
            "amount": amount,
            "paid": paid,
            "pending": pending,
            "free": amount is None,
            "label": f"${amount:.2f}" if amount is not None else "No fee",
        }

    def _resolve_fee_amount(self, application: Application) -> Optional[Decimal]:
        try:
            fee = ApplicationFee.objects.filter(university=application.university).first()
            if fee is not None:
                return fee.amount
        except ApplicationFee.DoesNotExist:
            pass
        if application.university_id:
            names = [
                application.university.university_name or "",
                application.university.university_short_name or "",
            ]
            for name in names:
                name = name.strip()
                if name in DEFAULT_APP_FEES:
                    return Decimal(DEFAULT_APP_FEES[name])
        return Decimal(FALLBACK_APP_FEE)
