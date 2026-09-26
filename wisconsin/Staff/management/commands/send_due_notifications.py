from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.urls import reverse

from Library.models import BorrowTransaction
from Staff.models import Notification


class Command(BaseCommand):

    help = "Send library book due-date notifications 3 days before due date."

    def handle(self, *args, **options):

        # =====================================================
        # TODAY
        # =====================================================

        today = timezone.localdate()

        # =====================================================
        # REMINDER DATE
        # Book should be due exactly 3 days from today
        # =====================================================

        reminder_date = today + timedelta(days=3)

        # =====================================================
        # FIND ACTIVE BORROWED BOOKS
        # =====================================================

        loans = (
            BorrowTransaction.objects
            .select_related(
                "library_user",
                "library_user__user",
                "copy",
                "copy__resource",
            )
            .filter(
                library_user__user_type__in=[
                    "STUDENT",
                    "FACULTY",
                    "STAFF",
                ],
                status="ISSUED",
                return_date__isnull=True,
                due_date=reminder_date,
            )
        )

        notification_count = 0

        # =====================================================
        # CREATE NOTIFICATION
        # =====================================================

        for loan in loans:

            user = loan.library_user.user

            book_title = loan.copy.resource.title

            # =================================================
            # PREVENT DUPLICATE NOTIFICATION
            # =================================================

            already_sent = Notification.objects.filter(
                user=user,
                related_borrow_transaction_id=loan.id,
                title="Book Due in 3 Days",
            ).exists()

            if already_sent:
                continue

            # =================================================
            # CREATE NOTIFICATION
            # =================================================

            Notification.objects.create(

                user=user,

                title="Book Due in 3 Days",

                message=(
                    f'Your book "{book_title}" '
                    f'is due in 3 days. '
                    f'Please return it by '
                    f'{loan.due_date.strftime("%b %d, %Y")}.'
                ),

                notification_type="WARNING",

                link="",

                related_borrow_transaction_id=loan.id,
            )

            notification_count += 1

        # =====================================================
        # RESULT
        # =====================================================

        self.stdout.write(
            self.style.SUCCESS(
                f"{notification_count} due-date notification(s) sent."
            )
        )