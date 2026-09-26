from django.contrib import admin
from .models import Holiday, FacultyAttendanceRecord, StaffAttendance, StaffLoginLog


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ("date", "name")
    list_filter = ("date",)
    search_fields = ("name",)
    date_hierarchy = "date"


@admin.register(FacultyAttendanceRecord)
class FacultyAttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ("faculty", "date", "check_in", "check_out", "status", "total_hours_worked", "marked_by")
    list_filter = ("status", "date")
    search_fields = ("faculty__employee_id", "faculty__user__first_name", "faculty__user__last_name")
    date_hierarchy = "date"
    list_select_related = ("faculty", "faculty__user", "marked_by")


@admin.register(StaffAttendance)
class StaffAttendanceAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "check_in", "check_out", "total_hours_worked")
    list_filter = ("date",)
    search_fields = ("user__username", "user__first_name", "user__last_name")
    date_hierarchy = "date"


@admin.register(StaffLoginLog)
class StaffLoginLogAdmin(admin.ModelAdmin):
    list_display = ("user", "login_time", "logout_time", "ip_address")
    list_filter = ("login_time",)
    search_fields = ("user__username", "user__first_name", "user__last_name")
    date_hierarchy = "login_time"
