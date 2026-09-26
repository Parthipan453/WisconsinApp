

# *************************************** Arun Code ********************************************************** 

import uuid
from django.db import models
from Admin.models import User
from Admin.Colleges.models import (
    University,
    School,
    Degree,
    AcademicProgram,
)
from Admin.bela_admin.models import Department, Course
from Admin.Colleges import *
from django_countries.fields import CountryField 
from django.db.models import Q 


## Leo's Code Start ##
from .Leo_Student.models import *
## Leo's Code End ##

MEMBERSHIP_STATUS = (
    ('ACTIVE', 'Active'),
    ('INACTIVE', 'Inactive'),
    ('ALUMNI', 'Alumni'),
    ('PENDING', 'Pending'),
)

from Admin.models import User  
from Faculty.models import FacultyProfile

class StudentProfile(models.Model):
    CITIZENSHIP_CHOICES = (
        ("CITIZEN", "Citizen"),
        ("PERMANENT_RESIDENT", "Permanent Resident"),
        ("INTERNATIONAL", "International"),
        ("OTHER", "Other"),
    )
    MARITAL_STATUS_CHOICES = (
        ("SINGLE", "Single"),
        ("MARRIED", "Married"),
        ("DIVORCED", "Divorced"),
        ("OTHER", "Other"),
    )
    STATUS_CHOICES = (
        ("ACTIVE", "Active"),
        ("LEAVE", "Leave"),
        ("GRADUATED", "Graduated"),
        ("WITHDRAWN", "Withdrawn"),
    )
    ACADEMIC_LEVEL_CHOICES = (
        ("UNDERGRADUATE", "Undergraduate"),
        ("GRADUATE", "Graduate"),
        ("PHD", "PhD"),
    )

    

    # One-to-one connect to user model
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="student_profile"
    )

    # Identifiers
    student_number = models.CharField(max_length=50, unique=True)

    # Personal Information
    preferred_name = models.CharField(max_length=100, blank=True, null=True)
    university_email = models.EmailField(unique=True)
    personal_email = models.EmailField(blank=True, null=True)
    citizenship_status = models.CharField(
        max_length=30, choices=CITIZENSHIP_CHOICES, blank=True, null=True
    )
    country_of_citizenship = CountryField(
        blank=True,
        null=True
    )
    marital_status = models.CharField(
        max_length=20, choices=MARITAL_STATUS_CHOICES, blank=True, null=True
    )
    # ***********bela code start**************
    program = models.ForeignKey(
        "Colleges.AcademicProgram",
        on_delete=models.PROTECT,
        related_name="students",
        null=True,
        blank=True,
    )
    #***************** bela code end *************
    # Academic Info
    admission_date = models.DateField(blank=True, null=True)
    expected_graduation_date = models.DateField(blank=True, null=True)
    current_status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="ACTIVE"
    )
    academic_level = models.CharField(
        max_length=20, choices=ACADEMIC_LEVEL_CHOICES, blank=True, null=True
    )
    cumulative_gpa = models.DecimalField(
        max_digits=4, decimal_places=2, blank=True, null=True
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_full_crud = models.BooleanField(default=False)

    #Blaze code start--------------------------------------------------->(06.07.26)

    tfa_enabled = models.BooleanField(default=False)
    tfa_secret = models.CharField(max_length=255, blank=True, null=True)
    tfa_backup_codes = models.TextField(blank=True, null=True)
    
    #Blaze code end--------------------------------------------------->(06.07.26)

    class Meta:
        db_table = "student_profiles"

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.student_number})"


class StudentAddress(models.Model):
    ADDRESS_TYPE_CHOICES = (
        ("PERMANENT", "Permanent"),
        ("MAILING", "Mailing"),
        ("CAMPUS_HOUSING", "Campus Housing"),
    )

    student = models.ForeignKey(
        StudentProfile, on_delete=models.CASCADE, related_name="addresses"
    )
    address_type = models.CharField(max_length=20, choices=ADDRESS_TYPE_CHOICES)
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    is_full_crud = models.BooleanField(default=False)

    

    class Meta:
        db_table = "student_addresses"

    def __str__(self):
        return f"{self.student} - {self.address_type}"


class StudentEmergencyContact(models.Model):
    student = models.ForeignKey(
        StudentProfile, on_delete=models.CASCADE, related_name="emergency_contacts"
    )
    contact_name = models.CharField(max_length=150)
    relationship = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    priority = models.PositiveSmallIntegerField(default=1)
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "student_emergency_contacts"
        ordering = ["priority"]

    def __str__(self):
        return f"{self.contact_name} ({self.relationship}) - {self.student}"


class StudentAcademicProfile(models.Model):

    student = models.OneToOneField(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="academic_profile"
    )

    university = models.ForeignKey(
        University,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="student_academic_profiles"
    )
    

    school = models.ForeignKey(
        School,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="student_academic_profiles"
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="student_academic_profiles"
    )

    degree = models.ForeignKey(
        Degree,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="student_academic_profiles"
    )

    program = models.ForeignKey(
        AcademicProgram,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="student_academic_profiles"
    )

    major = models.CharField(max_length=150, blank=True, null=True)
    minor = models.CharField(max_length=150, blank=True, null=True)
    concentration = models.CharField(max_length=150, blank=True, null=True)

    advisor_id = models.IntegerField(blank=True, null=True)
    catalog_year = models.PositiveSmallIntegerField(blank=True, null=True)

    is_full_crud = models.BooleanField(default=False)

    

    class Meta:
        db_table = "student_academic_profiles"

    def __str__(self):
        return f"{self.student} - {self.major}"
    
# ================================Parthi Update start====================================================    

class Semester(models.Model):
    SEMESTER_TYPES = [
        ('FA', 'Fall'),
        ('SP', 'Spring'),
        ('SU', 'Summer'),
        ('WI', 'Winter'),
    ]
    
    semester_id = models.AutoField(primary_key=True)
    semester_code = models.CharField(max_length=10, unique=True)
    semester_type = models.CharField(max_length=2, choices=SEMESTER_TYPES)
    academic_year = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    is_full_crud = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'semesters'
    
    def __str__(self):
        return f"{self.get_semester_type_display()} {self.academic_year}"


# class Course(models.Model):
#     course_id = models.AutoField(primary_key=True)
#     course_code = models.CharField(max_length=20, unique=True)
#     course_name = models.CharField(max_length=200)
#     credits = models.IntegerField(default=3)
#     department_id = models.IntegerField(blank=True, null=True)
#     is_full_crud = models.BooleanField(default=False)
    
#     class Meta:
#         db_table = 'courses'
    
#     def __str__(self):
#         return f"{self.course_code} - {self.course_name}"


class CourseSection(models.Model):
    SECTION_TYPES = [
        ('LEC', 'Lecture'),
        ('LAB', 'Lab'),
        ('TUT', 'Tutorial'),
        ('SEM', 'Seminar'),
        ('DIS', 'Discussion'),
    ]
    STATUS_CHOICES = (
        ("CONFIRMED", "Confirmed"),
        ("PENDING", "Pending"),
        ("CONFLICT", "Conflict"),
        ("CANCELLED", "Cancelled"),
    )
    course = models.ForeignKey(
        "bela_admin.Course",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    section_id = models.AutoField(primary_key=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    capacity = models.PositiveSmallIntegerField(default=30)
    # course_id = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sections')
    section_number = models.CharField(max_length=5)
    section_type = models.CharField(max_length=3, choices=SECTION_TYPES, default='LEC')
    semester_id = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='sections')
    room_number = models.CharField(max_length=50, blank=True)
    building_name = models.CharField(max_length=100, blank=True)
    faculty_name = models.CharField(max_length=100, blank=True)
    is_full_crud = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'course_sections'
    
    def __str__(self):
        return f"{self.course.course_code} - Sec {self.section_number}"


class Schedule(models.Model):
    DAYS_OF_WEEK = [
        ('MON', 'Monday'),
        ('TUE', 'Tuesday'),
        ('WED', 'Wednesday'),
        ('THU', 'Thursday'),
        ('FRI', 'Friday'),
        ('SAT', 'Saturday'),
        ('SUN', 'Sunday'),
    ]
    
    schedule_id = models.AutoField(primary_key=True)
    section_id = models.ForeignKey(CourseSection, on_delete=models.CASCADE, related_name='schedules')
    day_of_week = models.CharField(max_length=3, choices=DAYS_OF_WEEK)
    dates = models.JSONField(default=list)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=50)
    building = models.CharField(max_length=100)
    is_online = models.BooleanField(default=False)
    is_full_crud = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'schedules'
        ordering = ['day_of_week', 'start_time']

    # Students/models.py — inside Schedule class

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._check_conflicts()

    def _check_conflicts(self):
        overlaps = Schedule.objects.filter(
            day_of_week=self.day_of_week,
            room=self.room,
            building=self.building,
        ).exclude(schedule_id=self.schedule_id).filter(
            Q(start_time__lt=self.end_time),
            Q(end_time__gt=self.start_time),
        )

        section = self.section_id
        if overlaps.exists():
            section.status = "CONFLICT"
        elif section.status == "CONFLICT":
            # re-check: was this the only conflict? if so, clear it
            section.status = "CONFIRMED"
        section.save(update_fields=["status"])
    
    def __str__(self):
        return f"{self.section_id} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"
    
# ================================Parthi Update end====================================================    




class StudentEnrollment(models.Model):
    ENROLLMENT_STATUS_CHOICES = (
        ("FULL_TIME", "Full-Time"),
        ("PART_TIME", "Part-Time"),
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
        ("WITHDRAWN", "Withdrawn"),
        ("LEAVE", "Leave of Absence"),
    )
    ACADEMIC_STANDING_CHOICES = (
        ("GOOD_STANDING", "Good Standing"),
        ("PROBATION", "Probation"),
        ("SUSPENSION", "Suspension"),
        ("HONOR_ROLL", "Honor Roll"),
        ("DEAN_LIST", "Dean's List"),
    )
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="enrollments"
    )
    section_id = models.ForeignKey(
        CourseSection,
        on_delete=models.CASCADE,
        related_name="enrollments"
    )
    semester = models.ForeignKey(
        Semester,
        on_delete=models.CASCADE,
        related_name="enrollments"
    )
    enrollment_status = models.CharField(
        max_length=20,
        choices=ENROLLMENT_STATUS_CHOICES
    )
    credit_load = models.PositiveSmallIntegerField(
        blank=True,
        null=True
    )
    academic_standing = models.CharField(
        max_length=20,
        choices=ACADEMIC_STANDING_CHOICES,
        blank=True,
        null=True
    )
    class Meta:
        unique_together = (
            "student",
            "section_id",
            "semester",
        )
    def __str__(self):
        return f"{self.student} - {self.section_id}"

# ================================Parthi Update start ====================================================


    section_id = models.ForeignKey(
        CourseSection, 
            on_delete=models.SET_NULL, 
            null=True, 
            blank=True, 
            related_name='enrollments'
    )
    is_full_crud = models.BooleanField(default=False)

# ================================Parthi Update end====================================================    

    class Meta:
        db_table = "student_enrollments"
        # unique_together = ("student", "term_id")

    def __str__(self):
        return f"{self.student} - Term {self.term_id}"


class StudentFinancialAid(models.Model):

    AID_TYPE_CHOICES = (
        ("SCHOLARSHIP", "Scholarship"),
        ("GRANT", "Grant"),
        ("FELLOWSHIP", "Fellowship"),
        ("ASSISTANTSHIP", "Assistantship"),
        ("LOAN", "Loan"),
    )

    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("UNDER_REVIEW", "Under Review"),
        ("AWARDED", "Awarded"),
        ("REJECTED", "Rejected"),
        ("CANCELLED", "Cancelled"),
        ("EXPIRED", "Expired"),
    )

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="financial_aids"
    )

    aid_type = models.CharField(
        max_length=20,
        choices=AID_TYPE_CHOICES
    )

    academic_year = models.CharField(max_length=20)

    reason = models.TextField()

    supporting_document = models.FileField(
        upload_to="students/financial_aid/",
        blank=True,
        null=True
    )

    award_amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
        default=0.00
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING"
    )

    remarks = models.TextField(
        blank=True,
        null=True
    )
    is_full_crud = models.BooleanField(default=False)

    applied_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    #Blaze code start--------------------------------------------------->(03.07.26)



    financial_need_description = models.TextField(blank=True, null=True)
    
    # Loan-specific fields
    loan_amount_requested = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    loan_purpose = models.TextField(blank=True, null=True)
    cosigner_name = models.CharField(max_length=200, blank=True, null=True)
    cosigner_relationship = models.CharField(max_length=100, blank=True, null=True)
    
    # Assistantship-specific fields
    preferred_department = models.CharField(max_length=200, blank=True, null=True)
    faculty_interest = models.TextField(blank=True, null=True)
    relevant_skills = models.TextField(blank=True, null=True)
    
    # Tracking
    application_number = models.CharField(max_length=50, blank=True, null=True)
    terms_accepted = models.BooleanField(default=False)
    terms_accepted_date = models.DateTimeField(blank=True, null=True)
    
    #Blaze code End--------------------------------------------------->(03.07.26)

    class Meta:
        db_table = "student_financial_aids"

    def __str__(self):
        return f"{self.student} - {self.aid_type} ({self.academic_year})"

class StudentFee(models.Model):

    STATUS_CHOICES = (
        ("UNPAID", "Unpaid"),
        ("PARTIALLY_PAID", "Partially Paid"),
        ("PAID", "Paid"),
    )

    FEE_TYPE_CHOICES = (
        ("TUITION", "Tuition"),
        ("HOSTEL", "Hostel"),
        ("TRANSPORT", "Transport"),
        ("LIBRARY", "Library"),
        ("LAB", "Laboratory"),
        ("OTHER", "Other"),
    )

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="fees"
    )

    fee_type = models.CharField(
        max_length=30,
        choices=FEE_TYPE_CHOICES
    )

    is_full_crud = models.BooleanField(default=True)

    description = models.CharField(max_length=255)

    academic_year = models.CharField(max_length=20)

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    due_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="UNPAID"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    late_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0) #------> just add by Blaze (01.06.2026)

    class Meta:
        db_table = "student_fees"

    def __str__(self):
        return f"{self.student} - {self.description}"

class StudentFeePayment(models.Model):

    PAYMENT_METHOD_CHOICES = (
        ("CREDIT_CARD", "Credit Card"),
        ("DEBIT_CARD", "Debit Card"),
        ("BANK_TRANSFER", "Bank Transfer"),
        ("UPI", "UPI"),
        ("CASH", "Cash"),
    )

    STATUS_CHOICES = (
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
        ("PENDING", "Pending"),
    )

    fee = models.ForeignKey(
        StudentFee,
        on_delete=models.CASCADE,
        related_name="payments"
    )

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="fee_payments"
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    payment_method = models.CharField(
        max_length=30,
        choices=PAYMENT_METHOD_CHOICES
    )

    transaction_id = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    payment_date = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="SUCCESS"
    )

    remarks = models.TextField(
        blank=True,
        null=True
    )

    is_full_crud = models.BooleanField(default=True)


    class Meta:
        db_table = "student_fee_payments"

    def __str__(self):
        return f"{self.student} - {self.amount}"
    
class StudentHousing(models.Model):
    student = models.ForeignKey(
        StudentProfile, on_delete=models.CASCADE, related_name="housing_records"
    )
    residence_hall = models.CharField(max_length=150)
    room_number = models.CharField(max_length=20)
    move_in_date = models.DateField()
    move_out_date = models.DateField(blank=True, null=True)
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "student_housing"

    def __str__(self):
        return f"{self.student} - {self.residence_hall} {self.room_number}"


class StudentResearchProfile(models.Model):
    student = models.ForeignKey(
        StudentProfile, on_delete=models.CASCADE, related_name="research_profiles"
    )
    faculty_mentor_id = models.IntegerField(blank=True, null=True)
    research_area = models.CharField(max_length=255, blank=True, null=True)
    project_title = models.CharField(max_length=255)
    participation_start = models.DateField()
    participation_end = models.DateField(blank=True, null=True)
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "student_research_profiles"

    def __str__(self):
        return f"{self.student} - {self.project_title}"


class StudentOrganization(models.Model):
    school = models.ForeignKey(
        School, on_delete=models.CASCADE, related_name="organizations", null=True, blank=True,
    )
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="organizations",
    )
    organization_name = models.CharField(max_length=200, unique=True)
    motto = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    max_members = models.PositiveIntegerField(
        blank=True, null=True,
        help_text="Leave blank for unlimited members."
    )
    founded_date = models.DateField(blank=True, null=True)
    advisor = models.ForeignKey(
        FacultyProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name="advised_organizations",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    cover_image = models.ImageField(upload_to="organizations/covers/", blank=True, null=True)

    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "student_organizations"
        ordering = ["organization_name"]

    def __str__(self):
        return self.organization_name

    @property
    def active_member_count(self):
        return self.members.filter(status="ACTIVE").count()

    @property
    def is_full(self):
        return self.max_members is not None and self.active_member_count >= self.max_members
    
class StudentOrganizationMembership(models.Model):

    MEMBERSHIP_STATUS = (
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('ALUMNI', 'Alumni'),
        ('PENDING', 'Pending'),
    )

    membership_id = models.AutoField(
        primary_key=True
    )

    organization = models.ForeignKey(
        StudentOrganization,
        on_delete=models.CASCADE,
        related_name="members"
    )

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="organization_memberships"
    )

    role = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    start_date = models.DateField()

    end_date = models.DateField(
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=MEMBERSHIP_STATUS,
        default="ACTIVE"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    is_full_crud = models.BooleanField(
        default=False
    )

    class Meta:
        db_table = "student_organization_memberships"
        unique_together = ("organization", "student")

    def __str__(self):
        return f"{self.student} - {self.organization.organization_name}"


class StudentCareerProfile(models.Model):
    student = models.OneToOneField(
        StudentProfile, on_delete=models.CASCADE, related_name="career_profile"
    )
    internship_company = models.CharField(max_length=200, blank=True, null=True)
    internship_title = models.CharField(max_length=150, blank=True, null=True)
    internship_start = models.DateField(blank=True, null=True)
    internship_end = models.DateField(blank=True, null=True)
    career_interest = models.TextField(blank=True, null=True)
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "student_career_profiles"

    def __str__(self):
        return f"{self.student} - Career Profile"


class StudentDocument(models.Model):
    DOCUMENT_TYPE_CHOICES = (
        ("PASSPORT", "Passport"),
        ("VISA", "Visa"),
        ("TRANSCRIPT", "Transcript"),
        ("DEGREE_CERTIFICATE", "Degree Certificate"),
        ("FINANCIAL_DOCUMENT", "Financial Document"),
        ("OTHER", "Other"),
    )
    VERIFICATION_STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("VERIFIED", "Verified"),
        ("REJECTED", "Rejected"),
    )

    student = models.ForeignKey(
        StudentProfile, on_delete=models.CASCADE, related_name="documents"
    )
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPE_CHOICES)
    file_name = models.CharField(max_length=255)
    file = models.FileField(upload_to="students/documents/", blank=True, null=True)
    upload_date = models.DateTimeField(auto_now_add=True)
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default="PENDING",
    )
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "student_documents"

    def __str__(self):
        return f"{self.student} - {self.document_type}"
    

class CourseMaterial(models.Model):
    MATERIAL_TYPE_CHOICES = (
        ('SYLLABUS', 'Syllabus'),
        ('SLIDES', 'Slides'),
        ('HANDOUT', 'Handout'),
        ('LAB_MANUAL', 'Lab Manual'),
        ('OTHER', 'Other'),
    )
    course_section = models.ForeignKey(
        CourseSection, on_delete=models.CASCADE, related_name='materials'
    )
    title = models.CharField(max_length=255)
    material_type = models.CharField(max_length=20, choices=MATERIAL_TYPE_CHOICES, default='OTHER')
    file = models.FileField(upload_to='course_materials/')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = "course_materials"

    def __str__(self):
        return f"{self.course_section} - {self.title}"


class SupportTicket(models.Model):
    STATUS_CHOICES = (
        ('OPEN', 'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
    )
    PRIORITY_CHOICES = (
        ('LOW', 'Low'), ('MEDIUM', 'Medium'), ('URGENT', 'Urgent'),
    )
    course_section = models.ForeignKey(
        CourseSection, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets'
    )
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='submitted_tickets')
    subject = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    is_full_crud = models.BooleanField(default=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_tickets')

    class Meta:
        db_table = "support_tickets"

    def __str__(self):
        return f"{self.subject} ({self.status})"


from django.db import models
from django.utils import timezone

from Staff.models import StaffProfile
from Faculty.models import FacultyProfile

from Students.models import (
    CourseSection,
    Semester,
    StudentProfile,
)

from Admin.bela_admin.models import Room

class Exam(models.Model):

    EXAM_TYPE_CHOICES = (
        ("QUIZ", "Quiz"),
        ("MIDTERM", "Midterm"),
        ("FINAL", "Final"),
        ("PRACTICAL", "Practical"),
    )

    STATUS_CHOICES = (
        ("DRAFT", "Draft"),
        ("SCHEDULED", "Scheduled"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    )

    course_section = models.ForeignKey(
        CourseSection,
        on_delete=models.CASCADE,
        related_name="exams"
    )

    semester = models.ForeignKey(
        Semester,
        on_delete=models.CASCADE,
        related_name="exams"
    )

    exam_name = models.CharField(max_length=200)

    exam_type = models.CharField(
        max_length=20,
        choices=EXAM_TYPE_CHOICES
    )

    exam_date = models.DateField()

    start_time = models.TimeField()

    end_time = models.TimeField()

    duration_minutes = models.PositiveIntegerField()

    total_marks = models.PositiveIntegerField(default=100)

    pass_marks = models.PositiveIntegerField(default=40)

    instructions = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="DRAFT"
    )

    created_by = models.ForeignKey(
        StaffProfile,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_exams"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    is_full_crud = models.BooleanField(default=False)
    class Meta:
        db_table = "exam_master"
        ordering = ["exam_date", "start_time"]

    def __str__(self):
        return f"{self.exam_name}"


class ExamRoomAllocation(models.Model):

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="room_allocations"
    )

    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE
    )

    allocated_capacity = models.PositiveIntegerField()

    allocated_by = models.ForeignKey(
        StaffProfile,
        on_delete=models.SET_NULL,
        null=True
    )

    allocated_at = models.DateTimeField(auto_now_add=True)

    is_full_crud = models.BooleanField(default=True)
    class Meta:
        db_table = "exam_room_allocations"

    def __str__(self):
        return f"{self.exam} - {self.room}"


class ExamInvigilator(models.Model):

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="invigilators"
    )

    faculty = models.ForeignKey(
        FacultyProfile,
        on_delete=models.CASCADE
    )

    assigned_by = models.ForeignKey(
        StaffProfile,
        on_delete=models.SET_NULL,
        null=True
    )

    assigned_at = models.DateTimeField(auto_now_add=True)
    is_full_crud = models.BooleanField(default=True)
    class Meta:
        db_table = "exam_invigilators"

    def __str__(self):
        return f"{self.exam} - {self.faculty}"


class ExamSeat(models.Model):

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="seat_allocations"
    )

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE
    )

    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE
    )

    seat_number = models.CharField(max_length=20)

    is_full_crud = models.BooleanField(default=True)
    class Meta:
        db_table = "exam_seats"

    def __str__(self):
        return f"{self.student} - {self.seat_number}"


class ExamAttendance(models.Model):

    ATTENDANCE_CHOICES = (
        ("PRESENT", "Present"),
        ("ABSENT", "Absent"),
        ("MALPRACTICE", "Malpractice"),
    )

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE
    )

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE
    )

    attendance = models.CharField(
        max_length=20,
        choices=ATTENDANCE_CHOICES,
        default="PRESENT"
    )

    remarks = models.TextField(blank=True)

    is_full_crud = models.BooleanField(default=True)
    class Meta:
        db_table = "exam_attendance"

    def __str__(self):
        return f"{self.student}"


class ExamConflict(models.Model):

    CONFLICT_CHOICES = (
        ("ROOM", "Room Conflict"),
        ("FACULTY", "Faculty Conflict"),
        ("STUDENT", "Student Conflict"),
    )

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE
    )

    conflict_type = models.CharField(
        max_length=20,
        choices=CONFLICT_CHOICES
    )

    description = models.TextField()

    resolved = models.BooleanField(default=False)

    resolved_by = models.ForeignKey(
        StaffProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    resolved_at = models.DateTimeField(
        blank=True,
        null=True
    )

    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = "exam_conflicts"

    def __str__(self):
        return self.conflict_type


from Staff.models import (
    StaffProfile,
    MessageThread,
)

class StudentOrgMessageThread(models.Model):
    organization = models.OneToOneField(
        'Students.StudentOrganization', on_delete=models.CASCADE, related_name='chat_thread'
    )
    thread = models.ForeignKey(MessageThread, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_full_crud = models.BooleanField(default=True)

    def __str__(self):
        return f"Chat thread for {self.organization.organization_name}"

# *************************************** Arun Code ********************************************************** 






# <-------------------------BLAZE CODE START STUDENT LEAVE REQ - (25.07.26)--------------------------->


from django.db import models
from django.conf import settings
from django.utils import timezone

class StudentLeaveType(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    max_days_per_year = models.IntegerField(default=30)
    is_paid = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=True)
    color = models.CharField(max_length=7, default='#3b82f6')
    icon = models.CharField(max_length=50, default='ti ti-calendar')
    is_half_day_allowed = models.BooleanField(default=True)
    is_full_crud = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

    class Meta:
        db_table = "student_leave_types"


class StudentLeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    HALF_DAY_CHOICES = [
        ('full', 'Full Day'),
        ('first_half', 'First Half (Morning)'),
        ('second_half', 'Second Half (Afternoon)'),
    ]
    
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='student_leave_requests'
    )
    leave_type = models.ForeignKey(StudentLeaveType, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    half_day_type = models.CharField(max_length=20, choices=HALF_DAY_CHOICES, default='full')
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Attachments
    attachment = models.FileField(upload_to='student_leave_attachments/%Y/%m/', null=True, blank=True)
    attachment_name = models.CharField(max_length=255, blank=True, null=True)
    
    # Approval
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='student_approved_leaves'
    )
    approved_date = models.DateTimeField(null=True, blank=True)
    approval_remarks = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    is_full_crud = models.BooleanField(default=True)
    
    class Meta:
        db_table = "student_leave_requests"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.leave_type.name}"
    
    @property
    def days_count(self):
        if self.half_day_type != 'full':
            return 0.5
        delta = self.end_date - self.start_date
        return delta.days + 1
    
    @property
    def display_status(self):
        status_map = {
            'pending': 'Pending',
            'approved': 'Approved',
            'rejected': 'Rejected',
            'cancelled': 'Cancelled',
        }
        return status_map.get(self.status, self.status)


class StudentLeaveBalance(models.Model):
    student = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='student_leave_balance'
    )
    annual_leave_balance = models.FloatField(default=30.0)
    sick_leave_balance = models.FloatField(default=15.0)
    casual_leave_balance = models.FloatField(default=10.0)
    earned_leave_balance = models.FloatField(default=0.0)
    compensatory_leave_balance = models.FloatField(default=0.0)
    
    is_full_crud = models.BooleanField(default=True)
    
    class Meta:
        db_table = "student_leave_balances"
    
    def __str__(self):
        return f"{self.student.get_full_name()} - Leave Balance"


# <-------------------------BLAZE CODE END STUDENT LEAVE REQ (25.07.26)--------------------------->


# <-------------------------BLAZE CODE START REQ (28.08.26)--------------------------->

import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class MaintenanceRequest(models.Model):
    PRIORITY_CHOICES = (
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('EMERGENCY', 'Emergency'),
    )
    
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('ASSIGNED', 'Assigned'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    )
    
    ISSUE_TYPE_CHOICES = (
        ('PLUMBING', 'Plumbing'),
        ('ELECTRICAL', 'Electrical'),
        ('FURNITURE', 'Furniture'),
        ('APPLIANCE', 'Appliance'),
        ('HVAC', 'HVAC / Heating / Cooling'),
        ('PEST_CONTROL', 'Pest Control'),
        ('CLEANING', 'Cleaning'),
        ('SECURITY', 'Security'),
        ('OTHER', 'Other'),
    )
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='maintenance_requests')
    room = models.ForeignKey('Admin.Room', on_delete=models.CASCADE, related_name='maintenance_requests')
    
    issue_type = models.CharField(max_length=50, choices=ISSUE_TYPE_CHOICES)
    description = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    preferred_time = models.CharField(max_length=100, blank=True)
    photos = models.ImageField(upload_to='maintenance/', blank=True, null=True)
    
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_maintenance')
    completed_date = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_full_crud = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'maintenance_requests'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.room.room_number} - {self.get_issue_type_display()} ({self.status})"
    
    def get_priority_color(self):
        colors = {
            'LOW': 'secondary',
            'MEDIUM': 'info',
            'HIGH': 'warning',
            'EMERGENCY': 'danger'
        }
        return colors.get(self.priority, 'secondary')
    
    def get_status_color(self):
        colors = {
            'PENDING': 'warning',
            'ASSIGNED': 'primary',
            'IN_PROGRESS': 'info',
            'COMPLETED': 'success',
            'CANCELLED': 'secondary'
        }
        return colors.get(self.status, 'secondary')


class RoomInspection(models.Model):
    STATUS_CHOICES = (
        ('PASSED', 'Passed'),
        ('FAILED', 'Failed'),
        ('PENDING', 'Pending'),
    )
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    room = models.ForeignKey('Admin.Room', on_delete=models.CASCADE, related_name='inspections')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inspections')
    
    inspection_date = models.DateTimeField()
    inspector_name = models.CharField(max_length=100)
    
    condition = models.TextField(blank=True, null=True)
    cleanliness = models.IntegerField(default=5)
    damages = models.TextField(blank=True, null=True)
    repairs_needed = models.TextField(blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    remarks = models.TextField(blank=True, null=True)
    photos = models.ImageField(upload_to='inspections/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_full_crud = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'room_inspections'
        ordering = ['-inspection_date']
    
    def __str__(self):
        return f"{self.room.room_number} - {self.inspection_date.date()}"
        
# <-------------------------BLAZE CODE END REQ (28.08.26)--------------------------->
