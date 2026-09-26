## Leo's Code Start ##

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class PhDVideoEvidence(models.Model):
    EVIDENCE_TYPE_CHOICES = (
        ("PROGRAM_ASSIGNMENT", "PhD Program Assignment"),
        ("ADVISOR_ASSIGNMENT", "Research Advisor Assignment"),
        ("COMMITTEE_ASSIGNMENT", "Doctoral Committee Assignment"),
        ("PRELIMINARY_EXAMINATION", "Preliminary / Qualifying Examination"),
        ("DISSERTATION_PROPOSAL", "Dissertation Proposal Submission / Hearing"),
        ("DOCTORAL_CANDIDACY", "Doctoral Candidacy"),
        ("DISSERTATION_DEFENSE", "Dissertation Defense"),
        ("FINAL_DISSERTATION_SUBMISSION", "Final Dissertation Submission / Approval"),
        ("GRADUATION", "Graduation"),
    )

    video_evidence_id = models.AutoField(primary_key=True)

    phd_student = models.ForeignKey(
        "Students.PhDStudent",
        on_delete=models.CASCADE,
        related_name="video_evidences",
    )

    evidence_type = models.CharField(
        max_length=50,
        choices=EVIDENCE_TYPE_CHOICES,
    )

    target_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name="phd_video_evidences",
    )

    target_object_id = models.PositiveBigIntegerField()

    target = GenericForeignKey(
        "target_content_type",
        "target_object_id",
    )

    video = models.FileField(
        upload_to="phd/video_evidence/",
    )

    uploaded_by = models.ForeignKey(
        "Admin.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="phd_video_evidences",
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "phd_video_evidences"
        ordering = [
            "-uploaded_at",
            "-video_evidence_id",
        ]
        indexes = [
            models.Index(
                fields=["target_content_type", "target_object_id"],
                name="phd_video_target_idx",
            ),
            models.Index(
                fields=["phd_student", "evidence_type"],
                name="phd_video_student_type_idx",
            ),
        ]

    def __str__(self):
        return f"{self.phd_student} - {self.get_evidence_type_display()}"


class PhD(models.Model):

    STATUS_CHOICES = (
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
    )

    DEGREE_TYPE_CHOICES = (("PHD", "PhD"),)

    phd_program_id = models.AutoField(
        primary_key=True,
    )

    department = models.ForeignKey(
        "bela_admin.Department",
        on_delete=models.CASCADE,
        related_name="phd_programs",
    )

    program_name = models.CharField(
        max_length=255,
    )

    degree_type = models.CharField(
        max_length=10,
        choices=DEGREE_TYPE_CHOICES,
        default="PHD",
    )

    total_credits_required = models.PositiveIntegerField()

    residency_requirement = models.PositiveIntegerField()

    duration_years = models.PositiveIntegerField()

    program_description = models.TextField(
        blank=True,
        null=True,
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="ACTIVE",
    )

    is_full_crud = models.BooleanField(
        default=False,
    )

    class Meta:

        db_table = "phd_programs"

        ordering = [
            "program_name",
        ]

    def __str__(self):

        return self.program_name


class PhDStudent(models.Model):

    STATUS_CHOICES = (
        ("ACTIVE", "Active"),
        ("ON_HOLD", "On Hold"),
        ("COMPLETED", "Completed"),
        ("WITHDRAWN", "Withdrawn"),
    )

    phd_student_id = models.AutoField(
        primary_key=True,
    )

    student = models.ForeignKey(
        "Students.StudentProfile",
        on_delete=models.CASCADE,
        related_name="phd_students",
    )

    phd_program = models.ForeignKey(
        "Students.PhD",
        on_delete=models.CASCADE,
        related_name="phd_students",
    )

    advisor = models.ForeignKey(
        "Faculty.FacultyProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="phd_advisees",
    )

    admission_date = models.DateField()

    cohort_year = models.PositiveIntegerField()

    current_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE",
    )

    expected_graduation_date = models.DateField(
        null=True,
        blank=True,
    )

    is_full_crud = models.BooleanField(
        default=False,
    )

    class Meta:

        db_table = "phd_students"

        ordering = [
            "student",
        ]

    def __str__(self):

        return f"{self.student}"


class ResearchAdvisor(models.Model):

    advisor_id = models.AutoField(primary_key=True)

    faculty = models.OneToOneField(
        "Faculty.FacultyProfile",
        on_delete=models.CASCADE,
        related_name="research_advisor",
    )

    research_area = models.CharField(max_length=255)

    lab_name = models.CharField(max_length=255)

    available_slots = models.PositiveIntegerField()

    publications_count = models.PositiveIntegerField(default=0)
    is_full_crud = models.BooleanField(default=False)

    class Meta:

        db_table = "research_advisors"

        ordering = [
            "faculty",
        ]

    def __str__(self):

        return f"{self.faculty}"


class DoctoralCommittee(models.Model):

    APPROVAL_STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    )

    committee_id = models.AutoField(primary_key=True)

    phd_student = models.OneToOneField(
        "Students.PhDStudent",
        on_delete=models.CASCADE,
        related_name="doctoral_committee",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    
    chair_faculty = models.ForeignKey(
        "Faculty.FacultyProfile",
        on_delete=models.CASCADE,
        related_name="committee_chairs",
    )

    formation_date = models.DateField()

    approval_status = models.CharField(
        max_length=20, choices=APPROVAL_STATUS_CHOICES, default="PENDING"
    )
    is_full_crud = models.BooleanField(default=False)

    class Meta:

        db_table = "doctoral_committees"

        ordering = [
            "-formation_date",
        ]

    def __str__(self):

        return f"{self.phd_student}"

    
class CommitteeMember(models.Model):

    ROLE_CHOICES = (
        ("CHAIR", "Chair"),
        ("CO_CHAIR", "Co-Chair"),
        ("INTERNAL_MEMBER", "Internal Member"),
        ("EXTERNAL_MEMBER", "External Member"),
    )

    member_id = models.AutoField(primary_key=True)

    committee = models.ForeignKey(
        "Students.DoctoralCommittee",
        on_delete=models.CASCADE,
        related_name="committee_members",
    )

    faculty = models.ForeignKey(
        "Faculty.FacultyProfile",
        on_delete=models.CASCADE,
        related_name="phd_committee_memberships",
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    department = models.ForeignKey(
        "bela_admin.Department",
        on_delete=models.CASCADE,
        related_name="committee_members",
    )
    is_full_crud = models.BooleanField(default=False)

    class Meta:

        db_table = "committee_members"

        ordering = [
            "committee",
            "role",
        ]

    def __str__(self):

        return f"{self.faculty} - {self.get_role_display()}"


class PreliminaryExamination(models.Model):

    EXAM_TYPE_CHOICES = (
        ("QUALIFYING", "Qualifying"),
        ("PRELIMINARY", "Preliminary"),
    )

    STATUS_CHOICES = (
        ("DRAFT", "Draft"),
        ("SCHEDULED", "Scheduled"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    )

    RESULT_CHOICES = (
        ("PENDING", "Pending"),
        ("PASS", "Pass"),
        ("FAIL", "Fail"),
    )

    prelim_exam_id = models.AutoField(primary_key=True)

    phd_student = models.ForeignKey(
        "Students.PhDStudent",
        on_delete=models.CASCADE,
        related_name="preliminary_examinations",
    )

    exam_type = models.CharField(
        max_length=20,
        choices=EXAM_TYPE_CHOICES,
    )

    title = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    description = models.TextField(
        blank=True,
        null=True,
    )

    exam_date = models.DateField()

    start_time = models.TimeField(
        null=True,
        blank=True,
    )

    end_time = models.TimeField(
        null=True,
        blank=True,
    )

    venue = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="DRAFT",
    )

    result = models.CharField(
        max_length=20,
        choices=RESULT_CHOICES,
        default="PENDING",
    )

    remarks = models.TextField(
        blank=True,
        null=True,
    )

    is_published = models.BooleanField(
        default=False,
    )

    is_full_crud = models.BooleanField(
        default=False,
    )

    class Meta:

        db_table = "preliminary_examinations"

        ordering = [
            "-exam_date",
            "-start_time",
        ]

    def __str__(self):

        return (
            f"{self.phd_student} - "
            f"{self.get_exam_type_display()} "
            f"({self.exam_date})"
        )


class DissertationProposal(models.Model):

    STATUS_CHOICES = (
        ("DRAFT", "Draft"),
        ("SUBMITTED", "Submitted"),
        ("ADVISOR_REVIEW", "Advisor Review"),
        ("COMMITTEE_EVALUATION", "Committee Evaluation"),
        ("FINAL_REVIEW", "Final Review"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
        ("REVISION_REQUIRED", "Revision Required"),
    )

    ADVISOR_REVIEW_STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
        ("REVISION_REQUIRED", "Revision Required"),
    )

    RESULT_CHOICES = (
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
        ("REVISION_REQUIRED", "Revision Required"),
    )

    proposal_id = models.AutoField(
        primary_key=True,
    )

    phd_student = models.OneToOneField(
        "Students.PhDStudent",
        on_delete=models.CASCADE,
        related_name="dissertation_proposal",
    )

    approved_by = models.ForeignKey(
        "Students.DoctoralCommittee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_dissertation_proposals",
    )

    proposal_title = models.CharField(
        max_length=255,
    )

    abstract = models.TextField()

    proposal_file = models.FileField(
        upload_to="dissertation_proposals/",
        null=True,
        blank=True,
    )

    submission_date = models.DateField(
        null=True,
        blank=True,
    )

    hearing_date = models.DateField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="DRAFT",
    )

    advisor_review_status = models.CharField(
        max_length=30,
        choices=ADVISOR_REVIEW_STATUS_CHOICES,
        default="PENDING",
    )

    advisor_review_remarks = models.TextField(
        null=True,
        blank=True,
    )

    advisor_reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    result = models.CharField(
        max_length=30,
        choices=RESULT_CHOICES,
        default="PENDING",
    )

    final_remarks = models.TextField(
        null=True,
        blank=True,
    )

    finalized_by = models.ForeignKey(
        "Faculty.FacultyProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="finalized_dissertation_proposals",
    )

    finalized_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    resubmission_count = models.PositiveIntegerField(
        default=0,
    )

    is_full_crud = models.BooleanField(
        default=False,
    )

    class Meta:

        db_table = "dissertation_proposals"

        ordering = [
            "-submission_date",
            "-proposal_id",
        ]

    def __str__(self):

        return self.proposal_title


class DissertationProposalEvaluation(models.Model):

    RECOMMENDATION_CHOICES = (
        ("ACCEPT", "Accept"),
        ("MINOR_REVISION", "Minor Revision"),
        ("MAJOR_REVISION", "Major Revision"),
        ("REJECT", "Reject"),
    )

    evaluation_id = models.AutoField(
        primary_key=True,
    )

    proposal = models.ForeignKey(
        "Students.DissertationProposal",
        on_delete=models.CASCADE,
        related_name="evaluations",
    )

    committee_member = models.ForeignKey(
        "Students.CommitteeMember",
        on_delete=models.CASCADE,
        related_name="dissertation_proposal_evaluations",
    )

    submission_number = models.PositiveIntegerField(
        default=1,
    )

    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )

    recommendation = models.CharField(
        max_length=30,
        choices=RECOMMENDATION_CHOICES,
    )

    comments = models.TextField(
        blank=True,
        null=True,
    )

    is_submitted = models.BooleanField(
        default=False,
    )

    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    is_full_crud = models.BooleanField(
        default=False,
    )

    class Meta:

        db_table = "dissertation_proposal_evaluations"

        ordering = [
            "committee_member__role",
            "committee_member__faculty__user__first_name",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "proposal",
                    "committee_member",
                    "submission_number",
                ],
                name="unique_proposal_committee_submission_evaluation",
            ),
        ]

    def __str__(self):

        return f"{self.proposal} - {self.committee_member}"


class DissertationProposalResubmissionRequest(models.Model):

    STATUS_CHOICES = (
        ("PENDING", "Pending Review"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    )

    request_id = models.AutoField(
        primary_key=True,
    )

    proposal = models.ForeignKey(
        "Students.DissertationProposal",
        on_delete=models.CASCADE,
        related_name="resubmission_requests",
    )

    submission_number = models.PositiveIntegerField(
        default=1,
    )

    reason = models.TextField()

    assurance = models.TextField()

    student_declaration = models.BooleanField(
        default=False,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
    )

    reviewed_by = models.ForeignKey(
        "Faculty.FacultyProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="dissertation_resubmission_reviews",
    )

    review_remarks = models.TextField(
        null=True,
        blank=True,
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    requested_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    is_full_crud = models.BooleanField(
        default=True,
    )

    class Meta:

        db_table = "dissertation_proposal_resubmission_requests"

        ordering = [
            "-requested_at",
            "-request_id",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "proposal",
                    "submission_number",
                ],
                name="unique_proposal_resubmission_number",
            ),
        ]

    def __str__(self):

        return (
            f"Resubmission Request #{self.submission_number} - "
            f"{self.proposal.proposal_title}"
        )


# PhD student -> Researcher Promotion
class DoctoralCandidacy(models.Model):

    CANDIDACY_STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    )

    candidacy_id = models.AutoField(primary_key=True)

    phd_student = models.OneToOneField(
        "Students.PhDStudent",
        on_delete=models.CASCADE,
        related_name="doctoral_candidacy",
    )

    candidacy_date = models.DateField()

    candidacy_status = models.CharField(
        max_length=20, choices=CANDIDACY_STATUS_CHOICES, default="PENDING"
    )

    approval_date = models.DateField(null=True, blank=True)
    is_full_crud = models.BooleanField(default=False)

    class Meta:

        db_table = "doctoral_candidacies"

        ordering = [
            "-candidacy_date",
        ]

    def __str__(self):

        return f"{self.phd_student}"


# Tracks important milestones in a Ph.D. student's academic journey.
# Example:
# Coursework → Qualifying Exam → Proposal Approval →
# Doctoral Candidacy → Research → Defense → Graduation
class PhDMilestone(models.Model):

    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("IN_PROGRESS", "In Progress"),
        ("COMPLETED", "Completed"),
    )

    milestone_id = models.AutoField(primary_key=True)

    phd_student = models.ForeignKey(
        "Students.PhDStudent",
        on_delete=models.CASCADE,
        related_name="phd_milestones",
    )

    milestone_name = models.CharField(max_length=255)

    completion_date = models.DateField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    is_full_crud = models.BooleanField(default=False)

    class Meta:

        db_table = "phd_milestones"

        ordering = [
            "-completion_date",
        ]

    def __str__(self):

        return self.milestone_name


# a long piece of writing on something that you have studied, especially as part of a university degree.
# FINAL THESIS SUBMISSION - HUGE AND FINAL STEPS IN PhD
# Entire Research Work
class Dissertation(models.Model):

    STATUS_CHOICES = (
        ("DRAFT", "Draft"),
        ("SUBMITTED", "Submitted"),
        ("ADVISOR_REVIEW", "Advisor Review"),
        ("COMMITTEE_EVALUATION", "Committee Evaluation"),
        ("FINAL_REVIEW", "Final Review"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
        ("REVISION_REQUIRED", "Revision Required"),
    )

    ADVISOR_REVIEW_STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
        ("REVISION_REQUIRED", "Revision Required"),
    )

    dissertation_id = models.AutoField(
        primary_key=True,
    )

    phd_student = models.OneToOneField(
        "Students.PhDStudent",
        on_delete=models.CASCADE,
        related_name="dissertation",
    )

    dissertation_title = models.CharField(
        max_length=255,
    )

    abstract = models.TextField()

    submission_date = models.DateField(
        null=True,
        blank=True,
    )

    current_version = models.CharField(
        max_length=50,
        default="Version 1.0",
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="DRAFT",
    )

    dissertation_file = models.FileField(
        upload_to="dissertations/",
        null=True,
        blank=True,
    )

    advisor_review_status = models.CharField(
        max_length=30,
        choices=ADVISOR_REVIEW_STATUS_CHOICES,
        default="PENDING",
    )

    advisor_review_remarks = models.TextField(
        blank=True,
        null=True,
    )

    advisor_reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    final_remarks = models.TextField(
        blank=True,
        null=True,
    )

    finalized_by = models.ForeignKey(
        "Faculty.FacultyProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="finalized_dissertations",
    )

    finalized_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    is_full_crud = models.BooleanField(
        default=False,
    )

    class Meta:

        db_table = "dissertations"

        ordering = [
            "-submission_date",
            "-dissertation_id",
        ]

    def __str__(self):

        return self.dissertation_title


# Research publications demonstrate the academic contribution of a doctoral student. This model records journal class ResearchPublication(models.Model):
class ResearchPublication(models.Model):

    PUBLICATION_TYPE_CHOICES = (
        ("JOURNAL_ARTICLE", "Journal Article"),
        ("CONFERENCE_PAPER", "Conference Paper"),
        ("BOOK_CHAPTER", "Book Chapter"),
        ("REVIEW_ARTICLE", "Review Article"),
        ("PATENT", "Patent"),
        ("OTHER", "Other"),
    )

    PUBLICATION_STATUS_CHOICES = (
        ("DRAFT", "Draft"),
        ("SUBMITTED", "Submitted"),
        ("ACCEPTED", "Accepted"),
        ("PUBLISHED", "Published"),
    )

    INDEXED_STATUS_CHOICES = (
        ("INDEXED", "Indexed"),
        ("NOT_INDEXED", "Not Indexed"),
        ("UNDER_REVIEW", "Under Review"),
    )

    INDEXING_DATABASE_CHOICES = (
        ("SCOPUS", "Scopus"),
        ("WEB_OF_SCIENCE", "Web of Science"),
        ("UGC", "UGC"),
        ("PUBMED", "PubMed"),
        ("OTHER", "Other"),
        ("NOT_APPLICABLE", "Not Applicable"),
    )

    publication_id = models.AutoField(
        primary_key=True,
    )

    phd_student = models.ForeignKey(
        "Students.PhDStudent",
        on_delete=models.CASCADE,
        related_name="research_publications",
    )

    milestone = models.ForeignKey(
        "Faculty.ResearchMilestone",
        on_delete=models.SET_NULL,
        related_name="research_publications",
        blank=True,
        null=True,
    )

    title = models.CharField(
        max_length=255,
    )

    publication_type = models.CharField(
        max_length=30,
        choices=PUBLICATION_TYPE_CHOICES,
        default="JOURNAL_ARTICLE",
    )

    authors = models.TextField(
        blank=True,
        null=True,
    )

    journal = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    abstract = models.TextField(
        blank=True,
        null=True,
    )

    keywords = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Enter keywords separated by commas.",
    )

    publication_date = models.DateField()

    publication_status = models.CharField(
        max_length=20,
        choices=PUBLICATION_STATUS_CHOICES,
        default="PUBLISHED",
    )

    doi = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    indexed_status = models.CharField(
        max_length=20,
        choices=INDEXED_STATUS_CHOICES,
        default="UNDER_REVIEW",
    )

    indexing_database = models.CharField(
        max_length=30,
        choices=INDEXING_DATABASE_CHOICES,
        default="NOT_APPLICABLE",
    )

    manuscript_file = models.FileField(
        upload_to="phd/research/publications/manuscripts/",
        blank=True,
        null=True,
    )

    acceptance_letter = models.FileField(
        upload_to="phd/research/publications/acceptance/",
        blank=True,
        null=True,
    )

    supporting_document = models.FileField(
        upload_to="phd/research/publications/supporting/",
        blank=True,
        null=True,
    )

    student_remarks = models.TextField(
        blank=True,
        null=True,
    )

    is_full_crud = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:

        db_table = "research_publications"

        ordering = [
            "-publication_date",
            "-publication_id",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "phd_student",
                    "milestone",
                ],
                name="unique_student_research_publication_milestone",
            ),
        ]

    def __str__(self):

        return self.title


# perfomance of a PhD Student in an Annual Year
class AnnualProgressReview(models.Model):

    STATUS_CHOICES = (
        ("SATISFACTORY", "Satisfactory"),
        ("NEEDS_IMPROVEMENT", "Needs Improvement"),
        ("UNSATISFACTORY", "Unsatisfactory"),
    )

    review_id = models.AutoField(primary_key=True)

    phd_student = models.ForeignKey(
        "Students.PhDStudent",
        on_delete=models.CASCADE,
        related_name="annual_progress_reviews",
    )

    review_year = models.PositiveIntegerField()

    committee_comments = models.TextField()

    progress_score = models.DecimalField(max_digits=5, decimal_places=2)

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="SATISFACTORY"
    )
    is_full_crud = models.BooleanField(default=False)

    class Meta:

        db_table = "annual_progress_reviews"

        ordering = [
            "-review_year",
        ]

    def __str__(self):

        return f"{self.phd_student} - {self.review_year}"


class DissertationDefense(models.Model):

    RESULT_CHOICES = (
        ("PASS", "Pass"),
        ("FAIL", "Fail"),
        ("PENDING", "Pending"),
    )

    COMMITTEE_DECISION_CHOICES = (
        ("APPROVED", "Approved"),
        ("MINOR_REVISIONS", "Minor Revisions"),
        ("MAJOR_REVISIONS", "Major Revisions"),
        ("REJECTED", "Rejected"),
    )

    defense_id = models.AutoField(
        primary_key=True,
    )

    phd_student = models.OneToOneField(
        "Students.PhDStudent",
        on_delete=models.CASCADE,
        related_name="dissertation_defense",
    )

    defense_date = models.DateField()

    defense_time = models.TimeField()

    location = models.CharField(
        max_length=255,
    )

    result = models.CharField(
        max_length=20,
        choices=RESULT_CHOICES,
        default="PENDING",
    )

    committee_decision = models.CharField(
        max_length=20,
        choices=COMMITTEE_DECISION_CHOICES,
        default="MINOR_REVISIONS",
    )

    final_comments = models.TextField(
        blank=True,
        null=True,
    )

    is_full_crud = models.BooleanField(
        default=False,
    )

    class Meta:

        db_table = "dissertation_defenses"

        ordering = [
            "-defense_date",
            "-defense_time",
        ]

    def __str__(self):

        return f"{self.phd_student} - {self.defense_date} {self.defense_time}"


class DissertationDefenseEvaluation(models.Model):

    RECOMMENDATION_CHOICES = (
        ("PASS", "Pass"),
        ("FAIL", "Fail"),
        ("MINOR_REVISIONS", "Minor Revisions"),
        ("MAJOR_REVISIONS", "Major Revisions"),
    )

    evaluation_id = models.AutoField(
        primary_key=True,
    )

    defense = models.ForeignKey(
        "Students.DissertationDefense",
        on_delete=models.CASCADE,
        related_name="evaluations",
    )

    committee_member = models.ForeignKey(
        "Students.CommitteeMember",
        on_delete=models.CASCADE,
        related_name="dissertation_defense_evaluations",
    )

    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ],
    )

    recommendation = models.CharField(
        max_length=30,
        choices=RECOMMENDATION_CHOICES,
    )

    is_submitted = models.BooleanField(
        default=False,
    )

    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    is_full_crud = models.BooleanField(
        default=False,
    )

    class Meta:

        db_table = "dissertation_defense_evaluations"

        ordering = [
            "-submitted_at",
            "-evaluation_id",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "defense",
                    "committee_member",
                ],
                name="unique_dissertation_defense_committee_evaluation",
            ),
        ]

    def __str__(self):

        return f"{self.defense.phd_student} - " f"{self.committee_member.faculty}"


class DefenseLocation(models.Model):

    name = models.CharField(
        max_length=255,
        unique=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    is_full_crud = models.BooleanField(
        default=True,
    )

    class Meta:

        db_table = "defense_locations"

        ordering = [
            "name",
        ]

    def __str__(self):

        return self.name


class FinalDissertationSubmission(models.Model):

    STATUS_CHOICES = (
        ("DRAFT", "Draft"),
        ("SUBMITTED", "Submitted"),
        ("ADVISOR_REVIEW", "Advisor Review"),
        ("COMMITTEE_EVALUATION", "Committee Evaluation"),
        ("CHAIR_REVIEW", "Chair Review"),
        ("REVISION_REQUIRED", "Revision Required"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    )

    submission_id = models.AutoField(
        primary_key=True,
    )

    phd_student = models.ForeignKey(
        "Students.PhDStudent",
        on_delete=models.CASCADE,
        related_name="final_dissertation_submissions",
    )

    submission_number = models.PositiveIntegerField(
        default=1,
    )

    resubmission_count = models.PositiveIntegerField(
        default=0,
    )

    version = models.CharField(
        max_length=50,
        default="Version 1.0",
    )

    dissertation_title = models.CharField(
        max_length=255,
    )

    abstract = models.TextField()

    dissertation_file = models.FileField(
        upload_to="phd/final_dissertations/",
    )

    submission_date = models.DateField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="DRAFT",
    )

    student_remarks = models.TextField(
        blank=True,
        null=True,
    )

    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    finalized_by = models.ForeignKey(
        "Faculty.FacultyProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="finalized_dissertation_submissions",
    )

    finalized_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    is_full_crud = models.BooleanField(
        default=False,
    )

    class Meta:
        db_table = "final_dissertation_submissions"

        ordering = [
            "-submission_number",
            "-created_at",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "phd_student",
                    "submission_number",
                ],
                name="unique_final_dissertation_submission_number",
            ),
        ]

    def __str__(self):
        return (
            f"{self.phd_student} - "
            f"Final Dissertation Submission "
            f"#{self.submission_number}"
        )


class Graduation(models.Model):

    STATUS_CHOICES = (
        ("PENDING_CHAIR_APPROVAL", "Pending Chair Approval"),
        ("APPROVED", "Approved"),
        ("COMPLETED", "Completed"),
        ("REJECTED", "Rejected"),
    )

    graduation_id = models.AutoField(
        primary_key=True,
    )

    phd_student = models.OneToOneField(
        "Students.PhDStudent",
        on_delete=models.CASCADE,
        related_name="graduation",
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="PENDING_CHAIR_APPROVAL",
    )

    graduation_date = models.DateField(
        null=True,
        blank=True,
    )

    graduation_time = models.TimeField(
        null=True,
        blank=True,
    )

    graduation_location = models.CharField(
        max_length=255,
        default="University Common Hall",
    )

    degree_awarded = models.CharField(
        max_length=100,
        default="Doctor of Philosophy (PhD)",
    )

    final_gpa = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
    )

    dissertation_accepted = models.BooleanField(
        default=False,
    )

    defense_passed = models.BooleanField(
        default=False,
    )

    created_by = models.ForeignKey(
        "Staff.StaffProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_graduations",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    chair_approved_by = models.ForeignKey(
        "Faculty.FacultyProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_graduations",
    )

    chair_approved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    chair_congratulations_note = models.TextField(
        null=True,
        blank=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    is_full_crud = models.BooleanField(
        default=False,
    )

    class Meta:

        db_table = "graduations"

        ordering = [
            "-graduation_date",
            "-graduation_id",
        ]

    def __str__(self):

        return f"{self.phd_student}"


## Leo's Code End ##
