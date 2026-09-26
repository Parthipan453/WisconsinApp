""" Dominic Code """
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import ListView, TemplateView
from Admin.models import UserRole
from .decorators import administrator_only
from .models import PermissionAuditLog, PageAccess, Permission
from .utils import get_client_ip, get_user_permissions, log_audit, has_page_access
from .forms import AdministratorSetupForm
from django.db.models import Count
from .utils import (
    get_user_accessible_page_keys,
    get_all_tabs,
    get_tab_roles,
    get_tab_permissions,
    get_tab_pages,
)
from .humanize import build_lookup_maps, humanize_description
import traceback
from django.db.models import Q
from PermissionAccess.mixins import PermissionRequiredMixin, PageAccessMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from Medical.Dominic.models import MedicalStaffRole
from django.http import Http404

User = get_user_model()

class AdministratorSetupView(View):
    template_name = "permission_setup.html"
    
    def dispatch(self, request, *args, **kwargs):
        if self._administrator_exists():
            messages.info(request, "Administrator already created. Please login.")
            return redirect("/login/")
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request):
        form = AdministratorSetupForm()
        return render(request, self.template_name, {
            "page_title": "Administrator Setup",
            "form": form,
        })
        
    def post(self, request):
        form = AdministratorSetupForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {
                "page_title": "Administrator Setup",
                "form": form,
            })
            
        data = form.cleaned_data
        
        try:
            with transaction.atomic():
                if self._administrator_exists():
                    messages.error(request, "Administrator already exists. Please login.")
                    return redirect("/login/")
                
                user = User.objects.create_user(
                    username=data["username"],
                    email=data["email"],
                    password=data["password"],
                    first_name=data["first_name"],
                    last_name=data["last_name"],
                    is_admin=True,
                    is_super_admin=True,
                    account_status="ACTIVE",
                )
                user.mobile_number = data["mobile_number"]
                user.save()
                
                self._seed_permissions(user)
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, "Setup failed due to a server error. Please try again.")
            return render(request, self.template_name, {
                "page_title": "Administrator Setup",
                "form": form,
            })
        
        username = data["username"]
        messages.success(request, f"Administrator '{username}' created successfully.")
        return redirect("/login/")
    
    def _administrator_exists(self) -> bool:
        return User.objects.filter(is_admin = True, is_super_admin = True).exists()
    
    def _seed_permissions(self, admin_user) -> None:
        admin_role, _ = UserRole.objects.get_or_create(
            role_name = "Administrator",
            defaults = {
                "description": "Full system access. Created during initial setup."
            }
        )
        admin_role.permissions.set(Permission.objects.all())
        
        pages = [
            (
                "permission_dashboard", 
                "/permission/", 
                "Access Control Dashboard", 
                "Permission overview - stats and recent activity."
            ),
            (
                "permission_management",
                "/permission/roles/",
                "Permission Management",
                "Create, assign and modify permissions on roles."
            ),
            (
                "permission_page_access",
                "/permission/page-access/",
                "Page Access Control",
                "Control which roles can access which pages."
            ),
            (
                "permission_audit_log",
                "/permission/audit-log/",
                "Audit Log",
                "Immutable record of all access control changes."
            ),   
        ]
        
        for page_key, path_prefix, display_name, description in pages:
            page, _ = PageAccess.objects.get_or_create(
                page_key = page_key,
                defaults = {
                    "path_prefix": path_prefix,
                    "display_name": display_name,
                    "description": description,
                },
            )
            page.roles.add(admin_role)
            
        log_audit(
            action_by = admin_user,
            action = PermissionAuditLog.ActionType.ADMINISTRATOR_SETUP,
            description = (
                f"Administrator setup completed. "
                f"User '{admin_user.username}' created with full system access."
            ),
            target_user = admin_user,
            target_role = admin_role
        )

class DashboardView(LoginRequiredMixin, PageAccessMixin, TemplateView):
    page_key = "permission_dashboard"
    page_path = "Administartor > Permissions"
    template_name = "permission_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        role_permission_counts = list(
            UserRole.objects.exclude(
                Q(users__is_super_admin=True) |
                Q(role_name="Administrator")
            )
            .annotate(perm_count=Count("permissions", distinct=True))
            .order_by("-perm_count")
            .values("role_name", "perm_count")[:8]
        )

        action_label_map = dict(PermissionAuditLog.ActionType.choices)
        action_counts = [
            {"label": action_label_map.get(row["action"], row["action"]), "count": row["count"]}
            for row in (
                PermissionAuditLog.objects.values("action")
                .annotate(count=Count("id"))
                .order_by("-count")
            )
        ]

        recent_logs = list(
            PermissionAuditLog.objects.select_related(
                "action_by", "target_user", "target_role"
            ).order_by("-timestamp")[:5]
        )
        perm_lookup, page_lookup, page_prefix_lookup = build_lookup_maps()
        for log in recent_logs:
            log.friendly_description = humanize_description(
                log, perm_lookup, page_lookup, page_prefix_lookup
            )
            
        roles_qs = (
            UserRole.objects.exclude(
                Q(users__is_super_admin=True) |
                Q(role_name="Administrator")
            )
            .annotate(user_count=Count("users", distinct=True))
            .prefetch_related("permissions")\
            .order_by("-user_count", "role_name")[:6]
        )
        role_overview = _build_role_overview(roles_qs)

        medical_roles_qs = (
            MedicalStaffRole.objects.filter(is_active=True)
            .annotate(user_count=Count("staff_users", distinct=True))
            .prefetch_related("permissions")
            .order_by("-user_count", "category", "name")[:6]
        )
        medical_role_overview = _build_role_overview(medical_roles_qs)

        context.update({
            "page_title": "Access Control Dashboard",
            "total_roles": UserRole.objects.exclude(
                    Q(users__is_super_admin=True) |
                    Q(role_name="Administrator")
                ).count(),
            "total_medical_roles": MedicalStaffRole.objects.filter(is_active=True).count(),
            "total_permissions": Permission.objects.count(),
            "total_users": User.objects.exclude(
                    Q(is_super_admin=True) |
                    Q(is_superuser=True)
                ).count(),
            "recent_logs": recent_logs,
            "role_permission_counts": role_permission_counts,
            "action_counts": action_counts,
            "role_overview": role_overview,
            "medical_role_overview": medical_role_overview,
        })

        return context
    
_AVATAR_COLORS = ["red", "blue", "green", "amber", "purple", "gray"]

def _build_role_overview(roles):
    overview = []
    for i, role in enumerate(roles):
        perms = list(role.permissions.all())
        modules = sorted({
            p.model_label.replace("_", " ").title()
            for p in perms if p.action == Permission.Action.READ
        })
        overview.append({
            "role": role,
            "color": _AVATAR_COLORS[i % len(_AVATAR_COLORS)],
            "permission_count": len(perms),
            "modules": modules[:4],
            "extra_modules": max(0, len(modules) - 4),
        })
    return overview

def _role_display_name(role) -> str:
    return getattr(role, "role_name", None) or getattr(role, "name", "")

def _build_matrix(roles, permissions, role_type="user"):
    seen = {}
    for p in permissions:
        key = (p.app_label, p.model_label)
        if key not in seen:
            seen[key] = True
    module_keys = list(seen.keys())

    role_perm_sets = {}
    for role in roles:
        role_perm_sets[role.pk] = set(
            role.permissions.values_list("model_label", "action")
        )

    total_slots = len(module_keys) * 4

    rows = []
    for i, role in enumerate(roles):
        perm_set = role_perm_sets[role.pk]
        cells = {}
        granted_count = 0
        for (app, model) in module_keys:
            c = (model, "create") in perm_set
            r = (model, "read") in perm_set
            u = (model, "update") in perm_set
            d = (model, "delete") in perm_set
            cells[(app, model)] = {"create": c, "read": r, "update": u, "delete": d}
            granted_count += sum([c, r, u, d])

        rows.append({
            "role": role,
            "role_type": role_type,
            "display_name": _role_display_name(role),
            "user_count": getattr(role, "user_count", 0),
            "color": _AVATAR_COLORS[i % len(_AVATAR_COLORS)],
            "cells": cells,
            "granted_count": granted_count,
            "total_slots": total_slots,
        })

    return module_keys, rows

class RoleListView(PageAccessMixin, TemplateView):
    page_key = "permission_management_list"
    page_path = "Administrator > Permissions > Permission Role List"
    template_name = "permission_role_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        tabs = []
        for tab_code, tab_label in get_all_tabs():
            if tab_code == "medical":
                count_field, ordering = "staff_users", ("category", "name")
            else:
                count_field, ordering = "users", ("role_name",)

            roles = (
                get_tab_roles(tab_code)
                .annotate(user_count=Count(count_field, distinct=True))
                .prefetch_related("permissions")
                .order_by(*ordering)
            )
            permissions = get_tab_permissions(tab_code).order_by("app_label", "model_label", "action")
            module_keys, matrix_rows = _build_matrix(roles, permissions, role_type=tab_code)

            tabs.append({
                "code": tab_code,
                "label": tab_label,
                "module_keys": module_keys,
                "matrix_rows": matrix_rows,
            })

        context.update({
            "page_title": "Roles & Permissions",
            "can_edit": getattr(self.request.user, "is_administrator", False),
            "tabs": tabs,
        })
        return context
    
class RolePermissionsView(PageAccessMixin, View):
    page_key = "permission_management"
    template_name = "permission_role_permissions.html"

    def get_object(self, role_type, pk):
        valid_codes = {code for code, _ in get_all_tabs()}
        if role_type not in valid_codes:
            raise Http404("Unknown role type.")
        model = MedicalStaffRole if role_type == "medical" else UserRole
        return get_object_or_404(model, pk=pk)

    def get(self, request, role_type, pk):
        role = self.get_object(role_type, pk)
        context = self._build_context(role, role_type)
        context["can_edit"] = getattr(request.user, "is_administrator", False)
        return render(request, self.template_name, context)

    def post(self, request, role_type, pk):
        if not getattr(request.user, "is_administrator", False):
            messages.error(request, "Only the Administrator can modify permissions.")
            return redirect("Permission:permission_role_permissions", role_type=role_type, pk=pk)

        role = self.get_object(role_type, pk)
        role_label = _role_display_name(role)

        allowed_perms_qs = get_tab_permissions(role_type)
        allowed_ids = set(allowed_perms_qs.values_list("id", flat=True))

        submitted_ids = set(request.POST.getlist("permissions"))
        selected_ids = {pid for pid in submitted_ids if pid in {str(i) for i in allowed_ids}}

        always_on_ids = {
            str(i) for i in allowed_perms_qs.filter(action=Permission.Action.READ).values_list("id", flat=True)
        }
        selected_ids |= always_on_ids

        previous_ids = set(role.permissions.values_list("id", flat=True))

        role.permissions.set(Permission.objects.filter(id__in=selected_ids))

        added = selected_ids - previous_ids
        removed = previous_ids - selected_ids

        target_role = role if role_type != "medical" else None

        if added:
            log_audit(
                action_by=request.user,
                action=PermissionAuditLog.ActionType.PERMISSION_ASSIGNED,
                description=f"Assigned {len(added)} permission(s) to {role_type} role '{role_label}'.",
                target_role=target_role,
                ip_address=get_client_ip(request),
            )
        if removed:
            log_audit(
                action_by=request.user,
                action=PermissionAuditLog.ActionType.PERMISSION_REMOVED,
                description=f"Removed {len(removed)} permission(s) from {role_type} role '{role_label}'.",
                target_role=target_role,
                ip_address=get_client_ip(request),
            )

        messages.success(request, f"Permissions updated for '{role_label}'.")
        return redirect("Permission:permission_role_permissions", role_type=role_type, pk=role.pk)

    def _build_context(self, role, role_type):
        perms_qs = get_tab_permissions(role_type).order_by("app_label", "model_label", "action")

        role_perm_ids = set(role.permissions.values_list("id", flat=True))

        grouped = {}
        for perm in perms_qs:
            app = perm.app_label.replace("_", " ").title()
            model = perm.display_model_name
            grouped.setdefault(app, {}).setdefault(model, {})[perm.action] = {
                "perm": perm,
                "checked": perm.id in role_perm_ids,
            }

        for models_in_app in grouped.values():
            for actions in models_in_app.values():
                for action_key, _ in Permission.Action.choices:
                    actions.setdefault(action_key, None)

        total_available = perms_qs.count()
        total_assigned = len(role_perm_ids & set(perms_qs.values_list("id", flat=True)))
        role_label = _role_display_name(role)
        user_count = role.staff_users.count() if role_type == "medical" else role.users.count()
        tab_labels = dict(get_all_tabs())

        return {
            "role": role,
            "role_type": role_type,
            "role_type_label": tab_labels.get(role_type, role_type.title()),
            "role_label": role_label,
            "grouped": grouped,
            "page_title": f"Set Permissions — {role_label}",
            "total_assigned": total_assigned,
            "total_available": total_available,
            "user_count": user_count,
        }

@method_decorator(administrator_only, name="dispatch")
class SyncPageAccessView(View):
    def post(self, request):
        from .discovery import sync_page_access

        try:
            created = sync_page_access()

            if created:
                log_audit(
                    action_by=request.user,
                    action=PermissionAuditLog.ActionType.PAGE_ACCESS_CHANGED,
                    description=f"Page sync: {len(created)} new page(s) auto-discovered.",
                    ip_address=get_client_ip(request),
                )

                messages.success(request, f"{len(created)} new page(s) found successfully.")
            else:
                messages.info(request, "All caught up! No new pages found.")

        except Exception:
            traceback.print_exc()
            messages.error(request, "Could not scan for new pages. Please try again.")

        return redirect("Permission:permission_page_access_list")
        
@method_decorator(administrator_only, name="dispatch")
class PageAccessView(View):
    template_name = "permission_page_access.html"

    def get(self, request):
        return render(request, self.template_name, self._build_context())

    def post(self, request):
        pages = PageAccess.objects.prefetch_related("roles", "medical_roles").all()
        for page in pages:
            if self._is_medical_page(page) and not page.shared_with_user_roles:
                selected_medical_role_ids = request.POST.getlist(f"page_{page.pk}_medical_roles")
                page.medical_roles.set(MedicalStaffRole.objects.filter(id__in=selected_medical_role_ids))
                page.roles.clear()
            else:
                selected_role_ids = request.POST.getlist(f"page_{page.pk}_roles")
                page.roles.set(UserRole.objects.filter(id__in=selected_role_ids))
                page.medical_roles.clear()

            log_audit(
                action_by=request.user,
                action=PermissionAuditLog.ActionType.PAGE_ACCESS_CHANGED,
                description=f"Updated page access for '{page.display_name}'.",
                ip_address=get_client_ip(request),
            )

        messages.success(request, "Page access settings saved successfully.")
        return redirect("Permission:permission_page_access_list")

    @staticmethod
    def _is_medical_page(page) -> bool:
        return page.is_medical_page

    def _build_context(self):
        pages = list(PageAccess.objects.prefetch_related("roles", "medical_roles").order_by("category", "display_name"))
        medical_roles = list(MedicalStaffRole.objects.filter(is_active=True).order_by("category", "name"))
        admin_role = UserRole.objects.filter(role_name="Administrator").first()

        granted_role_ids_by_page = {
            page.pk: set(page.roles.values_list("id", flat=True)) for page in pages
        }
        granted_medical_role_ids_by_page = {
            page.pk: set(page.medical_roles.values_list("id", flat=True)) for page in pages
        }

        tabs = []
        for tab_code, tab_label in get_all_tabs():
            tab_pages = list(get_tab_pages(tab_code).order_by("category", "display_name"))
            grouped = {}
            for page in tab_pages:
                grouped.setdefault(page.category or "General", []).append(page)

            tabs.append({
                "code": tab_code,
                "label": tab_label,
                "pages": tab_pages,
                "grouped_pages": grouped,
                "roles": [] if tab_code == "medical" else list(get_tab_roles(tab_code)),
            })

        return {
            "pages": pages,
            "tabs": tabs,
            "medical_roles": medical_roles,
            "admin_role": admin_role,
            "granted_role_ids_by_page": granted_role_ids_by_page,
            "granted_medical_role_ids_by_page": granted_medical_role_ids_by_page,
            "page_title": "Page Access Control",
        }
        
@method_decorator(administrator_only, name="dispatch")
class PageAccessUpdateView(View):
    def post(self, request, pk):
        import json
        page = get_object_or_404(PageAccess, pk=pk)
        data = json.loads(request.body)

        page.display_name = data.get("display_name", page.display_name).strip() or page.display_name
        page.icon = data.get("icon", page.icon).strip() or "file"

        page.save()

        log_audit(
            action_by=request.user,
            action=PermissionAuditLog.ActionType.PAGE_ACCESS_CHANGED,
            description=f"Edited page details for '{page.display_name}'.",
            ip_address=get_client_ip(request),
        )
        return JsonResponse({"ok": True})

class AuditLogView(PageAccessMixin, ListView):
    page_key = "permission_audit_log"
    template_name = "permission_audit_log.html"
    context_object_name = "logs"
    paginate_by = 10

    def get_base_queryset(self):
        qs = (
            PermissionAuditLog.objects.select_related("action_by", "target_user", "target_role").order_by("-timestamp")
        )
        action_filter = self.request.GET.get("action", "").strip()
        user_filter = self.request.GET.get("user", "").strip()

        if action_filter:
            qs = qs.filter(action=action_filter)
        if user_filter:
            qs = qs.filter(action_by__email__icontains=user_filter)

        return qs

    def get_queryset(self):
        qs = self.get_base_queryset()
        role_scope = self.request.GET.get("role_scope", "all").strip().lower()

        if role_scope == "user":
            qs = qs.filter(target_role__isnull=False)
        elif role_scope == "medical":
            qs = qs.filter(description__icontains="medical role")

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        perm_lookup, page_lookup, page_prefix_lookup = build_lookup_maps()
        atl_rows = []
        for log in context["logs"]:
            log.friendly_description = humanize_description(
                log, perm_lookup, page_lookup, page_prefix_lookup
            )
            atl_rows.append({
                "id": log.id,
                "user": str(log.action_by) if log.action_by else "System",
                "action_label": log.get_action_display(),
                "target_role": log.target_role.role_name if log.target_role else "",
                "target_user": str(log.target_user) if log.target_user else "",
                "timestamp": log.timestamp.strftime("%d %b %Y, %I:%M %p"),
                "ip_address": log.ip_address or "",
                "description": log.friendly_description,
            })

        base_qs = self.get_base_queryset()

        context.update({
            "page_title": "Audit Log",
            "action_choices": PermissionAuditLog.ActionType.choices,
            "action_filter": self.request.GET.get("action", ""),
            "user_filter": self.request.GET.get("user", ""),
            "total_logs": PermissionAuditLog.objects.count(),
            "filtered_count": context["page_obj"].paginator.count,
            "atl_rows": atl_rows,
            "role_scope": self.request.GET.get("role_scope", "all").strip().lower(),
            "role_scope_all_count": base_qs.count(),
            "role_scope_user_count": base_qs.filter(target_role__isnull=False).count(),
            "role_scope_medical_count": base_qs.filter(description__icontains="medical role").count(),
        })
        return context
    
class MyPermissionsView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({
                "error": "Not authenticated."
            }, status = 401)
            
        return JsonResponse({
            "permissions": sorted(get_user_permissions(request.user)),
            "accessible_pages": sorted(get_user_accessible_page_keys(request.user)),
            "is_administrator": getattr(request.user, "is_administrator", False),
        })