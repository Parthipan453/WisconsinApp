"""
Import these from any app's views.py to push a live event.

    from notifications.utils import *
"""

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


# ====== ERIC CODE START ======

def _live_send(group: str, event: str, app_id: str):
    """Push one lightweight event to a live-update group."""
    import time

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group,
        {
            "type": "live.event",
            "event": event,
            "app": app_id,
            "ts": int(time.time() * 1000),
        },
    )
    return None


def notify_application(application, event: str, data: dict | None = None):
    """Live-update every open page for one application.

    `event` is a hint only — clients re-fetch the affected blocks from secured
    `?partial=` endpoints, so nothing sensitive travels over the socket.
    """
    _live_send(f"app_{application.application_id}", event, str(application.application_id))


def notify_live_user(user_id, event: str):
    """Live-update a specific staff user's list pages (e.g. my reviews)."""
    _live_send(f"appuser_{user_id}", event, "me")


def notify_live_admins(event: str):
    """Live-update the admissions admin queue/list pages."""
    _live_send("appadmins", event, "me")


def notify_live_applicant(applicant_id, event: str):
    """Live-update the applicant's hub/dashboard pages."""
    _live_send(f"appapplicant_{applicant_id}", event, "me")


# ====== ERIC CODE END ======

# ====== ERIC CODE START ======
# AJAX bell notification layer: persists a Notification row for a Django user
# (staff / admin) or an Applicant, so the polling bells on every page can show
# them. The in-app (DB) layer is separate from the WebSocket event-refetch above.


def notify_user(user_id, title, message="", notification_type="INFO", link=""):
    """Create a persistent in-app notification for a staff/admin user.

    Rendered by the AJAX bell on staff_base / dashboard_base pages.
    """
    from Staff.models import Notification

    Notification.objects.create(
        user_id=int(user_id),
        title=title,
        message=message or "",
        notification_type=notification_type,
        link=link or "",
    )


def notify_all_admins(title, message="", notification_type="INFO", link=""):
    """Create an in-app notification for every admin user (admissions team)."""
    from Admin.models import User

    for user in User.objects.filter(is_admin=True):
        notify_user(user.id, title, message, notification_type, link)


def notify_applicant(applicant, title, message="", notification_type="INFO", link=""):
    """Create a persistent in-app notification for an applicant.

    `applicant` may be an Applicant instance or its primary key. Rendered by the
    AJAX bell on the applicant portal dashboard.
    """
    from Applicants.models import ApplicantNotification

    applicant_id = getattr(applicant, "pk", None) or applicant
    ApplicantNotification.objects.create(
        applicant_id=applicant_id,
        title=title,
        message=message or "",
        notification_type=notification_type,
        link=link or "",
    )


# ====== ERIC CODE END ======

def send_notification(user_id, data: dict, event: str = "notification"):
    """Private -- only this one user (by their user id, not employee_id/student_number) sees it."""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{user_id}",
        {"type": "notify.message", "event": event, "data": data},
    )


def notify_admins(data: dict, event: str = "admin_alert"):
    """Only connected staff/admin users see it (e.g. 'new grade change request')."""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "admins",
        {"type": "admin.message", "event": event, "data": data},
    )


def broadcast_update(data: dict, event: str = "broadcast"):
    """Every connected client sees it, regardless of role."""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "broadcast",
        {"type": "broadcast.message", "event": event, "data": data},
    )