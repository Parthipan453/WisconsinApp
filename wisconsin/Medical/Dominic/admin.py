from django.contrib import admin
from .models import MedicalStaffRole

@admin.register(MedicalStaffRole)
class MedicalStaffRoleAdmin(admin.ModelAdmin):
    list_display = ( "name", "category", "is_active", "is_full_crud", "created_at",)
    list_display_links = ("name",)
    list_filter = ("category", "is_active", "is_full_crud", "created_at",)
    search_fields = ("name",)
    ordering = ("name",)
    readonly_fields = ("uuid", "created_at", "updated_at",)
    list_editable = ("is_active", "is_full_crud",)
    date_hierarchy = "created_at"
    fieldsets = (
        (
            "Role Information",
            {
                "fields": (
                    "name",
                    "category",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_full_crud",
                    "is_active",
                )
            },
        ),
        (
            "System Information",
            {
                "classes": ("collapse",),
                "fields": (
                    "uuid",
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )