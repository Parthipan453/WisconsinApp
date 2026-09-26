from datetime import date as date_type

from ..models import Holiday


class HolidayRepository:

    def get_holidays_for_date_range(self, start_date, end_date):
        return Holiday.objects.filter(date__gte=start_date, date__lte=end_date)

    def get_holidays_dict(self, start_date, end_date):
        return {
            h.date: h.name
            for h in Holiday.objects.filter(date__gte=start_date, date__lte=end_date)
        }

    def update_or_create(self, date, name):
        Holiday.objects.update_or_create(date=date, defaults={"name": name})

    def delete(self, date):
        deleted, _ = Holiday.objects.filter(date=date).delete()
        return deleted
