from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.sessions.models import Session
from .models import StaffAttendance, StaffLoginLog
from PermissionAccess.utils import get_client_ip


@receiver(user_logged_in)
def on_user_logged_in(sender, request, user, **kwargs):
    if not user.is_staff:
        return

    if not request.session.session_key:
        request.session.save()

    now = timezone.now()
    today = timezone.localdate()

    active_keys = set(
        Session.objects.filter(
            expire_date__gt=now
        ).values_list("session_key", flat=True)
    )

    stale_logs = StaffLoginLog.objects.filter(
        user=user,
        logout_time__isnull=True
    )
    for log in stale_logs:
        if log.session_key not in active_keys:
            log.logout_time = now
            log.save(update_fields=["logout_time"])

    attendance, _ = StaffAttendance.objects.get_or_create(
        user=user,
        date=today,
        defaults={"check_in": now}
    )
    if attendance.check_in is None:
        attendance.check_in = now
        attendance.save(update_fields=["check_in"])

    StaffLoginLog.objects.create(
        user=user,
        session_key=request.session.session_key,
        login_time=now,
        ip_address=get_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT"),
    )


@receiver(user_logged_out)
def on_user_logged_out(sender, request, user, **kwargs):
    if not user or not user.is_staff:
        return

    now = timezone.now()
    session_key = request.session.session_key

    if session_key:
        StaffLoginLog.objects.filter(
            user=user,
            session_key=session_key,
            logout_time__isnull=True
        ).update(logout_time=now)

    today = timezone.localdate()
    try:
        attendance = StaffAttendance.objects.get(user=user, date=today)
        if attendance.check_in:
            attendance.check_out = now
            delta = attendance.check_out - attendance.check_in
            hours = delta.total_seconds() / 3600
            attendance.total_hours_worked = round(hours, 2)
            attendance.save(update_fields=["check_out", "total_hours_worked"])
    except (StaffAttendance.DoesNotExist, StaffAttendance.MultipleObjectsReturned):
        pass
