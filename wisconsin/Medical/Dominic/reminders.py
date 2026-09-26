import logging
from datetime import datetime, timedelta
from django.urls import reverse
from django.utils import timezone
from Admin.Dominic.models import Notification
from Medical.models import MedicalStaffProfile, DailyNote
from Medical.Dominic.push import send_push_to_user

logger = logging.getLogger(__name__)

SHIFT_REMINDER_MINUTES_BEFORE = 10
WINDOW_MINUTES = 2

def fire_due_reminders_for_all():
    from Medical.Dominic.views import _build_calendar_entries, _shift_department_filter

    now = timezone.localtime()
    today = now.date()

    staff_profiles = MedicalStaffProfile.objects.filter(is_active=True).select_related("user", "department")

    for staff_profile in staff_profiles:
        user = staff_profile.user
        if not user:
            continue

        try:
            dept_filter, _, _ = _shift_department_filter(user)
            todays_entries = _build_calendar_entries(dept_filter, today, today).get(today, [])
            my_entries = [e for e in todays_entries if e.medical_staff_id == staff_profile.pk]

            for entry in my_entries:
                shift_start_dt = timezone.make_aware(datetime.combine(today, entry.start_time))
                remind_at = shift_start_dt - timedelta(minutes=SHIFT_REMINDER_MINUTES_BEFORE)
                if not (remind_at <= now <= remind_at + timedelta(minutes=WINDOW_MINUTES)):
                    continue

                already_sent = Notification.objects.filter(
                    recipient=user, schedule=entry.shift, event="shift_reminder",
                    created_at__date=today,
                ).exists()
                if already_sent:
                    continue

                link = reverse("Medical:my_shifts")
                message = f"Your {entry.shift_label} shift starts at {entry.start_time.strftime('%I:%M %p')}."
                notification = Notification.objects.create(
                    notification_type="SCHEDULE",
                    recipient=user,
                    schedule=entry.shift,
                    event="shift_reminder",
                    message=message,
                    icon="clock",
                    link_url=link,
                )
                send_push_to_user(user, title="Upcoming Shift", body=message, url=link, tag="shift_reminder", notif_id=notification.pk)

            candidate_notes = DailyNote.objects.filter(
                staff=staff_profile, date=today, reminder_sent=False,
                event_time__isnull=False, reminder_offset_minutes__isnull=False,
            )
            for note in candidate_notes:
                remind_at = note.reminder_datetime
                if remind_at is None:
                    continue
                remind_at = timezone.make_aware(remind_at)
                if not (remind_at <= now <= remind_at + timedelta(minutes=WINDOW_MINUTES)):
                    continue

                link = reverse("Medical:my_shifts")
                message = note.note_text[:255]
                notification = Notification.objects.create(
                    notification_type="SCHEDULE",
                    recipient=user,
                    event="note_reminder",
                    message=message,
                    icon="sticky-note",
                    link_url=link,
                )
                note.reminder_sent = True
                note.save(update_fields=["reminder_sent"])
                send_push_to_user(user, title="Reminder", body=message, url=link, tag="note_reminder", notif_id=notification.pk)

        except Exception:
            logger.exception("Reminder sweep failed for staff_profile id=%s", staff_profile.pk)

    DailyNote.objects.filter(date__lt=today).delete()