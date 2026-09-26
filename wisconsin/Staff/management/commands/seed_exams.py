"""
Management command to seed dummy Exam & Rooms data for testing.

Usage:
    python manage.py seed_exams
    python manage.py seed_exams --count 100
    python manage.py seed_exams --count 50 --clear   # wipes existing exams first
"""

import random
from datetime import date, timedelta, time

from django.core.management.base import BaseCommand
from django.db import transaction

from Students.models import (
    Exam,
    ExamRoomAllocation,
    ExamInvigilator,
    CourseSection,
    Semester,
)
from Staff.models import StaffProfile
from Faculty.models import FacultyProfile
from Admin.bela_admin.models import Room


EXAM_TYPES = ["MIDTERM", "FINAL", "QUIZ", "PRACTICAL"]
STATUSES = ["DRAFT", "SCHEDULED", "COMPLETED", "CANCELLED"]
# Weighted so most exams look "in progress" rather than random junk
STATUS_WEIGHTS = [0.25, 0.45, 0.20, 0.10]

EXAM_NAME_PREFIXES = [
    "Semester 1", "Semester 2", "Midterm Assessment", "Final Assessment",
    "Unit Test", "Practical Exam", "Class Test", "End Term",
]

START_HOURS = [9, 10, 11, 13, 14, 15, 16]


class Command(BaseCommand):
    help = "Seed dummy Exam records (with room + invigilator assignments) for testing."

    def add_arguments(self, parser):
        parser.add_argument(
            "--count", type=int, default=100,
            help="Number of exams to create (default: 100)",
        )
        parser.add_argument(
            "--clear", action="store_true",
            help="Delete all existing Exam records before seeding.",
        )

    def handle(self, *args, **options):
        count = options["count"]
        clear = options["clear"]

        course_sections = list(CourseSection.objects.select_related("course").all())
        semesters = list(Semester.objects.all())
        rooms = list(Room.objects.filter(status="AVAILABLE"))
        faculty = list(FacultyProfile.objects.filter(employment_status="ACTIVE"))
        staff = StaffProfile.objects.first()

        if not course_sections:
            self.stderr.write(self.style.ERROR(
                "No CourseSection records found. Create some course sections first."
            ))
            return
        if not semesters:
            self.stderr.write(self.style.ERROR(
                "No Semester records found. Create at least one semester first."
            ))
            return
        if not staff:
            self.stderr.write(self.style.ERROR(
                "No StaffProfile found. Exam.created_by needs at least one staff user."
            ))
            return

        if clear:
            deleted, _ = Exam.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Cleared existing exam records."))

        created = 0
        today = date.today()

        with transaction.atomic():
            for i in range(count):
                section = random.choice(course_sections)
                semester = random.choice(semesters)

                exam_type = random.choice(EXAM_TYPES)
                status = random.choices(STATUSES, weights=STATUS_WEIGHTS, k=1)[0]

                # Spread dates across ±60 days from today so some are past
                # (completed), some upcoming (scheduled/draft)
                offset_days = random.randint(-30, 60)
                exam_date = today + timedelta(days=offset_days)

                start_hour = random.choice(START_HOURS)
                duration_minutes = random.choice([60, 90, 120, 150, 180])
                start_time = time(hour=start_hour, minute=0)
                end_dt_minutes = start_hour * 60 + duration_minutes
                end_time = time(hour=(end_dt_minutes // 60) % 24, minute=end_dt_minutes % 60)

                total_marks = random.choice([50, 75, 100, 150])
                pass_marks = int(total_marks * 0.4)

                exam_name = f"{random.choice(EXAM_NAME_PREFIXES)} #{i + 1}"

                exam = Exam.objects.create(
                    course_section=section,
                    semester=semester,
                    exam_name=exam_name,
                    exam_type=exam_type,
                    exam_date=exam_date,
                    start_time=start_time,
                    end_time=end_time,
                    duration_minutes=duration_minutes,
                    total_marks=total_marks,
                    pass_marks=pass_marks,
                    instructions="No electronic devices allowed. Bring your student ID.",
                    created_by=staff,
                    status=status,
                )

                # Randomly assign a room to ~70% of non-draft exams
                if rooms and status != "DRAFT" and random.random() < 0.7:
                    room = random.choice(rooms)
                    already_booked = ExamRoomAllocation.objects.filter(
                        room=room,
                        exam__exam_date=exam.exam_date,
                        exam__start_time__lt=exam.end_time,
                        exam__end_time__gt=exam.start_time,
                    ).exists()
                    if not already_booked:
                        ExamRoomAllocation.objects.create(
                            exam=exam,
                            room=room,
                            allocated_capacity=min(room.capacity, section.capacity or room.capacity),
                            allocated_by=staff,
                        )

                # Randomly assign an invigilator to ~65% of non-draft exams
                if faculty and status != "DRAFT" and random.random() < 0.65:
                    invigilator = random.choice(faculty)
                    already_assigned = ExamInvigilator.objects.filter(
                        faculty=invigilator,
                        exam__exam_date=exam.exam_date,
                        exam__start_time__lt=exam.end_time,
                        exam__end_time__gt=exam.start_time,
                    ).exists()
                    if not already_assigned:
                        ExamInvigilator.objects.create(
                            exam=exam,
                            faculty=invigilator,
                            assigned_by=staff,
                        )

                created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Successfully created {created} exam records."
        ))