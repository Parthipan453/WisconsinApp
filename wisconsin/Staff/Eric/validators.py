from datetime import datetime, date as date_type

from django.shortcuts import redirect
from django.utils import timezone

from .constants import YEAR_MIN, YEAR_MAX


def clamp_year(year_val, default_year=None):
    if default_year is None:
        default_year = timezone.localdate().year
    if year_val < YEAR_MIN or year_val > YEAR_MAX:
        return default_year
    return year_val


def parse_date(date_string, fallback=None):
    if fallback is None:
        fallback = timezone.localdate()
    if not date_string:
        return fallback
    try:
        parsed = datetime.strptime(date_string, "%Y-%m-%d").date()
        if YEAR_MIN <= parsed.year <= YEAR_MAX:
            return parsed
    except (ValueError, TypeError):
        pass
    return fallback


def parse_time(time_string):
    if not time_string:
        return None
    try:
        return datetime.strptime(time_string.strip(), "%H:%M").time()
    except (ValueError, TypeError):
        return None


def check_owner_access(request, user_uuid):
    if str(request.user.uuid) != str(user_uuid):
        return redirect("login"), None
    try:
        staff_profile = request.user.staff_profile
    except Exception:
        return redirect("login"), None
    return None, staff_profile


def get_staff_profile(request):
    try:
        return request.user.staff_profile
    except Exception:
        return None
