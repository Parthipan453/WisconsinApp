from django.db import models
from Medical.models import *
from Admin.models import User
from Admin.bela_admin.models import Building,Room
import uuid
from django.utils import timezone


class MedicalCenter(models.Model):
    
    STATUS_CHOICES = (
        ("active","Active"),
        ("inactive","Inactive"),
        ("maintenance","Maintenance"),
    )
    uuid = models.UUIDField(default=uuid.uuid4,editable=False,unique=True)
    hospital_name = models.CharField(
        max_length=200,
        unique=True
        )
    
    hospital_building = models.ForeignKey(
        Building,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="medical_centers"
    ) 
    
    
    
    short_description = models.TextField(
        max_length=300
    )
    
    about_hospital = models.TextField()
    
    director_name = models.ForeignKey(
        "Admin.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="medical_centers"
    )
    
    ambulance_services = models.JSONField(default=list, blank=True,null=True)

    department = models.ForeignKey(
        "Medical.MedicalDepartment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    hospital_location = models.CharField(
        max_length=150,
        help_text="Example: Main Campus, Block A"
    )
    
    hospital_map = models.URLField(blank=True)
    
    hospital_phone = models.CharField(
        max_length=20
    )
    
    hospital_emgphone = models.CharField(
        max_length=20, 
        blank=True
        )
    
    hospital_email = models.EmailField(
        blank=True
    )
    
    working_hours = models.JSONField(default=dict, blank=True)
    
    established_year = models.PositiveSmallIntegerField(
        blank=True,
        null=True
    )
    
    hospital_status = models.CharField(max_length=50,choices=STATUS_CHOICES)
    
    is_active = models.BooleanField(
        default=True
    )
    
    hospital_banner = models.ImageField(
        upload_to="hospital/banner",
        blank=True,
        null=True
    )
    
    
    hospital_code = models.CharField(
    max_length=10,
    unique=True,
    editable=False
    )
    
    selected_facilities = models.JSONField(
        default=list,
        blank=True
    )
    
    selected_other_facilities = models.JSONField(
        default=list,
        blank=True
    )
    
    is_full_crud = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    
    def __str__(self):
        return self.hospital_name
    
class Facility(models.Model):
    FACILITY_TYPES = (
        ("medical", "Medical"),
        ("other", "Other"),
    )

    name = models.CharField(
        max_length=50,
        unique=True,
    )

    icon = models.CharField(
        max_length=50,
        help_text="Bootstrap Icon class (e.g. bi-heart-pulse)"
    )

    facility_type = models.CharField(
        max_length=20,
        choices=FACILITY_TYPES,
    )

    is_active = models.BooleanField(
        default=True,
    )
    
    is_available = models.BooleanField(
        default=True
    )
    
    room = models.ForeignKey(
        Room,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="medical_facilities"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )
    
    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = "facility"
        ordering = ["facility_type", "name"]
        verbose_name = "Facility"
        verbose_name_plural = "Facilities"

    def __str__(self):
        return self.name

class FacilityMaintenance(models.Model):

    STATUS_CHOICES = [
        ("running", "Running"),
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("emergency", "Emergency"),
    ]

    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    hospital = models.ForeignKey(
        MedicalCenter,
        on_delete=models.CASCADE,
        related_name="maintenances"
    )

    facility = models.ForeignKey(
        Facility,
        on_delete=models.CASCADE,
        related_name="maintenance_history"
    )

    title = models.CharField(max_length=200)

    description = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default="medium"
    )

    start_date = models.DateField()

    expected_completion = models.DateField(
        null=True,
        blank=True
    )

    completed_date = models.DateField(
        null=True,
        blank=True
    )

    assigned_engineer = models.CharField(
        max_length=150
    )

    contact_number = models.CharField(
        max_length=20,
        blank=True
    )

    remarks = models.TextField(
        blank=True
    )

    created_by = models.CharField(
        max_length=100,
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)
    
    is_full_crud = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.facility.name} - {self.status}"
    

class HospitalGallery(models.Model):
    hospital = models.ForeignKey(
        MedicalCenter,
        on_delete=models.CASCADE,
        related_name="gallery"
    )
    
    gallery_type = models.CharField(max_length=50,blank=True)

    image = models.ImageField(
        upload_to="hospital/gallery/"
    )

    caption = models.CharField(
        max_length=200,
        blank=True,
        help_text="Short caption for the image"
    )

    alt_text = models.CharField(
        max_length=200,
        blank=True,
        help_text="SEO / Accessibility"
    )

    display_order = models.PositiveIntegerField(
        default=0
    )
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    is_full_crud = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "id"]

    def __str__(self):
        return f"{self.hospital.hospital_name} - {self.caption or 'Gallery Image'}"
    

class HospitalStatistics(models.Model):

    medical_center = models.OneToOneField(
        MedicalCenter,
        on_delete=models.CASCADE,
        related_name="statistics"
    )

    total_rooms = models.PositiveIntegerField(
        default=0
    )

    total_beds = models.PositiveIntegerField(
        default=0
    )

    total_staff = models.PositiveIntegerField(
        default=0
    )

    total_operation_theatres = models.PositiveIntegerField(
        default=0
    )

    emergency_open = models.BooleanField(
        default=True
    )

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    is_full_crud = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.medical_center.hospital_name} Statistics" 