from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from .models import GradeChangeRequest, CourseGrade
from Admin.Elsa_admin.models import GradeScale


def resolve_grade_scale(score):
    if score is None:
        return None
    return GradeScale.objects.filter(
        minimum_percentage__lte=score,
        maximum_percentage__gte=score,
    ).first()


@receiver(pre_save, sender=GradeChangeRequest)
def _stash_previous_status(sender, instance, **kwargs):
    """Remember the DB's current approval_status before this save overwrites it,
    so post_save can tell whether this save is the transition into 'Approved'."""
    if instance.pk:
        try:
            instance._previous_approval_status = (
                GradeChangeRequest.objects.only("approval_status").get(pk=instance.pk).approval_status
            )
        except GradeChangeRequest.DoesNotExist:
            instance._previous_approval_status = None
    else:
        instance._previous_approval_status = None


@receiver(post_save, sender=GradeChangeRequest)
def apply_approved_grade_change(sender, instance, created, **kwargs):
    """When a GradeChangeRequest transitions into 'Approved' (from any other
    status, via any view — admin site, custom admin panel, shell, etc.),
    automatically push requested_score into the matching CourseGrade row."""
    previous_status = getattr(instance, "_previous_approval_status", None)

    if instance.approval_status != "Approved":
        return
    if previous_status == "Approved":
        return  # already applied on an earlier save; don't reapply

    grade = CourseGrade.objects.filter(
        student__student_number=instance.student_id,
        course__course_code=instance.course_id,
    ).first()

    if not grade:
        return  # nothing to apply to; silently skip rather than crash the admin's save

    grade.numeric_score = instance.requested_score
    grade.grade_scale = resolve_grade_scale(instance.requested_score)
    grade.save()