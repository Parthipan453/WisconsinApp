from django.core.management.base import BaseCommand
from Admin.models import UserRole
from PermissionAccess.models import Permission

class Command(BaseCommand):
    help = "Grants READ permission for all modules to every existing role."

    def handle(self, *args, **kwargs):
        read_perms = Permission.objects.filter(action=Permission.Action.READ)
        for role in UserRole.objects.all():
            role.permissions.add(*read_perms)
            self.stdout.write(f"Updated: {role.role_name}")