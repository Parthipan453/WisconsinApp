""" Dominic Code """
from urllib.parse import urlparse
from PermissionAccess.models import PermissionAuditLog, PageAccess, Permission
from django.db.models import Q
from django.db import connection

MEDICAL_TAB = "medical"

def get_user_type_choices() -> list:
    from Admin.models import UserRole
    return list(UserRole.USER_TYPE_CHOICES)

def get_user_type_codes() -> list:
    return [code for code, _ in get_user_type_choices()]

def get_all_tabs() -> list:
    return get_user_type_choices() + [(MEDICAL_TAB, "Medical")]

def get_tab_roles(tab_code: str):
    if tab_code == MEDICAL_TAB:
        from Medical.Dominic.models import MedicalStaffRole
        return MedicalStaffRole.objects.filter(is_active=True)

    from Admin.models import UserRole
    return UserRole.objects.filter(user_type=tab_code).exclude(
        Q(users__is_super_admin=True) | Q(role_name="Administrator")
    )

def get_tab_permissions(tab_code: str):
    base = Permission.objects.filter(is_full_crud=True)

    if tab_code == MEDICAL_TAB:
        return base.filter(app_label="Medical", shared_with_user_roles=False)

    non_medical = base.exclude(app_label="Medical")

    if tab_code == "admin":
        medical_crossover_ids = list(
            base.filter(app_label="Medical", shared_with_user_roles=True)
                .values_list("pk", flat=True)
        )
        admin_ids = [
            p.pk for p in non_medical.only("pk", "user_types")
            if not p.user_types or tab_code in p.user_types
        ]
        return base.filter(pk__in=medical_crossover_ids + admin_ids)

    tagged_ids = [
        p.pk for p in non_medical.only("pk", "user_types")
        if tab_code in (p.user_types or [])
    ]
    return base.filter(pk__in=tagged_ids)

def get_tab_pages(tab_code: str):
    base = PageAccess.objects.all()

    if tab_code == MEDICAL_TAB:
        return base.filter(category__iexact="medical", shared_with_user_roles=False)

    non_medical = base.exclude(category__iexact="medical")

    if tab_code == "admin":
        medical_crossover_ids = list(
            base.filter(category__iexact="medical", shared_with_user_roles=True)
                .values_list("pk", flat=True)
        )
        admin_ids = [
            p.pk for p in non_medical.only("pk", "user_types")
            if not p.user_types or tab_code in p.user_types
        ]
        return base.filter(pk__in=medical_crossover_ids + admin_ids)

    tagged_ids = [
        p.pk for p in non_medical.only("pk", "user_types")
        if tab_code in (p.user_types or [])
    ]
    return base.filter(pk__in=tagged_ids)

def resolve_base_template(request) -> str:
    if request.path.startswith("/medical/"):
        return "medical_base.html"

    referer = request.META.get("HTTP_REFERER", "")
    if referer:
        referer_path = urlparse(referer).path
        if referer_path.startswith("/medical/"):
            return "medical_base.html"

    return "dashboard_base.html"

def get_user_permissions(user) -> set:
    if not user or not getattr(user, "is_authenticated", False):
        return set()

    if getattr(user, "is_administrator", False):
        return set(Permission.objects.values_list("codename", flat=True))

    codenames = set()

    role = getattr(user, "role", None)
    if role is not None:
        codenames |= set(role.permissions.values_list("codename", flat=True))

    medical_role = getattr(user, "medical_role", None)
    if medical_role is not None:
        codenames |= set(medical_role.permissions.values_list("codename", flat=True))

    return codenames

def has_permission(user, codename: str) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False

    if getattr(user, "is_administrator", False):
        return True

    return codename in get_user_permissions(user)

def has_any_permission(user, *codenames: str) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False

    if getattr(user, "is_administrator", False):
        return True

    return bool(get_user_permissions(user) & set(codenames))

def has_all_permission(user, *codenames: str) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False

    if getattr(user, "is_administrator", False):
        return True

    user_perms = get_user_permissions(user)
    return all(c in user_perms for c in codenames)

def has_page_access(user, page_key: str) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False

    if getattr(user, "is_administrator", False):
        return True

    role = getattr(user, "role", None)
    medical_role = getattr(user, "medical_role", None)

    if role is None and medical_role is None:
        return False

    query = Q()
    if role is not None:
        query |= Q(roles=role)
    if medical_role is not None:
        query |= Q(medical_roles=medical_role)

    return PageAccess.objects.filter(query, page_key=page_key).exists()

def get_user_accessible_page_keys(user) -> set:
    if not user or not getattr(user, "is_authenticated", False):
        return set()

    if getattr(user, "is_administrator", False):
        return set(PageAccess.objects.values_list("page_key", flat=True))

    role = getattr(user, "role", None)
    medical_role = getattr(user, "medical_role", None)

    if role is None and medical_role is None:
        return set()

    query = Q()
    if role is not None:
        query |= Q(roles=role)
    if medical_role is not None:
        query |= Q(medical_roles=medical_role)

    return set(PageAccess.objects.filter(query).values_list("page_key", flat=True).distinct())

def log_audit(action_by, action, description, target_user=None, target_role=None, ip_address=None):
    return PermissionAuditLog.objects.create(
        action_by = action_by,
        action = action,
        description = description,
        target_user = target_user,
        target_role = target_role,
        ip_address = ip_address,
    )

def get_client_ip(request) -> str:
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")