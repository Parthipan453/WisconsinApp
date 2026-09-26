from django.db import models
import uuid

class TimeStampedModel(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
        
class MedicalStaffRole(TimeStampedModel):
    permission_label = "Medical > Staff > Manage Role/Types"
    CATEGORY_CHOICES = [
        ("DOCTOR", "Doctor / Physician"),
        ("NURSE", "Nurse"),
        ("LAB", "Lab Technician"),
        ("PHYSIO", "Physiotherapist"),
        ("PHARMACY", "Pharmacist"),
        ("FRONT_DESK", "Front Desk / Receptionist"),
        ("DIRECTOR", "Director"),
        ("OTHER", "Other"),
    ]
    
    name = models.CharField(max_length=100, unique=True, help_text="e.g. Doctor, Staff Nurse, ENT Specialist, Lab Technician — user-added, not fixed.")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="OTHER", help_text="Used internally to filter dropdowns (e.g. only DOCTOR-category staff show up when assigning a physician).")
    permissions = models.ManyToManyField("PermissionAccess.Permission", blank=True, related_name="medical_staff_roles")
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
        db_table = "medical_staff_role"
        ordering = ["name"]
        
    def __str__(self):
        return self.name
    