""" Dominic Code """
from django.core.management.base import BaseCommand
from PermissionAccess.discovery import sync_page_access


class Command(BaseCommand):
    help = "Scan the project's URLs for PermissionAccess-protected pages and register any new ones."

    def handle(self, *args, **options):
        created = sync_page_access()
        if not created:
            self.stdout.write(self.style.SUCCESS("No new pages found. Everything is already registered."))
            return
        self.stdout.write(self.style.SUCCESS(f"Registered {len(created)} new page(s):"))
        for page in created:
            self.stdout.write(f"  + {page.display_name}  ({page.page_key})")