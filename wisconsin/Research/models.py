import uuid
from django.db import models
from Faculty.models import *
from Students.models import *
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.utils import timezone
import os
from django.db.models import Q    

# ==== ELSA CODE START ========================================================

class ResearchCommittee(models.Model):    
    COMMITTEE_ROLES = [
        ('chair', 'Chairperson'),
        ('co-chair', 'Co-Chairperson'),
        ('secretary', 'Secretary'),
        ('member', 'Member'),
    ]    
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='research_committees')
    faculty = models.ForeignKey(FacultyProfile, on_delete=models.CASCADE, related_name='research_committees')
    faculty_rank = models.ForeignKey(FacultyRank,null=True,blank=True,on_delete=models.SET_NULL)
    role = models.CharField(max_length=30,choices=COMMITTEE_ROLES)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateField(auto_now_add=True)
    ended_at = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)    
    is_full_crud = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.faculty} - {self.role} ({self.department})"

    class Meta:
        ordering = ['-is_active', 'role', 'faculty__user__first_name']
        constraints = [
            models.UniqueConstraint(
                fields=['department'],
                condition=Q(role='chair', is_active=True),
                name='one_active_chairperson_per_department'
            )
        ]


class ResearchOpportunity(models.Model):
    STATUS_CHOICES = (
        ("DRAFT", "Draft"),
        ("OPEN", "Open"),
        ("ONGOING", "Ongoing"),
        ("COMPLETED", "Completed"),
        ("CLOSED", "Closed"),
    )
    PROJECT_STATUS_CHOICES = (
        ("DRAFT", "Draft"),
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
        ("ONGOING", "Ongoing"),
        ("ON_HOLD", "On Hold"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
        ("ARCHIVED", "Archived"),
    )
    updated_at = models.DateTimeField(auto_now=True)
    research_id = models.CharField(max_length=20,primary_key=True,editable=False)

    research_uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    department = models.ForeignKey(
    Department,
    on_delete=models.CASCADE,
    related_name="research_opportunities",
    null=True,
    blank=True,
)
    estimated_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Estimated budget required for this research"
)
    faculty = models.ForeignKey(
    FacultyProfile,
    on_delete=models.CASCADE,
    related_name="research_opportunities",
    null=True,
    blank=True,
)
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=150)
    short_description = models.TextField()
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    application_open_date = models.DateField(null=True, blank=True)
    application_deadline = models.DateField(null=True,blank=True)
    available_slots = models.PositiveIntegerField(default=1)
    required_skills = models.TextField(blank=True,help_text="Comma separated skills")
    reference_link = models.URLField( blank=True)
    additional_notes = models.TextField( blank=True)
    status = models.CharField( max_length=20, choices=STATUS_CHOICES, default="DRAFT")
    project_status = models.CharField(max_length=20, choices=PROJECT_STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    is_full_crud = models.BooleanField(default=True)
    def save(self, *args, **kwargs):
        if not self.research_id:
            year = timezone.now().year
            last_research = ResearchOpportunity.objects.filter(
                research_id__startswith=f"RES-{year}-"
            ).order_by("-research_id").first()
            if last_research:
                last_number = int(last_research.research_id.split("-")[-1])
                next_number = last_number + 1
            else:
                next_number = 1
            self.research_id = f"RES-{year}-{next_number:03d}"
        super().save(*args, **kwargs)    
    def __str__(self):
        return self.title
    @property
    def skill_list(self):
        return [
            skill.strip()
            for skill in self.required_skills.split(",")
            if skill.strip()
        ]
    
class ResearchOpportunityDocument(models.Model):
    opportunity = models.ForeignKey(ResearchOpportunity,on_delete=models.CASCADE,related_name="documents")
    document = models.FileField(upload_to="research_opportunity_documents/" )
    uploaded_at = models.DateTimeField( auto_now_add=True )
    is_full_crud = models.BooleanField(default=True)
    def __str__(self):
        return self.document.name


class ResearchMilestone(models.Model):

    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('delayed', 'Delayed'),
    ]
    milestone_id = models.AutoField(primary_key=True)
    research = models.ForeignKey(
        ResearchOpportunity,
        on_delete=models.CASCADE,
        related_name='milestones'
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    start_date = models.DateField()
    deadline = models.DateField()
    expected_percentage = models.PositiveIntegerField(
        default=0,
        help_text="Expected contribution percentage"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='not_started'
    )
    created_by = models.ForeignKey(
        FacultyProfile,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_milestones'
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )
    is_full_crud = models.BooleanField(default=True)
    def __str__(self):
        return self.title


class StudentMilestoneAssignment(models.Model):
    assignment_id = models.AutoField(primary_key=True)
    milestone = models.ForeignKey(
        ResearchMilestone,
        on_delete=models.CASCADE,
        related_name='student_assignments'
    )
    student = models.ForeignKey(
        'Students.StudentProfile',
        on_delete=models.CASCADE,
        related_name='assigned_milestones'
    )
    assigned_by = models.ForeignKey(
        FacultyProfile,
        on_delete=models.SET_NULL,
        null=True
    )
    assigned_date = models.DateField(
        auto_now_add=True
    )
    student_progress = models.PositiveIntegerField(
        default=0,
        help_text="Student completion percentage"
    )
    STATUS_CHOICES = [
        ('assigned','Assigned'),
        ('working','Working'),
        ('submitted','Submitted'),
        ('completed','Completed'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='assigned'
    )
    faculty_comment = models.TextField(
        blank=True,
        null=True
    )
    is_full_crud = models.BooleanField(default=True)
    def __str__(self):
        return f"{self.student} - {self.milestone}"


class StudentProgressReport(models.Model):
    REPORT_STATUS = [
        ('submitted','Submitted'),
        ('under_review','Under Review'),
        ('approved','Approved'),
        ('revision','Revision Required'),
        ('rejected','Rejected'),
    ]
    report_id = models.AutoField(primary_key=True)
    assignment = models.ForeignKey(
        StudentMilestoneAssignment,
        on_delete=models.CASCADE,
        related_name='reports'
    )
    title = models.CharField(
        max_length=255
    )
    description = models.TextField()
    progress_percentage = models.PositiveIntegerField()
    submitted_date = models.DateTimeField(
        auto_now_add=True
    )
    status = models.CharField(
        max_length=20,
        choices=REPORT_STATUS,
        default='submitted'
    )
    reviewed_by = models.ForeignKey(
        FacultyProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    faculty_feedback = models.TextField(
        blank=True,
        null=True
    )
    reviewed_date = models.DateTimeField(
        null=True,
        blank=True
    )
    is_full_crud = models.BooleanField(default=False)
    def __str__(self):
        return self.title
        
class StudentReportAttachment(models.Model):
    attachment_id = models.AutoField(primary_key=True)
    report = models.ForeignKey(
        StudentProgressReport,
        on_delete=models.CASCADE,
        related_name="attachments"
    )
    file = models.FileField(
        upload_to="research/report_attachments/"
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )
    is_full_crud = models.BooleanField(default=False)
    def __str__(self):
        return self.file.name



# ==== ELSA CODE END ========================================================

# ============================================ Jordan Code Start's Here ===========================================


from django.db import models
from django.utils import timezone
from django.core.validators import FileExtensionValidator
import uuid

# ===================== Research Student Application ==================

class StudentResearchApplication(models.Model):
    """
    Model for student research project applications.
    """
    
    APPLICATION_STATUS = (
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('shortlisted', 'Shortlisted'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    )
    
    TIME_COMMITMENT_CHOICES = (
        ('5-10', '5-10 hours/week'),
        ('10-15', '10-15 hours/week'),
        ('15-20', '15-20 hours/week'),
        ('20+', '20+ hours/week'),
    )
    
    AVAILABILITY_CHOICES = (
        ('semester', 'Full Semester'),
        ('summer', 'Summer Only'),
        ('winter', 'Winter Break'),
        ('year-round', 'Year Round'),
    )
    
    application_id = models.AutoField(primary_key=True)
    application_uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    
    reference_number = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        help_text="Auto-generated reference number"
    )
    
    status = models.CharField(
        max_length=20,
        choices=APPLICATION_STATUS,
        default='draft'
    )
    
    student = models.ForeignKey(
        'Students.StudentProfile',
        on_delete=models.CASCADE,
        related_name='research_applications'
    )
    
    research_opportunity = models.ForeignKey(
        'ResearchOpportunity',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='applications'
    )
    
    motivation = models.TextField()
    skills_contribution = models.TextField()
    prior_experience = models.TextField(blank=True, null=True)
    time_commitment = models.CharField(max_length=10, choices=TIME_COMMITMENT_CHOICES)
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES)
    additional_info = models.TextField(blank=True, null=True)
    
    resume = models.FileField(
        upload_to='applications/resumes/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])]
    )
    
    statement_of_interest = models.FileField(
        upload_to='applications/statements/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])]
    )
    
    academic_transcript = models.FileField(
        upload_to='applications/transcripts/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])]
    )
    
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    review_comments = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_full_crud = models.BooleanField(default=False)
    
    class Meta:
        db_table = "research_applications"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.reference_number} - {self.student.user.get_full_name()}"
    
    def save(self, *args, **kwargs):
        if not self.reference_number:
            year = timezone.now().year
            count = StudentResearchApplication.objects.filter(
                created_at__year=year
            ).count() + 1
            self.reference_number = f"RSP-{year}-{str(count).zfill(4)}"
        super().save(*args, **kwargs)
    
    def submit(self):
        self.status = 'submitted'
        self.submitted_at = timezone.now()
        self.save()
    
    def get_status_display(self):
        return dict(self.APPLICATION_STATUS).get(self.status, 'Unknown')
    
    def is_submitted(self):
        return self.status != 'draft'
    
    def can_edit(self):
        return self.status == 'draft'
    
    def get_time_commitment_display(self):
        return dict(self.TIME_COMMITMENT_CHOICES).get(self.time_commitment, 'Unknown')
    
    def get_availability_display(self):
        return dict(self.AVAILABILITY_CHOICES).get(self.availability, 'Unknown')


# ===================== Research Team and Research Team member ==================

class ResearchTeam(models.Model):
    research_details = models.ForeignKey(ResearchOpportunity, on_delete=models.CASCADE,related_name="research_teams",null=True, blank=True )

    team_name = models.CharField(max_length=200, unique=True)
    is_full_crud = models.BooleanField(default=False)


class ResearchTeamMember(models.Model):
    ROLE_ADVISOR = "ADVISOR"
    ROLE_CO_MENTOR = "CO_MENTOR"
    ROLE_STUDENT = "STUDENT"
    ROLE_CHOICES = (
        ('ADVISOR', 'Advisor'),
        ('CO_MENTOR', 'Co-Mentor'),
        ('STUDENT', 'Student'),
    )

    team = models.ForeignKey(ResearchTeam, on_delete=models.CASCADE, related_name='member')
    faculty = models.ForeignKey(FacultyProfile, on_delete=models.CASCADE, null=True, blank=True)
    student = models.ForeignKey(StudentProfile, null=True, blank=True, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES,)
    is_full_crud = models.BooleanField(default=False)
    def save(self, *args, **kwargs):
        if self.role:
            self.role = self.role.strip().upper()
        super().save(*args, **kwargs)

import uuid
from django.db import models

class StudentResearchPublication(models.Model):

    STATUS_CHOICES = (
        ("DRAFT", "Draft"),
        ("UNDER_REVIEW", "Under Internal Review"),
        ("COMMITTEE_REVIEW", "Committee Review"),
        ("READY", "Ready for Submission"),
        ("SUBMITTED", "Submitted"),
        ("REVISION", "Revision Required"),
        ("ACCEPTED", "Accepted"),
        ("REJECTED", "Rejected"),
        ("PUBLISHED", "Published"),
    )

    TYPE_CHOICES = (
        ("JOURNAL", "Journal"),
        ("CONFERENCE", "Conference"),
        ("BOOK_CHAPTER", "Book Chapter"),
        ("TECHNICAL_REPORT", "Technical Report"),
    )

    publication_id = models.AutoField(primary_key=True)

    publication_uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    research = models.ForeignKey(
        ResearchOpportunity,
        on_delete=models.CASCADE,
        related_name="publications"
    )

    title = models.CharField(max_length=500)

    abstract = models.TextField()

    keywords = models.TextField(
        help_text="Comma separated keywords"
    )

    publication_type = models.CharField(
        max_length=30,
        choices=TYPE_CHOICES
    )

    manuscript = models.FileField(
        upload_to="publications/drafts/",
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="DRAFT"
    )

    created_by = models.ForeignKey(
        "Faculty.FacultyProfile",
        on_delete=models.SET_NULL,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)
    is_full_crud = models.BooleanField(default=False)


    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class PublicationAuthor(models.Model):

    AUTHOR_ROLE = (
        ("FIRST", "First Author"),
        ("CORRESPONDING", "Corresponding Author"),
        ("CO_AUTHOR", "Co Author"),
    )

    publication = models.ForeignKey(
        StudentResearchPublication,
        on_delete=models.CASCADE,
        related_name="authors"
    )

    team_member = models.ForeignKey(
        ResearchTeamMember,
        on_delete=models.CASCADE
    )

    author_role = models.CharField(
        max_length=30,
        choices=AUTHOR_ROLE
    )

    author_order = models.PositiveIntegerField()
    is_full_crud = models.BooleanField(default=False)


    class Meta:
        ordering = ["author_order"]


class PublicationSubmission(models.Model):
    STATUS_CHOICES = (
    ("DRAFT", "Draft"),
    ("SUBMITTED", "Submitted"),
    ("UNDER_REVIEW", "Under Review"),
    ("REVISION_REQUIRED", "Revision Required"),
    ("RESUBMITTED", "Resubmitted"),
    ("ACCEPTED", "Accepted"),
    ("REJECTED", "Rejected"),
    ("PUBLISHED", "Published"),
    ("WITHDRAWN", "Withdrawn"),
    )

    publication = models.OneToOneField(
        StudentResearchPublication,
        on_delete=models.CASCADE,
        related_name="submission"
    )

    journal_name = models.CharField(
        max_length=300,
        blank=True
    )

    conference_name = models.CharField(
        max_length=300,
        blank=True
    )

    publisher = models.CharField(
        max_length=300,
        blank=True
    )

    submission_date = models.DateField(
        null=True,
        blank=True
    )

    manuscript_number = models.CharField(
        max_length=100,
        blank=True
    )

    acceptance_date = models.DateField(
        null=True,
        blank=True
    )

    publication_date = models.DateField(
        null=True,
        blank=True
    )

    doi = models.CharField(
        max_length=200,
        blank=True
    )

    publication_url = models.URLField(
        blank=True
    )

    status = models.CharField(
    max_length=30,
    choices=STATUS_CHOICES,
    default="DRAFT"
    )

    is_full_crud = models.BooleanField(default=False)


# =================== Jordan Code Ends's Here ==================



import secrets

class ResearchFunding(models.Model):

    funding_id = models.AutoField(primary_key=True)  # unchanged, internal use only

    funding_code = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
        blank=True,
        help_text="Non-sequential public-facing funding reference"
    )

    research = models.ForeignKey(
        ResearchOpportunity,
        on_delete=models.CASCADE,
        related_name='fundings'
    )

    funding_source = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    award_date = models.DateField()
    sponsor = models.CharField(max_length=255)
    is_full_crud = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.funding_code:
            year = timezone.now().year
            while True:
                candidate = f"FND-{year}-{secrets.token_hex(3).upper()}"
                if not ResearchFunding.objects.filter(funding_code=candidate).exists():
                    self.funding_code = candidate
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.funding_source} - {self.amount}"



class ResearchProgress(models.Model):

    progress_id = models.AutoField(primary_key=True)

    research = models.ForeignKey(
        ResearchOpportunity,
        on_delete=models.CASCADE,
        related_name='progress_updates'
    )

    milestone = models.CharField(max_length=255)

    progress_percentage = models.PositiveIntegerField()

    report_file = models.FileField(
        upload_to='research/progress_reports/',
        null=True,
        blank=True
    )

    submission_date = models.DateField()
    is_full_crud = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.research.title} - {self.progress_percentage}%"


class ResearchPresentation(models.Model):

    presentation_id = models.AutoField(primary_key=True)

    research = models.ForeignKey(
        ResearchOpportunity,
        on_delete=models.CASCADE,
        related_name='presentations'
    )

    event_name = models.CharField(max_length=255)

    presentation_date = models.DateField()

    certificate_file = models.FileField(
        upload_to='research/certificates/',
        null=True,
        blank=True
    )

    award = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    is_full_crud = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.event_name} - {self.research.title}"

class ResearchPresentationDocument(models.Model):

    document_id = models.AutoField(primary_key=True)

    presentation = models.ForeignKey(
        ResearchPresentation,
        on_delete=models.CASCADE,
        related_name='documents'
    )

    file = models.FileField(upload_to='research/presentation_documents/')

    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_full_crud = models.BooleanField(default=False)

    def __str__(self):
        return self.file.name

# ============================ Jordan code End's Here ==========================