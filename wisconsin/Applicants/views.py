import os
import re
import uuid
import logging
from typing import Optional

from django.conf import settings
from urllib.parse import quote as url_quote
from django.contrib import messages
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from Admin.Colleges.models import University as CollegesUniversity
from Admin.Colleges.models import AcademicProgram, Degree, School

from .models import (
    Applicant,
    Application,
    AdmissionCycle,
    ApplicantTypeRequirement,
    Document,
    DocumentRequirement,
    MaterialRequest,
    ApplicationLog,
    FormResponse,
    FormSection,
    FieldResponse,
    StateProvince,
    City,
    ValidationRule,
    ApplicantProfile,
    FeePayment,
)
from .services.applicant_service import ApplicantService
from .services.email_service import ApplicantEmailService
from .services.application_pdf_service import ApplicationPdfService
from .services.form_engine import DynamicFormEngine
from .services.review_context import (
    get_review_readiness,
    fulfill_completed_material_requests,
)
from .services.stripe_service import (
    create_checkout_session,
    verify_webhook_event,
    StripePaymentError,
)
from notifications.utils import notify_application, notify_applicant, notify_all_admins
from .forms import LoginForm, RegisterForm, DynamicForm


SERVICE = ApplicantService()
EMAIL_SERVICE = ApplicantEmailService()
PDF_SERVICE = ApplicationPdfService()


def _notify_submitted(app):
    """In-app notifications when an application is successfully submitted.

    Notifies every admissions admin so the queue appears immediately, and
    gives the applicant confirmation on their dashboard bell.
    """
    applicant_name = f"{app.applicant.first_name} {app.applicant.last_name}".strip()
    notify_all_admins(
        "New application submitted",
        f"{applicant_name or 'An applicant'} submitted {app.Reference_id} for admission.",
        "INFO",
        link=f"/dashboard/applications/{app.application_id}/",
    )
    notify_applicant(
        app.applicant,
        f"Application {app.Reference_id} submitted",
        "Your application has been submitted successfully and is now under review.",
        "SUCCESS",
        link=f"/applicants/?state=status&app_id={app.application_id}&uuid={app.applicant.uuid}",
    )

logger = logging.getLogger(__name__)


# ─── Helpers ───────────────────────────────────────────────────────────


def _login_applicant(request: HttpRequest, applicant: Applicant) -> None:
    request.session["applicant_id"] = applicant.pk
    request.session["applicant_email"] = applicant.email


def _require_applicant(view):
    def wrapper(request, *args, **kwargs):
        applicant_id = request.session.get("applicant_id")
        if not applicant_id:
            return redirect(".")
        applicant = SERVICE.repo.get_by_id(applicant_id)
        if not applicant:
            return redirect(".")
        return view(request, applicant, *args, **kwargs)
    return wrapper


def _get_app_or_404(applicant: Applicant, app_id: str) -> Application:
    return get_object_or_404(
        Application, pk=app_id, applicant=applicant, is_archived=False
    )


def _first_step_url(app: Application) -> str:
    engine = DynamicFormEngine()
    steps = engine.get_active_workflow_steps(app)
    for s in steps or []:
        if s.step_type == "form" and _section_visible_for_step(app, engine, s):
            return f"/applicants/?state=info&app_id={app.application_id}&uuid={app.applicant.uuid}&step={s.code}"
    return f"/applicants/?state=dashboard&app_id={app.application_id}&uuid={app.applicant.uuid}"


def _section_visible_for_step(
    app: Application, engine: DynamicFormEngine, step
) -> bool:
    """A form workflow step is reachable when its section exists and is assigned
    to the application's scope (or has no section-level assignments)."""
    section = FormSection.objects.filter(code=step.code, is_active=True).first()
    if not section:
        return True
    return engine.is_section_allowed(app, section)


def _next_step_url(app: Application, code: str) -> str:
    engine = DynamicFormEngine()
    steps = engine.get_active_workflow_steps(app)
    if not steps:
        return f"/applicants/?state=dashboard&app_id={app.application_id}&uuid={app.applicant.uuid}"

    form_steps = [s for s in steps if s.step_type == "form"]
    form_steps = [s for s in form_steps if _section_visible_for_step(app, engine, s)]
    codes = [s.code for s in form_steps]

    try:
        current_index = codes.index(code)
    except ValueError:
        return f"/applicants/?state=dashboard&app_id={app.application_id}&uuid={app.applicant.uuid}"

    if current_index + 1 < len(codes):
        next_code = codes[current_index + 1]
        return f"/applicants/?state=info&app_id={app.application_id}&uuid={app.applicant.uuid}&step={next_code}"
    return f"/applicants/?state=dashboard&app_id={app.application_id}&uuid={app.applicant.uuid}"


def _prev_step_url(app: Application, code: str) -> Optional[str]:
    engine = DynamicFormEngine()
    steps = engine.get_active_workflow_steps(app)
    if not steps:
        return f"/applicants/?state=dashboard&app_id={app.application_id}&uuid={app.applicant.uuid}"

    form_steps = [s for s in steps if s.step_type == "form"]
    form_steps = [s for s in form_steps if _section_visible_for_step(app, engine, s)]
    codes = [s.code for s in form_steps]

    try:
        current_index = codes.index(code)
    except ValueError:
        return None

    if current_index > 0:
        prev_code = codes[current_index - 1]
        return f"/applicants/?state=info&app_id={app.application_id}&uuid={app.applicant.uuid}&step={prev_code}"
    return None


def _build_step_statuses(
    app: Application,
    engine: DynamicFormEngine,
) -> list[dict]:
    steps = engine.get_active_workflow_steps(app)
    form_steps = (
        [s for s in steps if s.step_type == "form"] if steps else []
    )
    form_steps = [
        s for s in form_steps if _section_visible_for_step(app, engine, s)
    ]
    statuses = []
    complete_list = [
        engine.is_step_complete(app, s.code) for s in form_steps
    ]
    for i, s in enumerate(form_steps):
        statuses.append(
            {
                "step": s,
                "is_complete": complete_list[i],
                "is_locked": False,
            }
        )
    return statuses


SUBMITTED_STATUSES = ("submitted", "awaiting_materials", "complete", "under_review")


def _is_locked(app: Application) -> bool:
    """A submitted application is locked: no form edits, no form-path nav."""
    return app.status in SUBMITTED_STATUSES


# ─── Form Auth Handlers ────────────────────────────────────────────────


def _handle_logout(request: HttpRequest) -> Optional[HttpResponse]:
    if "logout" in request.GET:
        request.session.pop("applicant_id", None)
        request.session.pop("applicant_email", None)
        return redirect(".")
    return None


def _handle_auth(request: HttpRequest) -> HttpResponse:
    redirect_response = _handle_logout(request)
    if redirect_response:
        return redirect_response

    auth_mode = request.GET.get("auth", "home")
    form_class = _get_auth_form_class(auth_mode)

    if request.method == "POST" and form_class:
        form = form_class(request.POST)
        if form.is_valid():
            result = _process_auth_form(request, auth_mode, form)
            if result:
                return result
    else:
        form = form_class() if form_class else None

    return render(request, "Applicants/portal_body.html", {
        "view_mode": "auth",
        "auth_mode": auth_mode,
        "form": form,
    })


def _get_auth_form_class(auth_mode: str):
    if auth_mode == "login":
        return LoginForm
    if auth_mode == "register":
        return RegisterForm
    return None


def _process_auth_form(
    request: HttpRequest,
    auth_mode: str,
    form,
) -> Optional[HttpResponse]:
    if auth_mode == "login":
        email = form.cleaned_data["email"].strip().lower()
        password = form.cleaned_data["password"]
        applicant = SERVICE.authenticate(email, password)
        if applicant:
            _login_applicant(request, applicant)
            return redirect(".")
        messages.error(request, "Invalid email or password.")

    elif auth_mode == "register":
        email = form.cleaned_data["email"].strip().lower()
        password = form.cleaned_data["password"]
        first_name = form.cleaned_data["first_name"]
        last_name = form.cleaned_data["last_name"]
        mobile = _build_mobile_number(request)

        applicant = SERVICE.register(
            email, password, first_name, last_name, mobile_number=mobile
        )
        if applicant:
            login_url = request.build_absolute_uri(
                f"{reverse('applicants_home')}?auth=login"
            )
            EMAIL_SERVICE.send_account_created_email(applicant, login_url)
            messages.success(
                request,
                "Account created. We sent a confirmation email; please sign in.",
            )
            return redirect("./?auth=login")
        messages.error(request, "An account with this email already exists.")
    return None


def _build_mobile_number(request: HttpRequest) -> str:
    country_code = request.POST.get("country_code", "")
    phone = (
        request.POST.get("phone", "")
        .replace("-", "")
        .replace(" ", "")
        .replace("(", "")
        .replace(")", "")
    )
    if phone and not phone.isdigit():
        return ""
    return country_code + phone if phone else ""


# ─── Portal State Handlers ─────────────────────────────────────────────


def _handle_hub(request, applicant, ctx: dict) -> None:
    online = []
    offline = []
    for app in ctx.get("in_progress") or []:
        app.first_step_url = _first_step_url(app)
        if app.apply_method == "offline":
            offline.append(app)
        else:
            online.append(app)
    ctx["in_progress"] = online
    ctx["offline_apps"] = offline
    ctx["is_enrolled"] = Application.objects.filter(
        applicant=applicant, status__in=("enrolled", "offer_accepted")
    ).exists()


def _document_type_for_requirement(requirement) -> str:
    """Map a DocumentRequirement to the closest Document.doc_type."""
    code = (requirement.code or "").lower()
    if "transcript" in code:
        return "transcript"
    if "essay" in code or "writing" in code:
        return "essay"
    if "test" in code or "act" in code or "sat" in code:
        return "test_score"
    if "resume" in code or "cv" in code or "curriculum" in code:
        return "resume"
    if "id" in code or "passport" in code:
        return "id_proof"
    if "financial" in code or "bank" in code:
        return "financial"
    if "portfolio" in code:
        return "portfolio"
    if "sop" in code or "statement" in code or "purpose" in code:
        return "sop"
    return "other"


def _applicable_requirements(application) -> list[dict]:
    """Required documents for this application with their upload state."""
    items = []
    for req in DocumentRequirement.objects.filter(
        is_required=True, is_active=True
    ).order_by("sort_order", "name"):
        if req.university_id not in (None, application.university_id):
            continue
        if req.degree_level_id not in (None, application.degree_level_id):
            continue
        items.append(
            {
                "requirement": req,
                "uploaded": application.documents.filter(requirement=req).first(),
            }
        )
    return items


def _handle_status(
    request: HttpRequest,
    applicant: Applicant,
    ctx: dict,
) -> Optional[HttpResponse]:
    """Application status page: what staff requested and where to upload it."""
    app = _get_app_or_404(applicant, request.GET.get("app_id"))
    if app.status in ("draft", "in_progress"):
        return redirect(_portal_url("dashboard", app.application_id, request))

    fulfill_completed_material_requests(app)
    ctx["app"] = app
    ctx["fee_info"] = fee_info = SERVICE.get_application_fee_info(app)
    ctx["status_history"] = app.status_history.all()
    ctx["activity_logs"] = app.logs.all()[:50]
    ctx["status_labels"] = dict(Application.STATUS_CHOICES)
    ctx["requirements_status"] = _applicable_requirements(app)
    ctx["material_requests"] = app.material_requests.select_related(
        "requirement", "requested_by"
    ).order_by("-requested_at")
    ctx["correction_requests"] = (
        app.field_correction_requests.prefetch_related(
            "field_reviews__field_response__field",
            "field_reviews__field_response__response__section",
        )
    )
    ctx["section_issues"] = (
        app.review_assignment.section_reviews
        .filter(status="issue")
        .order_by("-reviewed_at")
        if hasattr(app, "review_assignment") else []
    )
    if hasattr(app, "review_assignment") and app.review_assignment and app.review_assignment.reviewer:
        ctx["reviewer_email"] = app.review_assignment.reviewer.email or ""
    else:
        ctx["reviewer_email"] = ""
    applicant_name = f"{app.applicant.first_name} {app.applicant.last_name}".strip() if app.applicant else ""
    contact_email = getattr(settings, "APPLICANT_CONTACT_EMAIL", "contact@go.wisconsin.edu")
    ctx["gmail_reply_urls"] = {}
    for sr in ctx["section_issues"]:
        subject = f"Clarification on {sr.section_title} - {app.Reference_id}"
        body = (
            f"Hi Admissions Team,\n\n"
            f"I am writing regarding my application ({app.Reference_id}).\n\n"
            f'Regarding the issue flagged in the "{sr.section_title}" section, '
            f"I would like to clarify the following:\n\n"
            f"[Please describe your clarification here]\n\n"
            f"Thank you for your time.\n\n"
            f"Regards,\n{applicant_name}"
        )
        gmail_url = (
            "https://mail.google.com/mail/"
            "?view=cm&fs=1"
            f"&to={url_quote(ctx['reviewer_email'])}"
            f"&su={url_quote(subject)}"
            f"&body={url_quote(body)}"
        )
        ctx["gmail_reply_urls"][sr.pk] = gmail_url
    ctx["uploaded_documents"] = app.documents.all().order_by("-uploaded_at")

    missing_docs = []
    for item in get_review_readiness(app)["missing"]:
        code = item["code"]
        if not code.startswith("doc:"):
            continue
        req_code = code[4:]
        req = DocumentRequirement.objects.filter(
            code=req_code,
            is_required=True,
        ).first()
        if req is None:
            continue
        already_uploaded = app.documents.filter(requirement=req).exists()
        if already_uploaded:
            continue
        missing_docs.append({
            "code": code,
            "label": item["label"],
            "requirement_id": req.pk,
            "allowed_extensions": req.allowed_extensions or "",
            "max_file_size_mb": req.max_file_size_mb,
        })

    if fee_info["amount"] is not None and not fee_info["paid"]:
        missing_docs.append(
            {"code": "fee", "label": "Application fee"}
        )
    ctx["missing_docs"] = missing_docs

    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "upload":
            upload = request.FILES.get("document")
            requirement_id = request.POST.get("requirement_id", "").strip()
            requirement = None
            if requirement_id.isdigit():
                requirement = (
                    DocumentRequirement.objects.filter(pk=int(requirement_id))
                    .first()
                )
            if not upload:
                messages.error(request, "Please choose a file to upload.")
            elif not requirement:
                messages.error(request, "That required material is not available.")
            else:
                name = (upload.name or "").lower()
                ext = os.path.splitext(name)[1].lower()
                allowed = [
                    a.strip().lower()
                    for a in (requirement.allowed_extensions or "").split(",")
                    if a.strip()
                ]
                max_bytes = requirement.max_file_size_mb * 1024 * 1024
                if allowed and ext not in allowed:
                    messages.error(
                        request,
                        f"Please upload a {', '.join(allowed)} file.",
                    )
                elif upload.size > max_bytes:
                    messages.error(
                        request,
                        f"File is too large. Maximum size is "
                        f"{requirement.max_file_size_mb} MB.",
                    )
                else:
                    path = default_storage.save(
                        "applications/"
                        f"{app.Reference_id}/materials/{_safe_filename(upload.name)}",
                        upload,
                    )
                    Document.objects.create(
                        application=app,
                        requirement=requirement,
                        doc_type=_document_type_for_requirement(requirement),
                        file_name=upload.name,
                        file_size=upload.size,
                        file_path=path,
                    )
                    fulfill_completed_material_requests(app)
                    ApplicationLog.objects.create(
                        application=app,
                        field_name="material_upload",
                        old_value="",
                        new_value=f"Applicant uploaded {upload.name}",
                        actor=(
                            f"{applicant.first_name} {applicant.last_name}".strip()
                            or applicant.email
                        ),
                    )
                    messages.success(
                        request,
                        f"{requirement.name} uploaded successfully.",
                    )
                    notify_application(app, "documents_changed")
        return redirect(_portal_url("status", app.application_id, request))
    return None


def _handle_create(
    request: HttpRequest,
    applicant: Applicant,
    ctx: dict,
) -> Optional[HttpResponse]:
    _ENROLLED_STATUSES = ("enrolled", "offer_accepted")
    enrolled_exists = Application.objects.filter(
        applicant=applicant, status__in=_ENROLLED_STATUSES
    ).exists()
    if enrolled_exists:
        messages.error(
            request,
            "You are already enrolled or have accepted an offer. You cannot submit another application.",
        )
        return redirect("./?state=hub")

    if request.method == "POST":
        return _execute_create_application(request, applicant)

    ctx["university"] = _lookup_or_none(CollegesUniversity, request.GET.get("u"))
    ctx["degree_level"] = _lookup_or_none(Degree, request.GET.get("dl"))
    ctx["cycle"] = _lookup_or_none(AdmissionCycle, request.GET.get("cy"))
    ctx["program"] = _lookup_or_none(AcademicProgram, request.GET.get("pid"))
    ctx["backup_program"] = _lookup_or_none(AcademicProgram, request.GET.get("bid"))
    ctx["campus_name"] = request.GET.get("campus") or "Main Campus"
    ctx["applicant_type_label"] = _resolve_applicant_type_label(request)
    ctx["state"] = "builder"
    ctx["builder_step"] = "create"
    return None


def _execute_create_application(
    request: HttpRequest,
    applicant: Applicant,
) -> HttpResponse:
    _ENROLLED_STATUSES = ("enrolled", "offer_accepted")
    enrolled_exists = Application.objects.filter(
        applicant=applicant, status__in=_ENROLLED_STATUSES
    ).exists()
    if enrolled_exists:
        messages.error(
            request,
            "You are already enrolled or have accepted an offer. You cannot submit another application.",
        )
        return redirect("./?state=hub")

    campus_name = request.GET.get("campus") or "Main Campus"
    applicant_type = (
        request.GET.get("at")
        or request.session.pop("selected_applicant_type", None)
        or ""
    )
    program_id = request.GET.get("pid") or request.POST.get("pid")
    if not program_id:
        messages.error(request, "Session expired. Please start over.")
        return redirect(".")

    app = SERVICE.create_application(
        applicant=applicant,
        university_id=request.GET.get("u"),
        campus_name=campus_name,
        degree_level_id=request.GET.get("dl"),
        program_id=program_id,
        cycle_id=request.GET.get("cy"),
        applicant_type=applicant_type,
        backup_program_id=request.GET.get("bid"),
    )
    offline = request.session.pop("apply_method", "online") == "offline"
    if offline:
        app.apply_method = "offline"
        app.save(update_fields=["apply_method"])
    EMAIL_SERVICE.send_application_started_email(
        app, request.build_absolute_uri(_first_step_url(app))
    )
    messages.success(request, f"Application created! Reference ID: {app.Reference_id}")
    if offline:
        return redirect("./?state=hub")
    return redirect(_first_step_url(app))


def _handle_builder(
    request: HttpRequest,
    applicant: Applicant,
    ctx: dict,
) -> Optional[HttpResponse]:
    _ENROLLED_STATUSES = ("enrolled", "offer_accepted")
    enrolled_exists = Application.objects.filter(
        applicant=applicant, status__in=_ENROLLED_STATUSES
    ).exists()
    if enrolled_exists:
        messages.error(
            request,
            "You are already enrolled or have accepted an offer. You cannot submit another application.",
        )
        return redirect("./?state=hub")

    builder_step = request.GET.get("step", "university")
    ctx["builder_step"] = builder_step
    handler = BUILDER_STEP_HANDLERS.get(builder_step)
    if handler:
        return handler(request, applicant, ctx)
    return None


def _builder_university(request, applicant, ctx):
    ctx["universities"] = SERVICE.get_active_universities()


def _builder_school(request, applicant, ctx):
    uid = request.GET.get("u")
    ctx["university"] = get_object_or_404(CollegesUniversity, pk=uid)
    ctx["campus_name"] = request.GET.get("campus") or "Main Campus"
    ctx["schools"] = School.objects.filter(university_id=uid, status="ACTIVE")


def _builder_degree(request, applicant, ctx):
    uid = request.GET.get("u")
    ctx["university"] = get_object_or_404(CollegesUniversity, pk=uid)
    ctx["school"] = _lookup_or_none(School, request.GET.get("school"))
    ctx["campus_name"] = request.GET.get("campus") or "Main Campus"
    ctx["levels"] = Degree.objects.exclude(degree_name="Bachelor of Arts")


def _builder_type(request, applicant, ctx):
    uid = request.GET.get("u")
    ctx["university"] = get_object_or_404(CollegesUniversity, pk=uid)
    ctx["school"] = _lookup_or_none(School, request.GET.get("school"))
    ctx["degree_level"] = get_object_or_404(Degree, pk=request.GET.get("dl"))
    ctx["campus_name"] = request.GET.get("campus") or "Main Campus"
    ctx["applicant_type_reqs"] = ApplicantTypeRequirement.objects.filter(
        degree_level=ctx["degree_level"], is_active=True
    ).select_related("degree_level")

    if request.method == "POST":
        applicant_type = request.POST.get("applicant_type")
        if applicant_type:
            request.session["selected_applicant_type"] = applicant_type
            return redirect(
                f"./?state=builder&step=cycle&u={uid}"
                f"&school={request.GET.get('school')}"
                f"&dl={request.GET.get('dl')}"
                f"&campus={request.GET.get('campus')}"
                f"&at={applicant_type}"
            )
    return None


def _builder_cycle(request, applicant, ctx):
    uid = request.GET.get("u")
    ctx["university"] = get_object_or_404(CollegesUniversity, pk=uid)
    ctx["school"] = _lookup_or_none(School, request.GET.get("school"))
    ctx["degree_level"] = get_object_or_404(Degree, pk=request.GET.get("dl"))
    ctx["campus_name"] = request.GET.get("campus") or "Main Campus"
    today = timezone.localdate()
    ctx["cycles"] = [
        c
        for c in SERVICE.get_active_cycles()
        if c.is_open
        and (c.application_deadline is None or c.application_deadline >= today)
    ]


def _builder_program(request, applicant, ctx):
    uid = request.GET.get("u")
    ctx["university"] = get_object_or_404(CollegesUniversity, pk=uid)
    school = _lookup_or_none(School, request.GET.get("school"))
    ctx["school"] = school
    ctx["degree_level"] = get_object_or_404(Degree, pk=request.GET.get("dl"))
    ctx["cycle"] = get_object_or_404(AdmissionCycle, pk=request.GET.get("cy"))
    ctx["campus_name"] = request.GET.get("campus") or "Main Campus"
    school_id = school.pk if school else None
    degree_level = ctx["degree_level"]
    programs = SERVICE.get_programs_for_university(
        university_id=uid,
        school_id=school_id,
        degree_level_id=degree_level.pk,
    )
    ctx["programs"] = programs

    groups = {}
    for p in programs:
        key = p.department.department_name if p.department else "Other"
        groups.setdefault(key, []).append(p)
    ctx["program_groups"] = groups


def _builder_create(request, applicant, ctx):
    uid = request.GET.get("u")
    ctx["university"] = get_object_or_404(CollegesUniversity, pk=uid)
    ctx["school"] = _lookup_or_none(School, request.GET.get("school"))
    ctx["degree_level"] = get_object_or_404(Degree, pk=request.GET.get("dl"))
    ctx["cycle"] = get_object_or_404(AdmissionCycle, pk=request.GET.get("cy"))
    ctx["program"] = _lookup_or_none(AcademicProgram, request.GET.get("pid"))
    ctx["backup_program"] = _lookup_or_none(AcademicProgram, request.GET.get("bid"))
    cname = request.GET.get("campus") or "Main Campus"
    ctx["campus_name"] = cname
    ctx["applicant_type_label"] = _resolve_applicant_type_label(request)

    if request.method == "POST":
        return _execute_create_application(request, applicant)
    ctx["builder_step"] = "create"
    return None


BUILDER_STEP_HANDLERS = {
    "university": _builder_university,
    "school": _builder_school,
    "degree": _builder_degree,
    "type": _builder_type,
    "cycle": _builder_cycle,
    "program": _builder_program,
    "create": _builder_create,
}


def _handle_dashboard(
    request: HttpRequest,
    applicant: Applicant,
    ctx: dict,
) -> Optional[HttpResponse]:
    app = _get_app_or_404(applicant, request.GET.get("app_id"))
    if _is_locked(app):
        fee_info = SERVICE.get_application_fee_info(app)
        if fee_info["amount"] is not None and not fee_info["paid"]:
            return redirect(f"/applicants/?state=payment&app_id={app.application_id}&uuid={app.applicant.uuid}")
        return redirect("/applicants/?state=hub")
    engine = DynamicFormEngine()
    progress = engine.calculate_progress(app)
    Application.objects.filter(pk=app.pk).update(progress_pct=progress)

    form_data = engine.get_all_application_data(app)

    ctx.update(
        {
            "app": app,
            "progress": progress,
            "logs": SERVICE.audit.get_logs(app, limit=10),
            "workflow_steps": _build_step_statuses(app, engine),
            "form_data": form_data,
            "locked": _is_locked(app),
        }
    )


def _handle_delete_app(
    request: HttpRequest,
    applicant: Applicant,
    ctx: dict,
) -> Optional[HttpResponse]:
    app = _get_app_or_404(applicant, request.GET.get("app_id"))
    if request.method == "POST":
        ref = app.Reference_id
        app.delete()
        messages.success(request, f"Application {ref} has been deleted.")
        return redirect(".")
    return redirect(".")


def _handle_info(
    request: HttpRequest,
    applicant: Applicant,
    ctx: dict,
) -> Optional[HttpResponse]:
    app = _get_app_or_404(applicant, request.GET.get("app_id"))
    if _is_locked(app):
        fee_info = SERVICE.get_application_fee_info(app)
        if fee_info["amount"] is not None and not fee_info["paid"]:
            messages.info(
                request,
                "Your application has been submitted. You can only pay the application fee now.",
            )
            return redirect(
                f"/applicants/?state=payment&app_id={app.application_id}&uuid={app.applicant.uuid}"
            )
        messages.info(
            request,
            "Your application has been submitted and can no longer be edited.",
        )
        return redirect("/applicants/?state=hub")

    code = request.GET.get("step") or "personal_info"
    engine = DynamicFormEngine()

    section = FormSection.objects.filter(code=code, is_active=True).first()
    if not section:
        messages.error(request, "Form section not found.")
        return redirect(f"/applicants/?state=dashboard&app_id={app.application_id}&uuid={app.applicant.uuid}")

    if not engine.is_section_allowed(app, section):
        messages.error(request, "This section is not part of your application.")
        return redirect(f"/applicants/?state=dashboard&app_id={app.application_id}&uuid={app.applicant.uuid}")

    if request.method == "POST":
        return _handle_info_post(request, app, section, engine, ctx)

    return _handle_info_get(request, app, section, engine, ctx)


def _get_dob_min_year(app: Application) -> Optional[int]:
    try:
        pi_sec = FormSection.objects.get(code="personal_info", is_active=True)
        pi_resp = FormResponse.objects.filter(application=app, section=pi_sec).first()
        if pi_resp:
            dob_fr = FieldResponse.objects.filter(response=pi_resp, field__code="date_of_birth").first()
            if dob_fr:
                dob_val = dob_fr.typed_value()
                if dob_val:
                    dob_year = dob_val.year if hasattr(dob_val, "year") else int(str(dob_val)[:4])
                    return dob_year + 15
    except Exception:
        pass
    return None


def _handle_info_post(
    request: HttpRequest,
    app: Application,
    section: FormSection,
    engine: DynamicFormEngine,
    ctx: dict,
) -> HttpResponse:
    response_obj = engine.get_or_create_response(app, section)
    form = DynamicForm(
        section, None, request.POST, request.FILES,
        dob_min_year=_get_dob_min_year(app),
    )

    if form.is_valid():
        engine.save_field_responses(section, response_obj, form.cleaned_data)
        SERVICE.audit.log_change(
            app, section.code, None, "updated",
            ip_address=request.META.get("REMOTE_ADDR"),
        )
        progress = engine.calculate_progress(app)
        Application.objects.filter(pk=app.pk).update(progress_pct=progress)
        messages.success(request, f"{section.title} saved.")
        return redirect(_next_step_url(app, section.code))

    engine.save_field_responses(section, response_obj, form.cleaned_data, mark_complete=False)
    return _render_info(request, app, form, section, code=None, engine=engine, ctx=ctx)


def _handle_info_get(
    request: HttpRequest,
    app: Application,
    section: FormSection,
    engine: DynamicFormEngine,
    ctx: dict,
) -> HttpResponse:
    response_obj = engine.get_or_create_response(app, section)
    existing = {}
    for fr in FieldResponse.objects.filter(response=response_obj):
        existing[fr.field.code] = fr.typed_value()
    form = DynamicForm(section, existing, dob_min_year=_get_dob_min_year(app))
    if not form.fields:
        form = DynamicForm(section, None, dob_min_year=_get_dob_min_year(app))
    return _render_info(request, app, form, section, section.code, engine, ctx)


def _render_info(
    request: HttpRequest,
    app: Application,
    form,
    section: FormSection,
    code: Optional[str],
    engine: DynamicFormEngine,
    ctx: dict,
) -> HttpResponse:
    response_obj = engine.get_or_create_response(app, section)
    dynamic_fields = engine.build_form_context(section, app, response_obj)
    dob_min = _get_dob_min_year(app)
    if dob_min:
        for fd in dynamic_fields["fields"]:
            f = fd["field"]
            if f.field_type == "year":
                min_rule = next((v for v in fd["validations"] if v.validation_type == "min_value"), None)
                current_min = int(min_rule.value) if min_rule else 1900
                if current_min < dob_min:
                    fd.setdefault("min_value_override", str(dob_min))
                    if min_rule:
                        min_rule.value = str(dob_min)
                    else:
                        fd["validations"].append(
                            ValidationRule(field=f, validation_type="min_value", value=str(dob_min))
                        )
    if form.errors:
        field_errors = {k: list(v) for k, v in form.errors.items()}
        for fd in dynamic_fields["fields"]:
            fc = fd["field"].code
            if fc in field_errors:
                fd["errors"] = field_errors[fc]
    ctx.update(
        {
            "form": form,
            "step_name": section.title,
            "step_code": code,
            "step_description": section.description,
            "step_section": "",
            "app": app,
            "prev_url": _prev_step_url(app, section.code),
            "next_url": _next_step_url(app, section.code),
            "dynamic_section": section,
            "dynamic_fields": dynamic_fields,
            "workflow_steps": _build_step_statuses(app, engine),
            "progress": engine.calculate_progress(app),
            "locked": _is_locked(app),
        }
    )
    return render(request, "Applicants/portal_body.html", ctx)


def _handle_how_to_apply(
    request: HttpRequest,
    applicant: Applicant,
    ctx: dict,
) -> None:
    pass


def _handle_find_term(
    request: HttpRequest,
    applicant: Applicant,
    ctx: dict,
) -> None:
    ctx["campuses"] = CollegesUniversity.objects.all().order_by("university_name")
    campus_id = request.GET.get("campus")
    app_type = request.GET.get("app_type")
    ctx["selected_campus"] = campus_id or ""
    ctx["selected_app_type"] = app_type or ""
    if campus_id and app_type:
        campus_obj = CollegesUniversity.objects.filter(pk=campus_id).first()
        campus_name = campus_obj.university_name if campus_obj else ""
        cycles = AdmissionCycle.objects.filter(is_active=True)
        term_data = []
        for cycle in cycles:
            open_date = cycle.application_start.strftime('%#m/%d/%Y') if cycle.application_start else 'TBD'
            deadline = cycle.application_deadline.strftime('%#m/%d/%Y') if cycle.application_deadline else 'TBD'
            if cycle.is_open:
                term_data.append({
                    "campus": campus_name,
                    "app_type": app_type,
                    "open": {
                        "term": f"{cycle.term} {cycle.academic_year}",
                        "start": open_date,
                    },
                })
            else:
                term_data.append({
                    "campus": campus_name,
                    "app_type": app_type,
                    "coming_soon": [
                        {
                            "term": f"{cycle.term} {cycle.academic_year}",
                            "opening": open_date,
                            "deadline": deadline,
                        },
                    ],
                })
        ctx["term_data"] = term_data
    ctx.setdefault("term_data", [])


def _handle_find_program(
    request: HttpRequest,
    applicant: Applicant,
    ctx: dict,
) -> None:
    programs = AcademicProgram.objects.filter(status="ACTIVE").select_related(
        "degree", "department", "department__school", "department__school__university"
    )

    keyword = request.GET.get("keyword", "").strip()
    career_cluster = request.GET.get("career_cluster", "").strip()
    campus = request.GET.get("campus", "").strip()
    program_level = request.GET.get("program_level", "").strip()
    program_type = request.GET.get("program_type", "").strip()
    course_delivery = request.GET.get("course_delivery", "").strip()

    ctx["keyword"] = keyword
    ctx["career_cluster"] = career_cluster
    ctx["campus"] = campus
    ctx["program_level"] = program_level
    ctx["program_type"] = program_type
    ctx["course_delivery"] = course_delivery

    if keyword:
        programs = programs.filter(program_name__icontains=keyword)
    if career_cluster:
        programs = programs.filter(department__department_name__iexact=career_cluster)
    if campus:
        programs = programs.filter(department__school__university__university_name__iexact=campus)
    if program_level:
        programs = programs.filter(degree__level__iexact=program_level)
    if program_type:
        programs = programs.filter(program_type__iexact=program_type)

    ctx["programs"] = programs
    ctx["career_clusters"] = sorted(set(
        p.department.department_name for p in programs if p.department
    ))
    ctx["campuses"] = sorted(set(
        p.department.school.university.university_name for p in programs if p.department and p.department.school and p.department.school.university
    ))
    ctx["program_levels"] = sorted(set(
        p.degree.level for p in programs if p.degree
    ))
    ctx["program_types"] = sorted(set(
        p.program_type for p in programs if p.program_type
    ))


CAMPUS_CHOICES = [
    "UW-Eau Claire",
    "UW-Eau Claire - Barron County",
    "UW-Green Bay",
    "UW-Green Bay - Manitowoc Campus",
    "UW-Green Bay - Sheboygan Campus",
    "UW-La Crosse",
    "UW-Madison",
    "UW-Milwaukee",
    "UW-Oshkosh",
    "UW-Parkside",
    "UW-Platteville",
    "UW-River Falls",
    "UW-Stevens Point",
    "UW-Stevens Point at Marshfield",
    "UW-Stevens Point at Wausau",
    "UW-Stout",
    "UW-Superior",
    "UW-Whitewater",
    "UW-Whitewater at Rock County",
]


def _handle_military_benefits(
    request: HttpRequest,
    applicant: Applicant,
    ctx: dict,
) -> None:
    ctx["campus_choices"] = CAMPUS_CHOICES
    ctx["cycles"] = AdmissionCycle.objects.filter(is_active=True).order_by("-academic_year")
    profile, _ = ApplicantProfile.objects.get_or_create(applicant=applicant)
    ctx["profile"] = profile
    ctx["applicant_obj"] = applicant
    ctx["countries"] = [
        ("CA", "Canada"), ("MX", "Mexico"), ("GB", "United Kingdom"), ("IN", "India"),
        ("CN", "China"), ("KR", "South Korea"), ("JP", "Japan"), ("DE", "Germany"),
        ("FR", "France"), ("BR", "Brazil"), ("NG", "Nigeria"), ("PH", "Philippines"),
        ("AU", "Australia"), ("VN", "Vietnam"), ("TW", "Taiwan"), ("IT", "Italy"),
        ("ES", "Spain"), ("CO", "Colombia"), ("KE", "Kenya"), ("GH", "Ghana"),
    ]
    ctx["us_states"] = [
        ("AL","Alabama"),("AK","Alaska"),("AZ","Arizona"),("AR","Arkansas"),
        ("CA","California"),("CO","Colorado"),("CT","Connecticut"),("DE","Delaware"),
        ("FL","Florida"),("GA","Georgia"),("HI","Hawaii"),("ID","Idaho"),
        ("IL","Illinois"),("IN","Indiana"),("IA","Iowa"),("KS","Kansas"),
        ("KY","Kentucky"),("LA","Louisiana"),("ME","Maine"),("MD","Maryland"),
        ("MA","Massachusetts"),("MI","Michigan"),("MN","Minnesota"),("MS","Mississippi"),
        ("MO","Missouri"),("MT","Montana"),("NE","Nebraska"),("NV","Nevada"),
        ("NH","New Hampshire"),("NJ","New Jersey"),("NM","New Mexico"),("NY","New York"),
        ("NC","North Carolina"),("ND","North Dakota"),("OH","Ohio"),("OK","Oklahoma"),
        ("OR","Oregon"),("PA","Pennsylvania"),("RI","Rhode Island"),("SC","South Carolina"),
        ("SD","South Dakota"),("TN","Tennessee"),("TX","Texas"),("UT","Utah"),
        ("VT","Vermont"),("VA","Virginia"),("WA","Washington"),("WV","West Virginia"),
        ("WI","Wisconsin"),("WY","Wyoming"),
    ]


def _handle_submit(
    request: HttpRequest,
    applicant: Applicant,
    ctx: dict,
) -> Optional[HttpResponse]:
    app = _get_app_or_404(applicant, request.GET.get("app_id"))
    if app.apply_method == "offline":
        return _handle_offline_submit(request, applicant, app, ctx)
    if app.status not in ("draft", "in_progress"):
        ctx.update({
            "app": app,
            "readiness": None,
            "workflow_steps": _build_step_statuses(
                app, DynamicFormEngine()
            ),
            "progress": DynamicFormEngine().calculate_progress(app),
            "locked": True,
        })
        return None
    fee_info = SERVICE.get_application_fee_info(app)
    fee_due = not fee_info["free"] and not fee_info["paid"]
    if request.method == "POST":
        signature = request.POST.get("signature", "").strip()
        if not signature:
            messages.error(request, "Please provide your signature.")
        elif not request.POST.get("certify"):
            messages.error(request, "You must certify the application.")
        elif fee_due:
            messages.error(
                request,
                "Please pay the application fee before submitting your application.",
            )
        else:
            success, errors = SERVICE.submit_application(app, signature)
            if success:
                EMAIL_SERVICE.send_application_submitted_email(
                    app,
                    request.build_absolute_uri(
                        _portal_url("dashboard", app.application_id, request)
                    ),
                )
                _notify_submitted(app)
                messages.success(
                    request,
                    f"Application {app.Reference_id} submitted successfully!",
                )
                return redirect(
                    f"./?state=submit&app_id={app.application_id}&uuid={app.applicant.uuid}"
                )
            for err in errors:
                messages.error(request, err)
    readiness_data = SERVICE.get_submission_readiness(app)
    engine = DynamicFormEngine()
    sections_done = readiness_data.get("sections_done", [])
    sections_missing = readiness_data.get("sections_missing", [])
    ctx.update({
        "app": app,
        "sections_done": sections_done,
        "sections_missing": sections_missing,
        "ready": (not sections_missing) and not fee_due,
        "workflow_steps": _build_step_statuses(app, engine),
        "progress": engine.calculate_progress(app),
        "fee_info": fee_info,
        "locked": False,
    })
    return None


def _handle_offline_submit(
    request: HttpRequest,
    applicant: Applicant,
    app: Application,
    ctx: dict,
) -> Optional[HttpResponse]:
    """Offline applications: download the printed form, upload the completed
    PDF, pay the application fee, then submit. Once submitted the page becomes
    a read-only confirmation."""
    if _is_locked(app):
        ctx.update({
            "app": app,
            "fee_info": SERVICE.get_application_fee_info(app),
            "workflow_steps": _build_step_statuses(app, DynamicFormEngine()),
            "locked": True,
            "is_offline": True,
            "submitted_confirmation": True,
        })
        return None

    fee_info = SERVICE.get_application_fee_info(app)
    fee_due = not fee_info["free"] and not fee_info["paid"]

    if request.method == "POST":
        action = request.POST.get("action", "")

        if action == "upload_document":
            if not app.offline_form_pdf:
                messages.error(
                    request,
                    "Please upload your completed form PDF (step 2) before adding transcripts or grades.",
                )
                return redirect(f"./?state=submit&app_id={app.application_id}&uuid={app.applicant.uuid}")
            upload = request.FILES.get("document")
            requirement_id = request.POST.get("requirement_id", "").strip()
            requirement = None
            if requirement_id.isdigit():
                requirement = DocumentRequirement.objects.filter(pk=int(requirement_id)).first()
            if not upload:
                messages.error(request, "Please choose a file to upload.")
            elif not requirement:
                messages.error(request, "That required material is not available.")
            else:
                name = (upload.name or "").lower()
                ext = os.path.splitext(name)[1].lower()
                allowed = [
                    a.strip().lower()
                    for a in (requirement.allowed_extensions or "").split(",")
                    if a.strip()
                ]
                max_bytes = requirement.max_file_size_mb * 1024 * 1024
                if allowed and ext not in allowed:
                    messages.error(request, f"Please upload a {', '.join(allowed)} file.")
                elif upload.size > max_bytes:
                    messages.error(
                        request,
                        f"File is too large. Maximum size is {requirement.max_file_size_mb} MB.",
                    )
                else:
                    path = default_storage.save(
                        "applications/"
                        f"{app.Reference_id}/materials/{_safe_filename(upload.name)}",
                        upload,
                    )
                    Document.objects.create(
                        application=app,
                        requirement=requirement,
                        doc_type=_document_type_for_requirement(requirement),
                        file_name=upload.name,
                        file_size=upload.size,
                        file_path=path,
                    )
                    fulfill_completed_material_requests(app)
                    ApplicationLog.objects.create(
                        application=app,
                        field_name="material_upload",
                        old_value="",
                        new_value=f"Applicant uploaded {upload.name}",
                        actor=(f"{applicant.first_name} {applicant.last_name}".strip() or applicant.email),
                    )
                    messages.success(request, f"{requirement.name} uploaded successfully.")
                    notify_application(app, "documents_changed")
            return redirect(f"./?state=submit&app_id={app.application_id}&uuid={app.applicant.uuid}")

        if action == "remove_document":
            requirement_id = request.POST.get("requirement_id", "").strip()
            if requirement_id.isdigit():
                requirement = DocumentRequirement.objects.filter(pk=int(requirement_id)).first()
                doc = (
                    app.documents.filter(requirement=requirement).first()
                    if requirement
                    else None
                )
                if doc:
                    doc.file_path.delete(save=False)
                    doc.delete()
                    ApplicationLog.objects.create(
                        application=app,
                        field_name="material_upload",
                        old_value="",
                        new_value=f"Applicant removed {requirement.name} document",
                        actor=(f"{applicant.first_name} {applicant.last_name}".strip() or applicant.email),
                    )
                    messages.info(request, f"{requirement.name} document removed.")
            return redirect(f"./?state=submit&app_id={app.application_id}&uuid={app.applicant.uuid}")

        if action == "pay":
            pending_docs = False
            for req in DocumentRequirement.objects.filter(
                is_required=True, is_active=True
            ):
                code = (req.code or "").lower()
                if "transcript" not in code and "grade" not in code:
                    continue
                if req.university_id not in (None, app.university_id):
                    continue
                if req.degree_level_id not in (None, app.degree_level_id):
                    continue
                if not app.documents.filter(requirement=req).exists():
                    pending_docs = True
                    break
            if pending_docs:
                messages.error(
                    request,
                    "Please upload your transcripts & grades (step 3) before paying the application fee.",
                )
                return redirect(f"./?state=submit&app_id={app.application_id}&uuid={app.applicant.uuid}")
            if fee_info["amount"] is None:
                messages.info(request, "No application fee is required for this campus.")
                return redirect(f"./?state=submit&app_id={app.application_id}&uuid={app.applicant.uuid}")
            return _start_checkout(
                request,
                app,
                fee_info["amount"],
                f"./?state=submit&app_id={app.application_id}&uuid={app.applicant.uuid}",
            )

        if action == "upload":
            upload = request.FILES.get("offline_pdf")
            if not upload:
                messages.error(request, "Please choose a PDF file to upload.")
            elif not _is_valid_pdf_upload(upload):
                messages.error(request, "Please upload a valid PDF file (max 10 MB).")
            else:
                path = default_storage.save(
                    f"offline-applications/{app.Reference_id}/{_safe_filename(upload.name)}",
                    upload,
                )
                if app.offline_form_pdf:
                    app.offline_form_pdf.delete(save=False)
                app.offline_form_pdf = path
                app.offline_form_text = None
                app.offline_form_extracted_at = None
                app.offline_extracted_test_scores = None
                app.save(update_fields=[
                    "offline_form_pdf",
                    "offline_form_text",
                    "offline_form_extracted_at",
                    "offline_extracted_test_scores",
                    "updated_date",
                ])
                messages.success(request, "Your completed PDF was uploaded.")
                notify_application(app, "offline_extracted")
            return redirect(f"./?state=submit&app_id={app.application_id}&uuid={app.applicant.uuid}")

        if action == "remove_pdf":
            if app.offline_form_pdf:
                app.offline_form_pdf.delete(save=False)
                app.offline_form_pdf = None
                app.offline_form_text = None
                app.offline_form_extracted_at = None
                app.offline_extracted_test_scores = None
                app.save(update_fields=[
                    "offline_form_pdf",
                    "offline_form_text",
                    "offline_form_extracted_at",
                    "offline_extracted_test_scores",
                    "updated_date",
                ])
                messages.info(request, "Uploaded PDF removed.")
            return redirect(f"./?state=submit&app_id={app.application_id}&uuid={app.applicant.uuid}")

        if action == "submit":
            signature = request.POST.get("signature", "").strip()

            if not app.offline_form_pdf:
                messages.error(request, "Please upload the completed PDF of your application form.")
            elif not signature:
                messages.error(request, "Please provide your signature.")
            elif not request.POST.get("certify"):
                messages.error(request, "You must certify that the information is accurate.")
            elif fee_due:
                messages.error(request, "You must pay the application fee before submitting.")
            else:
                success, errors = SERVICE.submit_application(
                    app, signature, skip_form_check=True
                )
                if success:
                    EMAIL_SERVICE.send_application_submitted_email(
                        app,
                        request.build_absolute_uri(
                            _portal_url("submit", app.application_id, request)
                        ),
                    )
                    _notify_submitted(app)
                    notify_application(app, "status_changed")
                    if app.apply_method == "offline":
                        from .services.offline_parser import extract_offline_content

                        try:
                            extracted = extract_offline_content(app)
                            if extracted["essays"] or extracted["test_scores"]:
                                messages.success(
                                    request,
                                    "Essay and test scores were read from your PDF for review.",
                                )
                            elif not extracted["text_available"]:
                                messages.warning(
                                    request,
                                    "No text could be read from your PDF — it appears to be a scanned image.",
                                )
                        except Exception:
                            logger.exception(
                                "Offline content extraction failed for %s", app.Reference_id
                            )
                    messages.success(
                        request,
                        f"Application {app.Reference_id} submitted successfully!",
                    )
                    return redirect(
                        f"./?state=submit&app_id={app.application_id}&uuid={app.applicant.uuid}"
                    )
                for err in errors:
                    messages.error(request, err)

    offline_docs = []
    for req in DocumentRequirement.objects.filter(
        is_required=True, is_active=True
    ).order_by("sort_order", "name"):
        code = (req.code or "").lower()
        if "transcript" not in code and "grade" not in code:
            continue
        if req.university_id not in (None, app.university_id):
            continue
        if req.degree_level_id not in (None, app.degree_level_id):
            continue
        offline_docs.append({
            "requirement": req,
            "uploaded": app.documents.filter(requirement=req).first(),
        })

    step2_done = bool(app.offline_form_pdf)
    step3_done = all(d["uploaded"] for d in offline_docs)
    step4_done = fee_info["free"] or fee_info["paid"]

    ctx.update({
        "app": app,
        "fee_info": fee_info,
        "fee_due": fee_due,
        "workflow_steps": _build_step_statuses(app, DynamicFormEngine()),
        "offline_docs": offline_docs,
        "step2_done": step2_done,
        "step3_done": step3_done,
        "step4_done": step4_done,
        "step2_enabled": True,
        "step3_enabled": step2_done,
        "step4_enabled": step3_done,
        "step5_enabled": step4_done,
        "locked": False,
        "is_offline": True,
    })
    return None


def _is_valid_pdf_upload(upload) -> bool:
    name = (upload.name or "").lower()
    if not name.endswith(".pdf"):
        return False
    if upload.size > 10 * 1024 * 1024:
        return False
    try:
        upload.seek(0)
        head = upload.read(5)
        upload.seek(0)
    except Exception:
        return False
    return head.startswith(b"%PDF-")


GRADE_SHEET_FILE_PREFIX = "Grade Sheet - "


def _is_valid_material_upload(upload, requirement=None):    
    """Return an error message string, or None if the file is acceptable."""
    ext = os.path.splitext((upload.name or "").lower())[1].lstrip(".")
    allowed = (
        requirement.allowed_extensions
        if requirement
        else ".pdf,.doc,.docx,.jpg,.png"
    )
    allowed_exts = [
        a.strip().lstrip(".").lower() for a in allowed.split(",") if a.strip()
    ]
    if allowed_exts and ext not in allowed_exts:
        return "Please upload a " + ", ".join(allowed_exts) + " file."
    max_mb = requirement.max_file_size_mb if requirement else 10
    if upload.size > max_mb * 1024 * 1024:
        return f"File is too large. Maximum size is {max_mb} MB."
    return None


def _save_material_upload(app, upload, *, requirement=None, doc_type="", grade_sheet=False):
    """Save an uploaded transcript/grade sheet as a Document, replacing the
    previous one so the offline page keeps a single slot per material."""
    safe = _safe_filename(upload.name or "document.pdf")
    path = default_storage.save(
        f"applications/{app.Reference_id}/materials/{safe}", upload
    )
    if grade_sheet:
        app.documents.filter(file_name__istartswith=GRADE_SHEET_FILE_PREFIX).delete()
        display = f"{GRADE_SHEET_FILE_PREFIX}{safe}"
    else:
        app.documents.filter(requirement=requirement).delete()
        display = upload.name or safe
    return Document.objects.create(
        application=app,
        requirement=requirement,
        doc_type=doc_type,
        file_name=display,
        file_size=upload.size,
        file_path=path,
    )


def _safe_filename(name: str) -> str:
    return os.path.basename(name or "form.pdf").replace(" ", "_")


def _start_checkout(request: HttpRequest, app: Application, amount, redirect_to: str, next_target: str = "") -> HttpResponse:
    """Create a Stripe checkout session for the application fee."""
    coupon = request.POST.get("coupon", "").strip()
    transaction_id = f"APP-{app.Reference_id}-{uuid.uuid4().hex[:10].upper()}"
    payment = app.payments.create(
        transaction_id=transaction_id,
        amount=amount,
        currency="USD",
        status="pending",
        payment_method="card",
        gateway_response={"coupon": coupon, "provider": "stripe"},
    )

    try:
        success_url = (
            request.build_absolute_uri(reverse("applicants_stripe_success"))
            + "?session_id={CHECKOUT_SESSION_ID}"
        )
        cancel_url = (
            request.build_absolute_uri(reverse("applicants_stripe_cancel"))
            + "?session_id={CHECKOUT_SESSION_ID}"
        )
        if next_target:
            success_url += f"&next={url_quote(next_target)}"
            cancel_url += f"&next={url_quote(next_target)}"
        session = create_checkout_session(app, payment, success_url, cancel_url)
    except StripePaymentError as exc:
        payment.status = "failed"
        payment.gateway_response["error"] = str(exc)
        payment.save(update_fields=["status", "gateway_response"])
        messages.error(request, f"Unable to start payment: {exc}")
        return redirect(redirect_to)

    payment.checkout_session_id = session.id
    payment.gateway_response["checkout_session_url"] = session.url
    payment.save(update_fields=["checkout_session_id", "gateway_response"])
    return redirect(session.url)


def _handle_payment(
    request: HttpRequest,
    applicant: Applicant,
    ctx: dict,
) -> Optional[HttpResponse]:
    app = _get_app_or_404(applicant, request.GET.get("app_id"))
    if app.status not in ("draft", "in_progress", "submitted", "awaiting_materials", "complete", "under_review"):
        return redirect(f"./?state=dashboard&app_id={app.application_id}&uuid={app.applicant.uuid}")

    fee_info = SERVICE.get_application_fee_info(app)

    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "not_now":
            messages.info(
                request,
                f"You can pay the application fee for {app.Reference_id} later from your account.",
            )
            if request.GET.get("next") == "submit":
                return redirect(f"./?state=submit&app_id={app.application_id}&uuid={app.applicant.uuid}")
            return redirect("./?state=hub")

        if action == "pay":
            amount = fee_info["amount"]
            if amount is None:
                messages.warning(request, "No application fee is required for this campus.")
                return redirect(f"./?state=dashboard&app_id={app.application_id}&uuid={app.applicant.uuid}")
            return _start_checkout(
                request,
                app,
                amount,
                f"./?state=payment&app_id={app.application_id}&uuid={app.applicant.uuid}",
                next_target=request.GET.get("next", ""),
            )

    ctx.update({
        "app": app,
        "fee_info": fee_info,
        "workflow_steps": _build_step_statuses(app, DynamicFormEngine()),
        "progress": 100,
        "locked": _is_locked(app),
        "next": request.GET.get("next", ""),
    })
    return None


def _handle_offline(
    request: HttpRequest,
    applicant: Applicant,
    ctx: dict,
) -> Optional[HttpResponse]:
    request.session["apply_method"] = "offline"
    return redirect("./?state=builder&step=university")


# ─── Stripe Checkout ───────────────────────────────────────────────────


def _complete_payment(payment: FeePayment) -> None:
    """Mark a payment completed (idempotent)."""
    if payment.status != "completed":
        payment.status = "completed"
        payment.paid_at = timezone.now()
        payment.gateway_response["provider_status"] = "approved"
        payment.save(
            update_fields=["status", "paid_at", "gateway_response", "checkout_session_id"]
        )
    fulfill_completed_material_requests(payment.application)


def _portal_url(state: str, application_id=None, request=None) -> str:
    url = reverse("applicants_home") + f"?state={state}"
    if application_id:
        url += f"&app_id={application_id}"
    if request is not None:
        applicant = _get_session_applicant(request)
        if applicant is not None:
            url += f"&uuid={applicant.uuid}"
    return url


def stripe_checkout_success(request: HttpRequest) -> HttpResponse:
    session_id = request.GET.get("session_id", "")
    is_deposit = request.GET.get("deposit") == "1"
    app_id = request.GET.get("app_id")

    payment = None
    if session_id:
        payment = (
            FeePayment.objects.filter(
                checkout_session_id=session_id,
                application__applicant__id=request.session.get("applicant_id"),
            )
            .first()
        )

    if is_deposit and payment and payment.status in ("pending", "completed"):
        _complete_payment(payment)
        app = payment.application
        app.deposit_paid_at = timezone.now()
        app.deposit_transaction_id = payment.transaction_id
        app.save(update_fields=["deposit_paid_at", "deposit_transaction_id"])

        ApplicationLog.objects.create(
            application=app,
            field_name="deposit_payment",
            old_value="",
            new_value=f"Deposit of ${app.deposit_amount} paid (Transaction: {payment.transaction_id})",
            actor=f"{app.applicant.first_name} {app.applicant.last_name}",
        )

        _send_deposit_confirmed_email(app)
        messages.success(request, f"Deposit of ${app.deposit_amount:.2f} paid! Your admission is now confirmed.")
        return redirect(_portal_url("status", app.application_id, request))

    if payment and payment.status in ("pending", "completed"):
        _complete_payment(payment)
        messages.success(
            request,
            f"Your application fee of ${payment.amount:.2f} for {payment.application.Reference_id} has been paid. Thank you!",
        )
        if payment.application.apply_method == "offline":
            return redirect(_portal_url("submit", payment.application.application_id, request))
        url = _portal_url("payment", payment.application.application_id, request)
        if request.GET.get("next") == "submit":
            url += "&next=submit"
        return redirect(url)

    messages.error(request, "We could not confirm your payment. If you were charged, please contact support.")
    return redirect(_portal_url("hub", request=request))


def stripe_checkout_cancel(request: HttpRequest) -> HttpResponse:
    session_id = request.GET.get("session_id", "")
    is_deposit = request.GET.get("deposit") == "1"
    app_id = request.GET.get("app_id")

    if session_id:
        payment = FeePayment.objects.filter(
            checkout_session_id=session_id,
            application__applicant__id=request.session.get("applicant_id"),
            status="pending",
        ).first()
        if payment:
            payment.status = "failed"
            payment.gateway_response["provider_status"] = "cancelled"
            payment.save(update_fields=["status", "gateway_response"])
            if is_deposit and app_id:
                messages.info(request, "Deposit payment was not completed. You can try again from your status page.")
                return redirect(_portal_url("status", app_id, request))
            messages.info(
                request,
                f"Your payment for {payment.application.Reference_id} was not completed. You can pay later from your dashboard.",
            )
            return redirect(_portal_url("payment", payment.application.application_id, request))
    messages.info(request, "Your payment was not completed.")
    return redirect(_portal_url("hub", request=request))


@csrf_exempt
def stripe_webhook(request: HttpRequest) -> HttpResponse:
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")

    try:
        event = verify_webhook_event(payload, sig_header)
    except StripePaymentError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        payment_id = session.get("metadata", {}).get("payment_id")
        payment = FeePayment.objects.filter(id=payment_id).first() if payment_id else None
        if payment and payment.status != "completed":
            payment.checkout_session_id = session.get("id", payment.checkout_session_id)
            _complete_payment(payment)
            return JsonResponse({"status": "ok", "payment": payment.transaction_id})

    return JsonResponse({"status": "ok"})


STATE_HANDLERS = {
    "hub": _handle_hub,
    "create": _handle_create,
    "builder": _handle_builder,
    "dashboard": _handle_dashboard,
    "delete_app": _handle_delete_app,
    "info": _handle_info,
    "submit": _handle_submit,
    "payment": _handle_payment,
    "offline": _handle_offline,
    "status": _handle_status,
    "how-to-apply": _handle_how_to_apply,
    "find-term": _handle_find_term,
    "find-program": _handle_find_program,
    "military-benefits": _handle_military_benefits,
}


# ─── Shared Utilities ──────────────────────────────────────────────────


def _lookup_or_none(model, pk):
    if not pk:
        return None
    try:
        return model.objects.get(pk=pk)
    except model.DoesNotExist:
        return None


def _resolve_applicant_type_label(request: HttpRequest) -> str:
    at = request.GET.get("at") or request.session.get("selected_applicant_type") or ""
    if at:
        return dict(Application.APPLICANT_TYPE_CHOICES).get(at, "")
    return ""


# ─── Public Views ──────────────────────────────────────────────────────


@_require_applicant
def validate_field_view(
    request: HttpRequest,
    applicant: Applicant,
) -> JsonResponse:
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    step = request.POST.get("step", "")
    field_code = request.POST.get("field", "")
    value = request.POST.get("value", "")

    section = FormSection.objects.filter(code=step, is_active=True).first()
    if not section:
        return JsonResponse({"valid": True})

    form = DynamicForm(section, data={field_code: value})
    if form.is_valid():
        return JsonResponse({"valid": True})

    errors = []
    if field_code in form.errors:
        for error in form.errors.as_data()[field_code]:
            errors.extend(error.messages)
    return JsonResponse({"valid": False, "errors": errors})


@_require_applicant
def autosave_dynamic_field(
    request: HttpRequest,
    applicant: Applicant,
) -> JsonResponse:
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    app = _get_app_or_404(applicant, request.POST.get("app_id"))
    section = get_object_or_404(
        FormSection,
        code=request.POST.get("section", ""),
        is_active=True,
    )
    field_code = request.POST.get("field", "")
    field = get_object_or_404(section.fields.filter(is_active=True), code=field_code)

    engine = DynamicFormEngine()
    active_form_ids = {
        step.form_id
        for step in engine.get_active_workflow_steps(app)
        if step.step_type == "form" and step.form_id
    }
    if section.form_id not in active_form_ids:
        return JsonResponse(
            {"error": "This form is not available for the application."},
            status=403,
        )

    response = engine.get_or_create_response(app, section)
    existing = {
        fr.field.code: fr.typed_value()
        for fr in FieldResponse.objects.filter(response=response)
    }
    ctx = {
        k[4:]: request.POST.get(k)
        for k in request.POST if k.startswith("ctx_")
    }
    existing.update(ctx)
    dynamic_form = DynamicForm(section, existing)
    form_field = dynamic_form.fields.get(field_code)
    if not form_field or field.field_type == "file":
        return JsonResponse(
            {"error": "This field cannot be saved automatically."},
            status=400,
        )

    field_type = field.field_type
    if field_type == "multi_select":
        raw_value = request.POST.getlist("value")
    else:
        raw_value = request.POST.get("value", "")

    if field_type == "checkbox":
        raw_value = str(raw_value).lower() in ("1", "true", "on", "yes")

    is_empty = raw_value == "" or raw_value == []
    if is_empty:
        if field_type == "multi_select":
            value = []
        elif field_type == "checkbox":
            value = False
        else:
            value = ""
    else:
        db_regex = field.validations.filter(
            validation_type="regex", is_active=True
        ).first()
        if db_regex and db_regex.value and not re.match(db_regex.value, str(raw_value)):
            return JsonResponse(
                {"valid": False, "errors": [db_regex.error_message or "Enter a valid value."]},
                status=400,
            )
        try:
            value = form_field.clean(raw_value)
        except ValidationError as exc:
            return JsonResponse({"valid": False, "errors": exc.messages}, status=400)

    engine.save_field_responses(
        section, response, {field_code: value}, mark_complete=False
    )
    return JsonResponse({"valid": True, "saved": True})


def portal_view(request: HttpRequest) -> HttpResponse:
    redirect_response = _handle_logout(request)
    if redirect_response:
        return redirect_response

    applicant_id = request.session.get("applicant_id")
    if not applicant_id:
        return _handle_auth(request)

    applicant = SERVICE.repo.get_by_id(applicant_id)
    if not applicant:
        return redirect(".")

    state = request.GET.get("state", "hub")
    ctx = {"view_mode": "portal", "state": state, "applicant": applicant}

    dashboard_context = SERVICE.get_dashboard_context(applicant)
    ctx.update(dashboard_context)

    handler = STATE_HANDLERS.get(state)
    if handler:
        result = handler(request, applicant, ctx)
        if isinstance(result, HttpResponse):
            return result

    partial = request.GET.get("partial")
    if partial == "status":
        return render(request, "Applicants/portal/portal_status.html", ctx)

    return render(request, "Applicants/portal_body.html", ctx)


@_require_applicant
def download_next_steps_pdf(request: HttpRequest, applicant: Applicant, app_id: int) -> HttpResponse:
    app = _get_app_or_404(applicant, app_id)
    if app.status not in SUBMITTED_STATUSES:
        return redirect(".")
    response = HttpResponse(PDF_SERVICE.build_next_steps_pdf(app), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{app.Reference_id}-next-steps.pdf"'
    return response


@_require_applicant
def download_application_pdf(request: HttpRequest, applicant: Applicant, app_id: int) -> HttpResponse:
    app = _get_app_or_404(applicant, app_id)
    if app.status not in SUBMITTED_STATUSES:
        return redirect(".")
    response = HttpResponse(PDF_SERVICE.build_application_pdf(app), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{app.Reference_id}-application.pdf"'
    return response


@_require_applicant
def download_offline_application_pdf(request: HttpRequest, applicant: Applicant, app_id: int) -> HttpResponse:
    app = _get_app_or_404(applicant, app_id)
    response = HttpResponse(
        PDF_SERVICE.build_offline_application_pdf(app),
        content_type="application/pdf",
    )
    response["Content-Disposition"] = f'attachment; filename="{app.Reference_id}-offline-application-form.pdf"'
    return response


def offer_action(request: HttpRequest) -> HttpResponse:
    """Accept or decline an admission offer."""
    applicant_id = request.session.get("applicant_id")
    if not applicant_id:
        return redirect("/applicants/")

    applicant = SERVICE.repo.get_by_id(applicant_id)
    if not applicant:
        return redirect("/applicants/")

    if request.method != "POST":
        return redirect("/applicants/?state=status&app_id=%s&uuid=%s" % (request.GET.get("app_id", ""), applicant.uuid))

    app_id = request.POST.get("app_id") or request.GET.get("app_id")
    action = request.POST.get("action", "").strip()

    if not app_id or action not in ("accept", "decline"):
        messages.error(request, "Invalid request.")
        return redirect("/applicants/")

    app = Application.objects.filter(application_id=app_id, applicant=applicant).first()
    if not app:
        messages.error(request, "Application not found.")
        return redirect("/applicants/")

    if app.offer_status != "pending":
        messages.error(request, "No pending offer for this application.")
        return redirect("/applicants/?state=status&app_id=%s&uuid=%s" % (app_id, applicant.uuid))

    now = timezone.now()
    if action == "accept":
        if not app.deposit_paid_at:
            messages.error(request, "Please pay the enrollment deposit before accepting the offer.")
            return redirect("/applicants/?state=status&app_id=%s&uuid=%s" % (app_id, applicant.uuid))
        app.offer_status = "accepted"
        app.offer_accepted_at = now
        app.status = "offer_accepted"
        app.save(update_fields=["offer_status", "offer_accepted_at", "status"])
        ApplicationLog.objects.create(
            application=app,
            field_name="offer_action",
            old_value="pending",
            new_value="Offer accepted by applicant — awaiting admin processing",
            actor=f"{applicant.first_name} {applicant.last_name}",
        )
        _send_offer_accepted_email(app)
        messages.success(request, "Offer accepted! Your application is being processed by the admissions team.")
    else:
        app.offer_status = "declined"
        app.offer_declined_at = now
        app.save(update_fields=["offer_status", "offer_declined_at"])
        ApplicationLog.objects.create(
            application=app,
            field_name="offer_action",
            old_value="pending",
            new_value="Offer declined by applicant",
            actor=f"{applicant.first_name} {applicant.last_name}",
        )
        messages.success(request, "You have declined the offer.")

    return redirect("/applicants/?state=status&app_id=%s&uuid=%s" % (app_id, applicant.uuid))


def deposit_payment(request: HttpRequest) -> HttpResponse:
    """Initiate Stripe checkout for the enrollment deposit."""
    applicant_id = request.session.get("applicant_id")
    if not applicant_id:
        return redirect("/applicants/")

    applicant = SERVICE.repo.get_by_id(applicant_id)
    if not applicant:
        return redirect("/applicants/")

    if request.method != "POST":
        return redirect("/applicants/?state=status&app_id=%s&uuid=%s" % (request.GET.get("app_id", ""), applicant.uuid))

    app_id = request.POST.get("app_id") or request.GET.get("app_id")
    if not app_id:
        messages.error(request, "Invalid request.")
        return redirect("/applicants/")

    app = Application.objects.filter(application_id=app_id, applicant=applicant).first()
    if not app:
        messages.error(request, "Application not found.")
        return redirect("/applicants/")

    if app.offer_status not in ("pending", "accepted"):
        messages.error(request, "No active offer for this application.")
        return redirect("/applicants/?state=status&app_id=%s&uuid=%s" % (app_id, applicant.uuid))

    if app.deposit_paid_at:
        messages.success(request, "Deposit already paid.")
        return redirect("/applicants/?state=status&app_id=%s&uuid=%s" % (app_id, applicant.uuid))

    import uuid as _uuid
    transaction_id = f"DEP-{app.Reference_id}-{_uuid.uuid4().hex[:8].upper()}"
    payment = app.payments.create(
        transaction_id=transaction_id,
        amount=app.deposit_amount,
        currency="USD",
        status="pending",
        payment_method="card",
        gateway_response={"type": "enrollment_deposit", "provider": "stripe"},
    )

    try:
        from .services.stripe_service import create_checkout_session, StripePaymentError
        success_url = (
            request.build_absolute_uri(reverse("applicants_stripe_success"))
            + "?session_id={CHECKOUT_SESSION_ID}&deposit=1&app_id=%s&uuid=%s" % (app.application_id, app.applicant.uuid)
        )
        cancel_url = (
            request.build_absolute_uri(reverse("applicants_stripe_cancel"))
            + "?session_id={CHECKOUT_SESSION_ID}&deposit=1&app_id=%s&uuid=%s" % (app.application_id, app.applicant.uuid)
        )
        session = create_checkout_session(app, payment, success_url, cancel_url)
    except StripePaymentError as exc:
        payment.status = "failed"
        payment.gateway_response["error"] = str(exc)
        payment.save(update_fields=["status", "gateway_response"])
        messages.error(request, f"Unable to start payment: {exc}")
        return redirect("/applicants/?state=status&app_id=%s&uuid=%s" % (app_id, applicant.uuid))

    payment.checkout_session_id = session.id
    payment.gateway_response["checkout_session_url"] = session.url
    payment.save(update_fields=["checkout_session_id", "gateway_response"])
    return redirect(session.url)


def _send_offer_accepted_email(app):
    """Send confirmation email after applicant accepts the offer."""
    from django.core.mail import EmailMultiAlternatives
    from django.template.loader import render_to_string
    from django.conf import settings as _settings

    applicant_name = f"{app.applicant.first_name} {app.applicant.last_name}".strip()
    program_name = app.program.program_name if app.program else "N/A"
    contact_email = getattr(_settings, "APPLICANT_CONTACT_EMAIL", "contact@go.wisconsin.edu")
    site_url = getattr(_settings, "SITE_URL", "http://127.0.0.1:8000")
    portal_url = f"{site_url}/applicants/?state=status&app_id={app.application_id}&uuid={app.applicant.uuid}"

    ctx = {
        "applicant_name": applicant_name,
        "program_name": program_name,
        "deposit_amount": app.deposit_amount,
        "portal_url": portal_url,
    }

    subject = f"Next Step: Complete Your Enrollment Deposit — {app.Reference_id}"
    html_body = render_to_string("Applicants/emails/offer_accepted.html", ctx)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=f"Dear {applicant_name},\n\nThank you for accepting your offer. Please pay your ${app.deposit_amount} deposit at: {portal_url}",
        from_email=contact_email,
        to=[app.applicant.email],
    )
    msg.attach_alternative(html_body, "text/html")
    msg.send(fail_silently=True)


def _send_deposit_confirmed_email(app):
    """Send confirmation email after deposit is paid."""
    from django.core.mail import EmailMultiAlternatives
    from django.template.loader import render_to_string
    from django.conf import settings as _settings

    applicant_name = f"{app.applicant.first_name} {app.applicant.last_name}".strip()
    program_name = app.program.program_name if app.program else "N/A"
    contact_email = getattr(_settings, "APPLICANT_CONTACT_EMAIL", "contact@go.wisconsin.edu")

    ctx = {
        "applicant_name": applicant_name,
        "program_name": program_name,
        "deposit_amount": app.deposit_amount,
        "deposit_date": app.deposit_paid_at.strftime("%B %d, %Y") if app.deposit_paid_at else "N/A",
        "transaction_id": app.deposit_transaction_id,
    }

    subject = f"Admission Confirmed! — {app.Reference_id}"
    html_body = render_to_string("Applicants/emails/deposit_confirmed.html", ctx)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=f"Dear {applicant_name},\n\nYour deposit of ${app.deposit_amount} has been received. Your admission is confirmed!",
        from_email=contact_email,
        to=[app.applicant.email],
    )
    msg.attach_alternative(html_body, "text/html")
    msg.send(fail_silently=True)


def api_get_states(request):
    country_code = request.GET.get("country", "").upper()
    states = StateProvince.objects.filter(country_code=country_code).values("id", "name", "code")
    return JsonResponse(list(states), safe=False)


def api_get_cities(request):
    state_id = request.GET.get("state")
    if not state_id:
        return JsonResponse([], safe=False)
    cities = City.objects.filter(state_id=state_id).values("id", "name")
    return JsonResponse(list(cities), safe=False)


# ---------------------------------------------------------------------------
# Applicant notification bell (AJAX)
# ---------------------------------------------------------------------------

APPLICANT_NOTIF_ICONS = {
    "INFO": "fa-info-circle",
    "SUCCESS": "fa-check-circle",
    "WARNING": "fa-exclamation-triangle",
    "ERROR": "fa-times-circle",
    "REQUEST": "fa-clipboard-check",
    "SYSTEM": "fa-cog",
}


def _get_session_applicant(request):
    from .models import Applicant

    applicant_id = request.session.get("applicant_id")
    if not applicant_id:
        return None
    try:
        return Applicant.objects.get(pk=int(applicant_id))
    except (Applicant.DoesNotExist, ValueError, TypeError):
        return None


def applicant_notifications_recent(request):
    """Latest notifications for the applicant bell dropdown."""
    applicant = _get_session_applicant(request)
    if applicant is None:
        return JsonResponse({"success": False, "notifications": [], "unread_count": 0})

    from .models import ApplicantNotification
    from django.utils.timesince import timesince

    notifications = ApplicantNotification.objects.filter(
        applicant=applicant
    ).order_by("-created_at")[:6]

    data = [{
        "id": n.id,
        "title": n.title,
        "message": n.message or "",
        "type": n.notification_type,
        "icon": APPLICANT_NOTIF_ICONS.get(n.notification_type, "fa-info-circle"),
        "is_read": n.is_read,
        "link": n.link or "",
        "delete_url": reverse("applicant_notifications_delete", args=[n.id]),
        "time_ago": timesince(n.created_at) + " ago",
    } for n in notifications]

    return JsonResponse({
        "success": True,
        "notifications": data,
        "unread_count": ApplicantNotification.objects.filter(
            applicant=applicant, is_read=False
        ).count(),
    })


def applicant_notifications_mark_all(request):
    if request.method != "POST":
        return JsonResponse({"success": False}, status=400)
    applicant = _get_session_applicant(request)
    if applicant is None:
        return JsonResponse({"success": False}, status=403)

    from .models import ApplicantNotification

    ApplicantNotification.objects.filter(applicant=applicant, is_read=False).update(is_read=True)
    return JsonResponse({"success": True, "unread_count": 0})


def applicant_notifications_mark_read(request, notification_id):
    if request.method != "POST":
        return JsonResponse({"success": False}, status=400)
    applicant = _get_session_applicant(request)
    if applicant is None:
        return JsonResponse({"success": False}, status=403)

    from .models import ApplicantNotification

    notif = get_object_or_404(
        ApplicantNotification, id=notification_id, applicant=applicant
    )
    notif.is_read = True
    notif.save(update_fields=["is_read"])
    return JsonResponse({
        "success": True,
        "unread_count": ApplicantNotification.objects.filter(
            applicant=applicant, is_read=False
        ).count(),
        "link": notif.link or "",
    })


def applicant_notifications_delete(request, notification_id):
    """Permanently dismiss a single applicant notification."""
    if request.method != "POST":
        return JsonResponse({"success": False}, status=400)
    applicant = _get_session_applicant(request)
    if applicant is None:
        return JsonResponse({"success": False}, status=403)

    from .models import ApplicantNotification

    ApplicantNotification.objects.filter(id=notification_id, applicant=applicant).delete()
    return JsonResponse({
        "success": True,
        "unread_count": ApplicantNotification.objects.filter(
            applicant=applicant, is_read=False
        ).count(),
    })


def applicant_notifications_page(request):
    """Full 'view all' notifications page for the applicant dashboard."""
    from django.core.paginator import Paginator

    from .models import ApplicantNotification

    applicant = _get_session_applicant(request)
    if applicant is None:
        return redirect("applicants_home")

    qs = ApplicantNotification.objects.filter(applicant=applicant).order_by("-created_at")
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    return render(request, "Applicants/portal/portal_notifications.html", {
        "applicant": applicant,
        "notifications": page_obj.object_list,
        "unread_count": qs.filter(is_read=False).count(),
        "has_previous": page_obj.has_previous(),
        "has_next": page_obj.has_next(),
        "page_obj": page_obj,
    })
