from django.db import models


class AttendanceStatus(models.TextChoices):
    PRESENT = "PRESENT", "Present"
    ABSENT = "ABSENT", "Absent"
    LATE = "LATE", "Late"
    HALF_DAY = "HALF_DAY", "Half Day"
    ON_LEAVE = "ON_LEAVE", "On Leave"


EXPECTED_START_MINUTES = 9 * 60
EXPECTED_END_MINUTES = 17 * 60
EXPECTED_DAY_DURATION_HOURS = 8

YEAR_MIN = 2020
YEAR_MAX = 2100

PAGINATE_BY = 15

EXPORT_HEADER_FONT_NAME = "Calibri"
EXPORT_HEADER_FONT_SIZE = 11
EXPORT_DATA_FONT_NAME = "Calibri"
EXPORT_DATA_FONT_SIZE = 10

WORKING_DAY_SENTINEL = "__working_day__"

UW_RED_HEX = "C5050C"
UW_RED_RGB = (0xC5 / 255, 0x05 / 255, 0x0C / 255)
