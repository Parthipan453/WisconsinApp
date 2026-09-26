######################### Steve code Start #################################################
from django.db import models
from Admin.models import User
import uuid

   

class University(models.Model):

    STATUS_CHOICES = (
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
    )

    UNIVERSITY_TYPE = (
        ("PUBLIC", "Public"),
        ("PRIVATE", "Private"),
    )

    OWNERSHIP_TYPE = (
        ("STATE", "State Government"),
        ("CENTRAL", "Central Government"),
        ("PRIVATE", "Private"),
    )

    university_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Identity
    university_name = models.CharField(max_length=255)
    university_short_name = models.CharField(max_length=100)
    university_code = models.CharField(max_length=30, unique=True)

    # Classification
    university_type = models.CharField(max_length=20, choices=UNIVERSITY_TYPE, default="PUBLIC")
    ownership_type = models.CharField(max_length=20, choices=OWNERSHIP_TYPE, default="STATE")
    
    # Contact
    official_email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20)
    website = models.URLField(blank=True, null=True)

    # Address
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)

    # Academic
    established_year = models.PositiveIntegerField()
    accreditation = models.CharField(max_length=255, blank=True, null=True)

    # Branding
    logo = models.ImageField(upload_to="universities/",blank=True,null=True)
    
    # System
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="ACTIVE")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_full_crud = models.BooleanField(default=False)
    
    def __str__(self):
        return self.university_name
    
    


class School(models.Model):

    STATUS_CHOICES = (
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
    )

    SCHOOL_TYPE = (
        ("ACADEMIC", "Academic"),
        ("PROFESSIONAL", "Professional"),
        ("GRADUATE", "Graduate"),
    )

    school_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Parent University
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name="schools")

    # Identity
    school_name = models.CharField(max_length=255)
    school_short_name = models.CharField(max_length=100)
    school_code = models.CharField(max_length=30)

    # Classification
    school_type = models.CharField(max_length=20, choices=SCHOOL_TYPE, default="ACADEMIC")

    dean = models.ForeignKey('Admin.User',on_delete=models.SET_NULL, null=True, blank=True, related_name="schools_as_dean")
    
    # Contact
    official_email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    website = models.URLField(blank=True, null=True)

    # Location
    building_name = models.CharField(max_length=255, blank=True, null=True)
    address_line_1 = models.CharField(max_length=255, blank=True, null=True)
    address_line_2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)

    # Academic
    established_year = models.PositiveIntegerField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    # Branding
    logo = models.ImageField(upload_to="schools/", blank=True, null=True)

    # System
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="ACTIVE")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_full_crud = models.BooleanField(default=False)

    def __str__(self):
        return self.school_name

    class Meta:
        ordering = ["school_name"]

        constraints = [
            models.UniqueConstraint(
                fields=["university", "school_name"],
                name="unique_school_name_per_university",
            ),
            models.UniqueConstraint(
                fields=["university", "school_code"],
                name="unique_school_code_per_university",
            ),
        ]


class Degree(models.Model):
    LEVEL_CHOICES = (
        ('UG', 'Undergraduate'),
        ('PG', 'Postgraduate'),
        ('PHD', 'Doctorate'),
    )

    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
    )

    degree_id = models.AutoField(primary_key=True)
    degree_name = models.CharField(max_length=255, unique=True)
    degree_code = models.CharField(max_length=50, unique=True)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')
    is_full_crud = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["level", "degree_name"]

    def __str__(self):
        return f"{self.degree_name} ({self.degree_code})"
    
class AreaOfInterest(models.Model):
    interest_name = models.CharField(max_length=100, unique=True)
    is_full_crud = models.BooleanField(default=False)
    status = models.CharField(
        max_length=10,
        choices=[
            ("ACTIVE", "Active"),
            ("INACTIVE", "Inactive"),
        ],
        default="ACTIVE",
    )

    class Meta:
        ordering = ["interest_name"]

    def __str__(self):
        return self.interest_name

class AcademicProgram(models.Model):

    PROGRAM_TYPE_CHOICES = (
        ('FULL_TIME', 'Full Time'),
        ('PART_TIME', 'Part Time'),
        ('ONLINE', 'Online'),
    )

    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
    )

    program_id       = models.AutoField(primary_key=True)
    program_code     = models.CharField(max_length=20, unique=True, null=True, blank=True)
    department       = models.ForeignKey('bela_admin.Department', on_delete=models.CASCADE, related_name='programs')
    degree           = models.ForeignKey( Degree, on_delete=models.CASCADE, related_name='programs')
    program_name     = models.CharField(max_length=100)
    program_type     = models.CharField(max_length=50, choices=PROGRAM_TYPE_CHOICES)
    duration         = models.PositiveIntegerField(help_text="Duration in years")
    total_credits    = models.PositiveIntegerField()
    description      = models.TextField(blank=True, null=True)
    status           = models.CharField( max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    is_full_crud = models.BooleanField(default=False)
    created_at       = models.DateTimeField( auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)
    areas_of_interest = models.ManyToManyField(AreaOfInterest,blank=True,related_name="programs")

    class Meta:
        ordering = ["program_name"]

        constraints = [
            models.UniqueConstraint(
                fields=["department", "degree", "program_name"],
                name="unique_department_degree_program"
            )
        ]

    def __str__(self):
        return self.program_name
    
    
class ProgramConcentration(models.Model):
    concentration_id     = models.AutoField(primary_key=True)
    program              = models.ForeignKey( AcademicProgram, on_delete=models.CASCADE, related_name='concentrations')
    concentration_name   = models.CharField(max_length=255)
    description          = models.TextField(blank=True, null=True)
    is_full_crud = models.BooleanField(default=False)

    def __str__(self):
        return self.concentration_name
    
    
class Subject(models.Model):
    subject_id         = models.AutoField(primary_key=True)
    subject_code       = models.CharField(max_length=50, unique=True)
    subject_name       = models.CharField(max_length=255)
    credits            = models.PositiveIntegerField()
    description        = models.TextField(blank=True, null=True)
    is_full_crud = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.subject_code} - {self.subject_name}"


# don't use this model instead use ProgramCourse model 
class ProgramSubject(models.Model):

    SEMESTER_CHOICES = (
        (1, 'Semester 1'),
        
        (2, 'Semester 2'),
        (3, 'Semester 3'),
        (4, 'Semester 4'),
        (5, 'Semester 5'),
        (6, 'Semester 6'),
        (7, 'Semester 7'),
        (8, 'Semester 8'),
    )

    program            = models.ForeignKey( AcademicProgram, on_delete=models.CASCADE, related_name='program_subjects')
    subject            = models.ForeignKey( Subject, on_delete=models.CASCADE, related_name='subject_programs')
    semester           = models.PositiveIntegerField(choices=SEMESTER_CHOICES)
    is_elective        = models.BooleanField(default=False)
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        unique_together = ('program', 'subject')

    def __str__(self):
        return f"{self.program.program_name} - {self.subject.subject_name}"
    


class StudentProgramEnrollment(models.Model):

    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('DROPPED', 'Dropped'),
        ('SUSPENDED', 'Suspended'),
    )

    enrollment_id     = models.AutoField(primary_key=True)
    # student           = models.ForeignKey(Students, on_delete=models.CASCADE, related_name='enrollments')
    program           = models.ForeignKey( AcademicProgram, on_delete=models.CASCADE, related_name='enrollments')
    admission_year    = models.PositiveIntegerField()
    current_semester  = models.PositiveIntegerField(default=1)
    enrollment_date   = models.DateField(auto_now_add=True)
    status            = models.CharField( max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    is_full_crud = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.program} ({self.admission_year})"
        # return f"{self.student} - {self.program}"



class ProgramCourse(models.Model):

    STATUS_CHOICES = (
        ("ACTIVE", "Active"), 
        ("INACTIVE", "Inactive"),
    )

    YEAR_CHOICES = (
        (1, "Year 1"),
        (2, "Year 2"),
        (3, "Year 3"),
        (4, "Year 4"),
        (5, "Year 5"),
    )

    TERM_CHOICES = (
        ("FALL", "Fall"),
        ("SPRING", "Spring"),  
        ("SUMMER", "Summer"),
        ("WINTER", "Winter"),
    )
    
    program_course_id = models.AutoField(primary_key=True)

    program = models.ForeignKey("Colleges.AcademicProgram", on_delete=models.CASCADE, related_name="program_courses")
    course = models.ForeignKey( "bela_admin.Course", on_delete=models.CASCADE, related_name="program_courses")
    study_year = models.PositiveSmallIntegerField(choices=YEAR_CHOICES)
    term = models.CharField(max_length=20, choices=TERM_CHOICES)
    is_elective = models.BooleanField(default=False, help_text="Check if this course is an elective.")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,default="ACTIVE")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_full_crud = models.BooleanField(default=False)
    class Meta:
        db_table = "program_course"

        ordering = [
            "program",
            "study_year",
            "term",
            "course",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "program",
                    "study_year",
                    "term",
                    "course",
                ],
                name="unique_program_curriculum"
            )
        ]

    def __str__(self):
        return f"{self.program} | Year {self.study_year} | {self.term} | {self.course}"
    
class AcademicTerm(models.Model):

    TERM_CHOICES = (
        ("FALL", "Fall"),
        ("SPRING", "Spring"),
        ("SUMMER", "Summer"),
        ("WINTER", "Winter"),
    )

    STATUS_CHOICES = (
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
    )

    term_id = models.AutoField(primary_key=True)
    academic_year = models.CharField( max_length=9, help_text="Example: 2026-2027")
    term_name = models.CharField( max_length=20, choices=TERM_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    registration_start = models.DateField(null=True, blank=True)
    registration_end = models.DateField(null=True, blank=True)
    status = models.CharField( max_length=20, choices=STATUS_CHOICES,default="ACTIVE")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        ordering = ["academic_year", "start_date"]

        unique_together = (
            "academic_year",
            "term_name",
        )

    def __str__(self):
        return f"{self.term_name} {self.academic_year}"


######################### Steve code end #################################################




