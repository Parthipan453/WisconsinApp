import secrets
from datetime import timedelta
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.utils import timezone

# Password Reset
class PasswordResetOTP(models.Model):

    OTP_LENGTH = 6
    OTP_VALIDITY_MINUTES = 10
    MAX_ATTEMPTS = 5
    RESEND_COOLDOWN_SECONDS = 60

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="password_reset_otps", 
    )
    otp_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    is_used = models.BooleanField(default=False)
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        indexes = [models.Index(fields=["user", "is_used"])]

    def __str__(self):
        return f"OTP for {self.user} (used={self.is_used})"

    @classmethod
    def generate_for_user(cls, user):
        cls.objects.filter(user=user, is_used=False).update(is_used=True)

        raw_otp = "".join(secrets.choice("0123456789") for _ in range(cls.OTP_LENGTH))
        instance = cls.objects.create(
            user=user,
            otp_hash=make_password(raw_otp),
            expires_at=timezone.now() + timedelta(minutes=cls.OTP_VALIDITY_MINUTES),
        )
        return instance, raw_otp

    def is_expired(self):
        return timezone.now() > self.expires_at

    def is_valid_for_attempt(self):
        return not self.is_used and not self.is_expired() and self.attempts < self.MAX_ATTEMPTS

    def verify(self, raw_otp):
        if not self.is_valid_for_attempt():
            return False

        if check_password(raw_otp, self.otp_hash):
            self.is_used = True
            self.save(update_fields=["is_used"])
            return True

        self.attempts += 1
        self.save(update_fields=["attempts"])
        return False
    
# Announcement
class Announcement(models.Model):
    user_types = ["admin"]
    VISIBILITY_WEBSITE = "website"
    VISIBILITY_DASHBOARD = "dashboard"
    VISIBILITY_BOTH = "both"
    
    VISIBILITY_CHOICES = [
        (VISIBILITY_WEBSITE, "Website"),
        (VISIBILITY_DASHBOARD, "Dashboard"),
        (VISIBILITY_BOTH, "Website & Dashboard"),
    ]
    
    PRIORITY_INFO = "info"
    PRIORITY_WARNING = "warning"
    PRIORITY_URGENT = "urgent"
    
    PRIORITY_CHOICES = [
        (PRIORITY_INFO, "Info"),
        (PRIORITY_WARNING, "Warning"),
        (PRIORITY_URGENT, "Urgent"),
    ]
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default=VISIBILITY_BOTH)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default=PRIORITY_INFO)
    is_pinned = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="announcements")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_full_crud = models.BooleanField(default=True)
    
    class Meta:
        ordering = ["-is_pinned", "-start_date"]
        
    def __str__(self):
        return self.title
    
    @property
    def status(self):
        now = timezone.now()
        if not self.is_active:
            return 'disabled'
        if self.start_date > now:
            return 'scheduled'
        if self.end_date and self.end_date < now:
            return 'expired'
        return 'active'
    
    @classmethod
    def visible_queryset(cls, channel):
        now = timezone.now()
        return cls.objects.filter(
            is_active = True,
            start_date__lte = now,
            visibility__in = [channel, cls.VISIBILITY_BOTH],
        ).filter(
            models.Q(end_date__isnull = True) | models.Q(end_date__gte = now)
        )
        
# Notification
class Notification(models.Model):
    EVENT_CHOICES = [
        ('new', 'New Announcement'),
        ('expired', 'Announcement Expired'),
        ('shift_assigned', 'Shift Assigned'),
        ('shift_updated', 'Shift Updated'),
        ('shift_cancelled', 'Shift Cancelled'),
        ('tournament_applied', 'Tournament Application Submitted'),
    ]

    NOTIFICATION_TYPE_CHOICES = [
        ('ANNOUNCEMENT', 'Announcement'),
        ('SCHEDULE', 'Schedule'),
        ('TOURNAMENT', 'Tournament'),
    ]

    notification_type = models.CharField( 
        max_length=20,
        choices=NOTIFICATION_TYPE_CHOICES,
        default='ANNOUNCEMENT'
    )

    recipient = models.ForeignKey(
        'Admin.User',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        help_text="Blank = broadcast announcement notification visible to everyone."
    )

    announcement = models.ForeignKey(
        Announcement,
        on_delete=models.CASCADE,
        related_name='announcement_notifications',
        null=True,
        blank=True
    )

    schedule = models.ForeignKey(
        'Medical.Shift',
        on_delete=models.CASCADE,
        related_name='shift_notifications',
        null=True,
        blank=True
    )

    tournament_application = models.ForeignKey(
        'Admin.TournamentApplication',
        on_delete=models.CASCADE,
        related_name='application_notifications',
        null=True,
        blank=True
    )

    event = models.CharField(max_length=255)
    message = models.CharField(max_length=255)
    icon = models.CharField(max_length=50, blank=True, help_text="Lucide icon name e.g. 'calendar-check', 'megaphone'")
    link_url = models.CharField(max_length=255, blank=True, help_text="Optional URL to open on click")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        if self.notification_type == 'SCHEDULE':
            return f"[{self.event}] {self.schedule}"
        if self.notification_type == 'TOURNAMENT':
            return f"[{self.event}] {self.tournament_application}"
        return f"[{self.event}] {self.announcement.title if self.announcement else ''}"