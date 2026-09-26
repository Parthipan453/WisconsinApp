from django.apps import AppConfig


class PermissionaccessConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'PermissionAccess'
    verbose_name = "Role Based Access Control"
    
    def ready(self):
        from . import signals
        from . import check
