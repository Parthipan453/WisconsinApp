from django.db import models
import uuid
from Admin.models import User
from Students.models import StudentProfile
from Faculty.models import FacultyProfile
from Staff.models import StaffProfile
from Admin.Jack.models import Athletic, Sport
from Medical.Dominic.models import *
from Medical.Alan.models import *
from Admin.bela_admin.models import Room
from datetime import datetime as _dt
from Medical.Alan.models import MedicalCenter
from Medical.models import Facility

################ Guru Code Start ####################

class TimeStampedModel(models.Model):

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    is_active = models.BooleanField(default=True)

    is_full_crud = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class EmergencyStampModel(models.Model):

    emergency_contact_name = models.CharField(
        max_length=100,
        blank=True
    )

    emergency_contact_phone = models.CharField(
        max_length=20,
        blank=True
    )

    class Meta:
        abstract = True


# ---------------- Medical Department ---------------- #

class MedicalDepartment(TimeStampedModel):

    department_code = models.CharField(
        max_length=20,
        unique=True
    )
 
    department_name = models.CharField(
        max_length=100,
        unique=True
    )

    short_name = models.CharField(
        max_length=20,
        blank=True
    )

    department_type = models.CharField(
        max_length=150,
    )

    description = models.TextField(
        blank=True
    )

    location = models.CharField(
        max_length=150
    )

    phone = models.CharField(
        max_length=20,
        blank=True
    )

    email = models.EmailField(
        blank=True
    )

    opening_time = models.TimeField()

    closing_time = models.TimeField()

    is_emergency = models.BooleanField(
        default=False
    )

    """ Dominic Code Start's """
    hospitals = models.ManyToManyField(
        "Medical.MedicalCenter",
        related_name="departments",
        blank=True,
        help_text=(
            "Hospitals where this department is directly available. Optional — "
            "leave empty and the department will still show up for a hospital "
            "once a staff member is assigned there (old behavior, unaffected)."
        ),
    )
    """ Dominic Code End's """

    shared_with_user_roles = models.BooleanField(
            default=True,
            help_text=(
                "Only meaningful when app_label is 'Medical'. When True, this "
                "model's CRUD permissions also show up (and can be granted) in "
                "the Organization Roles tab, not just Medical Roles. Mirrors the "
                "source model's own `shared_with_user_roles` flag — set it as a "
                "field on the model (see signals.py), not here."
            ),
        )

    class Meta:
        db_table = "medical_department"
        ordering = ["department_name"]


    def __str__(self):
        return self.department_name


# ---------------- Medical Staff Profile ---------------- #

class MedicalStaffProfile(TimeStampedModel, EmergencyStampModel):

    EMPLOYMENT_TYPES = [
        ("FULL_TIME", "Full Time"),
        ("PART_TIME", "Part Time"),
        ("CONTRACT", "Contract"),
        ("VISITING", "Visiting Consultant"),
    ]

    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("ON_LEAVE", "On Leave"),
        ("OFF_DUTY", "Off Duty"),
        ("RETIRED", "Retired"),
    ]

    employee_id = models.CharField(max_length=20, unique=True)

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="medical_staff_profile"
    )

    department = models.ForeignKey(
        MedicalDepartment,
        on_delete=models.CASCADE,
        related_name="staff_members"
    )
    
    """ Dominic Code Start's """
    hospital = models.ForeignKey(
        MedicalCenter,
        on_delete=models.PROTECT,
        related_name="medical_staff",
        null=True,
        blank=True,
    )
    """ Dominic Code End's """

    # Contact
    work_email = models.EmailField(unique=True)

    personal_email = models.EmailField(blank=True, null=True)

    phone = models.CharField(max_length=20)

    address = models.TextField(blank=True)

    # Preferred name
    preferred_name = models.CharField(max_length=100, blank=True, null=True)

    """ Dominic's Update Code Start's """
    role = models.ForeignKey(MedicalStaffRole, on_delete=models.PROTECT, related_name="staff_members")
    """ Dominic's Update Code End's """

    qualification = models.CharField(max_length=150)

    specialization = models.CharField(max_length=150, blank=True)

    medical_license_number = models.CharField(
        max_length=100,
        blank=True
    )

    years_of_experience = models.PositiveIntegerField(default=0)

    hire_date = models.DateField()

    employment_type = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_TYPES,
        default="FULL_TIME"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE"
    )
    
    """ Dominic Code Start's """
    shared_with_user_roles = models.BooleanField(
        default=True,
        help_text=(
            "Only meaningful when app_label is 'Medical'. When True, this "
            "model's CRUD permissions also show up (and can be granted) in "
            "the Organization Roles tab, not just Medical Roles. Mirrors the "
            "source model's own `shared_with_user_roles` flag — set it as a "
            "field on the model (see signals.py), not here."
        ),
    ) 
    
    is_senior = models.BooleanField(
        default=False,
        help_text="Marks this staff member as senior. Senior staff appear as reporting-staff options for their juniors.",
    )

    reporting_to = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="direct_reports",
        help_text="Senior staff this person reports to. Left blank for senior doctors — they report directly to the hospital director instead.",
    )

    work_facilities = models.ManyToManyField(
        Facility,
        blank=True,
        related_name="assigned_staff",
        help_text="Hospital facilities this staff member primarily works in.",
    )
    """ Dominic Code End's """

    class Meta:
        db_table = "medical_staff_profile"

    def __str__(self):
        return f"{self.user} ({self.role})"


# ---------------- Patient Profile ---------------- #

class PatientProfile(TimeStampedModel, EmergencyStampModel):

    PATIENT_TYPES = [
        ("STUDENT", "Student"),
        ("FACULTY", "Faculty"),
        ("STAFF", "Staff"),
        ("ADMIN", "Admin"),
        ("VISITOR", "Visitor"),
    ]

    BLOOD_GROUPS = [
        ("A+", "A+"),
        ("A-", "A-"),
        ("B+", "B+"),
        ("B-", "B-"),
        ("AB+", "AB+"),
        ("AB-", "AB-"),
        ("O+", "O+"),
        ("O-", "O-"),
    ]

    patient_number = models.CharField(
        max_length=20,
        unique=True
    )

    patient_type = models.CharField(
        max_length=20,
        choices=PATIENT_TYPES
    )

    student = models.OneToOneField(
        StudentProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="patient_student_profile"
    )

    staff = models.OneToOneField(
        StaffProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="patient_staff_profile"
    )

    faculty = models.OneToOneField(
        FacultyProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="patient_faculty_profile"
    )
    ########## swetha's code start ###################

    admin = models.OneToOneField(User,on_delete=models.CASCADE,
            null=True,
            blank=True,
            related_name="patient_admin_profile",
            limit_choices_to={"is_admin": True},)

    visitor_name = models.CharField(
        max_length=150,
        blank=True)

    visitor_gender = models.CharField(
        max_length=20,
        blank=True)

    visitor_phone = models.CharField(
        max_length=20,
        blank=True)

    visitor_email = models.EmailField(
        blank=True)

    visitor_date_of_birth = models.DateField(
        null=True,
        blank=True)

    visitor_address = models.TextField(
        blank=True,
        null=True,)

    ########## swetha's code end ###################

    blood_group = models.CharField(
        max_length=5,
        choices=BLOOD_GROUPS,
        blank=True
    )

    allergies = models.TextField(blank=True)

    chronic_conditions = models.TextField(blank=True)

    remarks = models.TextField(blank=True)

    class Meta:
        db_table = "medical_patient_profile"

    def __str__(self):
        if self.student:
            return f"{self.student}"
        elif self.staff:
            return f"{self.staff}"
        elif self.faculty:
            return f"{self.faculty}"
        elif self.admin:
           return self.admin.full_name

        return self.visitor_name


    @property
    def patient_name(self):
        import re

        def _clean(value):
            if not value:
                return value
            return re.sub(r'\s*\([^)]*\)\s*$', '', str(value)).strip()

        try:
            if self.student:
                return _clean(getattr(self.student, 'full_name', None) or str(self.student))
            if self.staff:
                return _clean(getattr(self.staff, 'full_name', None) or str(self.staff))
            if self.faculty:
                return _clean(getattr(self.faculty, 'full_name', None) or str(self.faculty))
            if self.admin:
                return _clean(getattr(self.admin, 'full_name', None) or str(self.admin))
        except Exception:
            pass
        return self.visitor_name or '—'


# ---------------- Athlete Medical Profile ---------------- #

class AthleteMedicalProfile(TimeStampedModel, EmergencyStampModel):

    MEDICAL_CLEARANCE_STATUS = [
        ("NOT SELECTED", "Not selected"),
        ("FIT", "Fit to Play"),
        ("LIMITED", "Limited Participation"),
        ("REHAB", "Under Rehabilitation"),
        ("NOT_FIT", "Not Fit to Play"),
    ]

    FITNESS_LEVELS = [
        ("NOT SELECTED", "Not selected"),
        ("EXCELLENT", "Excellent"),
        ("GOOD", "Good"),
        ("AVERAGE", "Average"),
        ("POOR", "Poor"),
    ]

    INJURY_RISK = [
        ("NOT SELECTED", "Not selected"),
        ("LOW", "Low"),
        ("MEDIUM", "Medium"),
        ("HIGH", "High"),
    ]

    athlete_medical_id = models.CharField(
        max_length=20,
        unique=True)

    athlete = models.OneToOneField(
        Athletic,
        on_delete=models.CASCADE,
        related_name="medical_profile"
    )

    patient_profile = models.OneToOneField(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name="athlete_profile",
        null=True,
        blank=True
    )

    primary_sport = models.ForeignKey(
        Sport,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    medical_clearance_status = models.CharField(
        max_length=20,
        choices=MEDICAL_CLEARANCE_STATUS,
        default="NOT SELECTED"
    )

    clearance_date = models.DateField(null=True, blank=True)

    clearance_expiry = models.DateField(null=True, blank=True)

    fitness_level = models.CharField(
        max_length=20,
        choices=FITNESS_LEVELS,
        default="NOT SELECTED"
    )

    injury_risk = models.CharField(
        max_length=20,
        choices=INJURY_RISK,
        default="NOT SELECTED"
    )

    previous_injuries = models.TextField(blank=True)

    current_medical_restrictions = models.TextField(blank=True)

    emergency_action_plan = models.TextField(blank=True)

    team_physician = models.ForeignKey(
        MedicalStaffProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_athletes_as_doctor"
    )

    physiotherapist = models.ForeignKey(
        MedicalStaffProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_athletes_as_physio"
    )

    last_medical_checkup = models.DateField(null=True, blank=True)

    next_medical_checkup = models.DateField(null=True, blank=True)

    notes = models.TextField(blank=True)

    class Meta:
        db_table = "athlete_medical_profile"

    def __str__(self):
        return f"{self.athlete} Medical Profile"


# ---------------- Injury Record ---------------- #

class InjuryRecord(TimeStampedModel):

    SIDE_CHOICES = [
        ("LEFT", "Left"),
        ("RIGHT", "Right"),
        ("BOTH", "Both"),
        ("CENTER", "Center"),
    ]

    SEVERITY_CHOICES = [
        ("MINOR", "Minor"),
        ("MODERATE", "Moderate"),
        ("SEVERE", "Severe"),
        ("CRITICAL", "Critical"),
    ]

    INJURY_STATUS = [
        ("ACTIVE", "Under Treatment"),
        ("RECOVERING", "Recovering"),
        ("REHABILITATION", "Rehabilitation"),
        ("RECOVERED", "Recovered"),
        ("RETURNED", "Returned to Sport"),
    ]

    medical_profile = models.ForeignKey(
        AthleteMedicalProfile,
        on_delete=models.CASCADE,
        related_name="injury_records"
    )

    injury_title = models.CharField(max_length=150)

    injury_type = models.CharField(
        max_length=150,
    )

    body_part = models.CharField(
        max_length=150,
    )

    side = models.CharField(
        max_length=10,
        choices=SIDE_CHOICES,
        blank=True
    )

    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES
    )

    cause = models.CharField(
        max_length=150,
        blank=True
    )

    injury_date = models.DateField()

    injury_time = models.TimeField(
        null=True,
        blank=True
    )

    location = models.CharField(
        max_length=150,
        blank=True
    )

    symptoms = models.TextField(blank=True)

    diagnosis = models.TextField(blank=True)

    treatment = models.TextField(blank=True)

    treated_by = models.ForeignKey(
        MedicalStaffProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    hospitalization_required = models.BooleanField(default=False)

    surgery_required = models.BooleanField(default=False)

    estimated_recovery_days = models.PositiveIntegerField(
        default=0
    )

    expected_return_date = models.DateField(
        null=True,
        blank=True
    )

    actual_return_date = models.DateField(
        null=True,
        blank=True
    )

    injury_status = models.CharField(
        max_length=20,
        choices=INJURY_STATUS,
        default="ACTIVE"
    )

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-injury_date"]

    def __str__(self):
        return f"{self.medical_profile} - {self.injury_title}"


# ---------------- Medical Visit ---------------- #

class MedicalVisit(TimeStampedModel):

    VISIT_TYPES = [
        ("CONSULTATION", "Consultation"),
        ("FOLLOW_UP", "Follow-up"),
        ("EMERGENCY", "Emergency"),
        ("INJURY", "Sports Injury"),
        ("HEALTH_CHECK", "Routine Health Check"),
        ("VACCINATION", "Vaccination"),
    ]

    VISIT_STATUS = [
        ("OPEN", "Open"),
        ("COMPLETED", "Completed"),
        ("REFERRED", "Referred"),
        ("CANCELLED", "Cancelled"),
    ]

    visit_number = models.CharField(
        max_length=20,
        unique=True
    )

    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name="medical_visits"
    )

    athlete_profile = models.ForeignKey(
        AthleteMedicalProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="medical_visits"
    )

    injury_record = models.ForeignKey(
        InjuryRecord,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="medical_visits"
    )

    attending_staff = models.ForeignKey(
        MedicalStaffProfile,
        on_delete=models.CASCADE,
        related_name="medical_visits"
    )

    department = models.ForeignKey(
        MedicalDepartment,
        on_delete=models.CASCADE,
        related_name="medical_visits"
    )

    visit_type = models.CharField(
        max_length=20,
        choices=VISIT_TYPES,
        default="CONSULTATION"
    )

    visit_date = models.DateField()

    visit_time = models.TimeField()

    chief_complaint = models.TextField()

    diagnosis = models.TextField(blank=True)

    treatment = models.TextField(blank=True)

    medications = models.TextField(blank=True)

    follow_up_required = models.BooleanField(default=False)

    follow_up_date = models.DateField(
        null=True,
        blank=True
    )

    visit_status = models.CharField(
        max_length=20,
        choices=VISIT_STATUS,
        default="OPEN"
    )

    notes = models.TextField(blank=True)

    class Meta:
        db_table = "medical_visit"
        ordering = ["-visit_date", "-visit_time"]

    def __str__(self):
        return f"{self.visit_number} - {self.patient}"

# ---------------- Medical Service ---------------- #

class MedicalService(TimeStampedModel):

    SERVICE_CATEGORIES = [
        ("CONSULTATION", "Consultation"),
        ("EMERGENCY", "Emergency"),
        ("SPORTS", "Sports Medicine"),
        ("PHYSIOTHERAPY", "Physiotherapy"),
        ("LABORATORY", "Laboratory"),
        ("DENTAL", "Dental"),
        ("MENTAL_HEALTH", "Mental Health"),
        ("VACCINATION", "Vaccination"),
        ("CERTIFICATION", "Medical Certification"),
    ]

    service_code = models.CharField(
        max_length=20,
        unique=True
    )

    department = models.ForeignKey(
        MedicalDepartment,
        on_delete=models.CASCADE,
        related_name="services"
    )

    service_name = models.CharField(
        max_length=150,
        unique=True
    )

    service_category = models.CharField(
        max_length=30,
        choices=SERVICE_CATEGORIES
    )

    description = models.TextField(blank=True)

    estimated_duration = models.PositiveIntegerField(
        help_text="Duration in minutes"
    )

    requires_appointment = models.BooleanField(default=True)

    available_for_athletes = models.BooleanField(default=True)

    available_for_students = models.BooleanField(default=True)

    available_for_staff = models.BooleanField(default=True)

    available_for_faculty = models.BooleanField(default=True)

    is_emergency_service = models.BooleanField(default=False)

    notes = models.TextField(blank=True)

    class Meta:
        db_table = "medical_service"
        ordering = ["service_name"]

    def __str__(self):
        return self.service_name


# ---------------- Medical Appointment ---------------- #
class Appointment(TimeStampedModel):
 
    PRIORITY_CHOICES = [
        ("LOW", "Low"),
        ("NORMAL", "Normal"),
        ("HIGH", "High"),
        ("EMERGENCY", "Emergency"),
    ]
 
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("CONFIRMED", "Confirmed"),
        ("ARRIVED", "Arrived"),
        ("CHECKED_IN", "Checked In"),
        ("IN_PROGRESS", "In Progress"),
        ("COMPLETED", "Completed"),
        ("ADMITTED", "Admitted"),
        ("CANCELLED", "Cancelled"),
        ("NOT_ARRIVED", "Not Arrived"),
    ]
 
    appointment_number = models.CharField(
        max_length=20,
        unique=True
    )
 
    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="appointments"
    )

    athlete = models.ForeignKey(
        AthleteMedicalProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="appointments"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="appointments"
    )
 
    medical_staff = models.ForeignKey(
        MedicalStaffProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="appointments"
    )
    hospital = models.ForeignKey(
        MedicalCenter,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="appointments"
    )
    service = models.CharField(
        max_length=100
    )
 
    appointment_date = models.DateField()
 
    appointment_time = models.TimeField(  null=True,blank=True)
 
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default="NORMAL"
    )
 
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING"
    )
 
    reason = models.TextField()
 
    cancellation_reason = models.TextField(
        blank=True
    )
 
    checked_in_at = models.DateTimeField(
        null=True,
        blank=True
    )
 
    completed_at = models.DateTimeField(
        null=True,
        blank=True
    )
 
    notes = models.TextField(
        blank=True
    )
 
    class Meta:
        db_table = "medical_appointment"
        ordering = [
            "appointment_date",
            "appointment_time"
        ]
 
    def __str__(self):
        return self.appointment_number

# ---------------- Patient Registry ---------------- #

class PatientRegistry(TimeStampedModel):

    PATIENT_TYPES = [
        ("STUDENT", "Student"),
        ("ATHLETE", "Athlete"),
        ("FACULTY", "Faculty"),
        ("STAFF", "Staff"),
    ]

    patient_number = models.CharField(
        max_length=20,
        unique=True
    )

    patient_type = models.CharField(
        max_length=20,
        choices=PATIENT_TYPES
    )

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="patient_records"
    )

    athlete = models.ForeignKey(
        Athletic,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="patient_records"
    )

    staff = models.ForeignKey(
        StaffProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="patient_records"
    )

    faculty = models.ForeignKey(
        FacultyProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="patient_records"
    )

    # Only for visitors
    first_name = models.CharField(
        max_length=50,
        blank=True
    )

    last_name = models.CharField(
        max_length=50,
        blank=True
    )

    gender = models.CharField(
        max_length=20,
        blank=True
    )

    date_of_birth = models.DateField(
        null=True,
        blank=True
    )

    registration_date = models.DateField(
        auto_now_add=True
    )

    notes = models.TextField(
        blank=True
    )


    class Meta:
        db_table = "patient_registry"
        ordering = ["patient_number"]

    def __str__(self):
        if self.student:
            return f"{self.patient_number} - {self.student}"
        if self.athlete:
            return f"{self.patient_number} - {self.athlete}"
        if self.staff:
            return f"{self.patient_number} - {self.staff}"
        if self.faculty:
            return f"{self.patient_number} - {self.faculty}"
        return f"{self.patient_number} - {self.first_name} {self.last_name}"


# ---------------- Shift (Template - no staff attached) ---------------- #

""" Dominic Code Start's """
class Shift(TimeStampedModel):
    RECURRENCE_CHOICES = [
        ("DAILY", "Daily (Single Date)"),
        ("WEEKLY", "Weekly (Full Week)"),
        ("MONTHLY", "Monthly (Full Month)"),
    ]

    SHIFT_LABEL_CHOICES = [
        ("MORNING", "Morning"),
        ("AFTERNOON", "Afternoon"),
        ("EVENING", "Evening"),
        ("NIGHT", "Night"),
    ]

    WEEKDAY_CHOICES = [
        ("MON", "Monday"),
        ("TUE", "Tuesday"),
        ("WED", "Wednesday"),
        ("THU", "Thursday"),
        ("FRI", "Friday"),
        ("SAT", "Saturday"),
        ("SUN", "Sunday"),
    ]

    department = models.ForeignKey(MedicalDepartment, on_delete=models.CASCADE, related_name="shifts")
    hospital = models.ForeignKey(MedicalCenter, on_delete=models.PROTECT, related_name="shifts", null=True, blank=True, help_text="Which hospital this shift belongs to. Needed since the same department name can exist across multiplhospitals.")
    shift_label = models.CharField( max_length=60, help_text="Name this shift yourself, e.g. 'Morning Rounds', 'ICU Night Cover', 'Weekend OPD'.")
    shift_type = models.CharField(max_length=20, choices=SHIFT_LABEL_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    recurrence_type = models.CharField( max_length=10, choices=RECURRENCE_CHOICES, default="DAILY")
    start_date = models.DateField(help_text="Anchor date. For WEEKLY this becomes the Monday of that week; for MONTHLY the 1st of that month.")
    end_date = models.DateField(editable=False, help_text="Auto-calculated from recurrence_type.")
    weekday_pattern = models.CharField(max_length=30, default="MON,TUE,WED,THU,FRI,SAT,SUN", help_text="Comma-separated active weekdays within the range. Only meaningful for WEEKLY/MONTHLY.")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_shifts")
    
    shared_with_user_roles = models.BooleanField(
        default=True,
        help_text=(
            "Only meaningful when app_label is 'Medical'. When True, this "
            "model's CRUD permissions also show up (and can be granted) in "
            "the Organization Roles tab, not just Medical Roles. Mirrors the "
            "source model's own `shared_with_user_roles` flag — set it as a "
            "field on the model (see signals.py), not here."
        ),
    )

    class Meta:
        db_table = "medical_shift"
        ordering = ["-start_date", "start_time"]

    def active_weekdays(self):
        return [d for d in self.weekday_pattern.split(",") if d]
    
    def time_bucket(self):
        hour = self.start_time.hour if self.start_time else 0
        if hour < 12:
            return "morning"
        elif hour < 16:
            return "afternoon"
        elif hour < 20:
            return "evening"
        return "night"

    def get_active_dates(self):
        from datetime import timedelta
        weekday_map = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
        active_codes = set(self.active_weekdays())
        dates = []
        current = self.start_date
        while current <= self.end_date:
            if weekday_map[current.weekday()] in active_codes:
                dates.append(current)
            current += timedelta(days=1)
        return dates

    def clean(self):
        from django.core.exceptions import ValidationError
        from calendar import monthrange
        from datetime import timedelta

        if not self.start_date:
            raise ValidationError({"start_date": "Start date is required."})

        if self.recurrence_type == "DAILY":
            self.end_date = self.start_date
            self.weekday_pattern = "MON,TUE,WED,THU,FRI,SAT,SUN"

        elif self.recurrence_type == "WEEKLY":
            monday = self.start_date - timedelta(days=self.start_date.weekday())
            self.start_date = monday
            self.end_date = monday + timedelta(days=6)

        elif self.recurrence_type == "MONTHLY":
            first_day = self.start_date.replace(day=1)
            last_day_num = monthrange(first_day.year, first_day.month)[1]
            self.start_date = first_day
            self.end_date = first_day.replace(day=last_day_num)

        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValidationError({"end_time": "End time must be after start time."})

        if not self.active_weekdays():
            raise ValidationError({"weekday_pattern": "Select at least one active weekday."})

        if self.hospital_id and self.start_time and self.end_time:
            working_hours = self.hospital.working_hours or {}
            schedule = working_hours.get("weekly_schedule", {})
            overrides = working_hours.get("overrides", {})
            
            for active_date in self.get_active_dates():
                window = self._resolve_working_window(schedule, overrides, active_date)

                if window["closed"]:
                    raise ValidationError(
                        f"{active_date.isoformat()} is marked as a holiday/closed for this hospital."
                    )
                if not window["enabled"]:
                    raise ValidationError({
                        "weekday_pattern": f"{window['weekday_label']} is not a working day for this hospital."
                    })

                opening, closing = window["opening"], window["closing"]
                hours_label = (
                    f"the hospital's modified hours for {active_date.isoformat()}"
                    if window["is_override"] else f"{window['weekday_label']}'s hospital hours"
                )
                if opening and self.start_time < _dt.strptime(opening, "%H:%M").time():
                    raise ValidationError({
                        "start_time": f"Shift starts before {hours_label} opening time ({opening})."
                    })
                if closing and self.end_time > _dt.strptime(closing, "%H:%M").time():
                    raise ValidationError({
                        "end_time": f"Shift ends after {hours_label} closing time ({closing})."
                    })

    @staticmethod
    def _resolve_working_window(schedule, overrides, date):
        weekday_to_key = {
            0: "monday", 1: "tuesday", 2: "wednesday", 3: "thursday",
            4: "friday", 5: "saturday", 6: "sunday",
        }
        key = weekday_to_key[date.weekday()]
        day_hours = schedule.get(key) or {}
        override = overrides.get(date.isoformat())

        if override and override.get("closed"):
            return {
                "closed": True, "enabled": False, "opening": None, "closing": None,
                "is_override": True, "weekday_label": key.title(),
            }

        if override:
            return {
                "closed": False,
                "enabled": True,
                "opening": override.get("opening") or day_hours.get("opening"),
                "closing": override.get("closing") or day_hours.get("closing"),
                "is_override": True,
                "weekday_label": key.title(),
            }

        return {
            "closed": False,
            "enabled": bool(day_hours.get("enabled")),
            "opening": day_hours.get("opening"),
            "closing": day_hours.get("closing"),
            "is_override": False,
            "weekday_label": key.title(),
        }

    def hospital_hours_conflicts(self):
        conflicts = []
        if not (self.hospital_id and self.start_time and self.end_time):
            return conflicts

        working_hours = self.hospital.working_hours or {}
        schedule = working_hours.get("weekly_schedule", {})
        overrides = working_hours.get("overrides", {})

        for active_date in self.get_active_dates():
            window = self._resolve_working_window(schedule, overrides, active_date)

            if window["closed"]:
                conflicts.append(f"{active_date.isoformat()} is now a holiday/closed for this hospital.")
                continue
            if not window["enabled"]:
                conflicts.append(f"{window['weekday_label']} is no longer a working day for this hospital.")
                continue

            opening, closing = window["opening"], window["closing"]
            if opening and self.start_time < _dt.strptime(opening, "%H:%M").time():
                conflicts.append(f"{active_date.isoformat()}: shift starts before current opening time ({opening}).")
            if closing and self.end_time > _dt.strptime(closing, "%H:%M").time():
                conflicts.append(f"{active_date.isoformat()}: shift ends after current closing time ({closing}).")

        seen, unique = set(), []
        for msg in conflicts:
            if msg not in seen:
                seen.add(msg)
                unique.append(msg)
        return unique

    def has_hospital_hours_conflict(self):
        return bool(self.hospital_hours_conflicts())

    def color_class(self):
        if not self.shift_label:
            return "c1"
        idx = sum(ord(ch) for ch in self.shift_label) % 6
        return f"c{idx + 1}"

    def __str__(self):
        hospital_part = f" @ {self.hospital.hospital_name}" if self.hospital_id else ""
        return f"{self.shift_label} - {self.department.department_name}{hospital_part} ({self.start_date} to {self.end_date})"

class ShiftAssignment(TimeStampedModel):
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name="assignments")
    medical_staff = models.ForeignKey(MedicalStaffProfile, on_delete=models.CASCADE, related_name="shift_assignments")
    room = models.ForeignKey(
        Room, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="shift_assignments",
        help_text="Which room this staff member is covering for this shift assignment.",
    )
    assignment_start_date = models.DateField(help_text="Defaults to the shift's full start date unless coverage is split.")
    assignment_end_date = models.DateField(help_text="Defaults to the shift's full end date unless coverage is split.")
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_shift_assignments")
    is_full_crud = models.BooleanField(default=True)
    shared_with_user_roles = models.BooleanField(
        default=True,
        help_text=(
            "Only meaningful when app_label is 'Medical'. When True, this "
            "model's CRUD permissions also show up (and can be granted) in "
            "the Organization Roles tab, not just Medical Roles. Mirrors the "
            "source model's own `shared_with_user_roles` flag — set it as a "
            "field on the model (see signals.py), not here."
        ),
    )

    class Meta:
        db_table = "medical_shift_assignment"
        ordering = ["assignment_start_date"]
        unique_together = ("shift", "medical_staff")

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.assignment_start_date and self.assignment_end_date:
            if self.assignment_start_date > self.assignment_end_date:
                raise ValidationError({"assignment_end_date": "End date must be on or after start date."})

        if self.shift_id:
            if self.assignment_start_date < self.shift.start_date or self.assignment_end_date > self.shift.end_date:
                raise ValidationError("Assignment dates must fall within the shift's own date range.")

    def __str__(self):
        return f"{self.medical_staff} -> {self.shift} ({self.assignment_start_date} to {self.assignment_end_date})"

class DailyNote(TimeStampedModel):
    REMINDER_CHOICES = [
        (5, "5 minutes before"),
        (10, "10 minutes before"),
        (15, "15 minutes before"),
        (30, "30 minutes before"),
    ]

    staff = models.ForeignKey(MedicalStaffProfile, on_delete=models.CASCADE, related_name="daily_notes")
    date = models.DateField(help_text="Calendar date this note belongs to.")
    note_text = models.TextField(max_length=500)
    event_time = models.TimeField(null=True, blank=True, help_text="Time of day this note refers to (e.g. a meeting at 2:00 PM). Required only if a reminder is set.")
    reminder_offset_minutes = models.PositiveSmallIntegerField( choices=REMINDER_CHOICES, null=True, blank=True, help_text="How many minutes before event_time to notify the staff member. Leave blank for a note with no reminder.")
    reminder_sent = models.BooleanField(default=False, help_text="Set True once the reminder notification has fired, to avoid duplicates.")
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "medical_daily_note"
        ordering = ["date"]
        unique_together = ("staff", "date")

    def __str__(self):
        return f"{self.staff} note on {self.date}"

    @property
    def reminder_datetime(self):
        if not self.event_time or not self.reminder_offset_minutes:
            return None
        from datetime import datetime, timedelta
        event_dt = datetime.combine(self.date, self.event_time)
        return event_dt - timedelta(minutes=self.reminder_offset_minutes)
    
""" Dominic Code End's """
#------------------------------patient Regiration ----------------------------------------#

""" swetha's code start """
class PatientRegistration(TimeStampedModel):

    STATUS = [
        ("WAITING", "Waiting"),
        ("IN_PROGRESS", "In Progress"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    ]

    ADMISSION_STATUS = [
        ("NOT_REQUESTED", "Not Requested"),
        ("REQUESTED", "Requested"),
        ("ADMITTED", "Admitted"),
        ("DISCHARGED", "Discharged"),
    ]

    registration_number = models.CharField(max_length=20, unique=True)

    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name="registrations"
    )
    hospital = models.ForeignKey(
        MedicalCenter,
        on_delete=models.PROTECT,
        related_name="patient_registrations",
        null=True,
        blank=False,
    )

    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="patient_registrations",
    )

    schedule = models.ForeignKey(
        Shift,
        on_delete=models.PROTECT,
        related_name="patient_registrations"
    )
    shift_assignment = models.ForeignKey(
        ShiftAssignment,
        on_delete=models.PROTECT,
        related_name="patient_registrations",
    )
    medical_visit = models.OneToOneField(
        MedicalVisit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="registration"
    )

    token_number = models.PositiveIntegerField( null=True,blank=True,)

    registration_type = models.CharField(
    max_length=20,
        choices=[
            ("WALK_IN", "Walk In"),
            ("APPOINTMENT", "Appointment"),
        ],
        default="WALK_IN"
    )

    priority = models.PositiveIntegerField(
        default=2
    )

    registration_date = models.DateField()
    registration_time = models.TimeField()
    chief_complaint = models.TextField(blank=True)

    arrived_by_ambulance = models.BooleanField(default=False)
    ambulance_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Ambulance UUID from MedicalCenter ambulance_services"
    )

    ambulance_unit_number = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    ambulance_plate = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    ambulance_service_type = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    status = models.CharField(max_length=20,choices=STATUS,default="WAITING")

    admission_status = models.CharField(
        max_length=20, choices=ADMISSION_STATUS, default="NOT_REQUESTED"
    )

    admission_remark = models.TextField(blank=True)

    admission_requested_by = models.ForeignKey(
        "Admin.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="requested_admissions",
    )

    admission_requested_at = models.DateTimeField(null=True, blank=True)

    assigned_room = models.ForeignKey(
        Room, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="admitted_registrations",
    )

    admitted_at = models.DateTimeField(null=True, blank=True)

    admitted_by = models.ForeignKey(
        "Admin.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="admitted_patients",
    )

    class Meta:
        db_table = "patient_registration"

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "shift_assignment",
                    "registration_date",
                    "token_number"
                ],
                name="unique_daily_assignment_token"
            )
        ]
    def __str__(self):
        number = (
        self.appointment.appointment_number
        if self.appointment
        else f"Token {self.token_number}"
    )
        return (f"{self.registration_number} | "
            f"{self.patient} |" f"{number}")
""" swetha's code end """

# ---------------- Medical Document ---------------- #

class MedicalDocument(TimeStampedModel):

    document_number = models.CharField(
        max_length=20,
        unique=True
    )

    patient = models.ForeignKey(
        PatientRegistry,
        on_delete=models.CASCADE,
        related_name="medical_documents"
    )

    medical_visit = models.ForeignKey(
        MedicalVisit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents"
    )

    uploaded_by = models.ForeignKey(
        MedicalStaffProfile,
        on_delete=models.PROTECT,
        related_name="uploaded_documents"
    )

    document_type = models.CharField(
        max_length=150,
    )

    title = models.CharField(
        max_length=200
    )

    description = models.TextField(
        blank=True
    )

    file = models.FileField(
        upload_to="medical/documents/"
    )

    document_date = models.DateField()

    expiry_date = models.DateField(
        null=True,
        blank=True
    )

    is_confidential = models.BooleanField(
        default=True,
        help_text="Only authorized medical staff can access this document."
    )

    class Meta:
        db_table = "medical_document"
        ordering = ["-document_date", "-created_at"]

    def __str__(self):
        return f"{self.document_number} - {self.title}"


# ---------------- Laboratory Test ---------------- #

class LaboratoryTest(TimeStampedModel):

    TEST_CATEGORIES = [
        ("BLOOD", "Blood Test"),
        ("URINE", "Urine Test"),
        ("STOOL", "Stool Test"),
        ("ECG", "ECG"),
        ("XRAY", "X-Ray"),
        ("MRI", "MRI"),
        ("CT_SCAN", "CT Scan"),
        ("ULTRASOUND", "Ultrasound"),
        ("COVID", "COVID Test"),
        ("OTHER", "Other"),
    ]

    SAMPLE_TYPES = [
        ("BLOOD", "Blood"),
        ("URINE", "Urine"),
        ("STOOL", "Stool"),
        ("SALIVA", "Saliva"),
        ("SWAB", "Swab"),
        ("NONE", "Not Applicable"),
    ]

    RESULT_STATUS = [
        ("NORMAL", "Normal"),
        ("ABNORMAL", "Abnormal"),
        ("CRITICAL", "Critical"),
    ]

    STATUS_CHOICES = [
        ("REQUESTED", "Requested"),
        ("COLLECTED", "Sample Collected"),
        ("PROCESSING", "Processing"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    ]

    test_number = models.CharField(
        max_length=20,
        unique=True
    )

    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name="laboratory_tests"
    )

    medical_visit = models.ForeignKey(
        MedicalVisit,
        on_delete=models.CASCADE,
        related_name="laboratory_tests"
    )

    requested_by = models.ForeignKey(
        MedicalStaffProfile,
        on_delete=models.PROTECT,
        related_name="requested_tests"
    )

    performed_by = models.ForeignKey(
        MedicalStaffProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="performed_tests"
    )

    test_name = models.CharField(max_length=150)

    test_category = models.CharField(
        max_length=30,
        choices=TEST_CATEGORIES
    )

    sample_type = models.CharField(
        max_length=20,
        choices=SAMPLE_TYPES,
        default="NONE"
    )

    requested_date = models.DateField()

    test_date = models.DateField(
        null=True,
        blank=True
    )

    result = models.TextField(
        blank=True
    )

    normal_range = models.CharField(
        max_length=100,
        blank=True
    )

    result_status = models.CharField(
        max_length=20,
        choices=RESULT_STATUS,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="REQUESTED"
    )

    remarks = models.TextField(
        blank=True
    )

    class Meta:
        db_table = "laboratory_test"
        ordering = ["-requested_date", "-created_at"]

    def __str__(self):
        return f"{self.test_number} - {self.test_name}"


# ---------------- Health Camp ---------------- #

class HealthCamp(TimeStampedModel):

    CAMP_TYPES = [
        ("GENERAL", "General Health Camp"),
        ("SPORTS", "Sports Medical Camp"),
        ("BLOOD_DONATION", "Blood Donation Camp"),
        ("EYE", "Eye Screening Camp"),
        ("DENTAL", "Dental Camp"),
        ("MENTAL_HEALTH", "Mental Health Camp"),
        ("VACCINATION", "Vaccination Drive"),
        ("FITNESS", "Fitness Assessment Camp"),
        ("NUTRITION", "Nutrition Awareness"),
    ]

    TARGET_AUDIENCE = [
        ("ALL", "All"),
        ("STUDENTS", "Students"),
        ("ATHLETES", "Athletes"),
        ("FACULTY", "Faculty"),
        ("STAFF", "Staff"),
    ]

    STATUS_CHOICES = [
        ("PLANNED", "Planned"),
        ("OPEN", "Open for Registration"),
        ("ONGOING", "Ongoing"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    ]

    camp_code = models.CharField(
        max_length=20,
        unique=True
    )

    camp_name = models.CharField(
        max_length=200
    )

    department = models.ForeignKey(
        MedicalDepartment,
        on_delete=models.PROTECT,
        related_name="health_camps"
    )

    organizer = models.ForeignKey(
        MedicalStaffProfile,
        on_delete=models.PROTECT,
        related_name="organized_health_camps"
    )

    camp_type = models.CharField(
        max_length=30,
        choices=CAMP_TYPES
    )

    target_audience = models.CharField(
        max_length=20,
        choices=TARGET_AUDIENCE,
        default="ALL"
    )

    start_date = models.DateField()

    end_date = models.DateField()

    start_time = models.TimeField()

    end_time = models.TimeField()

    venue = models.CharField(
        max_length=200
    )

    max_participants = models.PositiveIntegerField(
        default=100
    )

    registered_participants = models.PositiveIntegerField(
        default=0
    )

    description = models.TextField(
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PLANNED"
    )

    remarks = models.TextField(
        blank=True
    )

    class Meta:
        db_table = "health_camp"
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.camp_name} ({self.camp_code})"


# ---------------- Health Camp Registry ---------------- #

class HealthCampRegistry(TimeStampedModel):

    PARTICIPANT_TYPES = [
        ("STUDENT", "Student"),
        ("ATHLETE", "Athlete"),
        ("FACULTY", "Faculty"),
        ("STAFF", "Staff"),
        ("VISITOR", "Visitor"),
    ]

    ATTENDANCE_STATUS = [
        ("REGISTERED", "Registered"),
        ("ATTENDED", "Attended"),
        ("NO_SHOW", "No Show"),
    ]

    registration_number = models.CharField(
        max_length=20,
        unique=True
    )

    health_camp = models.ForeignKey(
        HealthCamp,
        on_delete=models.CASCADE,
        related_name="registrations"
    )

    participant_name = models.CharField(
        max_length=150
    )

    participant_type = models.CharField(
        max_length=20,
        choices=PARTICIPANT_TYPES
    )

    university_id = models.CharField(
        max_length=30,
        blank=True
    )

    phone_number = models.CharField(
        max_length=15,
        blank=True
    )

    email = models.EmailField(
        blank=True
    )

    gender = models.CharField(
        max_length=20,
        blank=True
    )

    date_of_birth = models.DateField(
        null=True,
        blank=True
    )

    registration_date = models.DateTimeField(
        auto_now_add=True
    )

    attendance_status = models.CharField(
        max_length=20,
        choices=ATTENDANCE_STATUS,
        default="REGISTERED"
    )

    remarks = models.TextField(
        blank=True
    )

    class Meta:
        db_table = "health_camp_registry"
        ordering = ["-registration_date"]

    def __str__(self):
        return f"{self.registration_number} - {self.participant_name}"


################ Guru Code End ####################


################ MrGow Code Start ####################

""" Dominic Code Start's """
class PushSubscription(TimeStampedModel):
    user = models.ForeignKey(
        'Admin.User',
        on_delete=models.CASCADE,
        related_name='push_subscriptions',
    )
    endpoint = models.URLField(max_length=500, unique=True)
    p256dh = models.CharField(max_length=255)
    auth = models.CharField(max_length=255)
    user_agent = models.CharField(max_length=255, blank=True)
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "medical_push_subscription"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Push subscription for {self.user} ({self.user_agent[:30]})"
""" Dominic Code End's """

class MedicalStaffLeave(TimeStampedModel):

    LEAVE_TYPES = [
        ("CASUAL", "Casual Leave"),
        ("SICK", "Sick Leave"),
        ("ANNUAL", "Annual Leave"),
        ("EMERGENCY", "Emergency Leave"),
        ("MATERNITY", "Maternity Leave"),
        ("PATERNITY", "Paternity Leave"),
        ("UNPAID", "Unpaid Leave"),
        ("PERMISSION", "Permission"),
    ]

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
        ("CANCELLED", "Cancelled"),
    ]

    medical_staff = models.ForeignKey(
        MedicalStaffProfile,
        on_delete=models.CASCADE,
        related_name="leave_applications",
    )

    leave_type = models.CharField(
        max_length=20,
        choices=LEAVE_TYPES,
    )

    # For normal leave
    start_date = models.DateField()

    end_date = models.DateField()

    # For Permission
    permission_start_time = models.TimeField(
        null=True,
        blank=True,
    )

    permission_end_time = models.TimeField(
        null=True,
        blank=True,
    )

    reason = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
    )

    approved_by = models.ForeignKey(
        MedicalStaffProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_medical_staff_leaves",
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    rejection_reason = models.TextField(
        blank=True,
        null=True,
    )
 
    class Meta:
        db_table = "medical_staff_leave"
        ordering = ["-start_date", "-created_at"]

    def __str__(self):
        return (
            f"{self.medical_staff} - "
            f"{self.get_leave_type_display()} - "
            f"{self.start_date}"
        )


################### kali code ##################
class RoomCheckupNote(TimeStampedModel):
    

    registration = models.ForeignKey(
        PatientRegistration,
        on_delete=models.CASCADE,
        related_name="checkup_notes",
    )

    note = models.TextField()

    created_by = models.ForeignKey(
        "Admin.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="room_checkup_notes",
    )

    class Meta:
        db_table = "room_checkup_note"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Checkup note for {self.registration_id} @ {self.created_at:%d %b %Y %H:%M}"

################### kali code End ##################