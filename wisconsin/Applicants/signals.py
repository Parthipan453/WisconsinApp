"""Signal handlers for the Applicants app."""

import logging

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Application

logger = logging.getLogger(__name__)

# These statuses already send their own dedicated emails from the views.
DEDICATED_EMAIL_STATUSES = ("submitted", "offer_accepted")


@receiver(pre_save, sender=Application)
def _stash_previous_status(sender, instance, **kwargs):
    instance._pre_status = None
    if not instance.pk:
        return
    try:
        instance._pre_status = (
            Application.objects.filter(pk=instance.pk)
            .values_list("status", flat=True)
            .first()
        )
    except Application.DoesNotExist:
        instance._pre_status = None


@receiver(post_save, sender=Application)
def _notify_status_change(sender, instance, created, **kwargs):
    old = getattr(instance, "_pre_status", None)
    new = instance.status
    if created or not old or old == new:
        return
    if new in DEDICATED_EMAIL_STATUSES:
        return
    applicant = instance.applicant
    if not applicant or not applicant.email:
        return
    try:
        if new == "enrolled":
            from Students.Eric.services import create_student_from_application

            if not applicant.converted_to_user_id:
                create_student_from_application(
                    instance.application_id, created_by="System"
                )
        else:
            from .services.email_service import ApplicantEmailService

            ApplicantEmailService().send_status_changed_email(instance, old)
    except Exception:
        logger.exception(
            "Could not notify applicant %s about status change for application %s",
            applicant.pk,
            instance.application_id,
        )