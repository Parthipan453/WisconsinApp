from django.db import models
from Students.models import StudentProfile


class ScholarshipCategory(models.Model):

    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
    )

    category_name = models.CharField(
        max_length=100,
        unique=True
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='ACTIVE'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )
    is_full_crud = models.BooleanField(default=False)

    def __str__(self):
        return self.category_name
    


class Scholarship(models.Model):

    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('CLOSED', 'Closed'),
        ('DRAFT', 'Draft'),
    )

    STUDENT_TYPE_CHOICES = (
        ('DOMESTIC', 'Domestic'),
        ('INTERNATIONAL', 'International'),
        ('BOTH', 'Both'),
    )

    DEGREE_LEVEL_CHOICES = (
        ('UNDERGRADUATE', 'Undergraduate'),
        ('GRADUATE', 'Graduate'),
        ('PHD', 'PhD'),
        ('ALL', 'All'),
    )

    AWARD_TYPE_CHOICES = (
        ('FULL_TUITION', 'Full Tuition'),
        ('PARTIAL_TUITION', 'Partial Tuition'),
        ('FIXED_AMOUNT', 'Fixed Amount'),
        ('ROOM_AND_BOARD', 'Room and Board'),
        ('STIPEND', 'Stipend'),
        ('FELLOWSHIP', 'Fellowship'),
        ('ASSISTANTSHIP', 'Assistantship'),
        ('COMBINATION', 'Combination'),
    )

    category = models.ForeignKey(
        ScholarshipCategory,
        on_delete=models.CASCADE,
        related_name='scholarships'
    )

    scholarship_code = models.CharField(
        max_length=30,
        unique=True
    )

    scholarship_name = models.CharField(
        max_length=255
    )

    short_description = models.CharField(
        max_length=500
    )

    description = models.TextField()

    sponsor_name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    award_type = models.CharField(
        max_length=30,
        choices=AWARD_TYPE_CHOICES
    )

    award_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True
    )

    number_of_awards = models.PositiveIntegerField(
        default=1
    )

    renewable = models.BooleanField(
        default=False
    )

    renewal_duration_years = models.PositiveIntegerField(
        default=0
    )

    student_type = models.CharField(
        max_length=20,
        choices=STUDENT_TYPE_CHOICES,
        default='BOTH'
    )

    degree_level = models.CharField(
        max_length=20,
        choices=DEGREE_LEVEL_CHOICES,
        default='ALL'
    )

    minimum_gpa = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        blank=True,
        null=True
    )

    minimum_credits = models.PositiveIntegerField(
        blank=True,
        null=True
    )

    financial_need_required = models.BooleanField(
        default=False
    )

    first_generation_required = models.BooleanField(
        default=False
    )

    leadership_required = models.BooleanField(
        default=False
    )

    community_service_required = models.BooleanField(
        default=False
    )

    essay_required = models.BooleanField(
        default=False
    )

    recommendation_required = models.BooleanField(
        default=False
    )

    additional_requirements = models.TextField(
        blank=True,
        null=True
    )

    application_start_date = models.DateField()

    application_deadline = models.DateField()

    announcement_date = models.DateField(
        blank=True,
        null=True
    )

    website_url = models.URLField(
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='ACTIVE'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )
    is_full_crud = models.BooleanField(default=False)

    def __str__(self):
        return self.scholarship_name
    


class ScholarshipDocument(models.Model):

    scholarship = models.ForeignKey(
        Scholarship,
        on_delete=models.CASCADE,
        related_name='required_documents'
    )

    document_name = models.CharField(
        max_length=255
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    is_required = models.BooleanField(
        default=True
    )
    is_full_crud = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.scholarship.scholarship_name} - {self.document_name}"
    


class ScholarshipApplication(models.Model):

    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('UNDER_REVIEW', 'Under Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('WAITLISTED', 'Waitlisted'),
    )

    scholarship = models.ForeignKey(
        Scholarship,
        on_delete=models.CASCADE,
        related_name='applications'
    )

    
    student = models.ForeignKey(
    'Students.StudentProfile',
    on_delete=models.CASCADE
)

    application_number = models.CharField(
        max_length=50,
        unique=True
    )

    application_date = models.DateField(
        auto_now_add=True
    )

    personal_statement = models.TextField(
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT'
    )

    remarks = models.TextField(
        blank=True,
        null=True
    )

    submitted_at = models.DateTimeField(
        blank=True,
        null=True
    )

    reviewed_at = models.DateTimeField(
        blank=True,
        null=True
    )
    is_full_crud = models.BooleanField(default=False)

    def __str__(self):
        return self.application_number
    

class ScholarshipApplicationDocument(models.Model):

    application = models.ForeignKey(
        ScholarshipApplication,
        on_delete=models.CASCADE,
        related_name='documents'
    )

    document_name = models.CharField(
        max_length=255
    )

    file = models.FileField(
        upload_to='scholarship_documents/'
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )
    is_full_crud = models.BooleanField(default=False)

    def __str__(self):
        return self.document_name
    

class ScholarshipAward(models.Model):

    scholarship = models.ForeignKey(
        Scholarship,
        on_delete=models.CASCADE,
        related_name='awards'
    )

    student = models.ForeignKey(
    'Students.StudentProfile',
    on_delete=models.CASCADE
)

    application = models.ForeignKey(
        ScholarshipApplication,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    academic_year = models.CharField(
        max_length=20
    )

    awarded_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    award_date = models.DateField()

    renewal_status = models.BooleanField(
        default=False
    )

    notes = models.TextField(
        blank=True,
        null=True
    )
    is_full_crud = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student} - {self.scholarship}"