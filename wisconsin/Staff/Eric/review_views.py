"""Staff admissions review workflow (Eric)."""

import json

from django.conf import settings
from django.http import JsonResponse

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from Admin.Colleges.models import AcademicProgram
from Applicants.models import (
    AdmissionCycle,
    Application,
    ApplicationLog,
    ApplicationReviewAssignment,
    Document,
    DocumentRequirement,
    FieldCorrectionRequest,
    FieldResponse,
    FieldReview,
    MaterialRequest,
    SectionReview,
)
from Applicants.services.applicant_service import ApplicantService
from Applicants.services.form_engine import DynamicFormEngine
from Applicants.services.review_context import (
    _format_field_response,
    build_review_context,
    build_review_materials,
    get_review_readiness,
)

from Admin.Eric.services import (
    notify_field_corrections,
    notify_material_request,
    notify_missing_materials,
    notify_ready_for_decision,
)

from notifications.utils import (
    notify_application,
    notify_live_admins,
    notify_live_user,
    notify_applicant,
    notify_all_admins,
)

# The five categories a reviewer actually cares about. Each requestable
# category maps to a DocumentRequirement where one exists; payment and
# high school grades have no uploadable file, so they fall back to a
# generic doc_type request.
REQUEST_CATEGORIES = [
    ("transcript", "Transcript", "transcript_hs"),
    ("essays", "Essays", "personal_statement"),
    ("test_scores", "Test scores", "english_proficiency"),
    ("payment", "Application fee", None),
    ("grades", "High school grades", None),
]

from .validators import check_owner_access

service = ApplicantService()


def _get_assignment_or_none(request, application_id):
    app = get_object_or_404(Application, application_id=application_id)
    assignment = getattr(app, "review_assignment", None)
    if assignment is None:
        return app, None
    if assignment.reviewer_id != request.user.id:
        return app, None
    return app, assignment


@login_required
def my_reviews(request, user_uuid):
    access_response, staff_profile = check_owner_access(request, user_uuid)
    if access_response:
        return access_response

    filter_key = request.GET.get("filter", "active")
    query = (request.GET.get("q") or "").strip()
    program_id = request.GET.get("program") or ""
    cycle_id = request.GET.get("semester") or ""

    qs = (
        ApplicationReviewAssignment.objects.filter(
            reviewer=request.user
        )
        .select_related(
            "application__applicant",
            "application__university",
            "application__program",
            "application__degree_level",
            "application__admission_cycle",
            "assigned_by",
        )
        .annotate(
            docs_total=Count("application__documents", distinct=True),
            docs_verified=Count(
                "application__documents",
                filter=Q(application__documents__is_verified=True),
                distinct=True,
            ),
            docs_unverified=Count(
                "application__documents",
                filter=Q(application__documents__is_verified=False),
                distinct=True,
            ),
        )
    )

    if filter_key == "ready_for_decision":
        qs = qs.filter(status="ready_for_decision")
    elif filter_key == "awaiting_materials":
        qs = qs.filter(status="awaiting_materials")
    elif filter_key == "completed":
        qs = qs.filter(status="decided")
    else:
        qs = qs.exclude(status="decided")

    if query:
        qs = qs.filter(
            Q(application__applicant__first_name__icontains=query)
            | Q(application__applicant__last_name__icontains=query)
            | Q(application__Reference_id__icontains=query)
            | Q(application__applicant__email__icontains=query)
        )

    if program_id:
        qs = qs.filter(application__program_id=program_id)

    if cycle_id:
        qs = qs.filter(application__admission_cycle_id=cycle_id)

    base = ApplicationReviewAssignment.objects.filter(reviewer=request.user)
    counts = {
        "active": base.exclude(status="decided").count(),
        "awaiting_materials": base.filter(status="awaiting_materials").count(),
        "ready_for_decision": base.filter(status="ready_for_decision").count(),
        "completed": base.filter(status="decided").count(),
    }

    status_items = [
        {"key": "active", "label": "Active", "count": counts["active"]},
        {
            "key": "awaiting_materials",
            "label": "Awaiting Materials",
            "count": counts["awaiting_materials"],
        },
        {
            "key": "ready_for_decision",
            "label": "Ready for Decision",
            "count": counts["ready_for_decision"],
        },
        {"key": "completed", "label": "Completed", "count": counts["completed"]},
    ]

    programs = (
        AcademicProgram.objects.filter(
            applications__review_assignment__reviewer=request.user
        )
        .distinct()
        .order_by("program_name")
    )

    cycles = (
        AdmissionCycle.objects.filter(
            applications__review_assignment__reviewer=request.user
        )
        .distinct()
        .order_by("-application_deadline")
    )

    context = {
        "assignments": qs,
        "filter_key": filter_key,
        "counts": counts,
        "status_items": status_items,
        "programs": programs,
        "program": program_id,
        "cycles": cycles,
        "semester": cycle_id,
        "query": query,
    }

    partial = request.GET.get("partial", "")
    if partial == "rows":
        return render(request, "Eric/partials/live/review_rows.html", context)

    return render(request, "Eric/review_list.html", context)


@login_required
def review_detail(request, user_uuid, application_id):
    access_response, staff_profile = check_owner_access(request, user_uuid)
    if access_response:
        return access_response

    app, assignment = _get_assignment_or_none(request, application_id)
    if assignment is None:
        messages.error(
            request, "This application is not assigned to you for review."
        )
        return redirect("my_reviews", user_uuid=user_uuid)

    context = _build_review_detail_context(request, application_id, assignment)

    partial = request.GET.get("partial", "")
    if partial == "workspace":
        return render(request, "Eric/partials/live/workspace.html", context)
    if partial == "workflow":
        return render(request, "Eric/partials/staff_workflow.html", context)

    issue_draft = request.session.pop("issue_email_draft", None)
    if issue_draft:
        context["issue_email_draft"] = issue_draft

    return render(request, "Eric/review_detail.html", context)


def _build_review_detail_context(request, application_id, assignment):
    """Shared context for the review page and its ?partial= workspace block."""
    context = build_review_context(application_id)
    context["doc_types"] = Document.DOC_TYPES
    context["requirements"] = DocumentRequirement.objects.all().order_by("name")
    context["unverified_docs_count"] = context["documents"].filter(
        is_verified=False
    ).count()
    context["request_options"] = [
        {"key": key, "label": label} for key, label, _ in REQUEST_CATEGORIES
    ]
    # Pre-review (not yet started): the page is a materials checklist.
    # Once the review has started the same route becomes the review itself
    # and shows the full form responses instead.
    if assignment.status == "assigned":
        context["review_materials"] = build_review_materials(
            context["app"], context["form_groups"]
        )
    else:
        from Applicants.services.review_context import MANUAL_SECTION_DEFS, _load_offline_pages

        section_reviews = assignment.section_reviews.all()
        context["section_reviews"] = section_reviews

        form_groups = context["form_groups"]
        form_group_codes = [f"academics_{i}" for i in range(len(form_groups))]
        context["form_group_codes"] = form_group_codes

        excluded = {"academics", "essays", "additional"}
        base_count = len([s for s in MANUAL_SECTION_DEFS if s["code"] not in excluded])
        context["section_defs"] = MANUAL_SECTION_DEFS

        offline_pages = []
        offline_text_available = False
        offline_sections = []
        app = context["app"]
        if app.apply_method == "offline" and app.offline_form_pdf:
            offline_pages = _load_offline_pages(app)
            offline_text_available = any(p.get("text") for p in offline_pages)
            from Applicants.services.offline_parser import widget_values_by_section
            from Applicants.models import FormField, FormSection

            widget_data = widget_values_by_section(offline_pages)
            _REVIEW_SECTION_ORDER = [
                "personal_info", "contact_info",
                "parent_guardian_info", "residency_info",
                "high_school", "higher_education_check", "test_scores",
                "activities", "work_experience", "essay",
            ]
            _order_map = {t: i for i, t in enumerate(_REVIEW_SECTION_ORDER)}

            for scode, fields_map in widget_data.items():
                section_obj = FormSection.objects.filter(code=scode).first()
                section_title = section_obj.title if section_obj else scode.replace("_", " ").title()
                fields = []
                for fc, val in fields_map.items():
                    field_obj = FormField.objects.filter(section__code=scode, code=fc).first()
                    label = field_obj.label if field_obj else fc.replace("_", " ").title()
                    fields.append({"label": label, "value": val})
                offline_sections.append({
                    "code": scode,
                    "title": section_title,
                    "fields": fields,
                    "order": _order_map.get(scode, 999),
                })
            offline_sections.sort(key=lambda s: s["order"])
        context["offline_pages"] = offline_pages
        context["offline_text_available"] = offline_text_available
        context["offline_test_scores"] = app.offline_extracted_test_scores or []
        context["offline_pdf_name"] = app.offline_form_pdf.name if app.offline_form_pdf else ""
        base_codes = {s["code"] for s in MANUAL_SECTION_DEFS if s["code"] not in excluded}
        offline_sections = [s for s in offline_sections if s["code"] not in base_codes]
        context["offline_sections"] = offline_sections

        if app.apply_method == "offline":
            context["section_total"] = base_count + len(offline_sections)
        else:
            context["section_total"] = base_count + len(form_group_codes)
    context["is_assigned_reviewer"] = assignment.reviewer_id == request.user.id
    context["sidebar_workflow_include"] = "Eric/partials/staff_workflow.html"
    return context


@login_required
def save_section_review(request, user_uuid, application_id):
    """Save the reviewer's manual verdict + note for one checklist section."""
    access_response, staff_profile = check_owner_access(request, user_uuid)
    if access_response:
        return access_response

    app, assignment = _get_assignment_or_none(request, application_id)
    if assignment is None:
        messages.error(request, "This application is not assigned to you.")
        return redirect("my_reviews", user_uuid=user_uuid)

    if request.method == "POST":
        code = request.POST.get("section_code", "").strip()
        status = request.POST.get("status", "not_reviewed").strip()
        note = request.POST.get("note", "").strip()
        applicant_question = request.POST.get("applicant_question", "").strip()
        internal_note = request.POST.get("internal_note", "").strip()

        from Applicants.services.review_context import MANUAL_SECTION_DEFS

        base_code = code.split("_")[0] if code.startswith("academics_") else code
        if code.startswith("page_"):
            base_code = "academics"
        section_def = next(
            (d for d in MANUAL_SECTION_DEFS if d["code"] == base_code), None
        )
        if section_def is None:
            from Applicants.models import FormSection
            fs = FormSection.objects.filter(code=base_code).first()
            if fs:
                section_def = {"code": base_code, "title": fs.title, "icon": "ti-file"}
            else:
                section_def = {"code": base_code, "title": base_code.replace("_", " ").title(), "icon": "ti-file"}

        if status not in ("not_reviewed", "reviewed", "issue", "issue_solved"):
            status = "not_reviewed"

        if assignment.status in ("assigned", "ready_for_decision") and status != "not_reviewed":
            if assignment.status == "assigned":
                assignment.status = "in_progress"
                assignment.started_at = timezone.now()
            else:
                assignment.status = "in_progress"
                assignment.is_verified = False
                assignment.recommendation = ""
                assignment.recommendation_note = ""
                assignment.completed_at = None
            assignment.save(
                update_fields=[
                    "status", "started_at", "is_verified",
                    "recommendation", "recommendation_note", "completed_at",
                    "updated_at",
                ]
            )

        review, _ = SectionReview.objects.update_or_create(
            assignment=assignment,
            section_code=code,
            defaults={
                "section_title": section_def["title"],
                "status": status,
                "note": applicant_question or note,
                "internal_note": internal_note,
                "reviewed_by": request.user,
                "reviewed_at": timezone.now() if status != "not_reviewed" else None,
                "is_full_crud": not code.startswith("academics_"),
            },
        )

        actor = request.user.get_full_name() or request.user.username
        status_label = review.get_status_display()
        ApplicationLog.objects.create(
            application=app,
            field_name="section_review",
            old_value="",
            new_value=f"{section_def['title']} → {status_label}"
            + (f" — {note}" if note else ""),
            actor=actor,
        )
        messages.success(request, f"{section_def['title']} saved as {status_label}.")
        notify_application(app, "section_reviewed")

        if status == "issue":
            contact_email = getattr(settings, "APPLICANT_CONTACT_EMAIL", "contact@go.wisconsin.edu")
            applicant_name = f"{app.applicant.first_name} {app.applicant.last_name}".strip()
            email_subject = f"Action needed on {app.Reference_id}: issue found in {section_def['title']}"
            email_body = (
                f"Dear {applicant_name},\n\n"
                f"While reviewing your application (Reference: {app.Reference_id}), an issue was identified in the following section:\n\n"
                f"Section: {section_def['title']}\n\n"
                f"Please reply to this email to provide clarification or correct the information.\n\n"
                f"If you have questions, contact us at {contact_email}.\n\n"
                f"Regards,\nOffice of Admissions\n{contact_email}"
            )
            email_draft = {
                "to": app.applicant.email,
                "subject": email_subject,
                "body": email_body,
                "section_title": section_def["title"],
            }
        else:
            email_draft = None

        section_reviews = assignment.section_reviews.all()
        reviewed_count = section_reviews.filter(status="reviewed").count()
        issue_count = section_reviews.filter(status="issue").count()
        issue_solved_count = section_reviews.filter(status="issue_solved").count()
        not_reviewed_count = section_reviews.filter(status="not_reviewed").count()

        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
        if is_ajax:
            return JsonResponse({
                "ok": True,
                "section_code": code,
                "status": status,
                "status_label": status_label,
                "internal_note": internal_note,
                "section_title": section_def["title"],
                "reviewed_count": reviewed_count,
                "issue_count": issue_count,
                "issue_solved_count": issue_solved_count,
                "not_reviewed_count": not_reviewed_count,
                "email_draft": email_draft,
            })

        if email_draft:
            request.session["issue_email_draft"] = email_draft

    return redirect("review_detail", user_uuid=user_uuid, application_id=app.application_id)


@login_required
def extract_offline_pdf(request, user_uuid, application_id):
    """(Re)extract text from the uploaded offline application PDF."""
    access_response, staff_profile = check_owner_access(request, user_uuid)
    if access_response:
        return access_response

    app, assignment = _get_assignment_or_none(request, application_id)
    if assignment is None:
        messages.error(request, "This application is not assigned to you.")
        return redirect("my_reviews", user_uuid=user_uuid)

    if request.method == "POST" and app.offline_form_pdf:
        from Applicants.services.review_context import _load_offline_pages
        from Applicants.services.offline_parser import extract_offline_content

        app.offline_form_text = None
        app.save(update_fields=["offline_form_text", "updated_date"])
        pages = _load_offline_pages(app)
        if not pages:
            messages.warning(
                request,
                "Could not open the PDF file. Check that the file exists in storage "
                "and is not corrupted. Re-upload the PDF from the applicant portal.",
            )
        elif any(p.get("text") for p in pages):
            messages.success(
                request,
                f"Extracted text from {len(pages)} page(s) of the uploaded PDF.",
            )
            extracted = extract_offline_content(app)
            if extracted["essays"] or extracted["test_scores"]:
                messages.success(
                    request,
                    "Re-read essays and test scores from the PDF text.",
                )
        else:
            messages.warning(
                request,
                "No text could be extracted -- the PDF appears to be a scanned form "
                "with no text layer. Install Tesseract OCR for automatic OCR, "
                "or open the PDF directly and review it manually.",
            )
        notify_application(app, "offline_extracted")
    return redirect("review_detail", user_uuid=user_uuid, application_id=app.application_id)


@login_required
def start_review(request, user_uuid, application_id):
    access_response, staff_profile = check_owner_access(request, user_uuid)
    if access_response:
        return access_response

    app, assignment = _get_assignment_or_none(request, application_id)
    if assignment is None:
        messages.error(request, "This application is not assigned to you.")
        return redirect("my_reviews", user_uuid=user_uuid)

    if request.method == "POST" and assignment.status == "assigned":
        readiness = get_review_readiness(app)
        if not readiness["ready"]:
            messages.error(
                request,
                "You cannot start the review yet — required materials are still "
                "missing from the applicant. Request them below first.",
            )
            return redirect(
                "review_detail",
                user_uuid=user_uuid,
                application_id=app.application_id,
            )
        assignment.status = "in_progress"
        assignment.started_at = timezone.now()
        assignment.save(update_fields=["status", "started_at", "updated_at"])
        actor = request.user.get_full_name() or request.user.username
        ApplicationLog.objects.create(
            application=app,
            field_name="review_start",
            old_value="",
            new_value="Review started by " + actor,
            actor=actor,
        )
        messages.success(request, "Review started.")
        notify_application(app, "review_started")
    return redirect("review_detail", user_uuid=user_uuid, application_id=app.application_id)


@login_required
def verify_document(request, user_uuid, application_id, document_id):
    access_response, staff_profile = check_owner_access(request, user_uuid)
    if access_response:
        return access_response

    app, assignment = _get_assignment_or_none(request, application_id)
    if assignment is None:
        messages.error(request, "This application is not assigned to you.")
        return redirect("my_reviews", user_uuid=user_uuid)

    doc = get_object_or_404(Document, pk=document_id, application=app)
    actor = request.user.get_full_name() or request.user.username
    if doc.is_verified:
        doc.is_verified = False
        doc.verified_by = ""
        doc.verified_at = None
        message = f"Verification removed for {doc.file_name}"
    else:
        doc.is_verified = True
        doc.verified_by = actor
        doc.verified_at = timezone.now()
        message = f"Verified {doc.file_name}"

    doc.save(update_fields=["is_verified", "verified_by", "verified_at"])
    ApplicationLog.objects.create(
        application=app,
        field_name="document_verification",
        old_value="",
        new_value=message,
        actor=actor,
    )
    messages.success(request, message + ".")
    notify_application(app, "documents_changed")
    return redirect("review_detail", user_uuid=user_uuid, application_id=app.application_id)


@login_required
def request_material(request, user_uuid, application_id):
    access_response, staff_profile = check_owner_access(request, user_uuid)
    if access_response:
        return access_response

    app, assignment = _get_assignment_or_none(request, application_id)
    if assignment is None:
        messages.error(request, "This application is not assigned to you.")
        return redirect("my_reviews", user_uuid=user_uuid)

    if request.method == "POST":
        category = request.POST.get("category", "").strip()
        message = request.POST.get("message", "").strip()

        requirement = None
        doc_type = ""
        if category:
            req_code = dict((k, c) for k, _, c in REQUEST_CATEGORIES).get(category)
            if req_code:
                requirement = DocumentRequirement.objects.filter(code=req_code).first()
            elif category in ("payment", "grades"):
                doc_type = "other"
                if not message:
                    message = (
                        "Application fee is still outstanding."
                        if category == "payment"
                        else "High school academic information is incomplete."
                    )
        else:
            doc_type = request.POST.get("doc_type", "").strip()
            requirement_id = request.POST.get("requirement_id", "").strip()
            if not doc_type and not requirement_id:
                messages.error(request, "Choose a document type or requirement.")
                return redirect("review_detail", user_uuid=user_uuid, application_id=app.application_id)
            if requirement_id.isdigit():
                requirement = DocumentRequirement.objects.filter(pk=int(requirement_id)).first()
            if not doc_type and requirement:
                doc_type = ""

        material_request = MaterialRequest.objects.create(
            application=app,
            requested_by=request.user,
            requirement=requirement,
            doc_type=doc_type,
            message=message,
            status="pending",
        )
        actor = request.user.get_full_name() or request.user.username
        ApplicationLog.objects.create(
            application=app,
            field_name="material_request",
            old_value="",
            new_value=f"Requested {material_request.get_doc_type_display() or requirement.name if requirement else 'material'} from applicant",
            actor=actor,
        )
        if assignment.status == "in_progress":
            assignment.status = "awaiting_materials"
            assignment.save(update_fields=["status", "updated_at"])
        if app.status in ("under_review", "submitted"):
            service.update_status(
                app, "awaiting_materials",
                actor=actor,
                note="Additional materials requested by reviewer",
            )
        notify_material_request(app, material_request)
        notify_application(app, "materials_requested")
        notify_applicant(
            app.applicant,
            f"Additional materials requested: {app.Reference_id}",
            material_request.message or "A reviewer requested additional materials for your application.",
            "WARNING",
            link=f"/applicants/?state=status&app_id={app.application_id}",
        )
        messages.success(request, "Material request sent to the applicant.")
    return redirect("review_detail", user_uuid=user_uuid, application_id=app.application_id)


@login_required
def request_missing_materials(request, user_uuid, application_id):
    access_response, staff_profile = check_owner_access(request, user_uuid)
    if access_response:
        return access_response

    app, assignment = _get_assignment_or_none(request, application_id)
    if assignment is None:
        messages.error(request, "This application is not assigned to you.")
        return redirect("my_reviews", user_uuid=user_uuid)

    if request.method == "POST":
        readiness = get_review_readiness(app)
        if readiness["ready"]:
            messages.info(request, "No missing materials — nothing to request.")
        else:
            req_by_code = {
                r.code: r
                for r in DocumentRequirement.objects.filter(is_required=True)
            }
            pending = MaterialRequest.objects.filter(application=app, status="pending")
            created = 0
            for item in readiness["missing"]:
                if item["code"].startswith("doc:"):
                    req = req_by_code.get(item["code"][4:])
                    if req and not pending.filter(requirement=req).exists():
                        MaterialRequest.objects.create(
                            application=app,
                            requested_by=request.user,
                            requirement=req,
                            message="Required material not yet received.",
                            status="pending",
                        )
                        created += 1

            actor = request.user.get_full_name() or request.user.username
            ApplicationLog.objects.create(
                application=app,
                field_name="materials_requested",
                old_value="",
                new_value=(
                    f"Emailed applicant for {len(readiness['missing'])} missing "
                    f"required material(s)"
                ),
                actor=actor,
            )
            if assignment.status == "in_progress":
                assignment.status = "awaiting_materials"
                assignment.save(update_fields=["status", "updated_at"])
            if app.status in ("under_review", "submitted"):
                service.update_status(
                    app,
                    "awaiting_materials",
                    actor=actor,
                    note="Missing required materials requested from applicant",
                )

            sent = notify_missing_materials(app, readiness["missing"])
            notify_application(app, "materials_requested")
            notify_applicant(
                app.applicant,
                f"Missing materials: {app.Reference_id}",
                "Your application is missing required materials. Please upload them from your dashboard.",
                "WARNING",
                link=f"/applicants/?state=status&app_id={app.application_id}",
            )
            if sent:
                messages.success(
                    request,
                    "Email sent to the applicant listing the missing materials.",
                )
            else:
                messages.warning(
                    request,
                    "Material requests recorded, but the email could not be sent.",
                )
    return redirect("review_detail", user_uuid=user_uuid, application_id=app.application_id)


@login_required
def mark_ready(request, user_uuid, application_id):
    access_response, staff_profile = check_owner_access(request, user_uuid)
    if access_response:
        return access_response

    app, assignment = _get_assignment_or_none(request, application_id)
    if assignment is None:
        messages.error(request, "This application is not assigned to you.")
        return redirect("my_reviews", user_uuid=user_uuid)

    if request.method == "POST" and not assignment.is_verified:
        unverified = app.documents.filter(is_verified=False).exists()
        if unverified:
            messages.warning(
                request,
                "Some uploaded documents are not verified yet. Mark them verified before submitting.",
            )
            return redirect("review_detail", user_uuid=user_uuid, application_id=app.application_id)

        if app.apply_method == "online":
            unsent = FieldReview.objects.filter(
                assignment=assignment,
                status="rejected",
                correction_request__isnull=True,
            ).exists()
            if unsent:
                messages.warning(
                    request,
                    "Some responses are flagged for correction but the applicant has not "
                    "been asked to fix them yet. Send the correction request first.",
                )
                return redirect(
                    "field_review",
                    user_uuid=user_uuid,
                    application_id=app.application_id,
                )

        recommendation = request.POST.get("recommendation", "").strip()
        recommendation_note = request.POST.get("recommendation_note", "").strip()
        valid_choices = {c[0] for c in ApplicationReviewAssignment.RECOMMENDATION_CHOICES}
        if recommendation not in valid_choices:
            messages.warning(request, "Choose a recommendation before submitting.")
            return redirect("review_detail", user_uuid=user_uuid, application_id=app.application_id)

        pending_sections = assignment.section_reviews.exclude(status="reviewed").exists()
        if pending_sections:
            messages.warning(
                request,
                "Not every section has been marked as reviewed yet. Review all sections "
                "before submitting your recommendation.",
            )
            return redirect("review_detail", user_uuid=user_uuid, application_id=app.application_id)

        assignment.is_verified = True
        assignment.recommendation = recommendation
        assignment.recommendation_note = recommendation_note
        assignment.status = "ready_for_decision"
        assignment.completed_at = timezone.now()
        assignment.save(update_fields=[
            "is_verified", "recommendation", "recommendation_note",
            "status", "completed_at", "updated_at",
        ])
        actor = request.user.get_full_name() or request.user.username
        ApplicationLog.objects.create(
            application=app,
            field_name="ready_for_decision",
            old_value="",
            new_value=f"Ready for decision by {actor} — {assignment.get_recommendation_display()}",
            actor=actor,
        )
        notify_ready_for_decision(app, assignment)
        notify_application(app, "ready_for_decision")
        notify_live_user(request.user.id, "my_reviews_changed")
        notify_live_admins("admin_queue_changed")
        notify_all_admins(
            "Ready for decision",
            f"Application {app.Reference_id} has been verified and awaits your final decision.",
            "REQUEST",
            link=f"/dashboard/applications/{app.application_id}/",
        )
        messages.success(request, "Application marked ready for the admission decision.")
    return redirect("review_detail", user_uuid=user_uuid, application_id=app.application_id)


# ---------------------------------------------------------------------------
# Field-by-field review of online form responses
# ---------------------------------------------------------------------------

HIDDEN_FIELD_TYPES = {"hidden", "heading", "section_break", "page_break"}


def _build_field_review_items(app, assignment):
    """Flatten every submitted form response into reviewable field items.

    Each item carries the stored value, the automatic validation result, and
    the reviewer's manual verdict (FieldReview) if one has been given yet.
    """
    reviews = {
        r.field_response_id: r
        for r in FieldReview.objects.filter(assignment=assignment)
    }
    engine = DynamicFormEngine()
    items = []
    for response in (
        app.form_responses.select_related("section")
        .prefetch_related("field_responses__field")
        .order_by("section__sort_order", "repeat_index")
    ):
        for fr in response.field_responses.select_related("field"):
            field = fr.field
            if field.field_type in HIDDEN_FIELD_TYPES or field.code.startswith("_"):
                continue
            valid, msg = engine.validate_field(field, fr.typed_value())
            review = reviews.get(fr.pk)
            items.append(
                {
                    "field_response": fr,
                    "field": field,
                    "section": response.section.title,
                    "section_code": response.section.code,
                    "repeat_index": response.repeat_index,
                    "value": _format_field_response(fr),
                    "file_url": fr.file or "",
                    "valid": valid,
                    "validation_msg": msg,
                    "review": review,
                }
            )
    return items


@login_required
def field_review(request, user_uuid, application_id):
    """Field-by-field review of every submitted form response.

    The reviewer works through each field, marking responses correct or
    flagging them for correction. Flagged fields accumulate in a cart that
    can be sent to the applicant as one correction request.
    """
    access_response, staff_profile = check_owner_access(request, user_uuid)
    if access_response:
        return access_response

    app, assignment = _get_assignment_or_none(request, application_id)
    if assignment is None:
        messages.error(
            request, "This application is not assigned to you for review."
        )
        return redirect("my_reviews", user_uuid=user_uuid)

    items = _build_field_review_items(app, assignment)

    groups = []
    by_key = {}
    for item in items:
        key = (item["section"], item["repeat_index"])
        if key not in by_key:
            by_key[key] = {
                "section": item["section"],
                "repeat_index": item["repeat_index"],
                "fields": [],
            }
            groups.append(by_key[key])
        by_key[key]["fields"].append(item)

    total = len(items)

    reviews = FieldReview.objects.filter(assignment=assignment)
    verified_count = reviews.filter(status="verified").count()
    rejected_count = reviews.filter(status="rejected").count()
    sent_count = reviews.filter(
        status="rejected", correction_request__isnull=False
    ).count()
    pending_count = total - verified_count - rejected_count

    cart = [
        {
            "section": r.field_response.response.section.title,
            "field": r.field_response.field,
            "review": r,
        }
        for r in reviews.filter(
            status="rejected", correction_request__isnull=True
        ).select_related("field_response__field", "field_response__response__section")
    ]

    return render(
        request,
        "Eric/field_review.html",
        {
            "app": app,
            "applicant": app.applicant,
            "assignment": assignment,
            "groups": groups,
            "verified_count": verified_count,
            "pending_count": pending_count,
            "rejected_count": rejected_count,
            "sent_count": sent_count,
            "total": total,
            "cart": cart,
            "correction_requests": app.field_correction_requests.all(),
        },
    )


@login_required
def field_review_verdict(request, user_uuid, application_id):
    access_response, staff_profile = check_owner_access(request, user_uuid)
    if access_response:
        return access_response

    app, assignment = _get_assignment_or_none(request, application_id)
    if assignment is None:
        messages.error(request, "This application is not assigned to you.")
        return redirect("my_reviews", user_uuid=user_uuid)

    if request.method == "POST":
        action = request.POST.get("action", "")
        field_response_id = request.POST.get("field_response_id", "")
        note = request.POST.get("note", "").strip()
        fr = get_object_or_404(FieldResponse, pk=field_response_id, response__application=app)

        review, _ = FieldReview.objects.get_or_create(
            assignment=assignment,
            field_response=fr,
            defaults={"application": app},
        )
        actor = request.user.get_full_name() or request.user.username
        if action == "verify":
            review.status = "verified"
            review.note = ""
        elif action == "reject":
            review.status = "rejected"
            review.note = note
        elif action == "reset":
            review.status = "pending"
            review.note = ""
        else:
            messages.error(request, "Unknown action.")
            return redirect("field_review", user_uuid=user_uuid, application_id=app.application_id)
        review.reviewed_by = request.user
        review.reviewed_at = timezone.now()
        review.save()

        label = f"{fr.response.section.title} / {fr.field.label}"
        verdict = {
            "verify": f"Verified {label}",
            "reject": f"Flagged {label} for correction",
            "reset": f"Review reset for {label}",
        }[action]
        ApplicationLog.objects.create(
            application=app,
            field_name="field_review",
            old_value="",
            new_value=verdict + (f" — {note}" if note else ""),
            actor=actor,
        )
        messages.success(request, verdict + ".")
    return redirect("field_review", user_uuid=user_uuid, application_id=app.application_id)


@login_required
def send_field_corrections(request, user_uuid, application_id):
    access_response, staff_profile = check_owner_access(request, user_uuid)
    if access_response:
        return access_response

    app, assignment = _get_assignment_or_none(request, application_id)
    if assignment is None:
        messages.error(request, "This application is not assigned to you.")
        return redirect("my_reviews", user_uuid=user_uuid)

    if request.method == "POST":
        cart = FieldReview.objects.filter(
            assignment=assignment,
            status="rejected",
            correction_request__isnull=True,
        ).select_related("field_response__field", "field_response__response__section")
        if not cart.exists():
            messages.error(request, "No flagged fields to send.")
            return redirect("field_review", user_uuid=user_uuid, application_id=app.application_id)

        message = request.POST.get("message", "").strip()
        correction_request = FieldCorrectionRequest.objects.create(
            application=app,
            requested_by=request.user,
            status="pending",
            message=message,
        )
        cart.update(correction_request=correction_request)

        field_items = [
            {
                "section": r.field_response.response.section.title,
                "label": r.field_response.field.label,
                "old_value": _format_field_response(r.field_response),
                "note": r.note,
            }
            for r in cart.select_related(
                "field_response__field", "field_response__response__section"
            )
        ]

        actor = request.user.get_full_name() or request.user.username
        ApplicationLog.objects.create(
            application=app,
            field_name="field_corrections_requested",
            old_value="",
            new_value=(
                f"Correction request sent to applicant for "
                f"{len(field_items)} flagged field(s)"
            ),
            actor=actor,
        )
        if assignment.status == "in_progress":
            assignment.status = "awaiting_materials"
            assignment.save(update_fields=["status", "updated_at"])
        if app.status in ("under_review", "submitted"):
            service.update_status(
                app,
                "awaiting_materials",
                actor=actor,
                note="Corrections requested for flagged responses",
            )

        sent = notify_field_corrections(app, correction_request, field_items)
        notify_application(app, "materials_requested")
        notify_applicant(
            app.applicant,
            f"Corrections needed: {app.Reference_id}",
            "A reviewer flagged some information in your application for correction.",
            "WARNING",
            link=f"/applicants/?state=status&app_id={app.application_id}",
        )
        if sent:
            messages.success(
                request,
                f"Correction request sent to the applicant for {len(field_items)} field(s).",
            )
        else:
            messages.warning(
                request,
                "Corrections recorded, but the email could not be sent.",
            )
    return redirect("field_review", user_uuid=user_uuid, application_id=app.application_id)
