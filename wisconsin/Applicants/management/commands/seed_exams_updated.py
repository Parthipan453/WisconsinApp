"""
seed_all.py
------------
ONE management command that seeds everything, in order:
Departments -> Courses -> Semesters -> Users -> Rooms
-> Course Sections -> Exams

Place this file at:
    <your_app>/management/commands/seed_all.py

Run it with:
    python manage.py seed_all

NOTE: I don't have your real model field names, so several fields below
are best-guess placeholders marked with "# ADJUST:". Update those to match
your actual models before running.
"""

from datetime import date, time, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

# ADJUST: import paths / model names below to match your project
from Admin.bela_admin.models import Room, Course, Department, Building, Floor
from Students.models import (
    Exam,
    ExamRoomAllocation,
    ExamInvigilator,
    ExamSeat,
    ExamAttendance,
    StudentProfile,
    CourseSection,
    Semester,
)
from Faculty.models import FacultyProfile
from Staff.models import StaffProfile

User = get_user_model()


class Command(BaseCommand):
    help = "Seed the entire database in correct order (single-file version)"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING(">>> Starting full database seeding...\n"))

        try:
            with transaction.atomic():
                seed_departments(self)
                seed_courses(self)
                seed_semesters(self)
                seed_users(self)
                seed_rooms(self)
                seed_course_sections(self)
                seed_exams(self)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n[ERROR] Seeding failed: {e}"))
            return

        self.stdout.write(self.style.SUCCESS("\n>>> ALL DATA SEEDED SUCCESSFULLY!"))


# ======================================================================
# 1. DEPARTMENTS
# ======================================================================
def seed_departments(cmd):
    cmd.stdout.write("... Seeding Departments...")

    if Department.objects.exists():
        cmd.stdout.write("[SKIP] Departments already exist, skipping...")
        return

    # ADJUST: field names (department_name, department_code) to match your model
    departments = [
        {"department_name": "Computer Science", "department_code": "CS"},
        {"department_name": "Electronics", "department_code": "EC"},
        {"department_name": "Mechanical", "department_code": "ME"},
    ]

    for dept in departments:
        Department.objects.create(**dept)

    cmd.stdout.write(cmd.style.SUCCESS("[OK] Departments seeded"))


# ======================================================================
# 2. COURSES
# ======================================================================
def seed_courses(cmd):
    cmd.stdout.write("... Seeding Courses...")

    if Course.objects.count() >= 10:
        cmd.stdout.write("[SKIP] 10+ Courses already exist, skipping...")
        return

    department = Department.objects.first()
    if department is None:
        cmd.stdout.write(cmd.style.ERROR("[ERROR] No Department found, cannot create Courses"))
        return

    created = 0
    for i in range(1, 11):
        course, was_created = Course.objects.get_or_create(
            course_code=f"CS{100 + i}",
            defaults={
                "course_name": f"Course {i}",
                "credits": 4,
                "department": department,
            },
        )
        if was_created:
            created += 1

    cmd.stdout.write(cmd.style.SUCCESS(f"[OK] Courses seeded ({created} created, {Course.objects.count()} total)"))


# ======================================================================
# 3. SEMESTERS
# ======================================================================
def seed_semesters(cmd):
    cmd.stdout.write("... Seeding Semesters...")

    if Semester.objects.exists():
        cmd.stdout.write("[SKIP] Semesters already exist, skipping...")
        return

    Semester.objects.create(
        semester_code="FA2026",
        semester_type="FA",  # FA=Fall, SP=Spring, SU=Summer, WI=Winter
        academic_year=2026,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=120),
        is_current=True,
    )

    cmd.stdout.write(cmd.style.SUCCESS("[OK] Semesters seeded"))


# ======================================================================
# 4. USERS (Students, Faculty, Staff)
# ======================================================================
def seed_users(cmd):
    cmd.stdout.write("... Seeding Users...")

    if StudentProfile.objects.exists() or FacultyProfile.objects.exists() or StaffProfile.objects.exists():
        cmd.stdout.write("[SKIP] Users already exist, skipping...")
        return

    # --- Staff (1) ---
    staff_user, _ = User.objects.get_or_create(
        username="staff1",
        defaults={"email": "staff1@example.com"},
    )
    staff_user.set_password("password123")
    staff_user.save()
    # ADJUST: field names on StaffProfile
    StaffProfile.objects.create(user=staff_user, employee_id="STF001")

    # --- Faculty (2) ---
    for i in range(1, 3):
        user, _ = User.objects.get_or_create(
            username=f"faculty{i}",
            defaults={"email": f"faculty{i}@example.com"},
        )
        user.set_password("password123")
        user.save()
        # ADJUST: field names on FacultyProfile
        FacultyProfile.objects.create(user=user, employee_id=f"FAC00{i}")

    # --- Students (10) ---
    for i in range(1, 11):
        user, _ = User.objects.get_or_create(
            username=f"student{i}",
            defaults={"email": f"student{i}@example.com"},
        )
        user.set_password("password123")
        user.save()
        StudentProfile.objects.create(
            user=user,
            student_number=f"STU{i:03d}",
            university_email=f"student{i}@example.com",
        )

    cmd.stdout.write(cmd.style.SUCCESS("[OK] Users (staff, faculty, students) seeded"))


# ======================================================================
# 5. ROOMS
# ======================================================================
def seed_rooms(cmd):
    cmd.stdout.write("... Seeding Rooms...")

    if Room.objects.exists():
        cmd.stdout.write("[SKIP] Rooms already exist, skipping...")
        return

    # Room requires a Floor, which requires a Building. Create the chain.
    building, _ = Building.objects.get_or_create(
        building_code="BLDG-A",
        defaults={"building_name": "Main Building"},
    )

    floor, _ = Floor.objects.get_or_create(
        building=building,
        floor_number=1,
        defaults={"floor_name": "Ground Floor"},
    )

    rooms = [
        {"room_number": "101", "room_name": "Room 101", "capacity": 30},
        {"room_number": "102", "room_name": "Room 102", "capacity": 30},
    ]

    for r in rooms:
        Room.objects.create(floor=floor, **r)

    cmd.stdout.write(cmd.style.SUCCESS("[OK] Rooms seeded"))


# ======================================================================
# 6. COURSE SECTIONS
# ======================================================================
def seed_course_sections(cmd):
    cmd.stdout.write("... Seeding Course Sections...")

    if CourseSection.objects.count() >= 10:
        cmd.stdout.write("[SKIP] 10+ Course Sections already exist, skipping...")
        return

    courses = list(Course.objects.all()[:10])
    semester = Semester.objects.first()

    if not courses or not semester:
        cmd.stdout.write(cmd.style.ERROR("[ERROR] Missing Courses or Semester, cannot create CourseSections"))
        return

    created = 0
    for course in courses:
        section, was_created = CourseSection.objects.get_or_create(
            course=course,
            semester_id=semester,  # field is literally named semester_id (assign the Semester instance)
            section_number="A",
            defaults={
                "section_type": "LEC",
                "capacity": 60,
                "status": "CONFIRMED",
            },
        )
        if was_created:
            created += 1

    cmd.stdout.write(cmd.style.SUCCESS(
        f"[OK] Course Sections seeded ({created} created, {CourseSection.objects.count()} total)"
    ))


# ======================================================================
# 7. EXAMS
# ======================================================================
def seed_exams(cmd):
    cmd.stdout.write("... Seeding Exams...")

    if Exam.objects.count() >= 10:
        cmd.stdout.write("[SKIP] 10+ Exams already exist, skipping...")
        return

    course_sections = list(CourseSection.objects.all()[:10])
    semester = Semester.objects.first()
    staff = StaffProfile.objects.first()
    rooms = list(Room.objects.all()[:2])
    faculty_list = list(FacultyProfile.objects.all()[:2])
    students = list(StudentProfile.objects.all()[:10])

    if not all([course_sections, semester, staff, rooms, faculty_list, students]):
        cmd.stdout.write(cmd.style.ERROR("[ERROR] Missing prerequisite data, cannot create Exams"))
        return

    created = 0
    for idx, course_section in enumerate(course_sections, start=1):
        exam, was_created = Exam.objects.get_or_create(
            course_section=course_section,
            exam_type="MIDTERM",
            defaults={
                "semester": semester,
                "exam_name": f"Midterm Exam - {course_section.course.course_code}",
                "exam_date": date.today(),
                "start_time": time(10, 0),
                "end_time": time(12, 0),
                "duration_minutes": 120,
                "total_marks": 100,
                "pass_marks": 40,
                "instructions": "Answer all questions",
                "status": "SCHEDULED",
                "created_by": staff,
            },
        )
        if not was_created:
            continue
        created += 1

        # Room allocation
        for room in rooms:
            ExamRoomAllocation.objects.create(
                exam=exam,
                room=room,
                allocated_capacity=30,
                allocated_by=staff,
            )

        # Invigilators
        for faculty in faculty_list:
            ExamInvigilator.objects.create(
                exam=exam,
                faculty=faculty,
                assigned_by=staff,
            )

        # Seat allocation
        for seat_idx, student in enumerate(students, start=1):
            room = rooms[(seat_idx - 1) % len(rooms)]
            ExamSeat.objects.create(
                exam=exam,
                student=student,
                room=room,
                seat_number=f"{idx}-{seat_idx}",
            )

        # Attendance
        for student in students:
            ExamAttendance.objects.create(
                exam=exam,
                student=student,
                attendance="PRESENT",
            )

    cmd.stdout.write(cmd.style.SUCCESS(f"[OK] Exams seeded ({created} created, {Exam.objects.count()} total)"))