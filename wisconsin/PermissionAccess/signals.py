""" Dominic Code """
from django.apps import apps
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver
from .models import *
from django.core.exceptions import FieldDoesNotExist
from django.db.models.fields import NOT_PROVIDED
from Admin.models import UserRole
from Medical.Dominic.models import MedicalStaffRole

EXCLUDED_APPS = {
    "auth",
    "contenttypes",
    "sessions",
    "admin",
    "PermissionAccess",
}

EXCLUDED_MODELS = {
    ("Admin", "usersession"),
    ("Admin", "usernotificationpreference"),
    ("Admin", "userauditlog"),
    ("Admin", "userroleassignment"),
}

_USER_TYPES_TYPO_CANDIDATES = {
    "user_pages", "user_type", "usertype", "user_page",
    "user_role_types", "usertypes",
}

def _warn_possible_user_types_typo(model):
    import sys
    hits = []
    for attr in _USER_TYPES_TYPO_CANDIDATES:
        value = getattr(model, attr, None)
        if isinstance(value, (list, tuple)):
            hits.append(attr)
    if hits:
        print(
            f"[PermissionAccess] WARNING: {model._meta.app_label}.{model.__name__} "
            f"defines {hits} but not `user_types` — this model will be treated "
            f"as untagged and its permissions will fall back to the Admin tab. "
            f"Did you mean `user_types`?",
            file=sys.stderr,
        )


@receiver(post_migrate)
def auto_create_permission(sender, **kwargs):
    for model in apps.get_models():
        app_label = model._meta.app_label
        model_name = model._meta.model_name

        if app_label in EXCLUDED_APPS:
            continue
        if (app_label, model_name) in EXCLUDED_MODELS:
            continue
        if model._meta.abstract:
            continue

        try:
            field = model._meta.get_field("is_full_crud")
            is_full_crud = field.default
            if is_full_crud is NOT_PROVIDED:
                is_full_crud = True
        except FieldDoesNotExist:
            is_full_crud = True

        try:
            field = model._meta.get_field("shared_with_user_roles")
            shared_with_user_roles = field.default
            if shared_with_user_roles is NOT_PROVIDED:
                shared_with_user_roles = False
        except FieldDoesNotExist:
            shared_with_user_roles = False
            
        is_medical = app_label.strip().lower() == "medical"
        if is_medical:
            model_user_types = []
        else:
            try:
                field = model._meta.get_field("user_types")
                default = field.default
                if default is NOT_PROVIDED:
                    model_user_types = []
                else:
                    model_user_types = list(default() if callable(default) else default)
            except FieldDoesNotExist:
                model_user_types = list(getattr(model, "user_types", []) or [])
                if not model_user_types:
                    _warn_possible_user_types_typo(model)

        model_permission_label = getattr(model, "permission_label", "") or ""

        for action, _ in Permission.Action.choices:
            if not is_full_crud and action != Permission.Action.READ:
                continue

            codename = f"{model_name}_{action}"
            display_name = f"Can {action.capitalize()} {model._meta.verbose_name.title()}"

            Permission.objects.update_or_create(
                codename=codename,
                defaults={
                    "name": display_name,
                    "model_label": model_name,
                    "app_label": app_label,
                    "action": action,
                    "description": f"Allows the user to {action} {model._meta.verbose_name_plural}.",
                    "is_full_crud": is_full_crud,
                    "shared_with_user_roles": shared_with_user_roles,
                    "user_types": model_user_types,
                    "display_label": model_permission_label,
                },
            )

        if not is_full_crud:
            Permission.objects.filter(
                app_label=app_label, model_label=model_name
            ).exclude(action=Permission.Action.READ).delete()


@receiver(post_migrate)
def auto_sync_page_access(sender, **kwargs):
    from .discovery import sync_page_access
    try:
        sync_page_access()
    except Exception:
        pass


@receiver(post_save, sender=UserRole)
def grant_default_read_permissions(sender, instance, created, **kwargs):
    if not created:
        return

    read_permissions = Permission.objects.filter(action=Permission.Action.READ)
    if read_permissions.exists():
        instance.permissions.add(*read_permissions)
        
@receiver(post_save, sender=MedicalStaffRole)
def grant_default_read_permissions_medical(sender, instance, created, **kwargs):
    if not created:
        return

    read_permissions = Permission.objects.filter(action=Permission.Action.READ)
    if read_permissions.exists():
        instance.permissions.add(*read_permissions)