from django.db import models
from Faculty.models import FacultyProfile


class StaffAttendance(models.Model):
    user = models.ForeignKey("Admin.User", on_delete=models.CASCADE, related_name="staff_attendances")
    date = models.DateField()
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)
    total_hours_worked = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    is_full_crud = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "staff_attendances"
        unique_together = ("user", "date")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.user} - {self.date}"


class StaffLoginLog(models.Model):
    user = models.ForeignKey("Admin.User", on_delete=models.CASCADE, related_name="staff_login_logs")
    session_key = models.CharField(max_length=40, blank=True, null=True)
    login_time = models.DateTimeField()
    logout_time = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    is_full_crud = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "staff_login_logs"
        ordering = ["-login_time"]

    def __str__(self):
        return f"{self.user} - {self.login_time}"


class Holiday(models.Model):
    date = models.DateField(unique=True)
    name = models.CharField(max_length=100)
    is_full_crud = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        db_table = "eric_holidays"
        ordering = ["date"]

    def __str__(self):
        return f"{self.name} - {self.date}"


class FacultyAttendanceRecord(models.Model):
    STATUS_CHOICES = (
        ("PRESENT", "Present"),
        ("ABSENT", "Absent"),
        ("LATE", "Late"),
        ("HALF_DAY", "Half Day"),
        ("ON_LEAVE", "On Leave"),
    )

    faculty = models.ForeignKey(
        FacultyProfile, on_delete=models.CASCADE, related_name="attendance_records")
    date = models.DateField()
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="PRESENT")
    late_minutes = models.PositiveSmallIntegerField(default=0)
    early_leave_minutes = models.PositiveSmallIntegerField(default=0)
    total_hours_worked = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True)
    marked_by = models.ForeignKey(
        "Staff.StaffProfile", on_delete=models.SET_NULL, null=True, blank=True)
    is_full_crud = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "faculty_attendance_records"
        unique_together = ("faculty", "date")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.faculty} - {self.date} ({self.get_status_display()})"
