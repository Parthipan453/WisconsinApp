# =====================================================
# Library/management/commands/backfill_resource_copies.py
# =====================================================

from datetime import date
from uuid import uuid4

from django.core.management.base import BaseCommand
from django.db.models import Count

from Library.models import LibraryResource, ResourceCopy


class Command(BaseCommand):

    help = (
        "Creates missing ResourceCopy rows for any LibraryResource "
        "whose total_copies doesn't match its actual copy count."
    )

    def handle(self, *args, **options):

        resources = LibraryResource.objects.annotate(
            real_copy_count=Count("copies")
        )

        total_created = 0
        resources_fixed = 0

        for resource in resources:

            missing = resource.total_copies - resource.real_copy_count

            if missing <= 0:
                continue

            new_copies = [
                ResourceCopy(
                    resource=resource,
                    barcode=f"{resource.id}-{uuid4().hex[:6].upper()}",
                    acquisition_date=date.today(),
                    condition="Unknown",
                    status="AVAILABLE",
                )
                for _ in range(missing)
            ]

            ResourceCopy.objects.bulk_create(new_copies)

            total_created += missing
            resources_fixed += 1

            self.stdout.write(
                f'  "{resource.title}" — created {missing} missing copy/copies '
                f'(had {resource.real_copy_count}, needed {resource.total_copies})'
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone. Fixed {resources_fixed} book(s), "
                f"created {total_created} ResourceCopy row(s) total."
            )
        )