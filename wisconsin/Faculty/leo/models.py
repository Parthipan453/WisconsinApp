## Leo's code start ##
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from Admin.bela_admin.models import Course
from django.core.validators import MaxValueValidator
from django.db import models
from django.utils import timezone


class AttendanceSession(models.Model):
    # to indicate the status of attendance (completed or not)
    STATUS_CHOICES = (
        ("OPEN", "Open"),
        ("CLOSED", "Closed"),
    )
    # faculty Details
    faculty = models.ForeignKey(
        "Faculty.FacultyProfile",
        on_delete=models.CASCADE,
        related_name="attendance_sessions",
    )
    # Course Details
    course = models.ForeignKey(
        "bela_admin.Course",
        on_delete=models.CASCADE,
        related_name="attendance_sessions",
    )
    # Details of the course, staff , type of the course
    section = models.ForeignKey(
        "Students.CourseSection",
        on_delete=models.CASCADE,
        related_name="attendance_sessions",
        null=True,
        blank=True,
    )
    schedule = models.ForeignKey(
        "Students.Schedule",
        on_delete=models.CASCADE,
        related_name="attendance_sessions",
        null=True,
        blank=True,
    )
    # Attendance Date
    attendance_date = models.DateField()
    # Attendance marking completed or not
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="OPEN",
    )
    # Time when this attendance session created
    created_at = models.DateTimeField(auto_now_add=True)
    # Time when this attendance session got updated
    updated_at = models.DateTimeField(auto_now=True)
    is_full_crud = models.BooleanField(default=False)

    # meta class used to tell django how to behave
    class Meta:
        # custom database table name
        db_table = "attendance_sessions"
        # section+attendancedate combo must be unique
        unique_together = ("section", "schedule", "attendance_date")
        # telling django how to order the attendance section
        ordering = ["-attendance_date"]

    # django admin page name in admin panel --- Faculty | Section | Dateculty ---
    def __str__(self):
        return (
            f"{self.faculty} | "
            f"{self.course.course_code} | "
            f"{self.section} | "
            f"{self.attendance_date}"
        )


class Attendance(models.Model):
    # Types of attendance
    # The first value is what get stored in database second one is what users will see
    STATUS_CHOICES = (
        ("PRESENT", "Present"),
        ("ABSENT", "Absent"),
        ("LATE", "Late"),
        ("LEAVE", "Leave"),
        ("HALF_DAY", "Half day"),
        ("PERMISSION", "Permission"),
    )
    # indicating which session
    attendance_session = models.ForeignKey(
        AttendanceSession, on_delete=models.CASCADE, related_name="attendance_records"
    )
    # student details to mark the attendance for particular people
    student = models.ForeignKey(
        "Students.StudentProfile",
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )
    # marking the status
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PRESENT")

    # if any remarks are there to be updated (optional)
    remarks = models.TextField(
        blank=True,
        null=True,
    )
    # Time when this attendance section created
    created_at = models.DateTimeField(auto_now_add=True)
    # Time when this attendance section got updated
    updated_at = models.DateTimeField(auto_now=True)
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        # custom db table
        db_table = "attendance"
        # combination of these two must be unique
        unique_together = ("attendance_session", "student")
        # ordering
        ordering = ["student__student_number"]

    # name of the model in admin_page --- Student Number | Date | Status ---
    def __str__(self):

        return (
            f"{self.student.student_number} | "
            f"{self.attendance_session.attendance_date} | "
            f"{self.status}"
        )


class Coursework(models.Model):

    coursework_id = models.AutoField(
        primary_key=True,
    )

    program = models.ForeignKey(
        "Students.PhD",
        on_delete=models.CASCADE,
        related_name="courseworks",
    )

    coursework_name = models.CharField(
        max_length=100,
    )

    description = models.TextField(
        blank=True,
        null=True,
    )

    credits = models.PositiveIntegerField()

    created_by = models.ForeignKey(
        "Faculty.FacultyProfile",
        on_delete=models.PROTECT,
        related_name="created_courseworks",
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
        default=False,
    )

    class Meta:
        db_table = "courseworks"

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "program",
                    "coursework_name",
                ],
                name="unique_program_coursework_name",
            ),
        ]

        ordering = [
            "coursework_name",
        ]

    def __str__(self):
        return (
            f"{self.coursework_name} | " f"{self.program} | " f"{self.credits} Credits"
        )


class FacultyCoursework(models.Model):

    STATUS_CHOICES = (
        ("NOT_STARTED", "Not Started"),
        ("IN_PROGRESS", "In Progress"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
    )

    faculty_coursework_id = models.AutoField(
        primary_key=True,
    )

    phd_student = models.ForeignKey(
        "Students.PhDStudent",
        on_delete=models.CASCADE,
        related_name="faculty_courseworks",
    )

    program = models.ForeignKey(
        "Students.PhD",
        on_delete=models.CASCADE,
        related_name="faculty_courseworks",
    )

    coursework = models.ForeignKey(
        "Faculty.Coursework",
        on_delete=models.PROTECT,
        related_name="faculty_courseworks",
    )

    academic_year = models.CharField(
        max_length=20,
    )

    start_date = models.DateField()

    expected_completion_date = models.DateField()

    completion_date = models.DateField(
        blank=True,
        null=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="NOT_STARTED",
    )

    progress_percentage = models.PositiveSmallIntegerField(
        default=0,
        validators=[
            MaxValueValidator(100),
        ],
    )

    remarks = models.TextField(
        blank=True,
        null=True,
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
        db_table = "faculty_courseworks"

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "phd_student",
                    "coursework",
                ],
                name="unique_student_coursework",
            ),
        ]

        ordering = [
            "-academic_year",
            "coursework__coursework_name",
        ]

    def __str__(self):
        return f"{self.phd_student} | " f"{self.program} | " f"{self.coursework}"


class CourseworkSubmission(models.Model):

    STATUS_CHOICES = (
        ("SUBMITTED", "Submitted"),
        ("UNDER_REVIEW", "Under Review"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    )

    submission_id = models.AutoField(
        primary_key=True,
    )

    coursework = models.OneToOneField(
        "Faculty.FacultyCoursework",
        on_delete=models.CASCADE,
        related_name="submission",
    )

    submission_file = models.FileField(
        upload_to="phd/coursework_submissions/",
    )

    remarks = models.TextField(
        blank=True,
        null=True,
    )

    submitted_at = models.DateTimeField(
        auto_now_add=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="SUBMITTED",
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
        db_table = "coursework_submissions"

        ordering = [
            "-submitted_at",
        ]

    def __str__(self):
        return (
            f"{self.coursework.phd_student.student_number} | "
            f"{self.coursework.coursework.coursework_name}"
        )


class CourseworkEvaluation(models.Model):

    GRADE_CHOICES = (
        ("A+", "A+"),
        ("A", "A"),
        ("B+", "B+"),
        ("B", "B"),
        ("C+", "C+"),
        ("C", "C"),
        ("F", "Fail"),
    )

    evaluation_id = models.AutoField(
        primary_key=True,
    )

    submission = models.OneToOneField(
        "Faculty.CourseworkSubmission",
        on_delete=models.CASCADE,
        related_name="evaluation",
    )

    evaluated_by = models.ForeignKey(
        "Faculty.FacultyProfile",
        on_delete=models.PROTECT,
        related_name="coursework_evaluations",
    )

    marks = models.PositiveSmallIntegerField(
        validators=[
            MaxValueValidator(100),
        ],
    )

    grade = models.CharField(
        max_length=5,
        choices=GRADE_CHOICES,
        blank=True,
    )

    faculty_feedback = models.TextField(
        blank=True,
        null=True,
    )

    evaluated_at = models.DateTimeField(
        default=timezone.now,
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
        db_table = "coursework_evaluations"

        ordering = [
            "-evaluated_at",
        ]

    def calculate_grade(self):

        if self.marks >= 90:
            return "A+"

        if self.marks >= 80:
            return "A"

        if self.marks >= 70:
            return "B+"

        if self.marks >= 60:
            return "B"

        if self.marks >= 50:
            return "C+"

        if self.marks >= 40:
            return "C"

        return "F"

    def save(self, *args, **kwargs):

        self.grade = self.calculate_grade()

        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.submission.coursework.coursework.coursework_name} | "
            f"{self.marks} | "
            f"{self.grade}"
        )


class PreliminaryExamEvaluation(models.Model):

    RECOMMENDATION_CHOICES = (
        ("PASS", "Pass"),
        ("FAIL", "Fail"),
        ("REVISION", "Revision"),
    )

    evaluation_id = models.AutoField(primary_key=True)

    examination = models.ForeignKey(
        "Students.PreliminaryExamination",
        on_delete=models.CASCADE,
        related_name="evaluations",
    )

    faculty = models.ForeignKey(
        "Faculty.FacultyProfile",
        on_delete=models.CASCADE,
        related_name="preliminary_exam_evaluations",
    )

    knowledge_score = models.PositiveSmallIntegerField()

    research_aptitude_score = models.PositiveSmallIntegerField()

    presentation_score = models.PositiveSmallIntegerField()

    technical_score = models.PositiveSmallIntegerField()

    comments = models.TextField(
        blank=True,
        null=True,
    )

    recommendation = models.CharField(
        max_length=20,
        choices=RECOMMENDATION_CHOICES,
    )

    submitted_at = models.DateTimeField(
        auto_now_add=True,
    )

    is_submitted = models.BooleanField(
        default=False,
    )

    is_full_crud = models.BooleanField(
        default=False,
    )

    class Meta:

        db_table = "preliminary_exam_evaluations"

        ordering = [
            "-submitted_at",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "examination",
                    "faculty",
                ],
                name="unique_preliminary_exam_faculty_evaluation",
            ),
        ]

    def __str__(self):

        return f"{self.examination} - " f"{self.faculty}"


class DissertationEvaluation(models.Model):

    RECOMMENDATION_CHOICES = (
        ("ACCEPT", "Accept"),
        ("MINOR_REVISION", "Minor Revision"),
        ("MAJOR_REVISION", "Major Revision"),
        ("REJECT", "Reject"),
    )

    evaluation_id = models.AutoField(primary_key=True)

    dissertation = models.ForeignKey(
        "Students.Dissertation",
        on_delete=models.CASCADE,
        related_name="committee_evaluations",
    )

    committee_member = models.ForeignKey(
        "Students.CommitteeMember",
        on_delete=models.CASCADE,
        related_name="dissertation_evaluations",
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
        blank=True,
    )

    remarks = models.TextField()

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

        db_table = "dissertation_evaluations"

        ordering = [
            "-submitted_at",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "dissertation",
                    "committee_member",
                ],
                name="unique_dissertation_committee_evaluation",
            )
        ]

    def __str__(self):

        return f"{self.dissertation} - " f"{self.committee_member.faculty}"


class DissertationApproval(models.Model):

    DECISION_CHOICES = (
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("MINOR_REVISION", "Minor Revision"),
        ("MAJOR_REVISION", "Major Revision"),
        ("REJECTED", "Rejected"),
    )

    approval_id = models.AutoField(primary_key=True)

    dissertation = models.OneToOneField(
        "Students.Dissertation",
        on_delete=models.CASCADE,
        related_name="final_approval",
    )

    chair_faculty = models.ForeignKey(
        "Faculty.FacultyProfile",
        on_delete=models.CASCADE,
        related_name="dissertation_approvals",
    )

    decision = models.CharField(
        max_length=30,
        choices=DECISION_CHOICES,
        default="PENDING",
    )

    final_remarks = models.TextField(
        blank=True,
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )
    allow_resubmission = models.BooleanField(
        default=False,
    )

    reopened_count = models.PositiveIntegerField(
        default=0,
    )

    reopened_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    resubmission_deadline = models.DateField(
        null=True,
        blank=True,
    )
    is_full_crud = models.BooleanField(
        default=False,
    )

    class Meta:

        db_table = "dissertation_approvals"

        ordering = [
            "-approved_at",
        ]

    def __str__(self):

        return f"{self.dissertation} - " f"{self.get_decision_display()}"


class DissertationAdvisorFeedback(models.Model):

    STATUS_CHOICES = (
        ("DRAFT", "Draft"),
        ("SUBMITTED", "Submitted"),
    )

    advisor_feedback_id = models.AutoField(
        primary_key=True,
    )

    dissertation = models.OneToOneField(
        "Students.Dissertation",
        on_delete=models.CASCADE,
        related_name="advisor_feedback",
    )

    advisor = models.ForeignKey(
        "Faculty.FacultyProfile",
        on_delete=models.CASCADE,
        related_name="advisor_feedbacks",
    )

    advisor_feedback = models.TextField()

    remarks = models.TextField(
        blank=True,
        null=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="DRAFT",
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

        db_table = "dissertation_advisor_feedbacks"

        ordering = [
            "-submitted_at",
            "-created_at",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "dissertation",
                    "advisor",
                ],
                name="unique_dissertation_advisor_feedback",
            ),
        ]

    def __str__(self):

        return f"{self.dissertation} - " f"{self.advisor}"


class DissertationChairReplyFeedback(models.Model):

    STATUS_CHOICES = (
        ("DRAFT", "Draft"),
        ("SUBMITTED", "Submitted"),
    )

    DECISION_CHOICES = (
        ("APPROVED", "Approved"),
        ("MINOR_REVISION", "Minor Revision"),
        ("MAJOR_REVISION", "Major Revision"),
        ("REJECTED", "Rejected"),
    )

    chair_reply_feedback_id = models.AutoField(
        primary_key=True,
    )

    advisor_feedback = models.OneToOneField(
        "Faculty.DissertationAdvisorFeedback",
        on_delete=models.CASCADE,
        related_name="chair_reply_feedback",
    )

    dissertation = models.OneToOneField(
        "Students.Dissertation",
        on_delete=models.CASCADE,
        related_name="chair_reply_feedback",
    )

    chair_faculty = models.ForeignKey(
        "Faculty.FacultyProfile",
        on_delete=models.CASCADE,
        related_name="chair_reply_feedbacks",
    )

    chair_reply_feedback = models.TextField()

    remarks = models.TextField(
        blank=True,
        null=True,
    )

    decision = models.CharField(
        max_length=30,
        choices=DECISION_CHOICES,
        default="MINOR_REVISION",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="DRAFT",
    )

    is_submitted = models.BooleanField(
        default=False,
    )

    replied_at = models.DateTimeField(
        blank=True,
        null=True,
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

        db_table = "dissertation_chair_reply_feedbacks"

        ordering = [
            "-replied_at",
            "-created_at",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "dissertation",
                    "chair_faculty",
                ],
                name="unique_dissertation_chair_reply_feedback",
            ),
        ]

    def __str__(self):

        return f"{self.dissertation} - " f"{self.chair_faculty}"


class DissertationAdvisorAdvice(models.Model):

    advice_id = models.AutoField(
        primary_key=True,
    )

    dissertation = models.OneToOneField(
        "Students.Dissertation",
        on_delete=models.CASCADE,
        related_name="advisor_advice",
    )

    advisor = models.ForeignKey(
        "Faculty.FacultyProfile",
        on_delete=models.CASCADE,
        related_name="dissertation_advices",
    )

    advice = models.TextField()

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
        db_table = "dissertation_advisor_advices"

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "dissertation",
                    "advisor",
                ],
                name="unique_dissertation_advisor_advice",
            ),
        ]

        ordering = [
            "-submitted_at",
            "-created_at",
        ]

    def __str__(self):
        return f"{self.dissertation} - {self.advisor}"


class ResearchMilestone(models.Model):

    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("IN_PROGRESS", "In Progress"),
        ("SUBMITTED", "Submitted"),
        ("UNDER_REVIEW", "Under Review"),
        ("REVISION_REQUIRED", "Revision Required"),
        ("COMPLETED", "Completed"),
    )

    milestone_id = models.AutoField(primary_key=True)

    phd_student = models.ForeignKey(
        "Students.PhDStudent",
        on_delete=models.CASCADE,
        related_name="research_milestones",
    )

    chair_faculty = models.ForeignKey(
        "Faculty.FacultyProfile",
        on_delete=models.PROTECT,
        related_name="created_research_milestones",
    )

    milestone_title = models.CharField(max_length=255)

    description = models.TextField(blank=True, null=True)

    sequence_number = models.PositiveIntegerField(default=1)

    expected_completion_date = models.DateField(null=True, blank=True)

    current_progress_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="PENDING")

    completion_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "research_milestones"

        constraints = [
            models.UniqueConstraint(
                fields=["phd_student", "sequence_number"],
                name="unique_student_research_milestone_sequence",
            )
        ]

        ordering = ["phd_student", "sequence_number"]

    def __str__(self):
        return (
            f"{self.phd_student} | "
            f"{self.milestone_title} | "
            f"{self.current_progress_percentage}%"
        )


class ResearchMilestoneSubmission(models.Model):

    STATUS_CHOICES = (
        ("SUBMITTED", "Submitted"),
        ("UNDER_REVIEW", "Under Review"),
        ("REVISION_REQUIRED", "Revision Required"),
        ("EVALUATED", "Evaluated"),
    )

    submission_id = models.AutoField(primary_key=True)

    milestone = models.ForeignKey(
        "Faculty.ResearchMilestone",
        on_delete=models.CASCADE,
        related_name="submissions",
    )

    submission_number = models.PositiveIntegerField(default=1)

    main_document = models.FileField(upload_to="phd/research/milestones/")

    additional_file_1 = models.FileField(
        upload_to="phd/research/milestones/additional/", null=True, blank=True
    )

    additional_file_2 = models.FileField(
        upload_to="phd/research/milestones/additional/", null=True, blank=True
    )

    additional_file_3 = models.FileField(
        upload_to="phd/research/milestones/additional/", null=True, blank=True
    )

    student_remarks = models.TextField(blank=True, null=True)

    status = models.CharField(
        max_length=30, choices=STATUS_CHOICES, default="SUBMITTED"
    )

    submitted_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "research_milestone_submissions"

        constraints = [
            models.UniqueConstraint(
                fields=["milestone", "submission_number"],
                name="unique_research_milestone_submission_number",
            )
        ]

        ordering = ["-submitted_at", "-submission_number"]

    def __str__(self):
        return (
            f"{self.milestone.milestone_title} | "
            f"Submission {self.submission_number}"
        )


class ResearchMilestoneEvaluation(models.Model):

    EVALUATOR_ROLE_CHOICES = (
        ("CHAIR", "Chair Faculty"),
        ("COMMITTEE_MEMBER", "Committee Member"),
    )

    DECISION_CHOICES = (
        ("REVISION_REQUIRED", "Revision Required"),
        ("COMPLETED", "Completed"),
    )

    evaluation_id = models.AutoField(primary_key=True)

    submission = models.ForeignKey(
        "Faculty.ResearchMilestoneSubmission",
        on_delete=models.CASCADE,
        related_name="evaluations",
    )

    evaluator = models.ForeignKey(
        "Faculty.FacultyProfile",
        on_delete=models.PROTECT,
        related_name="research_milestone_evaluations",
    )

    evaluator_role = models.CharField(max_length=30, choices=EVALUATOR_ROLE_CHOICES)

    progress_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    feedback = models.TextField(blank=True, null=True)

    decision = models.CharField(
        max_length=30,
        choices=DECISION_CHOICES,
        default="REVISION_REQUIRED",
    )

    evaluated_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "research_milestone_evaluations"

        constraints = [
            models.UniqueConstraint(
                fields=["submission", "evaluator"],
                name="unique_research_submission_evaluator",
            )
        ]

        ordering = ["-evaluated_at"]

    def __str__(self):
        return (
            f"{self.submission} | "
            f"{self.evaluator} | "
            f"{self.progress_percentage}%"
        )


class AdvisorResearchAdvice(models.Model):

    STATUS_CHOICES = (
        ("DRAFT", "Draft"),
        ("SUBMITTED", "Submitted"),
    )

    advice_id = models.AutoField(primary_key=True)

    submission = models.ForeignKey(
        "Faculty.ResearchMilestoneSubmission",
        on_delete=models.CASCADE,
        related_name="advisor_advices",
    )

    advisor = models.ForeignKey(
        "Faculty.FacultyProfile",
        on_delete=models.PROTECT,
        related_name="research_milestone_advices",
    )

    advice = models.TextField()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="DRAFT")

    is_submitted = models.BooleanField(default=False)

    submitted_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "advisor_research_advices"
        constraints = [
            models.UniqueConstraint(
                fields=["submission", "advisor"],
                name="unique_research_submission_advisor_advice",
            )
        ]

        ordering = ["-submitted_at", "-created_at"]

    def __str__(self):
        return f"{self.submission.milestone.milestone_title} | " f"{self.advisor}"


class FinalDissertationAdvisorEvaluation(models.Model):

    RECOMMENDATION_CHOICES = (
        ("APPROVE", "Approve"),
        ("REVISION_REQUIRED", "Revision Required"),
        ("REJECT", "Reject"),
    )

    evaluation_id = models.AutoField(
        primary_key=True,
    )

    submission = models.ForeignKey(
        "Students.FinalDissertationSubmission",
        on_delete=models.CASCADE,
        related_name="advisor_evaluations",
    )

    advisor = models.ForeignKey(
        "Faculty.FacultyProfile",
        on_delete=models.CASCADE,
        related_name="final_dissertation_advisor_evaluations",
    )

    submission_number = models.PositiveIntegerField(
        default=1,
    )

    resubmission_count = models.PositiveIntegerField(
        default=0,
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
        db_table = "final_dissertation_advisor_evaluations"

        ordering = [
            "-submitted_at",
            "-evaluation_id",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "submission",
                    "advisor",
                    "submission_number",
                ],
                name="unique_final_dissertation_advisor_evaluation",
            ),
        ]

    def __str__(self):
        return f"{self.submission} - " f"Advisor Evaluation"


class FinalDissertationCommitteeEvaluation(models.Model):

    REVIEWER_ROLE_CHOICES = (
        ("COMMITTEE_MEMBER", "Committee Member"),
        ("CHAIR", "Chair"),
    )

    RECOMMENDATION_CHOICES = (
        ("APPROVE", "Approve"),
        ("REVISION_REQUIRED", "Revision Required"),
        ("REJECT", "Reject"),
    )

    evaluation_id = models.AutoField(
        primary_key=True,
    )

    submission = models.ForeignKey(
        "Students.FinalDissertationSubmission",
        on_delete=models.CASCADE,
        related_name="committee_evaluations",
    )

    committee_member = models.ForeignKey(
        "Students.CommitteeMember",
        on_delete=models.CASCADE,
        related_name="final_dissertation_evaluations",
    )

    reviewer_role = models.CharField(
        max_length=30,
        choices=REVIEWER_ROLE_CHOICES,
    )

    submission_number = models.PositiveIntegerField(
        default=1,
    )

    resubmission_count = models.PositiveIntegerField(
        default=0,
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

    is_final_decision = models.BooleanField(
        default=False,
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
        db_table = "final_dissertation_committee_evaluations"

        ordering = [
            "-submitted_at",
            "-evaluation_id",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "submission",
                    "committee_member",
                    "submission_number",
                ],
                name="unique_final_dissertation_committee_evaluation",
            ),
        ]

    def __str__(self):
        return f"{self.submission} - " f"{self.committee_member}"


class AdvisorStudentMessage(models.Model):
    SENDER_ROLE_CHOICES = (
        ("STUDENT", "Student"),
        ("ADVISOR", "Advisor"),
    )

    message_id = models.AutoField(
        primary_key=True,
    )

    phd_student = models.ForeignKey(
        "Students.PhDStudent",
        on_delete=models.CASCADE,
        related_name="advisor_student_messages",
    )

    advisor = models.ForeignKey(
        "Faculty.FacultyProfile",
        on_delete=models.CASCADE,
        related_name="advisor_student_messages",
    )

    sender_role = models.CharField(
        max_length=10,
        choices=SENDER_ROLE_CHOICES,
    )

    message = models.TextField(
        blank=True,
        null=True,
    )

    is_read = models.BooleanField(
        default=False,
    )

    read_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    is_full_crud = models.BooleanField(
        default=False,
    )

    class Meta:
        db_table = "advisor_student_messages"
        ordering = [
            "created_at",
        ]

    def __str__(self):
        return f"{self.phd_student} - {self.advisor} - {self.sender_role}"


class AdvisorStudentMessageAttachment(models.Model):
    attachment_id = models.AutoField(
        primary_key=True,
    )

    message = models.ForeignKey(
        AdvisorStudentMessage,
        on_delete=models.CASCADE,
        related_name="attachments",
    )

    attachment = models.FileField(
        upload_to="phd/advisor_student_messages/",
    )

    original_name = models.CharField(
        max_length=255,
    )

    file_size = models.PositiveBigIntegerField(
        default=0,
    )

    content_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    is_full_crud = models.BooleanField(
        default=False,
    )

    class Meta:
        db_table = "advisor_student_message_attachments"
        ordering = [
            "attachment_id",
        ]

    def __str__(self):
        return self.original_name


## Leo's code end ##
