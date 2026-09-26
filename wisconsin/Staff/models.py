# Staff/models.py
from django.db import models
from Admin.models import User  
from Admin.models import User 
#___Eric code____ 
from Staff.Eric.models import *
#____Eric code End____


class StaffProfile(models.Model):
    EMPLOYMENT_STATUS_CHOICES = (
        ("ACTIVE", "Active"),
        ("LEAVE", "Leave"),
        ("RETIRED", "Retired"),
        ("TERMINATED", "Terminated"),
    )
    EMPLOYMENT_TYPE_CHOICES = (
        ("FULL_TIME", "Full-Time"),
        ("PART_TIME", "Part-Time"),
        ("TEMPORARY", "Temporary"),
    )

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="staff_profile"
    )

    # Identifiers
    employee_id = models.CharField(max_length=100, unique=True)

    # Contact
    work_email = models.EmailField(unique=True)
    personal_email = models.EmailField(blank=True, null=True)
    office_phone = models.CharField(max_length=20, blank=True, null=True)

    # Preferred name 
    preferred_name = models.CharField(max_length=100, blank=True, null=True)

    # Employment
    hire_date = models.DateField(blank=True, null=True)
    employment_status = models.CharField(
        max_length=20, choices=EMPLOYMENT_STATUS_CHOICES, default="ACTIVE"
    )
    employment_type = models.CharField(
        max_length=20, choices=EMPLOYMENT_TYPE_CHOICES, blank=True, null=True 
    )

    supervisor = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="subordinates",
    )
    ###################################### swetha's code ###################################################

    is_coach = models.BooleanField(default=False,help_text="Allow this position to be assigned as Coach")

    ###################################### swetha's code ###################################################

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_full_crud = models.BooleanField(default=False)

    #blaze code start----------------------------------------------------------------------------------->(06.07.26)

    tfa_enabled = models.BooleanField(default=False)
    tfa_secret = models.CharField(max_length=255, blank=True, null=True)
    tfa_backup_codes = models.TextField(blank=True, null=True)
    
    #blaze_code_end ----------------------------------------------------------------------------------->(06.07.26)


    class Meta:
        db_table = "staff_profiles"

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_id})"


class StaffPosition(models.Model):
    POSITION_STATUS_CHOICES = (
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
        ("PENDING", "Pending"),
    )

    staff = models.ForeignKey(
        StaffProfile, on_delete=models.CASCADE, related_name="positions"
    )


    job_title = models.CharField(max_length=150)
    job_code = models.CharField(max_length=50, blank=True, null=True)
    department_id = models.IntegerField(blank=True, null=True)  
    unit_id = models.IntegerField(blank=True, null=True)        
    position_start_date = models.DateField()
    position_end_date = models.DateField(blank=True, null=True)
    position_status = models.CharField(
        max_length=20, choices=POSITION_STATUS_CHOICES, default="ACTIVE"
    )
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "staff_positions"

    def __str__(self):
        return f"{self.staff} - {self.job_title}"


class StaffAddress(models.Model):
    ADDRESS_TYPE_CHOICES = (
        ("PERMANENT", "Permanent"),
        ("MAILING", "Mailing"),
        ("CAMPUS_HOUSING", "Campus Housing"),
    )

    staff = models.ForeignKey(
        StaffProfile, on_delete=models.CASCADE, related_name="addresses"
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
        db_table = "staff_addresses"

    def __str__(self):
        return f"{self.staff} - {self.address_type}"


class StaffEmergencyContact(models.Model):
    staff = models.ForeignKey(
        StaffProfile, on_delete=models.CASCADE, related_name="emergency_contacts"
    )
    contact_name = models.CharField(max_length=150)
    relationship = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    priority = models.PositiveSmallIntegerField(default=1)
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "staff_emergency_contacts"
        ordering = ["priority"]

    def __str__(self):
        return f"{self.contact_name} ({self.relationship}) - {self.staff}"


class StaffDepartmentAssignment(models.Model):
    staff = models.ForeignKey(
        StaffProfile, on_delete=models.CASCADE, related_name="department_assignments"
    )
    department_id = models.IntegerField()   
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    primary_assignment = models.BooleanField(default=False)
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "staff_department_assignments"

    def __str__(self):
        return f"{self.staff} - Dept {self.department_id}"


class StaffEducation(models.Model):
    staff = models.ForeignKey(
        StaffProfile, on_delete=models.CASCADE, related_name="education_records"
    )
    degree = models.CharField(max_length=100)
    institution_name = models.CharField(max_length=200)
    field_of_study = models.CharField(max_length=150, blank=True, null=True)
    graduation_year = models.PositiveSmallIntegerField(blank=True, null=True)
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "staff_education"

    def __str__(self):
        return f"{self.staff} - {self.degree} ({self.institution_name})"


class StaffCertification(models.Model):
    staff = models.ForeignKey(
        StaffProfile, on_delete=models.CASCADE, related_name="certifications"
    )
    certification_name = models.CharField(max_length=200)
    issuing_organization = models.CharField(max_length=200)
    issue_date = models.DateField()
    expiration_date = models.DateField(blank=True, null=True)
    is_full_crud = models.BooleanField(default=False)
    
    class Meta:
        db_table = "staff_certifications"

    def __str__(self):
        return f"{self.staff} - {self.certification_name}"


class StaffTraining(models.Model):
    TRAINING_STATUS_CHOICES = (
        ("COMPLETED", "Completed"),
        ("IN_PROGRESS", "In Progress"),
        ("ENROLLED", "Enrolled"),
        ("CANCELLED", "Cancelled"),
    )

    staff = models.ForeignKey(
        StaffProfile, on_delete=models.CASCADE, related_name="training_records"
    )
    training_title = models.CharField(max_length=200)
    provider = models.CharField(max_length=200, blank=True, null=True)
    completion_date = models.DateField(blank=True, null=True)
    training_status = models.CharField(
        max_length=20, choices=TRAINING_STATUS_CHOICES, default="ENROLLED"
    )
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "staff_training"

    def __str__(self):
        return f"{self.staff} - {self.training_title}"


class StaffPerformanceReview(models.Model):
    PERFORMANCE_RATING_CHOICES = (
        ("OUTSTANDING", "Outstanding"),
        ("EXCEEDS_EXPECTATIONS", "Exceeds Expectations"),
        ("MEETS_EXPECTATIONS", "Meets Expectations"),
        ("NEEDS_IMPROVEMENT", "Needs Improvement"),
        ("UNSATISFACTORY", "Unsatisfactory"),
    )

    staff = models.ForeignKey(
        StaffProfile, on_delete=models.CASCADE, related_name="performance_reviews"
    )
    review_period = models.CharField(max_length=50)  
    reviewer = models.ForeignKey(
        StaffProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviews_given",
    )
    performance_rating = models.CharField(
        max_length=30, choices=PERFORMANCE_RATING_CHOICES, blank=True, null=True
    )
    comments = models.TextField(blank=True, null=True)
    review_date = models.DateField()
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "staff_performance_reviews"

    def __str__(self):
        return f"{self.staff} - {self.review_period}"


class StaffLeave(models.Model):
    LEAVE_TYPE_CHOICES = (
        ("VACATION", "Vacation"),
        ("SICK", "Sick Leave"),
        ("PERSONAL", "Personal Leave"),
        ("FAMILY", "Family Leave"),
        ("UNPAID", "Unpaid Leave"),
    )
    APPROVAL_STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
        ("CANCELLED", "Cancelled"),
    )

    staff = models.ForeignKey(
        StaffProfile, on_delete=models.CASCADE, related_name="leave_records"
    )
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    approval_status = models.CharField(
        max_length=20, choices=APPROVAL_STATUS_CHOICES, default="PENDING"
    )
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "staff_leaves"

    def __str__(self):
        return f"{self.staff} - {self.leave_type} ({self.start_date})"


class StaffPayroll(models.Model):
    PAY_FREQUENCY_CHOICES = (
        ("WEEKLY", "Weekly"),
        ("BI_WEEKLY", "Bi-Weekly"),
        ("SEMI_MONTHLY", "Semi-Monthly"),
        ("MONTHLY", "Monthly"),
    )

    staff = models.ForeignKey( 
        StaffProfile, on_delete=models.CASCADE, related_name="payroll_records"
    )
    pay_grade = models.CharField(max_length=50, blank=True, null=True)
    annual_salary = models.DecimalField(max_digits=12, decimal_places=2)
    pay_frequency = models.CharField(
        max_length=20, choices=PAY_FREQUENCY_CHOICES, default="MONTHLY"
    )
    effective_date = models.DateField()
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "staff_payroll"

    def __str__(self):
        return f"{self.staff} - {self.annual_salary} (from {self.effective_date})"


class StaffAccessRole(models.Model):
    SYSTEM_ROLE_CHOICES = (
        ("REGISTRAR_ADMIN", "Registrar Admin"),
        ("ADMISSIONS_ADMIN", "Admissions Admin"),
        ("FINANCE_OFFICER", "Finance Officer"),
        ("HR_MANAGER", "HR Manager"),
        ("IT_SUPPORT", "IT Support"),
        ("LIBRARY_ADMINISTRATOR", "Library Administrator"),
    )

    staff = models.ForeignKey(
        StaffProfile, on_delete=models.CASCADE, related_name="access_roles"
    )
    system_role = models.CharField(max_length=30, choices=SYSTEM_ROLE_CHOICES)
    assigned_date = models.DateField()
    active = models.BooleanField(default=True)
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "staff_access_roles"

    def __str__(self):
        return f"{self.staff} - {self.system_role}"


# ************************************************ Arun Code ********************************************************

class StaffDocument(models.Model):
    DOCUMENT_TYPE_CHOICES = (
        ("ID_PROOF", "ID Proof"),
        ("EMPLOYMENT_CONTRACT", "Employment Contract"),
        ("DEGREE_CERTIFICATE", "Degree Certificate"),
        ("CERTIFICATION", "Certification"),
        ("BACKGROUND_CHECK", "Background Check"),
        ("OTHER", "Other"),
    )
    VERIFICATION_STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("VERIFIED", "Verified"),
        ("REJECTED", "Rejected"),
    )

    staff = models.ForeignKey(
        "StaffProfile", on_delete=models.CASCADE, related_name="documents"
    )
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPE_CHOICES)
    file_name = models.CharField(max_length=255)
    file = models.FileField(upload_to="staff/documents/", blank=True, null=True)
    upload_date = models.DateTimeField(auto_now_add=True)
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default="PENDING",
    )
    is_full_crud = models.BooleanField(default=True)


    class Meta:
        db_table = "staff_documents"

    def __str__(self):
        return f"{self.staff} - {self.document_type}"



import os
from django.db import models
from django.utils import timezone


def resource_upload_path(instance, filename):
    return f"resources/{instance.resource_type}/{filename}"


class Resource(models.Model):
    """
    Shared staff downloads library.
    Visible to ALL logged-in staff members — anyone who uploads a file
    makes it available to every staff member on the Downloads page.
    """

    TYPE_CHOICES = [
        ('document', 'Document'),
        ('template', 'Template'),
        ('form', 'Form'),
        ('guide', 'Guide'),
        ('presentation', 'Presentation'),
        ('spreadsheet', 'Spreadsheet'),
    ]
    CATEGORY_CHOICES = [
        ('student-services', 'Student Services'),
        ('academic-support', 'Academic Support'),
        ('financial-aid', 'Financial Aid'),
        ('records', 'Records'),
    ]

    FORM_CATEGORY_CHOICES = [
        ('hr', 'HR'),
        ('academic', 'Academic'),
        ('finance', 'Finance'),
        ('compliance', 'Compliance'),
        ('it', 'IT'),
    ]
 
    FORM_STATUS_CHOICES = [
        ('active', 'Active'),
        ('pending_signature', 'Pending Signature'),
        ('expiring', 'Expiring'),
        ('archived', 'Archived'),
    ]
 
    form_category = models.CharField(
        max_length=20, choices=FORM_CATEGORY_CHOICES, blank=True, null=True
    )
    department_name = models.CharField(max_length=150, blank=True, null=True)
    status = models.CharField(max_length=20, choices=FORM_STATUS_CHOICES, default='active')
    expires_at = models.DateField(blank=True, null=True)


    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    resource_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='document')
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='student-services')
    version = models.CharField(max_length=20, default='1.0')
    file = models.FileField(upload_to=resource_upload_path)
    file_size = models.PositiveIntegerField(default=0)  
    download_count = models.PositiveIntegerField(default=0)
    uploaded_by = models.ForeignKey(
        'Admin.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='uploaded_resources'
    )
    uploaded_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_full_crud = models.BooleanField(default=False)

    visible_to_staff = models.BooleanField(default=True)
    visible_to_faculty = models.BooleanField(default=False)
    visible_to_students = models.BooleanField(default=False)

    class Meta:
        ordering = ['-uploaded_at']

    def save(self, *args, **kwargs):
        if self.file and hasattr(self.file, 'size'):
            self.file_size = self.file.size
        super().save(*args, **kwargs)

    @property
    def file_extension(self):
        return os.path.splitext(self.file.name)[1].lstrip('.').upper() if self.file else ''

    @property
    def file_size_display(self):
        size = self.file_size
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.0f} KB"
        return f"{size / 1024 / 1024:.1f} MB"

    def __str__(self):
        return self.title

class ResourceAlert(models.Model):
    """
    One row per upload broadcast — not per recipient. Read state is
    tracked separately via ResourceAlertSeen so this table only grows
    with uploads, never with audience size.
    """
    resource = models.ForeignKey(
        Resource, on_delete=models.CASCADE, related_name="alerts"
    )
    message = models.CharField(max_length=255, blank=True)
    posted_by = models.ForeignKey(
        'Admin.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name="resource_alerts_posted"
    )
    visible_to_staff = models.BooleanField(default=False)
    visible_to_faculty = models.BooleanField(default=False)
    visible_to_students = models.BooleanField(default=False)
    posted_at = models.DateTimeField(auto_now_add=True)
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "resource_alerts"
        ordering = ["-posted_at"]

    def __str__(self):
        return f"Alert: {self.resource.title}"


class ResourceAlertSeen(models.Model):
    """
    One row per user. Updated in place on each visit — lets us compute
    an 'unread' count without ever inserting a per-recipient row.
    """
    user = models.OneToOneField(
        'Admin.User', on_delete=models.CASCADE, related_name="resource_alert_seen"
    )
    last_seen_at = models.DateTimeField(auto_now=True)
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "resource_alert_seen"

    def __str__(self):
        return f"{self.user} last saw resources at {self.last_seen_at}"
    

class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES = (
        ("INFO", "Info"),
        ("SUCCESS", "Success"),
        ("WARNING", "Warning"),
        ("ERROR", "Error"),
        ("REQUEST", "Request"),
        ("SYSTEM", "System"),
    )

    user = models.ForeignKey(
        "Admin.User", on_delete=models.CASCADE, related_name="staff_notifications"
    )
    title = models.CharField(max_length=255)
    message = models.TextField(blank=True, null=True)
    notification_type = models.CharField(
        max_length=20, choices=NOTIFICATION_TYPE_CHOICES, default="INFO"
    )
    link = models.CharField(max_length=500, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_full_crud = models.BooleanField(default=False)

    related_leave_id = models.IntegerField(null=True, blank=True)

    related_borrow_request_uuid = models.UUIDField(null=True, blank=True)

    related_borrow_transaction_id = models.IntegerField(null=True, blank=True, db_index=True)

    related_event_id = models.IntegerField(null=True, blank=True, db_index=True)   

    class Meta:
        db_table = "staff_notifications"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.title}"


from django.db import models
from Admin.models import User

class MessageThread(models.Model):
    """
    One conversation. Holds the subject line and who started it.
    A thread can have many Messages (the original + replies), just
    like a real email thread with 'RE:' replies.
    """
    subject = models.CharField(max_length=255)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="threads_started"
    )
    is_announcement = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "message_threads"
        ordering = ["-created_at"]

    def __str__(self):
        return self.subject

    def last_message(self):
        return self.messages.order_by("-sent_at").first()


class Message(models.Model):
    """
    A single message within a thread. The very first Message in a
    thread is the 'original'; anything after it is a reply.
    """
    thread = models.ForeignKey(
        MessageThread, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="messages_sent"
    )
    body = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "messages"
        ordering = ["sent_at"]

    def __str__(self):
        return f"{self.sender} @ {self.sent_at:%Y-%m-%d %H:%M}"


class MessageRecipient(models.Model):
    """
    Who a given Message was sent to, and that recipient's own
    read/archived state. Kept separate from Message so each
    recipient's inbox state is independent (same idea as a real
    mailbox: my 'read' status doesn't affect yours).
    """
    message = models.ForeignKey(
        Message, on_delete=models.CASCADE, related_name="recipients"
    )
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="messages_received"
    )
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(blank=True, null=True)
    archived = models.BooleanField(default=False)
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "message_recipients"
        unique_together = ("message", "recipient")

    def __str__(self):
        return f"{self.message} -> {self.recipient}"

def message_attachment_path(instance, filename):
    return f"message_attachments/{instance.message.thread_id}/{instance.message_id}/{filename}"


class MessageAttachment(models.Model):
    message = models.ForeignKey(
        Message, on_delete=models.CASCADE, related_name="attachments"
    )
    file = models.FileField(upload_to=message_attachment_path)
    original_name = models.CharField(max_length=255, blank=True)
    content_type = models.CharField(max_length=100, blank=True)
    size = models.PositiveIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_full_crud = models.BooleanField(default=False)

    def is_image(self):
        return (self.content_type or "").startswith("image/")

    def is_video(self):
        return (self.content_type or "").startswith("video/")
    
class Announcement(models.Model):
    """
    University/department-wide broadcasts. Not tied to a specific
    recipient — everyone (or everyone in a department) sees it.
    """
    PRIORITY_CHOICES = (
        ("URGENT", "Urgent"),
        ("INFO", "Info"),
        ("NOTICE", "Notice"),
    )

    title = models.CharField(max_length=255)
    body = models.TextField()
    posted_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="announcements_posted"
    )
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default="INFO")
    department_id = models.IntegerField(blank=True, null=True)  # null = university-wide
    posted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateField(blank=True, null=True)
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "announcements"
        ordering = ["-posted_at"]

    def __str__(self):
        return self.title

    def is_expired(self):
        from django.utils import timezone
        return bool(self.expires_at and self.expires_at < timezone.localdate())

# ************************************************ Arun Code ********************************************************



#<-------------------------- BLAZE CODE STAFF LEAVE REQUEST START(28.07.26)----------------------->


from django.db import models
from django.conf import settings
from django.utils import timezone

class StaffLeaveType(models.Model):
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
        db_table = "staff_leave_types"


class StaffLeaveRequest(models.Model):
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
    
    staff = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='staff_leave_requests'
    )
    leave_type = models.ForeignKey(StaffLeaveType, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    half_day_type = models.CharField(max_length=20, choices=HALF_DAY_CHOICES, default='full')
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Attachments
    attachment = models.FileField(upload_to='staff_leave_attachments/%Y/%m/', null=True, blank=True)
    attachment_name = models.CharField(max_length=255, blank=True, null=True)
    
    # Approval
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='staff_approved_leaves'
    )
    approved_date = models.DateTimeField(null=True, blank=True)
    approval_remarks = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    is_full_crud = models.BooleanField(default=True)
    
    class Meta:
        db_table = "staff_leave_requests"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.staff.get_full_name()} - {self.leave_type.name}"
    
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


class StaffLeaveBalance(models.Model):
    staff = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='staff_leave_balance'
    )
    annual_leave_balance = models.FloatField(default=30.0)
    sick_leave_balance = models.FloatField(default=15.0)
    casual_leave_balance = models.FloatField(default=10.0)
    earned_leave_balance = models.FloatField(default=0.0)
    compensatory_leave_balance = models.FloatField(default=0.0)
     
    is_full_crud = models.BooleanField(default=True)
    
    class Meta:
        db_table = "staff_leave_balances"
    
    def __str__(self):
        return f"{self.staff.get_full_name()} - Leave Balance"


#<-------------------------- BLAZE CODE STAFF LEAVE REQUEST END(28.07.26)----------------------->


# ************************** Bela Code Start  **************************

class AdvisorAssignment(models.Model):

    program = models.ForeignKey(
        "Colleges.AcademicProgram",
        on_delete=models.CASCADE,
        related_name="advisor_assignments"
    )

    admission_batch = models.PositiveIntegerField()

    roll_number_from = models.CharField(
        max_length=50
    )

    roll_number_to = models.CharField(
        max_length=50
    )

    advisor = models.ForeignKey(
        FacultyProfile,
        on_delete=models.PROTECT,
        related_name="advisor_assignments"
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = "advisor_assignments"

    def __str__(self):
        return (
            f"{self.program.program_name} - "
            f"{self.admission_batch} - "
            f"{self.roll_number_from} to "
            f"{self.roll_number_to}"
        )

# ************************** Bela Code end  **************************
