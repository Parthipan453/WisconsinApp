# /* kali's  code  */

import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from .Alan.models import *
from .Dominic.models import *
# from .Jack.models import *
# from Admin.Jack.models import SportTeamModel



class User(AbstractUser):
    GENDER_CHOICES = (
        ("MALE", "Male"),
        ("FEMALE", "Female"),
        ("TRANSGENDER", "Transgender"),
        ("NON_BINARY", "Non-binary"),
        ("OTHER", "Other"),
        ("PREFER_NOT_TO_SAY", "Prefer not to say"),
    )
    STATUS_CHOICES = (
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
        ("SUSPENDED", "Suspended"), 
        ("PENDING", "Pending"), 
    ) 

    
    uuid = models.UUIDField(default=uuid.uuid4,editable=False,unique=True)

    # University
    university_id = models.CharField( max_length=100,blank=True,null=True,unique=True )

    # Personal Information
    first_name = models.CharField( max_length=100, blank=True, null=True )
    middle_name = models.CharField( max_length=100, blank=True, null=True )
    last_name = models.CharField( max_length=100, blank=True, null=True )
    mobile_number = models.CharField( max_length=20, blank=True, null=True )
    profile_photo = models.ImageField( upload_to="users/profile_photos/",blank=True,null=True )
    date_of_birth = models.DateField( blank=True, null=True )
    gender = models.CharField( max_length=20, choices=GENDER_CHOICES, blank=True, null=True )

    # Status
    account_status = models.CharField( max_length=20, choices=STATUS_CHOICES, default="ACTIVE")
    email_verified = models.BooleanField(default=False)
    mobile_verified = models.BooleanField(default=False)
    role = models.ForeignKey(
        "UserRole",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users"
    )

    # Jack Code Start's

    ssn_number = models.CharField(
        max_length=11,
        unique=True,
        null=True,
        blank=True,
    )

    # Jack Code End's

    # User Type Flags
    is_student = models.BooleanField(default=False)
    is_faculty = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    has_firearm = models.BooleanField(default=False)

    # <-----------------Blaze code start (13.08.26)------------------->

    is_hostel_admin = models.BooleanField(
        default=False,
        help_text="Designates whether the user can manage hostel operations."
    )

    # <-----------------Blaze code End (13.08.26)------------------->

    
    """ Dominic Code Start's """ 
    is_super_admin = models.BooleanField(default=False, help_text=(
        "Designates this user as the system Administrator. "
        "This user bypassess all permission checks."
    ))
    is_full_crud = models.BooleanField(default=True)
    is_medical_staff = models.BooleanField(
        default=False,
        help_text="Checked automatically when this user is assigned a Medical Staff Profile."
    )
    medical_role = models.ForeignKey("Medical.MedicalStaffRole", null=True, blank=True, on_delete=models.SET_NULL, related_name="staff_users")
    """ Dominic Code End's """

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    #blaze code start----------------------------------------------------------------------------------->(09.07.26)
    # Timezone field to store user's preferred timezone

    timezone = models.CharField(
        max_length=50,
        default='America/Chicago',
        choices=[(tz, tz) for tz in [
            'America/New_York', 'America/Chicago', 'America/Denver', 
            'America/Los_Angeles', 'America/Anchorage', 'America/Honolulu',
            'Europe/London', 'Europe/Paris', 'Asia/Dubai', 'Asia/Kolkata',
            'Asia/Shanghai', 'Asia/Tokyo', 'Australia/Sydney', 'Pacific/Auckland'
        ]],
        blank=True,
        null=True )
    #blaze code end--------------------------------------------------------------------------------------->(09.07.26)    

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.username
    
    """ Dominic Code Start's """
    @property
    def is_administrator(self):
        return bool(self.is_admin and self.is_super_admin)
    
    @property
    def full_name(self):
        name = f"{self.first_name or ''} {self.last_name or ''}".strip()
        return name if name else self.username
    """ Dominic Code End's """


class UserSession(models.Model):
    session_id = models.CharField( max_length=255, unique=True)
    user = models.ForeignKey( User,on_delete=models.CASCADE,related_name="sessions")
    login_time = models.DateTimeField()
    logout_time = models.DateTimeField( blank=True, null=True )
    device_type = models.CharField( max_length=100, blank=True, null=True)
    browser = models.CharField( max_length=100, blank=True, null=True )

    class Meta:
        db_table = "user_sessions"

    def __str__(self):
        return f"{self.user.username} - {self.login_time}"


class UserNotificationPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="notification_preferences" )
    email_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=False)
    push_enabled = models.BooleanField(default=True)
    emergency_alert_enabled = models.BooleanField(default=True)

    class Meta:
        db_table = "user_notification_preferences"

    def __str__(self):
        return self.user.username



class UserAuditLog(models.Model):

    ACTION_CHOICES = [
        ("CREATE", "Create"),
        ("UPDATE", "Update"),
        ("DELETE", "Delete"),
        ("LOGIN", "Login"),
        ("LOGOUT", "Logout"),
        ("DOWNLOAD", "Download"),
        ("UPLOAD", "Upload"),
        ("EXPORT", "Export"), 
        ("IMPORT", "Import"),
        ("VIEW", "View"),
        ("PASSWORD_CHANGE", "Password Change"),
        ("ROLE_ASSIGN", "Role Assign"),
        ("ROLE_REMOVE", "Role Remove"),
        
        ("STATUS_CHANGE", "Status Change"),
        ("APPROVE", "Approve"),
        ("REJECT", "Reject"),
        ("ISSUE", "Issue"),
        ("RETURN", "Return"),
        ("RENEW", "Renew"),
        ("REQUEST", "Request"),
        ("CANCEL", "Cancel")


    ]
    STATUS_CHOICES = [
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
    ]
    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs"
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    module = models.CharField(max_length=100,blank=True)
    object_type = models.CharField(max_length=100,blank=True)
    object_id = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    browser = models.CharField(max_length=255, blank=True)
    operating_system = models.CharField(max_length=255, blank=True)
    device = models.CharField(max_length=255, blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    request_url = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="SUCCESS"
    )
    before_data = models.JSONField(null=True, blank=True)
    after_data = models.JSONField(null=True, blank=True)
    session_key = models.CharField(max_length=255, blank=True)
    request_id = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "user_audit_logs"
        ordering = ['-timestamp']




class UserRole(models.Model):
    USER_TYPE_CHOICES = (
        ("student", "Student"),
        ("faculty", "Faculty"),
        ("admin", "Admin"),
        ("staff", "Staff"),
    )
    role_name = models.CharField( max_length=100, unique=True )
    description = models.TextField( blank=True, null=True )
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    """ Dominic Code Start's """
    permissions = models.ManyToManyField("PermissionAccess.Permission", blank=True, related_name="user_roles", help_text="CRUD/page permissions granted to every user holding this role.")
    is_full_crud = models.BooleanField(default=True)
    """ Dominic Code End's """
    
    class Meta:
        db_table = "user_roles"

    def __str__(self):
        return self.role_name



class UserRoleAssignment(models.Model):
    user = models.ForeignKey( User, on_delete=models.CASCADE, related_name="role_assignments" )
    role = models.ForeignKey( UserRole, on_delete=models.CASCADE )
    start_date = models.DateField()
    end_date = models.DateField( blank=True, null=True )
    active = models.BooleanField(default=True)
    assigned_at = models.DateTimeField( auto_now_add=True )

    class Meta:
        db_table = "user_role_assignments"

    def __str__(self):
        return f"{self.user.username} - {self.role.role_name}"
    



class Firearm(models.Model):

    FIREARM_TYPE_CHOICES = [
        ("HANDGUN", "Handgun"),
        ("RIFLE", "Rifle"),
        ("SHOTGUN", "Shotgun"),
        ("TRAINING", "Training Firearm"),
        ("OTHER", "Other"),
    ]

    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("STORED", "Stored"),
        ("RETIRED", "Retired"),
        ("DISPOSED", "Disposed"),
    ]

    ACQUISITION_METHOD_CHOICES = [
        ("PURCHASE", "Purchase"),
        ("DONATION", "Donation"),
        ("TRANSFER", "Transfer"),
        ("OTHER", "Other"),
    ]

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    user = models.ForeignKey("Admin.User",on_delete=models.CASCADE,related_name="firearms",null=True,
    blank=True )

    firearm_name = models.CharField(max_length=150)
    firearm_type = models.CharField(max_length=30,choices=FIREARM_TYPE_CHOICES)
    manufacturer = models.CharField( max_length=150,blank=True, null=True)
    model_name = models.CharField( max_length=150, blank=True, null=True )
    serial_number = models.CharField( max_length=150, unique=True )
    caliber = models.CharField( max_length=50, blank=True, null=True)
    purchase_date = models.DateField( blank=True, null=True )
    acquisition_method = models.CharField(max_length=30, choices=ACQUISITION_METHOD_CHOICES, default="PURCHASE" )

    location_name = models.CharField( max_length=150, blank=True, null=True)
    building_name = models.CharField( max_length=150, blank=True, null=True)
    room_number = models.CharField( max_length=50, blank=True, null=True)
    security_level = models.CharField( max_length=100, blank=True, null=True)
    current_status = models.CharField( max_length=20,choices=STATUS_CHOICES,default="ACTIVE")

    notes = models.TextField(
        blank=True,
        null=True
    )
    is_full_crud = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "firearms"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.firearm_name} ({self.serial_number})"
    




from Admin.Jack.models import Athletic, Sport, SportTeamModel, Coach,SportClub ,SportsFacility


class OlympicAthlete(models.Model):

    OLYMPIC_STATUS = (
        ("PENDING", "Pending"),
        ("QUALIFIED", "Qualified"),
        ("SELECTED", "Selected"),
        ("PARTICIPATED", "Participated"),
        ("RETIRED", "Retired"),
    )

    QUALIFICATION_STATUS = (
        ("PENDING", "Pending"),
        ("QUALIFIED", "Qualified"),
        ("NOT_QUALIFIED", "Not Qualified"),
    )

    EVENT_CATEGORY = (
        ("INDIVIDUAL", "Individual"),
        ("TEAM", "Team"),
    )

    olympic_uuid = models.UUIDField(default=uuid.uuid4,editable=False,unique=True)
    athlete = models.OneToOneField(Athletic,on_delete=models.CASCADE,related_name="olympic_profile",null=True,blank=True)

    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, related_name="olympic_athletes", null=True, blank=True)
    team = models.ForeignKey(SportTeamModel, on_delete=models.SET_NULL, null=True,blank=True, related_name="olympic_players" )
    coach = models.ForeignKey( Coach, on_delete=models.SET_NULL, null=True, blank=True,related_name="olympic_athletes")
    athlete_number = models.CharField( max_length=30,unique=True)
    nationality = models.CharField( max_length=100 )
    olympic_status = models.CharField(max_length=20,choices=OLYMPIC_STATUS,default="PENDING")
    target_olympics = models.CharField( max_length=100)
    event_name = models.CharField(max_length=150)
    event_category = models.CharField(max_length=20,choices=EVENT_CATEGORY,default="INDIVIDUAL")
    governing_body = models.CharField( max_length=150)
    world_ranking = models.PositiveIntegerField(null=True, blank=True)
    qualification_date = models.DateField(null=True, blank=True)
    qualification_score = models.CharField( max_length=100, blank=True, null=True)
    qualification_standard = models.CharField( max_length=100, blank=True,null=True)
    qualification_status = models.CharField(max_length=30,choices=QUALIFICATION_STATUS,default="PENDING")
    personal_best = models.CharField(max_length=100,blank=True, null=True)
    biography = models.TextField(blank=True,null=True)
    profile_photo = models.ImageField(upload_to="olympics/athletes/",blank=True,null=True )
    is_active = models.BooleanField(default=True)
    is_full_crud = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.athlete.student.full_name} - {self.target_olympics}"
    


class OlympicPerformance(models.Model):

    COMPETITION_LEVEL = (
        ("STATE", "State"),
        ("NATIONAL", "National"),
        ("INTERNATIONAL", "International"),
        ("OLYMPICS", "  Olympics"),
    )

    MEDAL_CHOICES = (
        ("NONE", "No Medal"),
        ("GOLD", "Gold"),
        ("SILVER", "Silver"),
        ("BRONZE", "Bronze"),
    )

    PARTICIPATION_STATUS = (
        ("SCHEDULED", "Scheduled"),
        ("COMPLETED", "Completed"),
        ("WITHDRAWN", "Withdrawn"),
        ("DISQUALIFIED", "Disqualified"),
    )

    performance_uuid = models.UUIDField( default=uuid.uuid4, editable=False, unique=True )
    olympic_athlete = models.ForeignKey( OlympicAthlete, on_delete=models.CASCADE, related_name="performances", null=True, blank=True )
    competition_name = models.CharField( max_length=150)
    competition_level = models.CharField( max_length=20, choices=COMPETITION_LEVEL)
    event_name = models.CharField( max_length=150 )
    competition_date = models.DateField()
    host_city = models.CharField(max_length=100)
    host_country = models.CharField(max_length=100)
    score_time = models.CharField( max_length=100, blank=True, null=True)
    ranking = models.PositiveIntegerField( null=True, blank=True )
    medal = models.CharField( max_length=20, choices=MEDAL_CHOICES,default="NONE")
    participation_status = models.CharField( max_length=30,choices=PARTICIPATION_STATUS,default="SCHEDULED")
    remarks = models.TextField( blank=True, null=True)
    is_full_crud = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.competition_name} - {self.olympic_athlete}"


class Tournament(models.Model):

    TOURNAMENT_TYPE = (
        ("INTER_COLLEGE", "Inter College"),
        ("INTRA_COLLEGE", "Intra College"),
        ("INTER_DEPARTMENT", "Inter Department"),
        ("INTRA_DEPARTMENT", "Intra Department"),
        ("OPEN", "Open Tournament"),
    )

    PARTICIPATION_TYPE = (
        ("TEAM", "Team"),
        ("INDIVIDUAL", "Individual"),
    )

    STATUS_CHOICES = (
        ("INVITATION_SENT", "Invitation Sent"),
        ("REGISTRATION_OPEN", "Registration Open"),
        ("REGISTRATION_CLOSED", "Registration Closed"),
        ("VERIFICATION", "Participant Verification"),
        ("APPROVED", "Participants Approved"),
        ("FIXTURES_READY", "Fixtures Generated"),
        ("ONGOING", "Tournament Ongoing"),
        ("COMPLETED", "Completed"),
        ("ARCHIVED", "Archived"),
    )

    tournament_uuid = models.UUIDField(default=uuid.uuid4,
        editable=False,
        unique=True
    )
    tournament_name = models.CharField(max_length=200)
    tournament_code = models.CharField(max_length=30,unique=True)
    organizer = models.ForeignKey( User, on_delete=models.SET_NULL, null=True,related_name="organized_tournaments")
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE,related_name="tournaments")
    club = models.ForeignKey( SportClub, on_delete=models.SET_NULL, null=True, blank=True,related_name="tournaments" )
    venue = models.ForeignKey( SportsFacility,on_delete=models.SET_NULL, null=True,blank=True,related_name="tournaments")
    tournament_type = models.CharField(max_length=30, choices=TOURNAMENT_TYPE)
    participation_type = models.CharField( max_length=20,choices=PARTICIPATION_TYPE)
    banner = models.ImageField(
    upload_to="tournaments/banner/",blank=True, null=True)
    logo = models.ImageField(upload_to="tournaments/logo/", blank=True,null=True)
    description = models.TextField(blank=True)
    rules_pdf = models.FileField( upload_to="tournaments/rules/", blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    registration_deadline = models.DateField()
    minimum_participants = models.PositiveIntegerField(default=2,null=True,blank=True)
    maximum_participants = models.PositiveIntegerField(null=True,blank=True)
    entry_fee = models.DecimalField(max_digits=10,decimal_places=2,default=0)
    status = models.CharField(max_length=30,choices=STATUS_CHOICES,default="CREATED")
    winner = models.CharField( max_length=150,blank=True, null=True)
    runner_up = models.CharField(max_length=150, blank=True,null=True)
    is_active = models.BooleanField(default=True)
    is_full_crud = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class TournamentInvitation(models.Model):

    INVITATION_TYPE = (
        ("EMAIL", "Email"),
        ("DEPARTMENT", "Notification"),
    )

    APPLICATION_STATUS = (
        ("INVITED", "Invited"),
        ("APPLIED", "Applied"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    )

    invitation_uuid = models.UUIDField(default=uuid.uuid4,editable=False,unique=True)
    tournament = models.ForeignKey(Tournament,on_delete=models.CASCADE,related_name="invitations")
    invitation_type = models.CharField(max_length=20,choices=INVITATION_TYPE)
    college_name = models.CharField(max_length=200,blank=True,null=True)
    department_name = models.CharField(max_length=150, blank=True,null=True)
    contact_person = models.CharField(max_length=150,blank=True,null=True )
    email = models.EmailField()
    mobile_number = models.CharField(max_length=20, blank=True)
    receiver_faculty = models.ForeignKey(
        "Faculty.FacultyProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tournament_invitations",
    )
    invitation_token = models.UUIDField(default=uuid.uuid4,unique=True )
    application_status = models.CharField(max_length=20,choices=APPLICATION_STATUS,default="INVITED")
    applied_at = models.DateTimeField(blank=True, null=True )
    approved_at = models.DateTimeField(blank=True, null=True )
    invitation_sent_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True,null=True )
    is_full_crud = models.BooleanField(default=True)
    otp_hash = models.CharField(max_length=128, blank=True, null=True)
    otp_expires_at = models.DateTimeField(blank=True, null=True)
    otp_attempts = models.PositiveSmallIntegerField(default=0)
    otp_last_sent_at = models.DateTimeField(blank=True, null=True)




class TournamentParticipant(models.Model):

    PARTICIPANT_TYPE = (
        ("TEAM", "Team"),
        ("INDIVIDUAL", "Individual"),
    )

    RESULT = (
        ("PARTICIPATED", "Participated"),
        ("WINNER", "Winner"),
        ("RUNNER_UP", "Runner Up"),
        ("THIRD_PLACE", "Third Place"),
    )

    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name="participants"
    )

    invitation = models.OneToOneField(TournamentInvitation,on_delete=models.CASCADE,related_name="participant")
    internal_team = models.ForeignKey(SportTeamModel,on_delete=models.SET_NULL,null=True,blank=True)
    internal_athlete = models.ForeignKey(Athletic,on_delete=models.SET_NULL,null=True,blank=True)
    participant_name = models.CharField( max_length=200 )
    # college_name = models.CharField( max_length=200, blank=True, null=True)
    # coach_name = models.CharField(max_length=150, blank=True)
    team_name = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    college_name = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    coach_name = models.CharField(
        max_length=150,
        blank=True
    )
    players_count = models.PositiveIntegerField(default=1)
    final_position = models.PositiveIntegerField(blank=True,null=True )
    result = models.CharField(max_length=20,choices=RESULT, default="PARTICIPATED")
    score = models.CharField(max_length=100,blank=True,null=True)
    registered_at = models.DateTimeField(auto_now_add=True)
    is_full_crud = models.BooleanField(default=True)

class TournamentApplication(models.Model):

    STATUS_CHOICES = (
        ("APPLIED", "Applied"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    )

    application_uuid = models.UUIDField(default=uuid.uuid4,editable=False,unique=True )
    tournament = models.ForeignKey(Tournament,on_delete=models.CASCADE,related_name="applications")
    invitation = models.OneToOneField(TournamentInvitation,on_delete=models.CASCADE,related_name="application")
    applicant_faculty = models.ForeignKey("Faculty.FacultyProfile",on_delete=models.SET_NULL,null=True,blank=True,related_name="tournament_applications")
    participant = models.OneToOneField(TournamentParticipant,on_delete=models.SET_NULL,null=True,blank=True,related_name="application")
    entry_name = models.CharField(max_length=200)
    coach_name = models.CharField( max_length=150,blank=True)
    contact_person = models.CharField(max_length=150,blank=True )
    contact_mobile = models.CharField( max_length=20, blank=True)
    players_count = models.PositiveIntegerField(default=1)
    players = models.JSONField(default=list,blank=True)
    faculty_remarks = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20,choices=STATUS_CHOICES, default="APPLIED")
    admin_remarks = models.TextField( blank=True, null=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField( blank=True, null=True)
    reviewed_by = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True,related_name="reviewed_tournament_applications")
    is_full_crud = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    internal_team = models.ForeignKey(
        SportTeamModel, null=True, blank=True, on_delete=models.SET_NULL
    )
    team_name = models.CharField(max_length=200, blank=True, default="",null=True)





    


# <--------------------Blaze code start (13.08.26)------------------------>

import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


class Hostel(models.Model):
    """Hostel/Residence Hall Model"""
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('MAINTENANCE', 'Under Maintenance'),
    )
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=100, help_text="Hostel name (e.g., Witte Hall)")
    code = models.CharField(max_length=20, unique=True, help_text="Hostel code (e.g., WH)")
    address = models.TextField(blank=True, null=True)
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    total_rooms = models.IntegerField(default=0)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')

    GENDER_CHOICES = (
        ('ANY', 'Co-ed / Any'),
        ('MALE', 'Male Only'),
        ('FEMALE', 'Female Only'),
    )
    gender_restriction = models.CharField(
        max_length=10, choices=GENDER_CHOICES, default='ANY',
        help_text="Used to warn when a student's gender doesn't match this hostel's eligibility"
    )

    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        help_text="Latitude for map display (e.g., 43.076592)"
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        help_text="Longitude for map display (e.g., -89.401230)"
    )

    total_floors = models.PositiveIntegerField(
        default=1, help_text="Total number of floors in this hostel"
    )
    image = models.ImageField(
        upload_to='hostel_images/', blank=True, null=True, help_text="Cover photo of the hostel"
    )

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='hostels_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = 'hostels'
        ordering = ['name']

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.name[:3].upper()
        super().save(*args, **kwargs)

    def can_delete(self):
        """Check if hostel can be deleted (no rooms with occupants)"""
        # Check if any room in this hostel has active allocations
        has_occupied_rooms = Room.objects.filter(
            hostel=self,
            status='OCCUPIED'
        ).exists()
        
        # Check if any room has active allocations
        has_active_allocations = RoomAllocation.objects.filter(
            room__hostel=self,
            status='ACTIVE'
        ).exists()
        
        return not (has_occupied_rooms or has_active_allocations)

    def get_occupied_rooms_count(self):
        """Get number of occupied rooms in this hostel"""
        return Room.objects.filter(hostel=self, status='OCCUPIED').count()

    def get_students_count(self):
        """Get total number of students allocated to this hostel"""
        return RoomAllocation.objects.filter(
            room__hostel=self,
            status='ACTIVE'
        ).values('student').distinct().count()


class Room(models.Model):
    """Room within a Hostel"""
    STATUS_CHOICES = (
        ('AVAILABLE', 'Available'),
        ('OCCUPIED', 'Occupied'),
        ('MAINTENANCE', 'Under Maintenance'),
        ('RESERVED', 'Reserved'),
    )
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    hostel = models.ForeignKey(
        Hostel, on_delete=models.CASCADE, related_name='rooms'
    )
    room_number = models.CharField(max_length=10)
    floor = models.IntegerField(default=1)
    capacity = models.IntegerField(default=2)
    current_occupancy = models.IntegerField(default=0)
    amenities = models.TextField(blank=True, null=True, help_text="Wi-Fi, AC, Laundry, etc.")
    rent_per_month = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    image = models.ImageField(
        upload_to='room_images/', blank=True, null=True, help_text="Photo of the room"
    )
    is_available = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='rooms_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = 'rooms'
        unique_together = ['hostel', 'room_number']
        ordering = ['hostel', 'room_number']

    def __str__(self):
        return f"{self.hostel.name} - Room {self.room_number}"

    def save(self, *args, **kwargs):
        try:
            capacity = int(self.capacity) if self.capacity is not None else 0
            occupancy = int(self.current_occupancy) if self.current_occupancy is not None else 0
            
            if capacity > 0 and occupancy >= capacity:
                self.is_available = False
                self.status = 'OCCUPIED'
            else:
                self.is_available = True
                if self.status == 'OCCUPIED':
                    self.status = 'AVAILABLE'
        except (ValueError, TypeError):
            pass
        
        super().save(*args, **kwargs)


class RoomAllocation(models.Model):
    """Student Room Allocation"""
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('PENDING', 'Pending'),
        ('EXPIRED', 'Expired'),
    )
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='allocations'
    )
    room = models.ForeignKey(
        Room, on_delete=models.CASCADE, related_name='allocations'
    )
    allocated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='allocations_made'
    )
    allocated_date = models.DateTimeField(auto_now_add=True)
    move_in_date = models.DateField()
    move_out_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    remarks = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = 'room_allocations'
        ordering = ['-allocated_date']

    def __str__(self):
        return f"{self.student.full_name} - {self.room.room_number}"


class HostelAuditLog(models.Model):
    """Audit log for hostel operations"""
    ACTION_CHOICES = (
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('ALLOCATE', 'Allocate'),
        ('DEALLOCATE', 'Deallocate'),
        ('MOVE', 'Move'),
    )
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='hostel_audit_logs'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    module = models.CharField(max_length=50, default='HOSTEL')
    object_type = models.CharField(max_length=50)
    object_id = models.IntegerField()
    changes = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = 'hostel_audit_logs'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.username if self.user else 'System'} - {self.action} - {self.module}"
             

    # <--------------------Blaze code start (13.08.26)------------------------>
        