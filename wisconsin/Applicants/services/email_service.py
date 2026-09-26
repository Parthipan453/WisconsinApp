"""Email notifications sent by the applicant portal."""

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from ..models import Applicant, Application


logger = logging.getLogger(__name__)


class ApplicantEmailService:
    """Delivers transactional email for applicant account activity."""

    def send_account_created_email(self, applicant: Applicant, login_url: str) -> bool:
        """Send the account-created confirmation without exposing email failures."""
        context = {
            "applicant": applicant,
            "login_url": login_url,
            "support_email": getattr(
                settings, "APPLICANT_SUPPORT_EMAIL", "app.example.edu"
            ),
            "contact_email": getattr(
                settings, "APPLICANT_CONTACT_EMAIL", "contact@example.edu"
            ),
        }
        subject = "Your Universities of Wisconsin application account is ready"
        text_body = render_to_string(
            "Applicants/emails/account_created.txt", context
        )
        html_body = render_to_string(
            "Applicants/emails/account_created.html", context
        )
        message = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[applicant.email],
        )
        message.attach_alternative(html_body, "text/html")

        try:
            return bool(message.send(fail_silently=False))
        except Exception:
            # Account creation must not fail simply because the mail provider is
            # temporarily unavailable. The error remains visible in server logs.
            logger.exception(
                "Could not send account-created email to applicant %s", applicant.pk
            )
            return False

    def send_application_started_email(
        self, application: Application, portal_url: str
    ) -> bool:
        """Confirm the application has been started and repeat the applicant's selections."""
        applicant = application.applicant
        details = [
            ("University", getattr(application.university, "university_name", "")),
            ("School", getattr(application.school, "school_name", "")),
            ("Program", getattr(application.program, "program_name", "")),
            ("Degree", getattr(application.degree_level, "degree_name", "")),
            ("Campus", application.campus_name),
            ("Applicant type", application.get_applicant_type_display()),
            (
                "Starting term",
                " ".join(
                    filter(
                        None,
                        (
                            getattr(application.admission_cycle, "term", ""),
                            getattr(application.admission_cycle, "academic_year", ""),
                        ),
                    )
                ),
            ),
            ("Application reference", application.Reference_id),
        ]
        context = {
            "applicant": applicant,
            "application": application,
            "details": [(label, value) for label, value in details if value],
            "portal_url": portal_url,
            "contact_email": getattr(
                settings, "APPLICANT_CONTACT_EMAIL", "contact@go.wisconsin.edu"
            ),
        }
        university_name = getattr(application.university, "university_name", "")
        subject = f"You started your {university_name} application"
        text_body = render_to_string(
            "Applicants/emails/application_started.txt", context
        )
        html_body = render_to_string(
            "Applicants/emails/application_started.html", context
        )
        message = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[applicant.email],
        )
        message.attach_alternative(html_body, "text/html")

        try:
            return bool(message.send(fail_silently=False))
        except Exception:
            logger.exception(
                "Could not send application-started email for application %s",
                application.application_id,
            )
            return False

    def send_application_submitted_email(
        self, application: Application, portal_url: str
    ) -> bool:
        """Send a confirmation after an applicant successfully submits."""
        applicant = application.applicant
        university = application.university
        context = {
            "applicant": applicant,
            "application": application,
            "university": university,
            "portal_url": portal_url,
            "contact_email": getattr(
                university, "official_email", "")
                or getattr(settings, "APPLICANT_CONTACT_EMAIL", "contact@go.wisconsin.edu"),
            "contact_phone": getattr(university, "phone_number", ""),
            "contact_website": getattr(university, "website", ""),
            "program_name": getattr(application.program, "program_name", ""),
            "term": " ".join(
                filter(
                    None,
                    (
                        getattr(application.admission_cycle, "term", ""),
                        getattr(application.admission_cycle, "academic_year", ""),
                    ),
                )
            ),
        }
        university_name = getattr(university, "university_name", "Universities of Wisconsin")
        subject = f"Application submitted: {university_name}"
        text_body = render_to_string(
            "Applicants/emails/application_submitted.txt", context
        )
        html_body = render_to_string(
            "Applicants/emails/application_submitted.html", context
        )
        message = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[applicant.email],
        )
        message.attach_alternative(html_body, "text/html")

        try:
            return bool(message.send(fail_silently=False))
        except Exception:
            logger.exception(
                "Could not send application-submitted email for application %s",
                application.application_id,
            )
            return False

    STATUS_GUIDANCE = {
        "in_progress": "Your application is in progress. Continue anytime from your Applicant Portal.",
        "awaiting_materials": "We are evaluating your application, but some materials are still outstanding. Please sign in to your Applicant Portal and upload any missing items as soon as possible.",
        "complete": "Your application file is now complete and ready for review.",
        "under_review": "Your application is now under review by the admissions team. No action is needed from you at this time.",
        "admitted": "Congratulations! We are pleased to inform you that you have been admitted. Review your offer and next steps in your Applicant Portal.",
        "offer_accepted": "You have accepted your offer of admission. A member of our team will be in touch with next steps.",
        "waitlisted": "Your application has been placed on a waitlist. You will be notified if a space becomes available.",
        "denied": "Your application has not been approved for admission at this time. For questions about this decision, please contact the admissions team.",
        "enrolled": "Your admission is confirmed and you are now enrolled. Watch your email for pre-enrollment information and your student checklist.",
        "withdrawn": "Your application has been withdrawn. If you did not request this change, please contact the admissions team.",
        "archived": "Your application has been archived and is no longer active. Contact the admissions team if you believe this is an error.",
    }

    def send_status_changed_email(
        self, application: Application, old_status: str
    ) -> bool:
        """Send a UW-themed notification whenever an application status changes."""
        applicant = application.applicant
        university = application.university
        university_name = getattr(
            university, "university_name", "Universities of Wisconsin"
        )
        status_choices = dict(Application.STATUS_CHOICES)
        new_display = status_choices.get(application.status, application.status)
        old_display = status_choices.get(old_status, old_status)
        portal_base = getattr(
            settings, "APPLICANT_PORTAL_BASE_URL", "https://apply.wisconsin.edu"
        )
        portal_url = f"{portal_base}/?state=status&app_id={application.application_id}&uuid={application.applicant.uuid}"
        context = {
            "applicant": applicant,
            "application": application,
            "university_name": university_name,
            "program_name": getattr(application.program, "program_name", ""),
            "term": " ".join(
                filter(
                    None,
                    (
                        getattr(application.admission_cycle, "term", ""),
                        getattr(application.admission_cycle, "academic_year", ""),
                    ),
                )
            ),
            "old_status": old_display,
            "new_status": new_display,
            "guidance": self.STATUS_GUIDANCE.get(
                application.status,
                "Please sign in to your Applicant Portal to view the latest information about your application.",
            ),
            "portal_url": portal_url,
            "contact_email": getattr(
                settings, "APPLICANT_CONTACT_EMAIL", "contact@go.wisconsin.edu"
            ),
        }
        subject = f"Application status update: {new_display} - {university_name}"
        text_body = render_to_string(
            "Applicants/emails/status_changed.txt", context
        )
        html_body = render_to_string(
            "Applicants/emails/status_changed.html", context
        )
        message = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[applicant.email],
        )
        message.attach_alternative(html_body, "text/html")

        try:
            return bool(message.send(fail_silently=False))
        except Exception:
            logger.exception(
                "Could not send status-change email for application %s",
                application.application_id,
            )
            return False
