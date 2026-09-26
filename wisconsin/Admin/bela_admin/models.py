from django.db import models
import uuid
from django.utils.text import slugify
from Admin.Colleges.models import AcademicProgram, Degree


class Department(models.Model):

    department_id = models.AutoField(primary_key=True)
    department_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    slug = models.SlugField(max_length=255, unique=True, blank=True)

    school = models.ForeignKey(
        "Colleges.School", on_delete=models.CASCADE, related_name="departments"
    )

    department_code = models.CharField(max_length=20, unique=True)

    department_name = models.CharField(max_length=255)

    short_name = models.CharField(max_length=50, unique=True)

    description = models.TextField()

    website = models.URLField(blank=True, null=True)

    office_location = models.CharField(max_length=255, blank=True, null=True)

    email = models.EmailField(blank=True, null=True)

    phone_number = models.CharField(max_length=20, blank=True, null=True)

    established_year = models.PositiveIntegerField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=(("ACTIVE", "Active"), ("INACTIVE", "Inactive")),
        default="ACTIVE",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)
    is_full_crud = models.BooleanField(default=False)

    def __str__(self):
        return self.department_name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.department_name)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.department_name


class Course(models.Model):

    STATUS_CHOICES = (
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
    )

    course_id = models.AutoField(primary_key=True)
    course_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    department = models.ForeignKey(
        "Department", on_delete=models.CASCADE, related_name="courses"
    )

    academic_program = models.ForeignKey(
        "Colleges.AcademicProgram",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="courses",
    )

    degree = models.ForeignKey(
        "Colleges.Degree",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="courses",
    )

    course_code = models.CharField(
        max_length=20,
    )

    course_name = models.CharField(max_length=255)

    credits = models.PositiveSmallIntegerField()

    description = models.TextField(blank=True, null=True)

    email = models.EmailField(blank=True, null=True)

    phone_number = models.CharField(max_length=20, blank=True, null=True)

    website = models.URLField(blank=True, null=True)

    office_location = models.CharField(max_length=255, blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="ACTIVE")

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)
    is_full_crud = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.course_code} {self.course_name}")

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.course_code} - {self.course_name}"


class CourseRequirementType(models.Model):

    requirement_type_id = models.AutoField(primary_key=True)

    name = models.CharField(max_length=100, unique=True)

    description = models.TextField(blank=True, null=True)

    STATUS_CHOICES = (
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="ACTIVE")

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)
    is_full_crud = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class CourseRequirement(models.Model):

    requirement_id = models.AutoField(primary_key=True)

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="requirements"
    )

    requirement_type = models.ForeignKey(
        CourseRequirementType,
        on_delete=models.PROTECT,
        related_name="course_requirements",
    )

    related_course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="required_by",
        blank=True,
        null=True,
    )

    note = models.TextField(max_length=255, blank=True, null=True)

    display_order = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)
    is_full_crud = models.BooleanField(default=False)

    def __str__(self):
        if self.related_course:
            return f"{self.course.course_code} - {self.requirement_type.name} - {self.related_course.course_code}"
        return f"{self.course.course_code} - {self.requirement_type.name}"


class CourseDesignationType(models.Model):

    designation_type_id = models.AutoField(primary_key=True)

    designation_name = models.CharField(max_length=150, unique=True)

    description = models.TextField(blank=True, null=True)

    STATUS_CHOICES = (
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="ACTIVE")
    is_full_crud = models.BooleanField(default=False)

    def __str__(self):
        return self.designation_name


class CourseDesignation(models.Model):

    designation_id = models.AutoField(primary_key=True)

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="designations"
    )

    designation_type = models.ForeignKey(
        CourseDesignationType,
        on_delete=models.PROTECT,
        related_name="course_designations",
    )

    designation_value = models.CharField(max_length=255, blank=True, null=True)

    display_order = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)
    is_full_crud = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.course.course_code} - {self.designation_type.designation_name}"

    # Ranganayagi code start

    from django.db import models


class CourseOffering(models.Model):

    TERM_CHOICES = (
        ("Spring", "Spring"),
        ("Summer", "Summer"),
        ("Fall", "Fall"),
        ("Winter", "Winter"),
    )

    offering_id = models.AutoField(primary_key=True)

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="offerings"
    )

    term = models.CharField(max_length=20, choices=TERM_CHOICES)

    year = models.PositiveIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    is_full_crud = models.BooleanField(default=False)

    class Meta:
        ordering = ["-year", "-created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["course", "term", "year"], name="unique_course_offering"
            )
        ]

    def __str__(self):
        return f"{self.course.course_code} - {self.term} {self.year}"


class CourseLearningOutcome(models.Model):

    outcome_id = models.AutoField(primary_key=True)

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="learning_outcomes"
    )

    outcome = models.TextField()

    audience = models.CharField(
        max_length=100, blank=True, null=True, default="Undergraduate"
    )

    display_order = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    is_full_crud = models.BooleanField(default=False)

    class Meta:
        ordering = ["display_order"]

    def __str__(self):
        return f"{self.course.course_code} - Outcome {self.display_order}"

# ************************************************ Arun code *******************************************************
class Building(models.Model):
   
    building_type = models.CharField(
        max_length= 50,
        choices= (
            ("MEDICAL","Medical"),
            ("NORMAL","Normal")
        ),
        default="NORMAL"
    )
   
    # Gow
    hospital = models.ForeignKey(
        "Medical.MedicalCenter",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="buildings"
    )
 
    building_name = models.CharField(max_length=150)
 
    building_code = models.CharField(max_length=20, unique=True)
 
    address = models.TextField(blank=True)
 
    status = models.CharField(
        max_length=20,
        choices=(
            ("ACTIVE","Active"),
            ("INACTIVE","Inactive"),
        ),
        default="ACTIVE"
    )
 
    # ************************* Rupa code ************************************************************
 
    building_image = models.ImageField(
        upload_to="library/buildings/",
        blank=True,
        null=True
    )
 
    created_at = models.DateTimeField(auto_now_add=True)
 
    updated_at = models.DateTimeField(auto_now=True)
 
    # ************************ Rupa code end *********************************************************
 
    is_full_crud = models.BooleanField(default=True)
 
    def __str__(self):
        return self.building_name


class Floor(models.Model):

    building = models.ForeignKey(
        Building, on_delete=models.CASCADE, related_name="floors"
    )

    floor_name = models.CharField(max_length=100)

    floor_number = models.IntegerField()

    is_full_crud = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.building} - Floor {self.floor_number}"


class Room(models.Model):

    ROOM_TYPE_CHOICES = (
        ("CLASSROOM", "Classroom"),
        ("LAB", "Laboratory"),
        ("EXAM_HALL", "Exam Hall"),
        ("SEMINAR", "Seminar Hall"),
    )

    STATUS_CHOICES = (
        ("AVAILABLE","Available"),
        ("OCCUPIED","Occupied"),
        ("MAINTENANCE","Maintenance"),
        ("BLOCKED","Blocked"),
    )

    floor = models.ForeignKey(Floor, on_delete=models.CASCADE, related_name="rooms")

    room_number = models.CharField(max_length=30)

    room_name = models.CharField(max_length=150)

    room_type = models.CharField(max_length=30, choices=ROOM_TYPE_CHOICES)

    capacity = models.PositiveIntegerField()

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="AVAILABLE"
    )

    has_projector = models.BooleanField(default=False)

    has_computers = models.BooleanField(default=False)

    has_ac = models.BooleanField(default=True)

    is_full_crud = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.room_number} - {self.room_name}"


class FacilityRoomAllocation(models.Model):
    
    class Purpose(models.TextChoices):
        CONSULTATION = "Consultation Room", "Consultation Room"
        EXAMINATION = "Examination Room", "Examination Room"
        TREATMENT = "Treatment Room", "Treatment Room"
        LABORATORY = "Laboratory", "Laboratory"
        PHARMACY = "Pharmacy", "Pharmacy"
        EMERGENCY = "Emergency Room", "Emergency Room"
        PROCEDURE = "Procedure Room", "Procedure Room"
        OPERATION_THEATRE = "Operation Theatre", "Operation Theatre"
        RECOVERY = "Recovery Room", "Recovery Room"
        IMAGING = "Imaging / Radiology", "Imaging / Radiology"
        NURSING_STATION = "Nursing Station", "Nursing Station"
        STAFF = "Staff Room", "Staff Room"
        DOCTOR = "Doctor Room", "Doctor Room"
        WAITING = "Waiting Room", "Waiting Room"
        STORAGE = "Storage Room", "Storage Room"
        ADMINISTRATIVE = "Administrative Room", "Administrative Room"
        OTHER = "Other", "Other"

    medical_center = models.ForeignKey(
        "Medical.MedicalCenter",
        on_delete=models.CASCADE,
        related_name="facility_room_allocations",
    )

    facility = models.ForeignKey(
        "Medical.Facility", on_delete=models.CASCADE, related_name="room_allocations"
    )

    room = models.ForeignKey(
        Room, on_delete=models.CASCADE, related_name="facility_allocations"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_full_crud = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.facility} - {self.room}"

class RoomPurposeAllocation(models.Model):

    PURPOSE_CHOICES = [
    ("Patient Room", "Patient Room"),
    ("Consultation Room", "Consultation Room"),
    ("Examination Room", "Examination Room"),
    ("Treatment Room", "Treatment Room"),
    ("Procedure Room", "Procedure Room"),
    ("Operating Room", "Operating Room"),
    ("Pre-Operative Room", "Pre-Operative Room"),
    ("Post-Operative Recovery Room", "Post-Operative Recovery Room"),
    ("Emergency Room", "Emergency Room"),
    ("Trauma Room", "Trauma Room"),
    ("Isolation Room", "Isolation Room"),
    ("Negative Pressure Room", "Negative Pressure Room"),
    ("Infusion Room", "Infusion Room"),
    ("Laboratory", "Laboratory"),
    ("Pharmacy", "Pharmacy"),
    ("Nursing Station", "Nursing Station"),
    ("Doctor's Office", "Doctor's Office"),
    ("Staff Room", "Staff Room"),
    ("Waiting Room", "Waiting Room"),
    ("Patient Registration", "Patient Registration"),
    ("Medical Records Room", "Medical Records Room"),
    ("Clean Utility Room", "Clean Utility Room"),
    ("Soiled Utility Room", "Soiled Utility Room"),
    ("Sterilization Room", "Sterilization Room"),
    ("Storage Room", "Storage Room"),
    ("Housekeeping Room", "Housekeeping Room"),
    ("Administrative Office", "Administrative Office"),
    ("Conference Room", "Conference Room"),
    ("Other", "Other"),
]

    medical_center = models.ForeignKey(
        "Medical.MedicalCenter",
        on_delete=models.CASCADE,
        related_name="room_purpose_allocations"
    )

    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name="purpose_allocations"
    )

    purpose = models.CharField(
        max_length=100,
        choices=PURPOSE_CHOICES
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    is_full_crud = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["medical_center", "room"],
                name="unique_room_purpose_per_hospital"
            )
        ]

    def __str__(self):
        return f"{self.room} - {self.purpose}"

# ************************************************ MrGow code *******************************************************
