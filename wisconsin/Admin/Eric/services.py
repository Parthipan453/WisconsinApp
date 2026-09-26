"""Email notifications for the admissions review workflow (Eric)."""

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

EMAIL_TEMPLATE_DIR = "Eric/emails"


def _send(template_name, subject, to, context, reply_to=None):
    try:
        text_body = render_to_string(f"{EMAIL_TEMPLATE_DIR}/{template_name}.txt", context)
        html_body = render_to_string(f"{EMAIL_TEMPLATE_DIR}/{template_name}.html", context)
    except Exception:
        logger.exception("Email template missing for %s", template_name)
        return False
    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to],
        reply_to=[reply_to] if reply_to else None,
    )
    message.attach_alternative(html_body, "text/html")
    try:
        return bool(message.send(fail_silently=False))
    except Exception:
        logger.exception("Could not send email %s to %s", template_name, to)
        return False


def _applicant_common(application):
    return {
        "applicant": application.applicant,
        "application": application,
        "reference": application.Reference_id,
        "contact_email": getattr(
            settings, "APPLICANT_CONTACT_EMAIL", "contact@go.wisconsin.edu"
        ),
    }


def notify_reviewer_assignment(application, reviewer, assigned_by):
    context = {
        "reviewer": reviewer,
        "assigned_by": assigned_by,
        "application": application,
        "reference": application.Reference_id,
        "applicant_name": f"{application.applicant.first_name} {application.applicant.last_name}".strip(),
        "program": getattr(application.program, "program_name", ""),
        "cycle": str(application.admission_cycle or ""),
    }
    return _send(
        "reviewer_assignment",
        f"New review assigned: {application.Reference_id}",
        reviewer.email,
        context,
    )


def notify_material_request(application, material_request, portal_url="/applicants/"):
    context = {
        **_applicant_common(application),
        "material_request": material_request,
        "doc_label": (
            material_request.get_doc_type_display()
            or (material_request.requirement.name if material_request.requirement else "")
            or "document"
        ),
        "message": material_request.message,
        "portal_url": portal_url,
    }
    return _send(
        "material_request",
        f"Action needed on {application.Reference_id}: additional materials requested",
        application.applicant.email,
        context,
    )


def notify_missing_materials(application, missing_items, portal_url="/applicants/"):
    """Send one combined email listing every required material still outstanding."""
    context = {
        **_applicant_common(application),
        "missing_items": missing_items,
        "portal_url": portal_url,
    }
    return _send(
        "materials_required",
        f"Action needed on {application.Reference_id}: missing application materials",
        application.applicant.email,
        context,
    )


def notify_ready_for_decision(application, assignment):
    context = {
        "admin_user": assignment.assigned_by,
        "reviewer": assignment.reviewer,
        "application": application,
        "reference": application.Reference_id,
        "applicant_name": f"{application.applicant.first_name} {application.applicant.last_name}".strip(),
        "recommendation": assignment.recommendation_note,
    }
    return _send(
        "ready_for_decision",
        f"Ready for decision: {application.Reference_id}",
        assignment.assigned_by.email,
        context,
    )


def notify_decision(application, decision, decision_note="", portal_url="/applicants/"):
    context = {
        **_applicant_common(application),
        "decision": decision,
        "decision_label": dict(application.STATUS_CHOICES).get(decision, decision.title()),
        "decision_note": decision_note,
        "portal_url": portal_url,
    }
    return _send(
        "admission_decision",
        f"Admission decision available for {application.Reference_id}",
        application.applicant.email,
        context,
    )


def notify_field_corrections(application, correction_request, field_items, portal_url="/applicants/"):
    """Email the applicant asking them to resend correct values for the
    fields the reviewer flagged as wrong on an online application."""
    context = {
        **_applicant_common(application),
        "correction_request": correction_request,
        "field_items": field_items,
        "portal_url": portal_url,
    }
    return _send(
        "field_corrections",
        f"Action needed on {application.Reference_id}: please correct your information",
        application.applicant.email,
        context,
    )


def notify_section_issue_found(application, section_title, applicant_question="", portal_url="/applicants/"):
    """Email the applicant when a reviewer flags an issue on a section."""
    assignment = getattr(application, "review_assignment", None)
    reviewer_email = assignment.reviewer.email if assignment and assignment.reviewer else None
    context = {
        **_applicant_common(application),
        "section_title": section_title,
        "applicant_question": applicant_question,
        "portal_url": portal_url,
    }
    return _send(
        "section_issue_found",
        f"Action needed on {application.Reference_id}: issue found in {section_title}",
        application.applicant.email,
        context,
        reply_to=reviewer_email,
    )


def notify_issue_reply(application, section_title, reply_text, reply_by):
    """Forward applicant's email reply to the staff reviewer."""
    assignment = getattr(application, "review_assignment", None)
    if not assignment or not assignment.reviewer or not assignment.reviewer.email:
        return False
    context = {
        **_applicant_common(application),
        "section_title": section_title,
        "reply_text": reply_text,
        "reply_by": reply_by,
    }
    return _send(
        "issue_reply_received",
        f"Reply received on {application.Reference_id}: {section_title}",
        assignment.reviewer.email,
        context,
    )
