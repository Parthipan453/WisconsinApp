# Leo's Code Start

from django.db import models


# ACADEMIC STANDINGS MODEL #
class AcademicStanding(models.Model):
    # like serial number for the list of academic standings
    standing_id = models.AutoField(primary_key=True)

    # name of the standing
    standing_name = models.CharField(
        max_length=100,
        unique=True,
    )

    # minimum gpa for a standing like 4.
    minimum_gpa = models.DecimalField(
        max_digits=4,
        decimal_places=2,
    )
    # description of the standing
    description = models.TextField(
        max_length=500,
    )
    # status of the standing like active or inactive
    is_active = models.BooleanField(
        default=True,
        verbose_name="Active Status",
    )
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "academic_standing"
        ordering = ["-minimum_gpa"]
        verbose_name = "Academic Standing"
        verbose_name_plural = "Academic Standings"

    def __str__(self):
        return self.standing_name


# Leo's Code End
