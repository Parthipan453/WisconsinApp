from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import BooleanField, Count, Exists, ExpressionWrapper, OuterRef, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

from Admin.models import User
from Applicants.models import (
    Application,
    ApplicationReviewAssignment,
    ApplicationLog,
    FeePayment,
)
from Applicants.services.applicant_service import ApplicantService
from Applicants.services.review_context import build_review_context

from .services import notify_reviewer_assignment, notify_decision

from notifications.utils import (
    notify_application,
    notify_live_admins,
    notify_live_user,
    notify_applicant,
    notify_user,
)


service = ApplicantService()

DECISION_MAP = {
    "admit": "admitted",
    "waitlist": "waitlisted",
    "deny": "denied",
}

DECISION_NOTICE_MESSAGES = {
    "admitted": (
        "Congratulations! Your application for admission has been approved. "
        "Check your dashboard for your offer letter and next steps."
    ),
    "waitlisted": (
        "Your application has been placed on our waitlist. You will be notified "
        "if a place becomes available."
    ),
    "denied": (
        "We have carefully reviewed your application, but we are unable to offer "
        "you admission at this time."
    ),
}


def _decision_message(app, decision_key):
    return DECISION_NOTICE_MESSAGES.get(
        decision_key,
        f"Your application {app.Reference_id} has been updated.",
    )

ADMISSIONS_STATUSES = (
    "submitted", "awaiting_materials",
    "complete", "under_review", "admitted", "offer_accepted", "waitlisted",
    "denied", "enrolled", "withdrawn", "archived",
)

STATUS_LABEL_OVERRIDES = {
    "awaiting_materials": "Reviewed",
}


def _get_staff_reviewers():
    return User.objects.filter(
        staff_profile__isnull=False, account_status="ACTIVE"
    ).select_related("staff_profile").order_by("first_name", "last_name", "username")


def _status_applications(status):
    """Applications in a given status, annotated with payment state.
    If status is empty, returns all applications."""
    paid_exists = FeePayment.objects.filter(
        application_id=OuterRef("pk"), status="completed"
    )
    qs = Application.objects.annotate(
        paid=Exists(paid_exists),
        waived=ExpressionWrapper(
            Q(fee_waiver_approved=True), output_field=BooleanField()
        ),
    )
    if status:
        qs = qs.filter(status=status)
    return qs


@login_required
def applications(request):
    status = request.GET.get("status", "").strip()
    if status and status not in ADMISSIONS_STATUSES:
        status = ""

    payment = request.GET.get("payment", "").strip()
    query = request.GET.get("q", "").strip()
    assignment = request.GET.get("assignment", "").strip()
    view_mode = request.GET.get("view", "cards").strip()
    if view_mode not in ("cards", "table"):
        view_mode = "cards"

    apps = _status_applications(status).select_related(
        "applicant",
        "university",
        "degree_level",
        "program",
        "admission_cycle",
        "review_assignment__reviewer",
    ).order_by("-submitted_date", "-created_date")

    if payment == "paid":
        apps = apps.filter(Q(paid=True) | Q(waived=True))
    elif payment == "unpaid":
        apps = apps.filter(paid=False, waived=False)

    if assignment == "assigned":
        apps = apps.filter(review_assignment__isnull=False)
    elif assignment == "unassigned":
        apps = apps.filter(review_assignment__isnull=True)

    if query:
        apps = apps.filter(
            Q(Reference_id__icontains=query)
            | Q(applicant__first_name__icontains=query)
            | Q(applicant__last_name__icontains=query)
            | Q(applicant__email__icontains=query)
        )

    paginator = Paginator(apps, 25)
    page_obj = paginator.get_page(request.GET.get("page"))

    for app in page_obj.object_list:
        fee = service.get_application_fee_for(app)
        app.fee_label = f"${fee:.2f}" if fee is not None else "No fee"
        app.display_status = STATUS_LABEL_OVERRIDES.get(app.status, app.get_status_display())

    current = _status_applications(status)
    current_total = current.count()
    paid_total = current.filter(Q(paid=True) | Q(waived=True)).count()
    waived_total = current.filter(waived=True).count()
    assigned_total = current.filter(review_assignment__isnull=False).count()

    status_counts = {
        row["status"]: row["n"]
        for row in Application.objects.filter(status__in=ADMISSIONS_STATUSES)
        .values("status")
        .annotate(n=Count("pk"))
    }

    stats = {
        "total": current_total,
        "paid": paid_total,
        "unpaid": current_total - paid_total,
        "waived": waived_total,
        "assigned": assigned_total,
        "unassigned": current_total - assigned_total,
    }

    status_choices = dict(Application.STATUS_CHOICES)
    payment_items = [
        {"key": "", "label": "All fees", "count": current_total},
        {"key": "paid", "label": "Paid", "count": paid_total},
        {"key": "unpaid", "label": "Not paid", "count": stats["unpaid"]},
    ]
    status_items = [
        {"key": key, "label": STATUS_LABEL_OVERRIDES.get(key, status_choices.get(key, key)), "count": status_counts.get(key, 0)}
        for key in ADMISSIONS_STATUSES
    ]

    status_label = STATUS_LABEL_OVERRIDES.get(status, status_choices.get(status, status)) if status else "All Applications"

    context = {
        "page_obj": page_obj,
        "stats": stats,
        "status": status,
        "status_label": status_label,
        "status_items": status_items,
        "payment_items": payment_items,
        "payment": payment,
        "query": query,
        "assignment": assignment,
        "view_mode": view_mode,
    }

    if request.GET.get("partial") == "region":
        return render(request, "Eric/partials/applications_region.html", context)

    return render(request, "Eric/applications.html", context)


def _application_context(request, application_id):
    context = build_review_context(application_id)
    context["reviewers"] = _get_staff_reviewers()
    context["decided_statuses"] = (
        "admitted", "offer_accepted", "waitlisted", "denied", "enrolled", "withdrawn",
    )
    context["is_admin_user"] = bool(
        request.user.is_admin or request.user.is_super_admin
    )
    context["sidebar_workflow_include"] = "Eric/partials/admin_workflow.html"
    from Admin.Colleges.models import AcademicProgram
    context["all_programs"] = AcademicProgram.objects.filter(status="ACTIVE").select_related(
        "department", "degree"
    ).order_by("program_name")
    return context


@login_required
def application_detail(request, application_id):
    context = _application_context(request, application_id)
    if request.GET.get("partial") == "body":
        return render(request, "Eric/partials/application_sections.html", context)
    return render(
        request,
        "Eric/application_detail.html",
        context,
    )


@login_required
def assign_reviewer(request, application_id):
    app = get_object_or_404(Application, application_id=application_id)

    if request.method != "POST":
        return redirect("applications")

    reviewer_id = request.POST.get("reviewer_id", "").strip()
    if not reviewer_id or not reviewer_id.isdigit():
        messages.error(request, "Please choose a staff reviewer to assign.")
        return redirect("application_detail", application_id=app.application_id)

    reviewer = get_object_or_404(User, pk=int(reviewer_id))
    if not hasattr(reviewer, "staff_profile"):
        messages.error(request, "The selected user is not a staff reviewer.")
        return redirect("application_detail", application_id=app.application_id)

    assignment, created = ApplicationReviewAssignment.objects.update_or_create(
        application=app,
        defaults={
            "reviewer": reviewer,
            "assigned_by": request.user,
            "status": "assigned",
            "is_verified": False,
            "started_at": None,
            "completed_at": None,
            "recommendation_note": "",
            "decision_note": "",
        },
    )

    ApplicationLog.objects.create(
        application=app,
        field_name="review_assignment",
        old_value="",
        new_value=f"Assigned to {reviewer.get_full_name() or reviewer.username}",
        actor=request.user.get_full_name() or request.user.username,
    )

    if app.status == "submitted":
        service.update_status(
            app, "under_review", actor=request.user.get_full_name() or request.user.username,
            note="Assigned to reviewer for evaluation",
        )

    notify_reviewer_assignment(app, reviewer, request.user)
    notify_application(app, "assignment_created")
    notify_live_user(reviewer.id, "my_reviews_changed")
    notify_live_admins("admin_queue_changed")

    applicant_name = f"{app.applicant.first_name} {app.applicant.last_name}".strip()
    notify_user(
        reviewer.id,
        f"New review assigned: {app.Reference_id}",
        f"{applicant_name or 'An applicant'} application assigned to you for review.",
        "INFO",
        link=f"/staff/{reviewer.uuid}/admissions/reviews/{app.application_id}/",
    )
    notify_applicant(
        app.applicant,
        f"Application {app.Reference_id} is under review",
        "An admissions reviewer has been assigned to your application.",
        "INFO",
        link=f"/applicants/?state=status&app_id={app.application_id}",
    )

    verb = "reassigned" if not created else "assigned"
    messages.success(request, f"Application {app.Reference_id} {verb} to {reviewer.get_full_name() or reviewer.username}.")
    return redirect("application_detail", application_id=app.application_id)


@login_required
def decide(request, application_id):
    app = get_object_or_404(Application, application_id=application_id)

    if request.method != "POST":
        return redirect("application_detail", application_id=app.application_id)

    assignment = getattr(app, "review_assignment", None)
    if assignment is None:
        messages.error(
            request,
            "Assign the application to a staff reviewer before making a decision.",
        )
        return redirect("application_detail", application_id=app.application_id)
    if not assignment.is_verified:
        messages.error(
            request,
            "The reviewer has not finished verifying this application yet. Decisions can only be made after verification.",
        )
        return redirect("application_detail", application_id=app.application_id)

    decision = request.POST.get("decision", "").strip()
    decision_note = request.POST.get("decision_note", "").strip()

    if decision not in DECISION_MAP:
        messages.error(request, "Invalid decision.")
        return redirect("application_detail", application_id=app.application_id)

    new_status = DECISION_MAP[decision]
    actor = request.user.get_full_name() or request.user.username
    service.update_status(
        app,
        new_status,
        actor=actor,
        note=decision_note or f"Decision: {decision.title()}",
    )

    assignment.status = "decided"
    assignment.decision_note = decision_note
    assignment.completed_at = timezone.now()
    assignment.save(update_fields=["status", "decision_note", "completed_at", "updated_at"])

    ApplicationLog.objects.create(
        application=app,
        field_name="admission_decision",
        old_value="",
        new_value=f"{decision.title()} by {actor}",
        actor=actor,
    )

    if decision == "admit":
        app.offer_status = "pending"
        app.offer_sent_at = timezone.now()
        app.offer_note = decision_note
        app.save(update_fields=["offer_status", "offer_sent_at", "offer_note"])

        _send_offer_letter_email(app)

        notify_decision(app, new_status, decision_note)
        messages.success(request, f"{app.Reference_id} admitted — offer letter sent to applicant.")
    else:
        notify_decision(app, new_status, decision_note)
        messages.success(request, f"{app.Reference_id} marked as {new_status}.")

    notify_application(app, "decision_made")
    notify_live_user(assignment.reviewer_id, "my_reviews_changed")
    notify_live_admins("admin_queue_changed")

    adjust = "admitted" if decision == "admit" else new_status
    is_positive = decision == "admit"
    notify_applicant(
        app.applicant,
        f"Application {app.Reference_id}: {adjust.replace('_', ' ').title()}",
        _decision_message(app, adjust),
        "SUCCESS" if is_positive else "WARNING",
        link=f"/applicants/?state=status&app_id={app.application_id}",
    )
    notify_user(
        assignment.reviewer_id,
        f"Decision recorded: {app.Reference_id}",
        f"{app.Reference_id} was {adjust.replace('_', ' ')} by {request.user.get_full_name() or request.user.username}.",
        "INFO",
        link=f"/dashboard/applications/{app.application_id}/",
    )

    return redirect("application_detail", application_id=app.application_id)


def _send_offer_letter_email(app):
    """Send the offer letter email to the applicant."""
    applicant_name = f"{app.applicant.first_name} {app.applicant.last_name}".strip()
    program_name = app.program.program_name if app.program else "N/A"
    cycle_name = app.admission_cycle.name if app.admission_cycle else "Current"
    contact_email = getattr(settings, "APPLICANT_CONTACT_EMAIL", "contact@go.wisconsin.edu")
    site_url = getattr(settings, "SITE_URL", "http://127.0.0.1:8000")
    portal_url = f"{site_url}/applicants/?state=status&app_id={app.application_id}"

    deadline = app.admission_cycle.application_deadline if app.admission_cycle else None
    deadline_display = deadline.strftime("%B %d, %Y") if deadline else "as soon as possible"

    ctx = {
        "applicant_name": applicant_name,
        "reference_id": app.Reference_id,
        "program_name": program_name,
        "cycle_name": cycle_name,
        "offer_note": app.offer_note or "",
        "deposit_amount": app.deposit_amount,
        "deadline_display": deadline_display,
        "portal_url": portal_url,
        "contact_email": contact_email,
    }

    subject = f"Admission Offer — {app.Reference_id} — {program_name}"
    html_body = render_to_string("Applicants/emails/offer_letter.html", ctx)
    txt_body = render_to_string("Applicants/emails/offer_letter.txt", ctx)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=txt_body,
        from_email=contact_email,
        to=[app.applicant.email],
    )
    msg.attach_alternative(html_body, "text/html")
    msg.send(fail_silently=True)


@login_required
def promote_from_waitlist(request, application_id):
    """Promote a waitlisted applicant to admitted status."""
    app = get_object_or_404(Application, application_id=application_id)
    if request.method != "POST":
        return redirect("application_detail", application_id=app.application_id)

    if app.status != "waitlisted":
        messages.error(request, "This application is not currently waitlisted.")
        return redirect("application_detail", application_id=app.application_id)

    actor = request.user.get_full_name() or request.user.username
    decision_note = request.POST.get("decision_note", "").strip()
    service.update_status(
        app,
        "admitted",
        actor=actor,
        note=decision_note or "Promoted from waitlist",
    )

    assignment = getattr(app, "review_assignment", None)
    if assignment:
        assignment.status = "decided"
        assignment.decision_note = decision_note or "Promoted from waitlist"
        assignment.completed_at = timezone.now()
        assignment.save(update_fields=["status", "decision_note", "completed_at", "updated_at"])

    ApplicationLog.objects.create(
        application=app,
        field_name="waitlist_promotion",
        old_value="waitlisted",
        new_value=f"Promoted to admitted by {actor}",
        actor=actor,
    )

    app.offer_status = "pending"
    app.offer_sent_at = timezone.now()
    app.offer_note = decision_note or "Promoted from waitlist"
    app.save(update_fields=["offer_status", "offer_sent_at", "offer_note"])

    _send_offer_letter_email(app)

    notify_decision(app, "admitted", decision_note or "You have been promoted from the waitlist and admitted!")
    notify_application(app, "decision_made")
    reviewer = assignment.reviewer_id if assignment else None
    if not reviewer:
        try:
            reviewer = app.review_assignment.reviewer_id
        except Exception:
            reviewer = None
    if reviewer:
        notify_live_user(reviewer, "my_reviews_changed")
    notify_live_admins("admin_queue_changed")

    notify_applicant(
        app.applicant,
        f"Application {app.Reference_id}: Admitted",
        DECISION_NOTICE_MESSAGES["admitted"],
        "SUCCESS",
        link=f"/applicants/?state=status&app_id={app.application_id}",
    )

    messages.success(request, f"{app.Reference_id} promoted from waitlist — offer letter sent.")
    return redirect("application_detail", application_id=app.application_id)


@login_required
def update_program(request, application_id):
    """Admin changes the assigned program for an offer-accepted applicant."""
    app = get_object_or_404(Application, application_id=application_id)
    if request.method != "POST":
        return redirect("application_detail", application_id=app.application_id)

    if app.status != "offer_accepted":
        messages.error(request, "Program can only be changed for offer-accepted applications.")
        return redirect("application_detail", application_id=app.application_id)

    program_id = request.POST.get("program_id", "").strip()
    if not program_id or not program_id.isdigit():
        messages.error(request, "Please select a valid program.")
        return redirect("application_detail", application_id=app.application_id)

    from Admin.Colleges.models import AcademicProgram
    new_program = get_object_or_404(AcademicProgram, pk=int(program_id), status="ACTIVE")

    old_program_name = app.program.program_name if app.program else "(none)"
    actor = request.user.get_full_name() or request.user.username

    app.program = new_program
    app.save(update_fields=["program"])

    ApplicationLog.objects.create(
        application=app,
        field_name="program_changed",
        old_value=old_program_name,
        new_value=f"{new_program.program_name} by {actor}",
        actor=actor,
    )

    messages.success(
        request,
        f"Program changed from \"{old_program_name}\" to \"{new_program.program_name}\".",
    )
    notify_application(app, "status_changed")
    notify_live_admins("admin_queue_changed")
    return redirect("application_detail", application_id=app.application_id)


@login_required
def create_student(request, application_id):
    """Admin creates a student account from an offer-accepted application."""
    app = get_object_or_404(Application, application_id=application_id)
    if request.method != "POST":
        return redirect("application_detail", application_id=app.application_id)

    if app.status not in ("offer_accepted", "enrolled"):
        messages.error(request, "Application must be offer-accepted to create a student account.")
        return redirect("application_detail", application_id=app.application_id)

    if app.applicant.converted_to_user_id:
        messages.error(request, "A student account already exists for this applicant.")
        return redirect("application_detail", application_id=app.application_id)

    from Students.Eric.services import create_student_from_application
    try:
        result = create_student_from_application(
            app.application_id,
            created_by=request.user.get_full_name() or request.user.username,
        )
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("application_detail", application_id=app.application_id)

    messages.success(
        request,
        f"Student account created — {result['student_number']} ({result['university_email']}). "
        f"Welcome email sent to applicant's personal email.",
    )
    notify_application(app, "decision_made")
    notify_live_admins("admin_queue_changed")
    return redirect("application_detail", application_id=app.application_id)
