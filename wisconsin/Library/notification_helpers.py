from Admin.models import User
from Staff.models import Notification


def create_library_form_notification(
    *,
    title,
    message,
    link="",
):

    # ==================================================
    # GET ACTIVE LIBRARY STAFF
    # ==================================================

    library_admins = User.objects.filter(
        is_staff=True,
        account_status="ACTIVE",
    )

    # ==================================================
    # CREATE NOTIFICATIONS
    # ==================================================

    notifications = [
        Notification(
            user=admin_user,
            title=title,
            message=message,
            notification_type="REQUEST",
            link=link,
            is_read=False,
        )
        for admin_user in library_admins
    ]

    # ==================================================
    # SAVE
    # ==================================================

    if notifications:
        Notification.objects.bulk_create(
            notifications
        )

    return len(notifications)