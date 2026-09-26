from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
    RegexValidator,
)


class GradeScale(models.Model):
    letter_grade = models.CharField(
        max_length=5,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[A-Za-z]+[+-]?$',
                message="Grade can contain letters and an optional '+' or '-' at the end."
            )
        ]
    )
    description = models.CharField(max_length=30, blank=True)
    grade_points = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(4.0)
        ]
    )
    minimum_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ]
    )
    maximum_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ]
    )
    passing_grade = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    is_full_crud = models.BooleanField(default=False)
    class Meta:
        ordering = ["-minimum_percentage"]

    def __str__(self):
        return self.letter_grade
    def clean(self):
        if self.minimum_percentage > self.maximum_percentage:
            raise ValidationError({
                "minimum_percentage": "Minimum percentage cannot be greater than maximum percentage."
            })
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
