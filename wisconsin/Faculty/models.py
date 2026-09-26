from django.db import models
from Admin.models import User
from .Elsa_Faculty.models import *
from Admin.bela_admin.models import Department

class FacultyRank(models.Model):
    rank_name = models.CharField(max_length=100, unique=True)
    tenure_track = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "faculty_ranks"

    def __str__(self):
        return self.rank_name


class FacultyProfile(models.Model):
    user_types = ["faculty"]
    EMPLOYMENT_STATUS_CHOICES = (
        ("ACTIVE", "Active"),
        ("LEAVE", "Leave"),
        ("RETIRED", "Retired"),
    )

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="faculty_profile"
    )

    # Identifiers
    employee_id = models.CharField(max_length=100, unique=True)

    # Personal / Contact
    preferred_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    office_location = models.CharField(max_length=200, blank=True, null=True)
    profile_photo = models.ImageField(
        upload_to="faculty/profile_photos/", blank=True, null=True
    )
    biography = models.TextField(blank=True, null=True)

    # Employment
    hire_date = models.DateField(blank=True, null=True)
    employment_status = models.CharField(
        max_length=20, choices=EMPLOYMENT_STATUS_CHOICES, default="ACTIVE"
    )

    # Rank & Department
    faculty_rank = models.ForeignKey(
        FacultyRank,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="faculty_members",
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="faculties"
    )

    # ================== Jordan Code Start's Here ==================

    # Faculty Role
    is_mentor = models.BooleanField(default=False)


    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = "faculty_profiles"
    
    def get_mentor_roles(self):
        """Get list of active mentor roles"""
        roles = []
        if self.is_mentor:
            roles.append({'label': 'Mentor', 'class': 'mentor'})
        return roles

    def has_any_mentor_role(self):
        """Check if faculty has any mentor role assigned"""
        return self.is_mentor

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_id})"
    
    # ================== Jordan Code End's Here ==================
    @property
    def is_research_committee_member(self):
        return self.research_committees.filter(is_active=True).exists()
    
    @property
    def is_research_team_member(self):
        from Research.models import ResearchTeamMember
        return ResearchTeamMember.objects.filter(
            faculty=self,
            role__in=["ADVISOR", "CO_MENTOR"]
        ).exists()
    
    @property
    def research_committee_role(self):
        committee = self.research_committees.filter(is_active=True).first()

        if committee:
            return committee.get_role_display()

        return None


class FacultyAppointment(models.Model):
    APPOINTMENT_TYPE_CHOICES = (
        ("PRIMARY", "Primary"),
        ("JOINT", "Joint"),
        ("SECONDARY", "Secondary"),
        ("AFFILIATE", "Affiliate"),
    )

    faculty = models.ForeignKey(
        FacultyProfile, on_delete=models.CASCADE, related_name="appointments"
    )
    department_id = models.IntegerField()   
    appointment_type = models.CharField(max_length=20, choices=APPOINTMENT_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    percentage_effort = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True
    )
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "faculty_appointments"

    def __str__(self):
        return f"{self.faculty} - {self.appointment_type} (Dept {self.department_id})"


class FacultyEducation(models.Model):
    faculty = models.ForeignKey(
        FacultyProfile, on_delete=models.CASCADE, related_name="education_records"
    )
    degree = models.CharField(max_length=100)
    field_of_study = models.CharField(max_length=150, blank=True, null=True)
    institution_name = models.CharField(max_length=200)
    graduation_year = models.PositiveSmallIntegerField(blank=True, null=True)
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "faculty_education"

    def __str__(self):
        return f"{self.faculty} - {self.degree} ({self.institution_name})"


class FacultyCourseAssignment(models.Model):
    ROLE_CHOICES = (
        ("INSTRUCTOR", "Instructor"),
        ("COURSE_COORDINATOR", "Course Coordinator"),
        ("LAB_INSTRUCTOR", "Lab Instructor"),
        ("TEACHING_SUPERVISOR", "Teaching Supervisor"),
    )

    faculty = models.ForeignKey(
        FacultyProfile, on_delete=models.CASCADE, related_name="course_assignments"
    )
    course_section_id = models.IntegerField()   
    semester_id = models.IntegerField()       
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default="INSTRUCTOR")
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "faculty_course_assignments"

    def __str__(self):
        return f"{self.faculty} - Section {self.course_section_id} ({self.role})"


class FacultyResearch(models.Model):
    STATUS_CHOICES = (
        ("ONGOING", "Ongoing"),
        ("COMPLETED", "Completed"),
        ("ON_HOLD", "On Hold"),
        ("CANCELLED", "Cancelled"),
    )

    faculty = models.ForeignKey(
        FacultyProfile, on_delete=models.CASCADE, related_name="research_projects"
    )
    research_title = models.CharField(max_length=255)
    research_area = models.CharField(max_length=255, blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="ONGOING")
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "faculty_research"

    def __str__(self):
        return f"{self.faculty} - {self.research_title}"


class FacultyGrant(models.Model):
    faculty = models.ForeignKey(
        FacultyProfile, on_delete=models.CASCADE, related_name="grants"
    )
    grant_title = models.CharField(max_length=255)
    sponsor = models.CharField(max_length=200, blank=True, null=True)
    grant_amount = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True
    )
    award_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "faculty_grants"

    def __str__(self):
        return f"{self.faculty} - {self.grant_title}"


class FacultyPublication(models.Model):
    PUBLICATION_TYPE_CHOICES = (
        ("JOURNAL_ARTICLE", "Journal Article"),
        ("CONFERENCE_PAPER", "Conference Paper"),
        ("BOOK", "Book"),
        ("BOOK_CHAPTER", "Book Chapter"),
        ("PATENT", "Patent"),
    )

    faculty = models.ForeignKey(
        FacultyProfile, on_delete=models.CASCADE, related_name="publications"
    )
    title = models.CharField(max_length=300)
    publication_type = models.CharField(max_length=30, choices=PUBLICATION_TYPE_CHOICES)
    journal_or_conference = models.CharField(max_length=255, blank=True, null=True)
    publication_date = models.DateField(blank=True, null=True)
    doi = models.CharField(max_length=200, blank=True, null=True)
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "faculty_publications"

    def __str__(self):
        return f"{self.faculty} - {self.title}"


class FacultyOfficeHours(models.Model):
    DAY_CHOICES = (
        ("MONDAY", "Monday"),
        ("TUESDAY", "Tuesday"),
        ("WEDNESDAY", "Wednesday"),
        ("THURSDAY", "Thursday"),
        ("FRIDAY", "Friday"),
        ("SATURDAY", "Saturday"),
        ("SUNDAY", "Sunday"),
    )

    faculty = models.ForeignKey(
        FacultyProfile, on_delete=models.CASCADE, related_name="office_hours"
    )
    day_of_week = models.CharField(max_length=10, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=200, blank=True, null=True)
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "faculty_office_hours"

    def __str__(self):
        return f"{self.faculty} - {self.day_of_week} ({self.start_time} - {self.end_time})"


class FacultyCommittee(models.Model):
    ROLE_CHOICES = (
        ("MEMBER", "Member"),
        ("CHAIR", "Chair"),
        ("CO_CHAIR", "Co-Chair"),
        ("SECRETARY", "Secretary"),
    )

    faculty = models.ForeignKey(
        FacultyProfile, on_delete=models.CASCADE, related_name="committee_memberships"
    )
    committee_name = models.CharField(max_length=200)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="MEMBER")
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "faculty_committees"

    def __str__(self):
        return f"{self.faculty} - {self.committee_name} ({self.role})"


class FacultyEvaluation(models.Model):
    OVERALL_RATING_CHOICES = (
        ("OUTSTANDING", "Outstanding"),
        ("EXCEEDS_EXPECTATIONS", "Exceeds Expectations"),
        ("MEETS_EXPECTATIONS", "Meets Expectations"),
        ("NEEDS_IMPROVEMENT", "Needs Improvement"),
        ("UNSATISFACTORY", "Unsatisfactory"),
    )

    faculty = models.ForeignKey(
        FacultyProfile, on_delete=models.CASCADE, related_name="evaluations"
    )
    evaluation_period = models.CharField(max_length=50)  
    teaching_score = models.DecimalField(
        max_digits=4, decimal_places=2, blank=True, null=True
    )
    research_score = models.DecimalField(
        max_digits=4, decimal_places=2, blank=True, null=True
    )
    service_score = models.DecimalField(
        max_digits=4, decimal_places=2, blank=True, null=True
    )
    overall_rating = models.CharField(
        max_length=30, choices=OVERALL_RATING_CHOICES, blank=True, null=True
    )
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "faculty_evaluations"

    def __str__(self):
        return f"{self.faculty} - {self.evaluation_period}"



# ************************************************ Arun Code ********************************************************


class FacultyDocument(models.Model):
    DOCUMENT_TYPE_CHOICES = (
        ("DEGREE_CERTIFICATE", "Degree Certificate"),
        ("CV_RESUME", "CV / Resume"),
        ("APPOINTMENT_LETTER", "Appointment Letter"),
        ("ID_PROOF", "ID Proof"),
        ("PUBLICATION", "Publication"),
        ("OTHER", "Other"),
    )
    VERIFICATION_STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("VERIFIED", "Verified"),
        ("REJECTED", "Rejected"),
    )

    faculty = models.ForeignKey(
        "FacultyProfile", on_delete=models.CASCADE, related_name="documents"
    )
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPE_CHOICES)
    file_name = models.CharField(max_length=255)
    file = models.FileField(upload_to="faculty/documents/", blank=True, null=True)
    upload_date = models.DateTimeField(auto_now_add=True)
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default="PENDING",
    )
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "faculty_documents"

    def __str__(self):
        return f"{self.faculty} - {self.document_type}"
    

# ************************************************ Arun Code ********************************************************


#<---------------------------Blaze Code Start(22.07.26)--------------------------->

from django.db import models
from django.conf import settings
from django.utils import timezone

class LeaveType(models.Model):
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
        db_table = "faculty_leave_types"


class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    HALF_DAY_CHOICES = [
        ('full', 'Full Day'),
        ('first_half', 'First Half'),
        ('second_half', 'Second Half'),
    ]
    
    faculty = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='leave_requests'
    )
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    half_day_type = models.CharField(max_length=20, choices=HALF_DAY_CHOICES, default='full')
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Attachments
    attachment = models.FileField(upload_to='leave_attachments/%Y/%m/', null=True, blank=True)
    attachment_name = models.CharField(max_length=255, blank=True, null=True)
    
    # Approval
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='approved_leaves'
    )
    approved_date = models.DateTimeField(null=True, blank=True)
    approval_remarks = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    is_full_crud = models.BooleanField(default=True)
    
    class Meta:
        db_table = "faculty_leave_requests"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.faculty.get_full_name()} - {self.leave_type.name}"
    
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


class FacultyLeaveBalance(models.Model):
    faculty = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='leave_balance'
    )
    annual_leave_balance = models.FloatField(default=30.0)
    sick_leave_balance = models.FloatField(default=15.0)
    casual_leave_balance = models.FloatField(default=10.0)
    earned_leave_balance = models.FloatField(default=0.0)
    compensatory_leave_balance = models.FloatField(default=0.0)
    
    is_full_crud = models.BooleanField(default=True)
    
    class Meta:
        db_table = "faculty_leave_balances"
    
    def __str__(self):
        return f"{self.faculty.get_full_name()} - Leave Balance"


#Commends Model
# class LeaveComment(models.Model):
#     leave_request = models.ForeignKey(LeaveRequest, on_delete=models.CASCADE, related_name='comments')
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
#     comment = models.TextField()
#     created_at = models.DateTimeField(auto_now_add=True)
#     is_full_crud = models.BooleanField(default=True)
    
#     class Meta:
#         db_table = "faculty_leave_comments"
#         ordering = ['created_at']
    
#     def __str__(self):
#         return f"{self.user.get_full_name()} - {self.leave_request}"

#<---------------------------Blaze Code End  (22.07.26)--------------------------->


