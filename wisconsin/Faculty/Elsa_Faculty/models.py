import secrets
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from Admin.Elsa_admin.models import GradeScale

class CourseGrade(models.Model):
    student = models.ForeignKey("Students.StudentProfile", on_delete=models.CASCADE)
    course = models.ForeignKey("bela_admin.Course", on_delete=models.CASCADE)
    semester = models.ForeignKey("Students.Semester", on_delete=models.CASCADE)
    grade_scale = models.ForeignKey(GradeScale, on_delete=models.CASCADE, null=True, blank=True)
    numeric_score = models.DecimalField(max_digits=5,decimal_places=2, null=True, blank=True,
                                        validators=[MinValueValidator(Decimal('0.00')),MaxValueValidator(Decimal('100.00'))])
    instructor_id = models.CharField(max_length=20)
    grade_date = models.DateField(auto_now=True)
    is_finalized = models.BooleanField(default=False)
    finalized_at = models.DateTimeField(null=True, blank=True)
    is_full_crud = models.BooleanField(default=False)


class GradeChangeRequest(models.Model):
    request_id = models.AutoField(primary_key=True)
    request_code = models.CharField(max_length=12, unique=True, editable=False, blank=True)
    student_id = models.CharField(max_length=20)
    course_id = models.CharField(max_length=20)
    instructor_id = models.CharField(max_length=20)
    current_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.00")),
            MaxValueValidator(Decimal("100.00"))
        ]
    )
    requested_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.00")),
            MaxValueValidator(Decimal("100.00"))
        ]
    )
    current_grade = models.ForeignKey(
        GradeScale,
        on_delete=models.SET_NULL,
        null=True,
        related_name="current_grade_requests"
    )
    requested_grade = models.ForeignKey(
        GradeScale,
        on_delete=models.SET_NULL,
        null=True,
        related_name="requested_grade_requests"
    )
    reason = models.TextField()
    STATUS_CHOICES = (
        ("Pending", "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
    )
    approval_status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="Pending"
    )
    approved_by = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    approved_date = models.DateField(
        blank=True,
        null=True
    )
    request_date = models.DateTimeField(
        auto_now_add=True
    )
    is_full_crud = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.request_id} - {self.student_id}"

    def save(self, *args, **kwargs):
        if not self.request_code:
            self.request_code = self._generate_unique_code()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_unique_code():
        while True:
            code = "REQ-" + secrets.token_hex(3).upper()  # e.g. REQ-9F3A2B
            if not GradeChangeRequest.objects.filter(request_code=code).exists():
                return code