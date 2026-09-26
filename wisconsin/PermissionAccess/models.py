""" Dominic Code """
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone

class TimeStampedModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
        
class Permission(TimeStampedModel):
    class Action(models.TextChoices):
        CREATE = "create", "Create"
        READ = "read", "Read"
        UPDATE = "update", "Update"
        DELETE = "delete", "Delete"
        
    name = models.CharField(max_length=150, unique=True)
    codename = models.CharField(max_length=150, unique=True)
    model_label = models.CharField(max_length=100)
    app_label = models.CharField(max_length=100)
    action = models.CharField(max_length=10, choices=Action.choices)
    description = models.TextField(blank=True)
    display_label = models.CharField(
        max_length=150,
        blank=True,
        help_text=(
            "Optional override for how this permission is labelled in the "
            "Roles & Permissions UI. Can be a plain name ('Media Block') or "
            "a full breadcrumb using '>' as the separator "
            "(e.g. 'Medical > Staff > Assign Medical Staff') — the last "
            "segment is shown as the model name in the CRUD grid, and the "
            "full breadcrumb (plus the action) is shown in the C/R/U/D "
            "tooltip. Leave blank to auto-generate from the source model's "
            "verbose_name — most models never need to set this. Set as a "
            "`permission_label` class attribute on the source model (see "
            "signals.py), not here."
        ),
    )
    is_full_crud = models.BooleanField(
        default=True,
        help_text=(
            "Mirrors the source model's is_full_crud flag. False means this "
            "model only ever gets a 'read' permission and is hidden from the "
            "CRUD matrix UI."
        ),
    )
    shared_with_user_roles = models.BooleanField(
        default=False,
        help_text=(
            "Only meaningful when app_label is 'Medical'. When True, this "
            "model's CRUD permissions move to the Admin tab instead of the "
            "Medical tab (exclusive switch, not additive). Mirrors the "
            "source model's own `shared_with_user_roles` flag — set it as a "
            "field on the model (see signals.py), not here."
        ),
    )
    user_types = models.JSONField(
        default=list,
        blank=True,
        help_text=(
            "Which Admin.UserRole.user_type values (e.g. 'admin', 'staff', "
            "'faculty', 'student') can see and be granted this permission in "
            "the Roles & Permissions UI. A permission can belong to more than "
            "one tab (e.g. ['staff', 'admin']). Empty list = shows under the "
            "Admin tab only until explicitly tagged. Not used for app_label "
            "'Medical' — Medical uses `shared_with_user_roles` instead. Set "
            "as a `user_types` class attribute on the source model (see "
            "signals.py), not here."
        ),
    )
    
    class Meta:
        db_table = "permissions_access_permissions"
        verbose_name = "Permission"
        verbose_name_plural = "Permissions"
        ordering = ["app_label", "model_label", "action"]
        unique_together = [("model_label", "action", "app_label")]
        
    def __str__(self):
        return self.name

    @property
    def display_model_name(self) -> str:
        """
        Model name shown in the Roles & Permissions CRUD grid (the row
        label, not the tooltip). Respects a developer-set `permission_label`
        (stored on `display_label`) — if it's a breadcrumb ('Medical > Staff
        > Assign Medical Staff'), only the last segment is used here so the
        grid stays compact. Falls back to the auto-derived verbose_name when
        nothing was set.
        """
        if self.display_label:
            segments = [s.strip() for s in self.display_label.split(">") if s.strip()]
            return segments[-1] if segments else self.display_label.strip()

        model_display = self.model_label.replace("_", " ").title()
        try:
            from django.apps import apps as _apps
            model_cls = _apps.get_model(self.app_label, self.model_label)
            model_display = str(model_cls._meta.verbose_name).title()
        except LookupError:
            pass
        return model_display

    @property
    def breadcrumb_path(self) -> str:
        """
        Just the location breadcrumb, no action — e.g. 'Medical › Staff ›
        Manage Role/Types'. Used by the "path" chip next to the model name.
        """
        if self.display_label:
            segments = [s.strip() for s in self.display_label.split(">") if s.strip()]
            return " › ".join(segments) if segments else self.display_label.strip()
        return f"{self.app_label} › {self.display_model_name}"

    @property
    def display_path(self) -> str:
        """
        Full breadcrumb + action shown in the C/R/U/D tooltip
        (e.g. 'Medical › Staff › Assign Medical Staff › Create').
        """
        return f"{self.breadcrumb_path} › {self.get_action_display()}"
    
class PageAccess(TimeStampedModel):
    page_key = models.CharField(max_length=100, unique=True, help_text="Unique slug indentifying this page in code.")
    display_name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    path_prefix = models.CharField(max_length=200, unique=True, help_text=(
        "URL path prefix this page covers. "
        "Every request whose path starts with this prefix is checked "
        "against this PageAccess record by the middleware."
    ))
    category = models.CharField(max_length=100, default='General', help_text="Groups this page under a section in the Page Access UI (e.g. 'User Management').")
    icon = models.CharField(max_length=50, default='file', help_text="Lucide icon name shown next to this page in the Page Access UI.")
    is_auto_discovered = models.BooleanField(default=False, help_text="True if this record was created by the page-sync scanner rather than manually.")
    roles = models.ManyToManyField("Admin.UserRole", blank=True, related_name="page_accesses", help_text="UserRole groups allowed to see/open this page.")
    medical_roles = models.ManyToManyField("Medical.MedicalStaffRole", blank=True, related_name="page_accesses")

    shared_with_user_roles = models.BooleanField(
        default=False,
        help_text=(
            "Only meaningful when category is 'Medical'. When True, this page "
            "moves to the Admin tab instead of the Medical tab (exclusive "
            "switch, not additive) — use this only for the pages that live "
            "under the Admin sidebar's 'Medical' dropdown (e.g. Departments, "
            "Staff, Patients Profile, Appointments, Healthcamp Management, "
            "Hospital Dashboard, Book Appointment, Athletes Profile). "
            "Medical-only operational pages (Shift Management, My Shifts, "
            "Staff Schedule, Assign Medical Staff) must stay False so they "
            "always stay on the Medical tab. "
            "NOT admin-editable in the Page Access UI — set `shared_with_user_roles` "
            "as a class attribute on the view (see discovery.py) and click "
            "'Scan for new pages' to apply it."
        ),
    )
    user_types = models.JSONField(
        default=list,
        blank=True,
        help_text=(
            "Which Admin.UserRole.user_type values (e.g. 'admin', 'staff', "
            "'faculty', 'student') can see this page in the Roles & "
            "Permissions / Page Access UI. A page can belong to more than "
            "one tab (e.g. ['staff', 'faculty']). Empty list = shows under "
            "the Admin tab only until explicitly tagged. Not used when "
            "category is 'Medical' — Medical pages use `shared_with_user_roles` "
            "instead. NOT admin-editable here — set `user_types` as a class "
            "attribute on the view (see discovery.py) and click "
            "'Scan for new pages' to apply it."
        ),
    )
    breadcrumb = models.CharField(
        max_length=255,
        blank=True,
        help_text=(
            "Where this page sits, shown in the Page Access UI "
            "(e.g. 'Medical > Staff'). Developer-provided, NOT "
            "auto-generated and NOT admin-editable in the Page Access UI — "
            "set `page_path` as a class attribute on the view "
            "(PageAccessMixin) or a kwarg on `require_page_access` (see "
            "mixins.py / decorators.py), then click 'Scan for new pages' "
            "or re-run migrate to apply it. Left blank until the developer "
            "sets it — the UI falls back to 'Category > Display Name' "
            "meanwhile so nothing breaks."
        ),
    )
    
    class Meta:
        db_table = "permission_access_page_access"
        verbose_name = "Page Access"
        verbose_name_plural = "Page Accesses"
        ordering = ["category", "display_name"]
        
    def __str__(self):
        return self.display_name

    @property
    def is_medical_page(self) -> bool:
        return (self.category or "").strip().lower() == "medical"

    @property
    def display_breadcrumb(self) -> str:
        """
        Breadcrumb shown in the Page Access UI. Uses the developer's
        explicit `breadcrumb` (from `page_path`) when set; falls back to
        'Category › Display Name' only for pages nobody has tagged yet, so
        older/untagged pages don't render blank.
        """
        if self.breadcrumb:
            return self.breadcrumb
        return f"{self.category} › {self.display_name}"
    
class PermissionAuditLog(models.Model):
    class ActionType(models.TextChoices):
        PERMISSION_ASSIGNED = "permission_assigned", "Permission Assigned"
        PERMISSION_REMOVED = "permission_removed", "Permission Removed"
        PAGE_ACCESS_CHANGED = "page_access_changed", "Page Access Changed"
        UNAUTHORIZED_ATTEMPT = "unauthorized_attempt", "Unauthorized Attempt"
        ADMINISTRATOR_SETUP = "administrator_setup", "Administrator Setup"
        
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, unique=True, editable=False)
    action_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="permission_audit_actions")
    action = models.CharField(max_length=50, choices=ActionType.choices)
    target_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="rbac_audit_targets")
    target_role = models.ForeignKey("Admin.UserRole", on_delete=models.SET_NULL, null=True, blank=True, related_name="permission_audit_logs")
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now, editable=False)
    
    class Meta:
        db_table = "permission_access_audit_logs"
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        ordering = ["-timestamp"]
        
    def __str__(self):
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {self.action_by} -> {self.action}"
    
    def save(self, *args, **kwargs):
        if self.pk and PermissionAuditLog.objects.filter(pk=self.pk).exists():
            raise PermissionError("Audit logs are immutable and cannot be updated.")
        super().save(*args, **kwargs)
        
    def delete(self, *args, **kwargs):
        raise PermissionError("Audit logs are immutable and cannot be deleted.")