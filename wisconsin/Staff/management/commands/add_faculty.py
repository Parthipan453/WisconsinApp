from django.core.management.base import BaseCommand
from django.db import transaction

from Admin.models import User
from Faculty.models import FacultyProfile, FacultyRank
from Admin.bela_admin.models import Department


FACULTY_DATA = [
    {
        "username": "alice.johnson",
        "email": "alice.johnson@wisconsin.edu",
        "password": "faculty123",
        "first_name": "Alice",
        "last_name": "Johnson",
        "university_id": "U0061001",
        "employee_id": "FAC-001",
        "department_code": "CS",
        "rank_name": "Professor",
        "hire_date": "2020-08-15",
    },
    {
        "username": "bob.smith",
        "email": "bob.smith@wisconsin.edu",
        "password": "faculty123",
        "first_name": "Bob",
        "last_name": "Smith",
        "university_id": "U0061002",
        "employee_id": "FAC-002",
        "department_code": "MATH",
        "rank_name": "Associate Professor",
        "hire_date": "2018-01-10",
    },
    {
        "username": "carol.davis",
        "email": "carol.davis@wisconsin.edu",
        "password": "faculty123",
        "first_name": "Carol",
        "last_name": "Davis",
        "university_id": "U0061003",
        "employee_id": "FAC-003",
        "department_code": "ME",
        "rank_name": "Assistant Professor",
        "hire_date": "2022-06-01",
    },
    {
        "username": "daniel.wilson",
        "email": "daniel.wilson@wisconsin.edu",
        "password": "faculty123",
        "first_name": "Daniel",
        "last_name": "Wilson",
        "university_id": "U0061004",
        "employee_id": "FAC-004",
        "department_code": "ECE",
        "rank_name": "Professor",
        "hire_date": "2015-09-20",
    },
    {
        "username": "emma.brown",
        "email": "emma.brown@wisconsin.edu",
        "password": "faculty123",
        "first_name": "Emma",
        "last_name": "Brown",
        "university_id": "U0061005",
        "employee_id": "FAC-005",
        "department_code": "FIN",
        "rank_name": "Associate Professor",
        "hire_date": "2019-03-05",
    },
    {
        "username": "frank.martinez",
        "email": "frank.martinez@wisconsin.edu",
        "password": "faculty123",
        "first_name": "Frank",
        "last_name": "Martinez",
        "university_id": "U0061006",
        "employee_id": "FAC-006",
        "department_code": "CS",
        "rank_name": "Assistant Professor",
        "hire_date": "2023-01-15",
    },
    {
        "username": "grace.lee",
        "email": "grace.lee@wisconsin.edu",
        "password": "faculty123",
        "first_name": "Grace",
        "last_name": "Lee",
        "university_id": "U0061007",
        "employee_id": "FAC-007",
        "department_code": "MATH",
        "rank_name": "Senior Lecturer",
        "hire_date": "2017-08-22",
        "tenure_track": False,
    },
    {
        "username": "henry.taylor",
        "email": "henry.taylor@wisconsin.edu",
        "password": "faculty123",
        "first_name": "Henry",
        "last_name": "Taylor",
        "university_id": "U0061008",
        "employee_id": "FAC-008",
        "department_code": "ME",
        "rank_name": "Professor",
        "hire_date": "2010-11-01",
    },
    {
        "username": "isabella.anderson",
        "email": "isabella.anderson@wisconsin.edu",
        "password": "faculty123",
        "first_name": "Isabella",
        "last_name": "Anderson",
        "university_id": "U0061009",
        "employee_id": "FAC-009",
        "department_code": "ECE",
        "rank_name": "Associate Professor",
        "hire_date": "2021-04-18",
    },
    {
        "username": "jackson.thomas",
        "email": "jackson.thomas@wisconsin.edu",
        "password": "faculty123",
        "first_name": "Jackson",
        "last_name": "Thomas",
        "university_id": "U0061010",
        "employee_id": "FAC-010",
        "department_code": "FIN",
        "rank_name": "Assistant Professor",
        "hire_date": "2022-09-12",
    },
]


class Command(BaseCommand):
    help = "Create faculty users and profiles"

    def handle(self, *args, **options):
        dept_map = {d.department_code: d.department_id for d in Department.objects.all()}
        if not dept_map:
            self.stderr.write(self.style.ERROR("No departments found. Run migrations and ensure departments exist."))
            return

        rank_cache = {}

        for entry in FACULTY_DATA:
            dept_id = dept_map.get(entry["department_code"])
            if dept_id is None:
                self.stderr.write(self.style.WARNING(f"Department '{entry['department_code']}' not found, skipping {entry['username']}"))
                continue

            rank_name = entry.pop("rank_name")
            tenure_track = entry.pop("tenure_track", True)
            department_code = entry.pop("department_code")

            if rank_name not in rank_cache:
                rank, _ = FacultyRank.objects.get_or_create(
                    rank_name=rank_name,
                    defaults={"tenure_track": tenure_track},
                )
                rank_cache[rank_name] = rank

            with transaction.atomic():
                user, user_created = User.objects.get_or_create(
                    username=entry["username"],
                    defaults={
                        "email": entry["email"],
                        "first_name": entry["first_name"],
                        "last_name": entry["last_name"],
                        "university_id": entry["university_id"],
                        "is_faculty": True,
                    },
                )
                if user_created:
                    user.set_password(entry["password"])
                    user.save()
                    self.stdout.write(self.style.SUCCESS(f"Created user: {user.username}"))
                else:
                    self.stdout.write(self.style.WARNING(f"User already exists: {user.username}"))

                profile, profile_created = FacultyProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        "employee_id": entry["employee_id"],
                        "email": entry["email"],
                        "department_id": dept_id,
                        "faculty_rank": rank_cache[rank_name],
                        "hire_date": entry["hire_date"],
                    },
                )
                if profile_created:
                    self.stdout.write(self.style.SUCCESS(f"  -> Created profile: {profile.employee_id}"))
                else:
                    self.stdout.write(self.style.WARNING(f"  -> Profile already exists: {profile.employee_id}"))

        self.stdout.write(self.style.SUCCESS(f"\nDone. Created faculty records."))
