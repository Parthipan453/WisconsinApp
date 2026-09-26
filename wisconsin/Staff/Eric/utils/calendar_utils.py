from datetime import date as date_type, timedelta
from calendar import monthrange

from django.utils import timezone

from ..constants import WORKING_DAY_SENTINEL
from ..repositories.holiday_repository import HolidayRepository


def get_us_holidays_for_year(year):
    holiday_dates = {}

    def get_nth_weekday_date(month, weekday, nth):
        first_day = date_type(year, month, 1)
        days_to_add = (weekday - first_day.weekday()) % 7
        return first_day + timedelta(days=days_to_add + 7 * (nth - 1))

    def get_last_weekday_date(month, weekday):
        total_days = monthrange(year, month)[1]
        last_day = date_type(year, month, total_days)
        days_to_sub = (last_day.weekday() - weekday) % 7
        return last_day - timedelta(days=days_to_sub)

    holiday_dates[date_type(year, 1, 1)] = "New Year's Day"
    holiday_dates[get_nth_weekday_date(1, 0, 3)] = "Martin Luther King Jr. Day"
    holiday_dates[get_nth_weekday_date(2, 0, 3)] = "Presidents' Day"
    holiday_dates[get_last_weekday_date(5, 0)] = "Memorial Day"
    holiday_dates[date_type(year, 7, 4)] = "Independence Day"
    holiday_dates[get_nth_weekday_date(9, 0, 1)] = "Labor Day"
    holiday_dates[get_nth_weekday_date(10, 0, 2)] = "Columbus Day"
    holiday_dates[date_type(year, 11, 11)] = "Veterans Day"
    holiday_dates[get_nth_weekday_date(11, 3, 4)] = "Thanksgiving"
    holiday_dates[date_type(year, 12, 25)] = "Christmas"
    return holiday_dates


def get_holidays_for_month(year, month):
    _, last_day = monthrange(year, month)
    start = date_type(year, month, 1)
    end = date_type(year, month, last_day)
    standard = get_us_holidays_for_year(year)
    repo = HolidayRepository()
    custom = repo.get_holidays_dict(start, end)
    custom = {d: n for d, n in custom.items() if n != WORKING_DAY_SENTINEL}
    merged = {**standard, **custom}
    return {d: n for d, n in merged.items() if start <= d <= end}


def build_month_calendar_data(year, month, records_by_date, total_faculty_count):
    days_in_month = monthrange(year, month)[1]
    today = timezone.localdate()
    daily_data = []
    for day_num in range(1, days_in_month + 1):
        current_date = date_type(year, month, day_num)
        day_records = records_by_date.get(current_date, [])
        number_marked = len(day_records)
        counts = {"PRESENT": 0, "ABSENT": 0, "LATE": 0, "ON_LEAVE": 0, "HALF_DAY": 0}
        for r in day_records:
            if r.status in counts:
                counts[r.status] += 1
        marked_pct = round((number_marked / total_faculty_count) * 100) if total_faculty_count else 0
        daily_data.append({
            "day": day_num,
            "weekday": current_date.weekday(),
            "date": current_date,
            "marked": number_marked,
            "present": counts["PRESENT"],
            "absent": counts["ABSENT"],
            "late": counts["LATE"],
            "leave": counts["ON_LEAVE"],
            "halfday": counts["HALF_DAY"],
            "pct": marked_pct,
            "is_today": current_date == today,
            "is_weekend": current_date.weekday() >= 5,
        })
    return daily_data


MONTH_ABBREVIATIONS = [
    "", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
]
