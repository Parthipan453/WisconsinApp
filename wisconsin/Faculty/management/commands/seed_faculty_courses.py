"""
Idempotent seeder for Faculty course/schedule/advising demo data.

Populates: Semester, Course, CourseSection, Schedule,
FacultyCourseAssignment, StudentEnrollment, and advisee assignment
(StudentAcademicProfile.advisor_id), so the Faculty Dashboard has
real, non-zero data to display.

Safe to run multiple times — uses get_or_create/update_or_create everywhere.

Run with:
    python manage.py seed_faculty_courses --username jdoe
"""

from datetime import date, time, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction

from Faculty.models import FacultyProfile, FacultyCourseAssignment
from Students.models import (
    Course, CourseSection, Schedule, Semester,
    StudentEnrollment, StudentAcademicProfile,
)
from Admin.models import User
from Admin.bela_admin.models import Department
from Admin.Colleges.models import University,School


class Command(BaseCommand):
    help = "Seed courses, sections, schedules, enrollments, and advisees for a faculty account"

    def add_arguments(self, parser):
        parser.add_argument(
            "--username", type=str, default="jdoe",
            help="Username of the faculty account to attach demo data to (default: jdoe)",
        )
        parser.add_argument(
            "--num-students", type=int, default=5,
            help="Number of existing student1..N accounts to enroll/advise (default: 5)",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        username = options["username"]
        num_students = options["num_students"]

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                f"No user with username='{username}' found. "
                f"Run seed_dynamic_forms first, or pass --username <existing_faculty_username>."
            ))
            return

        try:
            faculty = FacultyProfile.objects.get(user=user)
        except FacultyProfile.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                f"User '{username}' has no FacultyProfile. Create one first."
            ))
            return

        semester = self._seed_semester()
        courses = self._seed_courses()
        sections = self._seed_sections(courses, semester)
        self._seed_assignments(faculty, sections)
        self._seed_schedules(sections)
        self._seed_enrollments(sections, num_students)
        self._seed_advisees(faculty, num_students)

        self.stdout.write(self.style.SUCCESS(
            f"Done seeding faculty course data for '{username}'."
        ))

    # ------------------------------------------------------------------
    from datetime import date

    def _seed_semester(self):
        semester, created = Semester.objects.get_or_create(
            academic_year=2026,
            semester_type="SPRING",
            defaults={
                "start_date": date(2026, 1, 20),
                "end_date": date(2026, 5, 15),
            },
        )
        if created:
            self.stdout.write("  Created Semester: Spring 2026")
        return semester

    # ------------------------------------------------------------------
    from Admin.bela_admin.models import Department

    def _seed_courses(self):
        university, _ = University.objects.get_or_create(
            university_code="UWM",
            defaults={
                "university_name": "University of Wisconsin-Madison",
                "university_short_name": "UW-Madison",
                "established_year": 1848,
            },
        )
        school, _ = School.objects.get_or_create(
            university=university, school_code="LS",
            defaults={
                "school_name": "College of Letters & Science",
                "school_short_name": "L&S",
                "school_type": "ACADEMIC",
            },
        )
        dept, _ = Department.objects.get_or_create(
            department_code="CS",
            defaults={
                "department_name": "Computer Sciences",
                "short_name": "CS",
                "school": school,
            },
        )

        course_data = [
            ("CS540", "Database Systems", 3),
            ("MATH101", "Calculus I", 4),
            ("ECE201", "Circuit Analysis", 3),
        ]
        courses = []
        for code, name, credits in course_data:
            course, created = Course.objects.get_or_create(
                course_code=code,
                defaults={
                    "course_name": name,
                    "credits": credits,
                    "department": dept,
                },
            )
            courses.append(course)
            if created:
                self.stdout.write(f"  Created Course: {code} - {name}")
        return courses
    # ------------------------------------------------------------------
    def _seed_sections(self, courses, semester):
        sections = []
        section_types = ["LEC", "LAB", "LEC"]
        capacities = [40, 25, 36]

        for i, course in enumerate(courses):
            section, created = CourseSection.objects.get_or_create(
                course=course,
                semester_id=semester,
                section_number="001",
                defaults={
                    "section_type": section_types[i % len(section_types)],
                    "capacity": capacities[i % len(capacities)],
                },
            )
            sections.append(section)
            if created:
                self.stdout.write(f"  Created CourseSection: {course.course_code} - 001")
        return sections

    # ------------------------------------------------------------------
    def _seed_assignments(self, faculty, sections):
        count = 0
        for section in sections:
            _, created = FacultyCourseAssignment.objects.get_or_create(
                faculty=faculty,
                course_section_id=section.section_id,
            )
            if created:
                count += 1
        if count:
            self.stdout.write(f"  Assigned {count} sections to faculty.")

    # ------------------------------------------------------------------
    def _seed_schedules(self, sections):
        """One weekly recurring class per section: today + a spread across the week."""
        today = date.today()
        week_start = today - timedelta(days=today.weekday())  # Monday

        day_codes = ["MON", "WED", "FRI"]
        start_times = [time(10, 0), time(13, 0), time(9, 0)]
        end_times = [time(11, 0), time(14, 30), time(10, 15)]
        rooms = [("Science Hall", "1310"), ("Engineering Hall", "2050"), ("Van Vleck", "B130")]

        count = 0
        for i, section in enumerate(sections):
            day_code = day_codes[i % len(day_codes)]
            day_offset = day_codes.index(day_code)  # 0=MON etc — adjust if your day_of_week uses ints

            # Generate this class's date for every week across a 16-week semester
            occurrence_dates = [
                (week_start + timedelta(days=day_offset) - timedelta(weeks=w)).isoformat()
                for w in range(-2, 14)  # 2 weeks back, 14 weeks forward
            ]
            # Make sure "today" is included if it lines up, so the dashboard's
            # "Teaching Schedule Today" card has something to show immediately.
            if today.strftime("%a").upper()[:3] == day_code[:3]:
                if today.isoformat() not in occurrence_dates:
                    occurrence_dates.append(today.isoformat())

            building, room = rooms[i % len(rooms)]

            schedule, created = Schedule.objects.get_or_create(
                section_id=section,
                day_of_week=day_code,
                defaults={
                    "start_time": start_times[i % len(start_times)],
                    "end_time": end_times[i % len(end_times)],
                    "room": room,
                    "building": building,
                    "is_online": False,
                    "dates": occurrence_dates,
                },
            )
            if not created:
                # Keep dates fresh even if the schedule row already existed
                schedule.dates = occurrence_dates
                schedule.save(update_fields=["dates"])
            if created:
                count += 1
        if count:
            self.stdout.write(f"  Created {count} schedule entries.")

    # ------------------------------------------------------------------
    def _seed_enrollments(self, sections, num_students):
        students = list(
            User.objects.filter(username__in=[f"student{i}" for i in range(1, num_students + 1)])
        )
        if not students:
            self.stdout.write(self.style.WARNING(
                "  No student1..N users found — run seed_dynamic_forms first to create them."
            ))
            return

        count = 0
        for section in sections:
            for student_user in students:
                _, created = StudentEnrollment.objects.get_or_create(
                    section_id=section,
                    student=student_user,
                )
                if created:
                    count += 1
        if count:
            self.stdout.write(f"  Created {count} student enrollments.")

    # ------------------------------------------------------------------
    def _seed_advisees(self, faculty, num_students):
        """Assign a couple of students as this faculty's advisees."""
        advisee_usernames = [f"student{i}" for i in range(1, min(3, num_students) + 1)]
        students = User.objects.filter(username__in=advisee_usernames)

        count = 0
        for student_user in students:
            try:
                profile = student_user.student_profile  # adjust related_name if different
            except Exception:
                continue

            academic_profile, _ = StudentAcademicProfile.objects.get_or_create(
                student=profile,
                defaults={"advisor_id": faculty.id},
            )
            if academic_profile.advisor_id != faculty.id:
                academic_profile.advisor_id = faculty.id
                academic_profile.save(update_fields=["advisor_id"])
            count += 1

        if count:
            self.stdout.write(f"  Assigned {count} advisees to faculty.")