from django.contrib import admin
from .models import *
from .Alan.admin import *
from Medical.Dominic.admin import *
from django.utils.html import format_html
from django.utils import timezone

# Register your models here.
admin.site.register(PatientProfile)
admin.site.register(AthleteMedicalProfile)
admin.site.register(InjuryRecord)
admin.site.register(MedicalVisit)
admin.site.register(MedicalService)

admin.site.register(PatientRegistry)
admin.site.register(MedicalDocument)
admin.site.register(LaboratoryTest)
admin.site.register(HealthCamp)
admin.site.register(HealthCampRegistry)

@admin.register(MedicalDepartment)
class MedicalDepartmentAdmin(admin.ModelAdmin):
    search_fields = ("department_name",)



@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):

    list_display = (
        "appointment_number",
        "patient",
        "athlete",
        "medical_staff",
        "hospital",
        "service",
        "appointment_date",
        "appointment_time",
        "status",
    )
 
    list_filter = (
        "status",
        "medical_staff",
        "hospital",
        "appointment_date",
    )

    search_fields = (
        "appointment_number",
        "patient__user__first_name",
        "patient__user__last_name",
        "medical_staff__user__first_name",
    )

    ordering = (
        "appointment_date",
        "appointment_time",
    )

@admin.register(MedicalStaffProfile)
class MedicalStaffProfileAdmin(admin.ModelAdmin):
    search_fields = ("user__first_name", "user__last_name", "user__username")


class UpcomingOneTimeFilter(admin.SimpleListFilter):
    title = "One-Time Date"
    parameter_name = "one_time_window"

    def lookups(self, request, model_admin):
        return [
            ("upcoming", "Upcoming"),
            ("past", "Past"),
            ("today", "Today"),
        ]

    def queryset(self, request, queryset):
        today = timezone.localdate()
        if self.value() == "upcoming":
            return queryset.filter(specific_date__gte=today)
        if self.value() == "past":
            return queryset.filter(specific_date__lt=today)
        if self.value() == "today":
            return queryset.filter(specific_date=today)
        return queryset


"""swetha's code start """

admin.site.register(PatientRegistration)

"""swetha's code end """

admin.site.register(MedicalStaffLeave)