""" Dominic Code """
from django.apps import apps
from django.core.checks import Error, register

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


@register()
def check_crud_flag_declared(app_configs, **kwargs):
    errors = []

    for model in apps.get_models():
        app_label = model._meta.app_label
        model_name = model._meta.model_name

        if app_label in EXCLUDED_APPS:
            continue
        if (app_label, model_name) in EXCLUDED_MODELS:
            continue
        if model._meta.abstract:
            continue

        if not hasattr(model, "is_full_crud"):
            try:
                model_file = model.__module__ + ".py"
            except Exception:
                model_file = "<unknown module>"

            errors.append(
                Error(
                    (
                        f"Model '{model.__name__}' (app: '{app_label}', "
                        f"table: '{model._meta.db_table}') is missing the "
                        f"required 'is_full_crud' field."
                    ),
                    hint=(
                        f"This model participates in PermissionAccess's "
                        f"automatic CRUD-permission generation, which "
                        f"requires every model to explicitly declare "
                        f"whether it gets full Create/Read/Update/Delete "
                        f"permissions or just 'Read'.\n\n"
                        f"  -> Open: {model_file}\n"
                        f"  -> Find: class {model.__name__}(...)\n"
                        f"  -> Add one of these lines inside it:\n\n"
                        f"       is_full_crud = models.BooleanField(default=True)\n"
                        f"       # use this if admins should be able to\n"
                        f"       # create/edit/delete '{model_name}' records\n\n"
                        f"     OR\n\n"
                        f"       is_full_crud = models.BooleanField(default=False)\n"
                        f"       # use this if '{model_name}' is a lookup/\n"
                        f"       # reference table only used via ForeignKey\n"
                        f"       # (only a 'read' permission will be created,\n"
                        f"       # and it will be hidden from the CRUD matrix UI)\n\n"
                        f"  -> Then run: python manage.py makemigrations {app_label}\n"
                        f"               python manage.py migrate\n\n"
                        f"  -> If this model genuinely can't carry the field "
                        f"(e.g. it inherits Django's AbstractUser/"
                        f"AbstractBaseUser and a clash is possible), add it "
                        f"directly anyway — see Admin.User for a working "
                        f"example — rather than skipping it. Models should "
                        f"only be exempted via EXCLUDED_APPS / "
                        f"EXCLUDED_MODELS in signals.py and checks.py, and "
                        f"that should be a deliberate, reviewed decision."
                    ),
                    obj=model,
                    id="permission_access.E001",
                )
            )

    return errors