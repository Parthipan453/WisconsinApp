from datetime import timedelta

from django.utils import timezone

from Library.models import BorrowTransaction
from Staff.models import Notification


DUE_SOON_THRESHOLD_DAYS = 3


def check_due_date_notifications():

    today = timezone.localdate()

    target_due_date = (
        today +
        timedelta(days=DUE_SOON_THRESHOLD_DAYS)
    )

    loans = (
        BorrowTransaction.objects
        .select_related(
            "library_user",
            "library_user__user",
            "copy",
            "copy__resource",
        )
        .filter(
            status="ISSUED",
            return_date__isnull=True,
            due_date=target_due_date,
        )
    )

    notification_count = 0

    for loan in loans:

        user = loan.library_user.user

        title = "Book Due Soon"

        message = (
            f'Your borrowed book '
            f'"{loan.copy.resource.title}" '
            f'is due on '
            f'{loan.due_date.strftime("%b %d, %Y")}. '
            f'Only {DUE_SOON_THRESHOLD_DAYS} days remain. '
            f'Please return or renew the book before the due date.'
        )

        notification_exists = (
            Notification.objects
            .filter(
                user=user,
                title=title,
                message=message,
            )
            .exists()
        )

        if notification_exists:
            continue

        Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type="WARNING",
        )

        notification_count += 1

    return notification_count