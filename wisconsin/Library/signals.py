from datetime import date

from django.db.models.signals import post_save
from django.dispatch import receiver

from Admin.models import User
from Library.models import LibraryUser


@receiver(post_save, sender=User)
def create_library_user(sender, instance, **kwargs):
    """
    Automatically create a LibraryUser profile for
    Students and Faculty.

    Your Admin user creation flow first creates the User,
    then later sets is_student / is_faculty and saves again.

    Therefore we DO NOT check 'created=True'.
    """

    # ---------------------------------------
    # Already has a library profile?
    # ---------------------------------------
    if LibraryUser.objects.filter(user=instance).exists():
        return

    # ---------------------------------------
    # Student
    # ---------------------------------------
    if instance.is_student:

        LibraryUser.objects.create(
            user=instance,
            user_type="STUDENT",
            membership_date=date.today(),
            borrowing_limit=5,
            active=True,
        )

        print(f"Library profile created for student: {instance.username}")

    # ---------------------------------------
    # Faculty
    # ---------------------------------------
    elif instance.is_faculty:

        LibraryUser.objects.create(
            user=instance,
            user_type="FACULTY",
            membership_date=date.today(),
            borrowing_limit=20,
            active=True,
        )

        print(f"Library profile created for faculty: {instance.username}")
        
    # ---------------------------------------
    # Staff
    # ---------------------------------------
    elif instance.is_staff:

        LibraryUser.objects.create(
            user=instance,
            user_type="STAFF",
            membership_date=date.today(),
            borrowing_limit=10,
            active=True,
        )

        print(f"Library profile created for staff: {instance.username}")
        

#creation of resource copy
# =====================================================
# AUTOMATIC RESOURCE COPY CREATION / SYNCHRONIZATION
# =====================================================

import uuid
from datetime import date

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from Library.models import LibraryResource, ResourceCopy


@receiver(post_save, sender=LibraryResource)
def create_resource_copies(sender, instance, created, **kwargs):

    # -------------------------------------------------
    # No copies are required
    # -------------------------------------------------

    if instance.total_copies <= 0:

        LibraryResource.objects.filter(
            pk=instance.pk
        ).update(
            available_copies=0
        )

        return

    # -------------------------------------------------
    # Count existing physical copies
    # -------------------------------------------------

    existing_copy_count = ResourceCopy.objects.filter(
        resource=instance
    ).count()

    # -------------------------------------------------
    # Calculate how many copies are needed
    # -------------------------------------------------

    missing_copies = (
        instance.total_copies -
        existing_copy_count
    )

    # -------------------------------------------------
    # If total_copies is greater than existing copies,
    # create only the missing copies.
    # -------------------------------------------------

    if missing_copies > 0:

        new_copies = []

        for _ in range(missing_copies):

            new_copies.append(
                ResourceCopy(
                    resource=instance,

                    barcode=(
                        f"{instance.id}-"
                        f"{uuid.uuid4().hex[:6].upper()}"
                    ),

                    acquisition_date=date.today(),

                    condition="GOOD",

                    status="AVAILABLE",
                )
            )

        ResourceCopy.objects.bulk_create(
            new_copies
        )

    # -------------------------------------------------
    # If total_copies is equal to or less than the
    # existing copies, do NOT delete anything.
    # -------------------------------------------------

    # -------------------------------------------------
    # Calculate the actual number of available copies
    # -------------------------------------------------

    available_count = ResourceCopy.objects.filter(
        resource=instance,
        status="AVAILABLE"
    ).count()

    # -------------------------------------------------
    # Keep LibraryResource.available_copies
    # synchronized with ResourceCopy records.
    # -------------------------------------------------

    LibraryResource.objects.filter(
        pk=instance.pk
    ).update(
        available_copies=available_count
    )