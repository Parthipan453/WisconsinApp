import calendar as cal_mod
from datetime import date as date_type
from calendar import monthrange

from ..models import Holiday
from ..constants import WORKING_DAY_SENTINEL
from ..repositories.holiday_repository import HolidayRepository
from ..utils.calendar_utils import get_us_holidays_for_year
from ..utils.calendar_utils import MONTH_ABBREVIATIONS


class HolidayService:

    def __init__(self):
        self.repo = HolidayRepository()

    def get_month_holidays_merged(self, year, month):
        _, last_day = monthrange(year, month)
        start = date_type(year, month, 1)
        end = date_type(year, month, last_day)
        standard = get_us_holidays_for_year(year)
        custom = self.repo.get_holidays_dict(start, end)
        custom = {d: n for d, n in custom.items() if n != WORKING_DAY_SENTINEL}
        merged = {**standard, **custom}
        return {d: n for d, n in merged.items() if start <= d <= end}, custom

    def build_calendar_days(self, year, month):
        _, num_days = monthrange(year, month)
        merged_holidays, custom_holidays = self.get_month_holidays_merged(year, month)
        working_overrides = self.get_working_day_overrides(year, month)
        today = date_type.today()

        cal = cal_mod.Calendar(cal_mod.SUNDAY).monthdayscalendar(year, month)
        days_list = []
        for week in cal:
            for day_num in week:
                if day_num == 0:
                    continue
                current = date_type(year, month, day_num)
                is_wd = current in working_overrides
                days_list.append({
                    "day": day_num,
                    "date": current,
                    "holiday_name": merged_holidays.get(current, ""),
                    "is_holiday": current in merged_holidays,
                    "is_custom": current in custom_holidays,
                    "is_weekend": current.weekday() >= 5,
                    "is_today": current == today,
                    "is_working_day_override": is_wd,
                })
        return days_list

    def add_holiday(self, date, name):
        self.repo.update_or_create(date, name)

    def delete_holiday(self, date):
        return self.repo.delete(date)

    def get_working_day_overrides(self, year, month):
        _, last_day = cal_mod.monthrange(year, month)
        start = date_type(year, month, 1)
        end = date_type(year, month, last_day)
        return set(
            Holiday.objects.filter(
                date__gte=start, date__lte=end, name=WORKING_DAY_SENTINEL
            ).values_list("date", flat=True)
        )

    def toggle_working_day(self, dt, reason=""):
        try:
            obj = Holiday.objects.get(date=dt, name=WORKING_DAY_SENTINEL)
            obj.delete()
            return False
        except Holiday.DoesNotExist:
            Holiday.objects.create(date=dt, name=WORKING_DAY_SENTINEL)
            return True

    def is_working_day_override(self, dt):
        return Holiday.objects.filter(date=dt, name=WORKING_DAY_SENTINEL).exists()
