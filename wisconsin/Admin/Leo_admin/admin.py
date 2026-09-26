from django.contrib import admin
from .models import AcademicStanding


@admin.register(AcademicStanding)
class AcademicStandingAdmin(admin.ModelAdmin):
    list_display = (
        "standing_id",
        "standing_name",
        "minimum_gpa",
        "is_active",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "standing_name",
        "description",
    )

    ordering = (
        "-minimum_gpa",
    )

    list_per_page = 25