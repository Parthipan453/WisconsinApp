# *********************  rupa code ****************************
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from Students.models import StudentOrganization
from Admin.Colleges.models import *

# Event Category
class EventCategory(models.Model):
    category_id = models.AutoField(primary_key=True)

    category_name = models.CharField(
        max_length=100,
        unique=True
    )

    description = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )
    is_full_crud = models.BooleanField(default=False)

    def __str__(self):
        return self.category_name
    
# Event Venue

class EventVenue(models.Model):

    venue_id = models.AutoField(
        primary_key=True
    )

    venue_name = models.CharField(
        max_length=255
    )

    building_name = models.CharField(
        max_length=255
    )

    room_number = models.CharField(
        max_length=50
    )
    is_full_crud = models.BooleanField(default=False)

    seating_capacity = models.PositiveIntegerField()

    location_details = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.venue_name
    
# Event

from django.conf import settings
from Admin.bela_admin.models import Department


class EventQuerySet(models.QuerySet):
    def update_completed(self):
        now = timezone.now()
        self.filter(
            end_datetime__isnull=False,
            end_datetime__lt=now
        ).exclude(
            event_status="Completed"
        ).update(event_status="Completed")
        return self


class EventManager(models.Manager):
    def get_queryset(self):
        qs = EventQuerySet(self.model, using=self._db)
        # qs.update_completed()
        return qs


class Event(models.Model):

    objects = EventManager()

    # Organizer Types Constants
    DEPARTMENT = "Department"
    STUDENT_ORGANIZATION = "Student Organization"
    ADMINISTRATION = "Administration"

    ORGANIZER_TYPES = [
        (DEPARTMENT, "Department"),
        (STUDENT_ORGANIZATION, "Student Organization"),
        (ADMINISTRATION, "Administration"),
    ]
    
    # Event Modes constants
    ONLINE = "Online"
    HYBRID = "Hybrid"
    OFFLINE = "Offline"

    EVENT_MODE_CHOICES = [
        (ONLINE, "Online"),
        (HYBRID, "Hybrid"),
        (OFFLINE, "Offline"),
    ]

    # Event Status constants
    DRAFT = "Draft"
    PUBLISHED = "Published"
    CANCELLED = "Cancelled"
    COMPLETED = "Completed"

    EVENT_STATUS = [
        (DRAFT, "Draft"),
        (PUBLISHED, "Published"),
        (CANCELLED, "Cancelled"),
        (COMPLETED, "Completed"),
    ]

    # Event Visibility constants
    PUBLIC = "Public"
    CAMPUS_ONLY = "Campus Only"
    INVITATION_ONLY = "Invitation Only"

    VISIBILITY_CHOICES = [
        (PUBLIC, "Public"),
        (CAMPUS_ONLY, "Campus Only"),
        (INVITATION_ONLY, "Invitation Only"),
    ]

    event_id = models.AutoField(
        primary_key=True
    )

    event_code = models.CharField(
        max_length=50,
        unique=True
    )

    event_title = models.CharField(
        max_length=255
    )
    
    event_subtitle = models.CharField(
        max_length=255,
        blank=True
    )

    event_description = models.TextField()

    event_category = models.ForeignKey(
        EventCategory,
        on_delete=models.CASCADE,
        related_name='events'
    )

    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='organized_events'
    )

    organizer_type = models.CharField(
        max_length=50,
        choices=ORGANIZER_TYPES
    )
    
    contact_email = models.EmailField(
        blank=True
    )

    contact_phone = models.CharField(
        max_length=20,
        blank=True
    )
    
    school = models.ForeignKey(
        School,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )   
    
    student_organization = models.ForeignKey(
        StudentOrganization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    ) 
    
    event_mode = models.CharField(
        max_length=10,
        choices=EVENT_MODE_CHOICES,
        default=OFFLINE,
    )

    venue = models.ForeignKey(
        EventVenue,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    event_status = models.CharField(
        max_length=20,
        choices=EVENT_STATUS,
        default='Draft'
    )

    event_visibility = models.CharField(
        max_length=20,
        choices=VISIBILITY_CHOICES,
        default='Campus Only'
    )

    invited_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="event_invitations",
    )

    start_datetime = models.DateTimeField()

    end_datetime = models.DateTimeField(
        blank=True,
        null=True
    )

    registration_required = models.BooleanField(
        default=False
    )
    
    # Pricing
    is_paid_event = models.BooleanField(
        default=False,
    )

    event_cost = models.TextField(
        blank=True,
    )

    # Event website
    event_website = models.URLField(
        blank=True,
    )

    # Accessibility
    has_accessibility_information = models.BooleanField(
        default=False,
    )

    accessibility_email = models.EmailField(
        blank=True
    )

    accessibility_phone = models.CharField(
        max_length=20,
        blank=True
    )

    max_capacity = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )
    is_full_crud = models.BooleanField(default=False)

    def __str__(self):
        return self.event_title

    @property
    def is_past_start(self):
        if not self.start_datetime:
            return False
        now = timezone.now()
        start_dt = self.start_datetime
        if timezone.is_aware(now) and timezone.is_naive(start_dt):
            start_dt = timezone.make_aware(start_dt, timezone.get_current_timezone())
        elif timezone.is_naive(now) and timezone.is_aware(start_dt):
            start_dt = timezone.make_naive(start_dt, timezone.get_current_timezone())
        return now > start_dt

    def clean(self):
        super().clean()
        if self.pk:
            orig = Event.objects.filter(pk=self.pk).values("event_status").first()
            if orig and orig["event_status"] == self.COMPLETED and self.event_status != self.COMPLETED:
                raise ValidationError("Once an event is completed, its status cannot be changed to any other status.")

    def save(self, *args, **kwargs):
        if self.end_datetime:
            now = timezone.now()
            end_dt = self.end_datetime
            if timezone.is_aware(now) and timezone.is_naive(end_dt):
                end_dt = timezone.make_aware(end_dt, timezone.get_current_timezone())
            elif timezone.is_naive(now) and timezone.is_aware(end_dt):
                end_dt = timezone.make_naive(end_dt, timezone.get_current_timezone())

            if now > end_dt:
                self.event_status = self.COMPLETED

        if self.pk:
            orig = Event.objects.filter(pk=self.pk).values("event_status").first()
            if orig and orig["event_status"] == self.COMPLETED:
                self.event_status = self.COMPLETED

        super().save(*args, **kwargs)
    
    @classmethod
    def generate_event_code(cls):

        current_year = timezone.now().year

        prefix = f"EV{current_year}"

        latest_event = (
            cls.objects.filter(
                event_code__startswith=prefix
            )
            .order_by("-event_code")
            .first()
        )

        if latest_event:

            latest_number = int(
                latest_event.event_code[-4:]
            )

            next_number = latest_number + 1

        else:

            next_number = 1

        return f"{prefix}{next_number:04d}"
    
# Event Registration

class EventRegistration(models.Model):

    ATTENDANCE_STATUS = (
        ('Registered', 'Registered'),
        ('Present', 'Present'),
        ('Absent', 'Absent'),
    )

    registration_id = models.AutoField(
        primary_key=True
    )

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='registrations'
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='event_registrations'
    )

    registration_date = models.DateTimeField(
        auto_now_add=True
    )

    attendance_status = models.CharField(
        max_length=20,
        choices=ATTENDANCE_STATUS,
        default='Registered'
    )

    check_in_time = models.DateTimeField(
        null=True,
        blank=True
    )
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        unique_together = ('event', 'user')

    def __str__(self):
        return f"{self.user.username} - {self.event.event_title}"
    

# Event Speaker

class EventSpeaker(models.Model):

    speaker_id = models.AutoField(
        primary_key=True
    )

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='speakers'
    )

    speaker_name = models.CharField(
        max_length=255
    )

    organization = models.CharField(
        max_length=255
    )

    designation = models.CharField(
        max_length=255
    )

    biography = models.TextField(
        blank=True,
        null=True
    )
    is_full_crud = models.BooleanField(default=False)

    email = models.EmailField()

    def __str__(self):
        return self.speaker_name
    
# Event Session

class EventSession(models.Model):

    session_id = models.AutoField(
        primary_key=True
    )

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='sessions'
    )

    speaker = models.ForeignKey(
        EventSpeaker,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    session_title = models.CharField(
        max_length=255
    )

    start_time = models.DateTimeField()

    end_time = models.DateTimeField()

    room_number = models.CharField(
        max_length=100
    )
    is_full_crud = models.BooleanField(default=False)

    def __str__(self):
        return self.session_title
    
# Event Sponsor

class EventSponsor(models.Model):

    SPONSORSHIP_TYPES = (
        ('Platinum', 'Platinum'),
        ('Gold', 'Gold'),
        ('Silver', 'Silver'),
        ('Bronze', 'Bronze'),
    )

    sponsor_id = models.AutoField(
        primary_key=True
    )

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='sponsors'
    )

    sponsor_name = models.CharField(
        max_length=255
    )

    sponsorship_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )
    is_full_crud = models.BooleanField(default=False)

    sponsorship_type = models.CharField(
        max_length=20,
        choices=SPONSORSHIP_TYPES
    )

# Event Budget

class EventBudget(models.Model):

    budget_id = models.AutoField(
        primary_key=True
    )

    event = models.OneToOneField(
        Event,
        on_delete=models.CASCADE,
        related_name='budget'
    )

    allocated_budget = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    actual_expense = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    is_full_crud = models.BooleanField(default=False)

    remaining_budget = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

# Event Feedback

class EventFeedback(models.Model):

    feedback_id = models.AutoField(
        primary_key=True
    )

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='feedbacks'
    )

    attendee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    rating = models.PositiveSmallIntegerField()

    comments = models.TextField(
        blank=True,
        null=True
    )
    is_full_crud = models.BooleanField(default=False)

    submitted_at = models.DateTimeField(
        auto_now_add=True
    )

# Event Certificate

class EventCertificate(models.Model):

    certificate_id = models.AutoField(
        primary_key=True
    )

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE
    )

    participant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    certificate_number = models.CharField(
        max_length=100,
        unique=True
    )
    is_full_crud = models.BooleanField(default=False)

    issue_date = models.DateField()

    certificate_url = models.URLField()

# Event Notification

class EventNotification(models.Model):

    NOTIFICATION_TYPES = (
        ('Registration Confirmation', 'Registration Confirmation'),
        ('Reminder', 'Reminder'),
        ('Schedule Change', 'Schedule Change'),
        ('Cancellation Notice', 'Cancellation Notice'),
        ('Thank You Message', 'Thank You Message'),
    )

    notification_id = models.AutoField(
        primary_key=True
    )

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    notification_type = models.CharField(
        max_length=50,
        choices=NOTIFICATION_TYPES
    )

    message = models.TextField()

    sent_at = models.DateTimeField(
        auto_now_add=True
    )
    is_full_crud = models.BooleanField(default=False)


# *******************************  rupa code ends *******************************

