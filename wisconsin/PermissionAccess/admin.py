""" Dominic Code """
from django.contrib import admin
from django.utils.html import format_html
from .models import PageAccess, Permission, PermissionAuditLog

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "codename",
        "app_label",
        "model_label",
        "action_badge",
        "is_full_crud",
        "created_at",
    )
    list_display_links = ("name", "codename")
    list_filter = ("app_label", "action", "is_full_crud")
    search_fields = ("name", "codename", "model_label", "app_label", "description")
    ordering = ("app_label", "model_label", "action")
    list_per_page = 50
    date_hierarchy = "created_at"
    readonly_fields = ("id", "created_at", "updated_at")

    fieldsets = (
        ("Identity", {
            "fields": ("name", "codename", "description"),
        }),
        ("Scope", {
            "fields": ("app_label", "model_label", "action", "is_full_crud"),
        }),
        ("Metadata", {
            "fields": ("id", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description="Action", ordering="action")
    def action_badge(self, obj):
        colors = {
            "create": "#16a34a",
            "read": "#2563eb",
            "update": "#d97706",
            "delete": "#dc2626",
        }
        color = colors.get(obj.action, "#6b7280")
        return format_html(
            '<span style="display:inline-block;padding:2px 10px;border-radius:999px;'
            'font-size:11px;font-weight:700;color:#fff;background:{}">{}</span>',
            color,
            obj.get_action_display(),
        )


@admin.register(PageAccess)
class PageAccessAdmin(admin.ModelAdmin):
    list_display = (
        "display_name",
        "page_key",
        "path_prefix",
        "category",
        "icon",
        "role_count",
        "medical_role_count",
        "is_auto_discovered",
    )
    list_display_links = ("display_name", "page_key")
    list_filter = ("category", "is_auto_discovered")
    search_fields = ("display_name", "page_key", "path_prefix", "description", "category")
    ordering = ("category", "display_name")
    list_per_page = 50
    filter_horizontal = ("roles", "medical_roles")
    readonly_fields = ("id", "created_at", "updated_at")

    fieldsets = (
        ("Page", {
            "fields": ("display_name", "page_key", "path_prefix", "description"),
        }),
        ("Display", {
            "fields": ("category", "icon", "is_auto_discovered"),
        }),
        ("Access", {
            "fields": ("roles", "medical_roles"),
            "description": "A page should be governed by either Organization roles "
                            "or Medical roles, not both — keep them scoped to one app.",
        }),
        ("Metadata", {
            "fields": ("id", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description="Org. roles")
    def role_count(self, obj):
        return obj.roles.count()

    @admin.display(description="Medical roles")
    def medical_role_count(self, obj):
        return obj.medical_roles.count()


@admin.register(PermissionAuditLog)
class PermissionAuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "timestamp",
        "action_badge",
        "action_by",
        "target_user",
        "target_role",
        "ip_address",
    )
    list_filter = ("action", "timestamp")
    search_fields = (
        "description",
        "action_by__email",
        "target_user__email",
        "target_role__role_name",
        "ip_address",
    )
    date_hierarchy = "timestamp"
    ordering = ("-timestamp",)
    list_per_page = 50
    list_select_related = ("action_by", "target_user", "target_role")
    readonly_fields = (
        "id", "action_by", "action", "target_user", "target_role",
        "description", "ip_address", "timestamp",
    )

    @admin.display(description="Action", ordering="action")
    def action_badge(self, obj):
        colors = {
            "permission_assigned": "#16a34a",
            "permission_removed": "#dc2626",
            "page_access_changed": "#d97706",
            "unauthorized_attempt": "#dc2626",
            "administrator_setup": "#2563eb",
        }
        color = colors.get(obj.action, "#6b7280")
        return format_html(
            '<span style="display:inline-block;padding:2px 10px;border-radius:999px;'
            'font-size:11px;font-weight:700;color:#fff;background:{}">{}</span>',
            color,
            obj.get_action_display(),
        )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
