import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction

from Admin.models import User
from Staff.models import StaffProfile


FIRST_NAMES = [
    "Aravind", "Praveen", "Harini", "Nithya", "Suresh", "Keerthana", "Aarthi", "Anitha", "Bhavani", "Haritha",
    "Arun", "Karthik", "Rahul", "Vignesh", "Naveen", "Divya", "Priya", "Kavya", "Swathi", "Meena"
]

LAST_NAMES = [
    "Rajan", "Kumar", "Selvaraj", "Balakrishnan", "Kumar", "Murugan", "Ramesh", "Devi", "Krishnan", "Murugan",
    "Kumar", "Raj", "Prakash", "Iyer", "Nair", "Reddy", "Pillai", "Menon", "Krishnan", "Varma"
]


class Command(BaseCommand):
    help = "Create dummy staff users"

    @transaction.atomic
    def handle(self, *args, **kwargs):

        for i in range(20):

            first = FIRST_NAMES[i]
            last = LAST_NAMES[i]

            username = f"staff{i+1}"
            email = f"{username}@college.edu"

            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "first_name": first,
                    "last_name": last,
                    "mobile_number": f"98{random.randint(10000000,99999999)}",
                    "gender": random.choice(["MALE","FEMALE"]),
                    "account_status": "ACTIVE",
                    "is_staff": True,
                    "is_active": True,
                }
            )

            if created:
                user.set_password("Staff@123")
                user.save()

            StaffProfile.objects.get_or_create(
                user=user,
                defaults={
                    "employee_id": f"EMP{1000+i}",
                    "work_email": email,
                    "personal_email": f"personal{i}@gmail.com",
                    "preferred_name": first,
                    "office_phone": f"04{random.randint(10000000,99999999)}",
                    "hire_date": date.today()-timedelta(days=random.randint(100,1500)),
                    "employment_status":"ACTIVE",
                    "employment_type":"FULL_TIME",
                }
            )

        self.stdout.write(
            self.style.SUCCESS("20 Staff users created.")
        )