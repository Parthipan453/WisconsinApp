
from django.core.exceptions import ValidationError

from .models import University, Degree, AcademicProgram, Subject
from Admin.bela_admin.models import Department, Course


def validate_global_code(code, instance=None):
    code = code.strip().upper()

    models_to_check = [
        (University, "university_code", "University"),
        (Degree, "degree_code", "Degree"),
        (AcademicProgram, "program_code", "Academic Program"),
        (Department, "department_code", "Department"),
        (Course, "course_code", "Course"),
        (Subject, "subject_code", "Subject"),
    ]

    for model, field, name in models_to_check:

        queryset = model.objects.filter(**{field: code})

   
        if instance and isinstance(instance, model):
            queryset = queryset.exclude(pk=instance.pk)

        if queryset.exists():
            raise ValidationError(
                f'The code "{code}" is already assigned to a {name}. Please use a different code.'
            )