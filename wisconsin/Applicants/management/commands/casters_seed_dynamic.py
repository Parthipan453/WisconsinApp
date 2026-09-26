 
import random
from datetime import date, timedelta
 
from django.core.management.base import BaseCommand
 
from Admin.models import User, UserRole
from Admin.Colleges.models import University, School, Degree, AcademicProgram, ProgramCourse
from Admin.bela_admin.models import Department, Course
from Faculty.models import FacultyRank, FacultyProfile
from Staff.models import StaffProfile, StaffPosition
from Students.models import (
    StudentProfile, StudentAcademicProfile, Semester,
  StudentEnrollment, Schedule, CourseSection
)
 
# ── constants ──────────────────────────────────────────────────────
 
FIRST_NAMES_M = [
    "James", "Michael", "Robert", "David", "William", "John", "Thomas",
    "Daniel", "Richard", "Charles", "Christopher", "Matthew", "Anthony",
    "Mark", "Donald", "Steven", "Paul", "Andrew", "Joshua", "Kenneth",
    "Kevin", "Brian", "George", "Timothy", "Ronald", "Jason", "Edward",
    "Jeffrey", "Ryan", "Jacob", "Nicholas", "Eric", "Jonathan", "Stephen",
    "Justin", "Scott", "Brandon", "Benjamin", "Samuel", "Raymond", "Gregory",
    "Frank", "Alexander", "Patrick", "Jack", "Dennis", "Tyler", "Aaron",
    "Jose", "Nathan", "Henry", "Peter", "Zachary", "Douglas", "Harold",
    "Carl", "Arthur", "Gerald", "Roger", "Keith", "Jeremy", "Terry",
    "Lawrence", "Sean", "Christian", "Ethan", "Austin", "Joe", "Louis",
    "Bobby", "Ralph", "Roy", "Eugene", "Randy", "Vincent", "Russell",
    "Billy", "Bobby", "Howard", "Philip", "Allen", "Leonard", "Karl",
]
 
FIRST_NAMES_F = [
    "Mary", "Patricia", "Jennifer", "Linda", "Barbara", "Elizabeth",
    "Susan", "Jessica", "Sarah", "Karen", "Lisa", "Nancy", "Betty",
    "Margaret", "Sandra", "Ashley", "Dorothy", "Kimberly", "Emily",
    "Donna", "Michelle", "Carol", "Amanda", "Melissa", "Deborah",
    "Stephanie", "Rebecca", "Sharon", "Laura", "Cynthia", "Kathleen",
    "Amy", "Angela", "Shirley", "Anna", "Brenda", "Pamela", "Emma",
    "Nicole", "Helen", "Samantha", "Katherine", "Christine", "Debra",
    "Rachel", "Carolyn", "Janet", "Catherine", "Maria", "Heather",
    "Diane", "Ruth", "Julie", "Olivia", "Joyce", "Virginia", "Victoria",
    "Kelly", "Lauren", "Christina", "Joan", "Evelyn", "Judith",
    "Megan", "Andrea", "Cheryl", "Hannah", "Jacqueline", "Martha",
    "Gloria", "Teresa", "Ann", "Sara", "Madison", "Frances", "Kathryn",
    "Janice", "Jean", "Abigail", "Alice", "Judy", "Sophia", "Grace",
]
 
LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
    "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green",
    "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz",
    "Parker", "Cruz", "Edwards", "Collins", "Reyes", "Stewart", "Morris",
    "Morales", "Murphy", "Cook", "Rogers", "Gutierrez", "Ortiz", "Morgan",
    "Cooper", "Peterson", "Bailey", "Reed", "Kelly", "Howard", "Ramos",
    "Kim", "Cox", "Ward", "Richardson", "Watson", "Brooks", "Chavez",
    "Wood", "James", "Bennett", "Gray", "Mendoza", "Ruiz", "Hughes",
    "Price", "Alvarez", "Castillo", "Sanders", "Patel", "Myers", "Long",
    "Ross", "Foster", "Jimenez", "Powell", "Jenkins", "Perry", "Russell",
]
 
DEPARTMENTS_DATA = [
    {"code": "CS", "name": "Computer Science", "short": "CS"},
    {"code": "EE", "name": "Electrical Engineering", "short": "EE"},
    {"code": "ME", "name": "Mechanical Engineering", "short": "ME"},
    {"code": "MATH", "name": "Mathematics", "short": "MATH"},
    {"code": "PHYS", "name": "Physics", "short": "PHYS"},
    {"code": "CHEM", "name": "Chemistry", "short": "CHEM"},
    {"code": "BIOL", "name": "Biology", "short": "BIOL"},
    {"code": "BUS", "name": "Business Administration", "short": "BUS"},
    {"code": "ENG", "name": "English", "short": "ENG"},
    {"code": "HIST", "name": "History", "short": "HIST"},
    {"code": "PSYCH", "name": "Psychology", "short": "PSYCH"},
    {"code": "ECON", "name": "Economics", "short": "ECON"},
]
 
# Course codes are NUMERIC ONLY (e.g. "101"), matching the app flow:
# CourseForm.clean_course_code enforces digits-only codes and the
# department FK provides the prefix (course_edit does int(course.course_code)).
COURSES_PER_DEPT = {
    "CS": [
        ("101", "Introduction to Computer Science", 3),
        ("201", "Data Structures", 3),
        ("301", "Algorithms", 3),
        ("302", "Operating Systems", 3),
        ("350", "Database Systems", 3),
        ("401", "Artificial Intelligence", 3),
        ("410", "Machine Learning", 3),
        ("420", "Software Engineering", 3),
        ("430", "Computer Networks", 3),
        ("440", "Cybersecurity", 3),
    ],
    "EE": [
        ("101", "Circuit Analysis I", 3),
        ("201", "Digital Logic Design", 3),
        ("301", "Signals and Systems", 3),
        ("310", "Microprocessors", 3),
        ("401", "Power Systems", 3),
        ("410", "Control Systems", 3),
        ("420", "Communication Systems", 3),
    ],
    "ME": [
        ("101", "Engineering Mechanics", 3),
        ("201", "Thermodynamics", 3),
        ("301", "Fluid Mechanics", 3),
        ("310", "Machine Design", 3),
        ("401", "Heat Transfer", 3),
        ("410", "Robotics", 3),
    ],
    "MATH": [
        ("101", "Calculus I", 4),
        ("102", "Calculus II", 4),
        ("201", "Linear Algebra", 3),
        ("301", "Differential Equations", 3),
        ("310", "Probability and Statistics", 3),
        ("401", "Numerical Analysis", 3),
    ],
    "PHYS": [
        ("101", "General Physics I", 4),
        ("102", "General Physics II", 4),
        ("201", "Mechanics", 3),
        ("301", "Electromagnetism", 3),
        ("401", "Quantum Mechanics", 3),
    ],
    "CHEM": [
        ("101", "General Chemistry I", 4),
        ("102", "General Chemistry II", 4),
        ("201", "Organic Chemistry I", 3),
        ("301", "Physical Chemistry", 3),
        ("401", "Biochemistry", 3),
    ],
    "BIOL": [
        ("101", "General Biology I", 4),
        ("102", "General Biology II", 4),
        ("201", "Genetics", 3),
        ("301", "Molecular Biology", 3),
        ("401", "Ecology", 3),
    ],
    "BUS": [
        ("101", "Introduction to Business", 3),
        ("201", "Accounting I", 3),
        ("301", "Marketing", 3),
        ("310", "Finance", 3),
        ("401", "Strategic Management", 3),
        ("410", "Organizational Behavior", 3),
    ],
    "ENG": [
        ("101", "English Composition", 3),
        ("201", "American Literature", 3),
        ("301", "World Literature", 3),
        ("310", "Creative Writing", 3),
        ("401", "Shakespeare Studies", 3),
    ],
    "HIST": [
        ("101", "World History I", 3),
        ("201", "American History", 3),
        ("301", "European History", 3),
        ("401", "Modern History", 3),
    ],
    "PSYCH": [
        ("101", "Introduction to Psychology", 3),
        ("201", "Developmental Psychology", 3),
        ("301", "Abnormal Psychology", 3),
        ("401", "Cognitive Psychology", 3),
        ("410", "Clinical Psychology", 3),
    ],
    "ECON": [
        ("101", "Principles of Microeconomics", 3),
        ("102", "Principles of Macroeconomics", 3),
        ("201", "Intermediate Microeconomics", 3),
        ("301", "Econometrics", 3),
        ("401", "International Economics", 3),
    ],
}
 
ROOMS = [
    ("101", "Science Hall"), ("102", "Science Hall"), ("103", "Science Hall"),
    ("201", "Engineering Building"), ("202", "Engineering Building"),
    ("301", "Liberal Arts Hall"), ("302", "Liberal Arts Hall"),
    ("101", "Business Center"), ("102", "Business Center"),
    ("Lab A", "Science Hall"), ("Lab B", "Engineering Building"),
]
 
FACULTY_RANKS = ["Professor", "Associate Professor", "Assistant Professor", "Lecturer"]
 
STAFF_TITLES = [
    "Enrollment Coordinator", "Academic Advisor", "Registrar",
    "Student Services Specialist", "Financial Aid Officer",
]
 
 
class Command(BaseCommand):
    help = "Seed casters demo data: admin, staff, faculty, 200 students, programs, courses, sections, enrollments"
 
    # ── university / school / degree ────────────────────────────────
 
    def _seed_university(self):
        self.stdout.write("  Seeding University...")
        uni, _ = University.objects.update_or_create(
            university_code="UW",
            defaults={
                "university_name": "University of Wisconsin",
                "university_short_name": "UW",
                "university_type": "PUBLIC",
                "ownership_type": "STATE",
                "official_email": "info@wisconsin.edu",
                "phone_number": "608-262-1234",
                "website": "https://www.wisconsin.edu",
                "address_line_1": "500 Lincoln Dr",
                "city": "Madison",
                "state": "Wisconsin",
                "country": "United States",
                "postal_code": "53706",
                "established_year": 1848,
                "status": "ACTIVE",
            },
        )
        return uni
 
    def _seed_school(self, uni):
        self.stdout.write("  Seeding School...")
        school, _ = School.objects.update_or_create(
            school_name="College of Science and Engineering",
            defaults={
                "university": uni,
                "school_short_name": "CSE",
                "school_code": "COS",
                "school_type": "ACADEMIC",
                "official_email": "cse@wisconsin.edu",
                "city": "Madison",
                "state": "Wisconsin",
                "country": "United States",
                "status": "ACTIVE",
            },
        )
        return school
 
    def _seed_degrees(self):
        self.stdout.write("  Seeding Degrees...")
        degrees = {}
        data = [
            ("Bachelor of Science", "BS", "UG"),
            ("Bachelor of Arts", "BA", "UG"),
            ("Master of Science", "MS", "PG"),
            ("Doctor of Philosophy", "PhD", "PHD"),
        ]
        for name, code, level in data:
            deg, _ = Degree.objects.update_or_create(
                degree_name=name,
                defaults={"degree_code": code, "level": level, "status": "ACTIVE"},
            )
            degrees[code] = deg
        return degrees
 
    # ── departments & courses ───────────────────────────────────────
 
    def _seed_departments(self, school):
        self.stdout.write("  Seeding Departments...")
        departments = {}
        for d in DEPARTMENTS_DATA:
            dept, _ = Department.objects.update_or_create(
                department_code=d["code"],
                defaults={
                    "school": school,
                    "department_name": d["name"],
                    "short_name": d["short"],
                    "description": f"The Department of {d['name']} at the University of Wisconsin.",
                    "status": "ACTIVE",
                },
            )
            departments[d["code"]] = dept
        return departments
 
    def _migrate_legacy_course_codes(self):
        """Older seed runs created prefixed codes like 'BUS201' / 'CS101'.
        The app flow requires numeric-only course codes (course_edit calls
        int(course.course_code)), so rewrite legacy rows in place instead of
        leaving them behind as broken duplicates. Existing sections,
        enrollments and curriculum links stay attached because only the
        course_code string changes."""
        import re
 
        from django.utils.text import slugify
 
        legacy = Course.objects.exclude(course_code__regex=r"^\d+$")
        if not legacy.exists():
            return
        self.stdout.write(f"  Migrating {legacy.count()} legacy non-numeric course codes...")
        for course in legacy:
            digits = "".join(ch for ch in course.course_code if ch.isdigit())
            candidate = digits if digits else "100"
            while Course.objects.filter(
                department=course.department,
                course_code=candidate,
            ).exclude(pk=course.pk).exists():
                candidate = str(int(candidate) + 1)
            course.course_code = candidate
            course.slug = slugify(f"{course.course_code} {course.course_name}")
            course.save(update_fields=["course_code", "slug", "updated_at"])
 
    def _seed_courses(self, departments, degrees):
        self.stdout.write("  Seeding Courses...")
        all_courses = {}
        default_degree = degrees.get("BS")
        for dept_code, course_list in COURSES_PER_DEPT.items():
            dept = departments[dept_code]
            for code, name, credits in course_list:
                # Unique per (department, code), same rule as CourseForm
                course, _ = Course.objects.update_or_create(
                    department=dept,
                    course_code=code,
                    defaults={
                        "course_name": name,
                        "credits": credits,
                        "description": f"Course: {name}",
                        "degree": default_degree,
                        "status": "ACTIVE",
                    },
                )
                all_courses[f"{dept_code}{code}"] = course
        return all_courses
 
    # ── programs & curriculum ───────────────────────────────────────
 
    def _seed_programs(self, departments, degrees):
        self.stdout.write("  Seeding Academic Programs...")
        programs = {}
        bs = degrees["BS"]
        # One program per department
        for dept_code, dept in departments.items():
            pname = f"{dept.department_name} (BS)"
            prog, _ = AcademicProgram.objects.update_or_create(
                program_code=f"{dept_code}-BS",
                defaults={
                    "department": dept,
                    "degree": bs,
                    "program_name": pname,
                    "program_type": "FULL_TIME",
                    "duration": 4,
                    "total_credits": 120,
                    "description": f"BS program in {dept.department_name}",
                    "status": "ACTIVE",
                },
            )
            programs[dept_code] = prog
        # Link courses to their department's program
        for dept_code, prog in programs.items():
            Course.objects.filter(department=prog.department, academic_program__isnull=True).update(academic_program=prog)
        return programs
 
    def _seed_program_curriculum(self, programs, all_courses):
        self.stdout.write("  Seeding Program Curriculum (ProgramCourse)...")
        count = 0
        terms = ["FALL", "SPRING"]
        for dept_code, prog in programs.items():
            # Assign courses from same department to this program
            matching = [c for c in all_courses.values() if c.department.department_code == dept_code]
            for i, course in enumerate(matching):
                year = (i // 2) + 1
                if year > 4:
                    year = 4
                term = terms[i % 2]
                pc, created = ProgramCourse.objects.get_or_create(
                    program=prog,
                    study_year=year,
                    term=term,
                    course=course,
                    defaults={"status": "ACTIVE"},
                )
                if created:
                    count += 1
        self.stdout.write(f"    Created {count} new curriculum entries")
 
    # ── semesters ───────────────────────────────────────────────────
 
    def _seed_semesters(self):
        self.stdout.write("  Seeding Semesters...")
        semesters = {}
        sem_data = [
            ("FA2023", "FA", 2023, "2023-08-28", "2023-12-15", False),
            ("SP2024", "SP", 2024, "2024-01-16", "2024-05-10", False),
            ("SU2024", "SU", 2024, "2024-06-03", "2024-08-02", False),
            ("FA2024", "FA", 2024, "2024-08-26", "2024-12-13", True),
            ("SP2025", "SP", 2025, "2025-01-21", "2025-05-09", False),
            ("FA2025", "FA", 2025, "2025-09-02", "2025-12-12", False),
        ]
        for code, stype, year, start, end, current in sem_data:
            sem, _ = Semester.objects.update_or_create(
                semester_code=code,
                defaults={
                    "semester_type": stype,
                    "academic_year": year,
                    "start_date": date.fromisoformat(start),
                    "end_date": date.fromisoformat(end),
                    "is_current": current,
                },
            )
            semesters[code] = sem
        return semesters
 
    # ── course sections ─────────────────────────────────────────────
 
    def _seed_sections(self, all_courses, semesters):
        self.stdout.write("  Seeding Course Sections...")
        sections = {}
        section_types = ['LEC', 'LEC', 'LAB']
        for course_code, course in all_courses.items():
            for sem_code, sem in semesters.items():
                for sec_idx in range(1, 4):
                    snum = str(sec_idx).zfill(2)
                    room, building = random.choice(ROOMS)
                    key = f"{course_code}_{sem_code}_s{sec_idx}"
                    sec, _ = CourseSection.objects.update_or_create(
                        course=course,
                        section_number=snum,
                        semester_id=sem,
                        defaults={
                            "section_type": section_types[sec_idx - 1],
                            "capacity": random.choice([25, 30, 35, 40]),
                            "room_number": room,
                            "building_name": building,
                            "faculty_name": "",
                            "status": "CONFIRMED",
                            "is_active": True,
                        },
                    )
                    sections[key] = sec
        return sections
 
    # ── users: admin, faculty, staff ────────────────────────────────
 
    def _seed_admin(self):
        self.stdout.write("  Seeding Admin user...")
        role, _ = UserRole.objects.get_or_create(role_name="System Admin", user_type="admin")
        if User.objects.filter(username="mass").exists():
            u = User.objects.get(username="mass")
            if not u.check_password("mass"):
                u.set_password("mass")
                u.save()
            return u
        u = User.objects.create_superuser(username="mass", email="admin@wisconsin.edu")
        u.set_password("mass")
        u.first_name = "System"
        u.last_name = "Administrator"
        u.is_admin = True
        u.is_super_admin = True
        u.role = role
        u.save()
        return u
 
    def _seed_faculty(self, departments):
        self.stdout.write("  Seeding Faculty users...")
        faculty_list = []
        roles = {}
        for rname in FACULTY_RANKS:
            rank, _ = FacultyRank.objects.get_or_create(rank_name=rname)
            roles[rname] = rank
 
        dept_list = list(departments.values())
 
        # First faculty: username=pass, password=pass
        dept = dept_list[0]
        if User.objects.filter(username="pass").exists():
            u = User.objects.get(username="pass")
            if not u.check_password("pass"):
                u.set_password("pass")
                u.save()
            faculty_list.append(FacultyProfile.objects.get(employee_id="FAC0001"))
        else:
            u = User.objects.create_user(
                username="pass", email="pass@wisconsin.edu",
            )
            u.set_password("pass")
            u.first_name = "Faculty"
            u.last_name = "Admin"
            u.is_faculty = True
            u.save()
            fp = FacultyProfile.objects.create(
                user=u,
                employee_id="FAC0001",
                email="pass@wisconsin.edu",
                faculty_rank=roles["Professor"],
                department=dept,
                hire_date=date(2018, 1, 15),
                employment_status="ACTIVE",
            )
            faculty_list.append(fp)
 
        for i in range(1, 12):
            dept = dept_list[i % len(dept_list)]
            fname = random.choice(FIRST_NAMES_M + FIRST_NAMES_F)
            lname = random.choice(LAST_NAMES)
            uname = f"faculty{i+1}"
            email = f"{uname}@wisconsin.edu"
            if User.objects.filter(username=uname).exists():
                u = User.objects.get(username=uname)
                if not u.check_password("faculty123"):
                    u.set_password("faculty123")
                    u.save()
                faculty_list.append(FacultyProfile.objects.get(employee_id=f"FAC{i+1:04d}"))
                continue
            u = User.objects.create_user(
                username=uname, email=email,
            )
            u.set_password("faculty123")
            u.first_name = fname
            u.last_name = lname
            u.is_faculty = True
            u.is_staff = False
            u.save()
            rank_name = FACULTY_RANKS[i % len(FACULTY_RANKS)]
            fp = FacultyProfile.objects.create(
                user=u,
                employee_id=f"FAC{i+1:04d}",
                email=email,
                faculty_rank=roles[rank_name],
                department=dept,
                hire_date=date(2018 + i, 1, 15),
                employment_status="ACTIVE",
            )
            faculty_list.append(fp)
        return faculty_list
 
    def _seed_staff(self):
        self.stdout.write("  Seeding Staff users...")
        staff_list = []
        role, _ = UserRole.objects.get_or_create(role_name="Staff", user_type="staff")
 
        # First staff: username=class, password=class
        if User.objects.filter(username="class").exists():
            u = User.objects.get(username="class")
            if not u.check_password("class"):
                u.set_password("class")
                u.save()
            staff_list.append(StaffProfile.objects.get(employee_id="STF0001"))
        else:
            u = User.objects.create_user(
                username="class", email="class@wisconsin.edu",
            )
            u.set_password("class")
            u.first_name = "Staff"
            u.last_name = "Admin"
            u.is_staff = True
            u.role = role
            u.save()
            sp = StaffProfile.objects.create(
                user=u,
                employee_id="STF0001",
                work_email="class@wisconsin.edu",
                hire_date=date(2019, 3, 1),
                employment_status="ACTIVE",
                employment_type="FULL_TIME",
            )
            StaffPosition.objects.create(
                staff=sp,
                job_title=STAFF_TITLES[0],
                position_start_date=date(2019, 3, 1),
                position_status="ACTIVE",
            )
            staff_list.append(sp)
 
        for i in range(1, 8):
            fname = random.choice(FIRST_NAMES_M + FIRST_NAMES_F)
            lname = random.choice(LAST_NAMES)
            uname = f"staff{i+1}"
            email = f"{uname}@wisconsin.edu"
            if User.objects.filter(username=uname).exists():
                u = User.objects.get(username=uname)
                if not u.check_password("staff123"):
                    u.set_password("staff123")
                    u.save()
                staff_list.append(StaffProfile.objects.get(employee_id=f"STF{i+1:04d}"))
                continue
            u = User.objects.create_user(
                username=uname, email=email,
            )
            u.set_password("staff123")
            u.first_name = fname
            u.last_name = lname
            u.is_staff = True
            u.role = role
            u.save()
            sp = StaffProfile.objects.create(
                user=u,
                employee_id=f"STF{i+1:04d}",
                work_email=email,
                hire_date=date(2019 + i, 3, 1),
                employment_status="ACTIVE",
                employment_type="FULL_TIME",
            )
            StaffPosition.objects.create(
                staff=sp,
                job_title=STAFF_TITLES[i % len(STAFF_TITLES)],
                position_start_date=date(2019 + i, 3, 1),
                position_status="ACTIVE",
            )
            staff_list.append(sp)
        return staff_list
 
    # ── students ────────────────────────────────────────────────────
 
    def _seed_students(self, departments, programs, semesters):
        self.stdout.write("  Seeding 200 Students...")
        role, _ = UserRole.objects.get_or_create(role_name="Student", user_type="student")
        dept_list = list(departments.values())
        sem_keys = sorted(semesters.keys())
        # Current semester is FA2024
        current_sem = semesters.get("FA2024") or list(semesters.values())[0]
 
        # Year distribution: more freshmen, fewer seniors
        year_weights = {1: 70, 2: 55, 3: 45, 4: 30}
        year_pool = []
        for y, w in year_weights.items():
            year_pool.extend([y] * w)
        random.seed(42)
        random.shuffle(year_pool)
 
        # Track sequence numbers per (program_code, admission_year)
        seq_counter = {}
 
        students = []
        for i in range(200):
            year = year_pool[i % len(year_pool)]
            dept = random.choice(dept_list)
            dept_code = dept.department_code
            prog = programs.get(dept_code)
            fname = random.choice(FIRST_NAMES_M if i % 2 == 0 else FIRST_NAMES_F)
            lname = random.choice(LAST_NAMES)
            uname = f"student{i+1:03d}"
            email = f"{uname}@my.wisconsin.edu"
            admission_year = 2024 - year + 1  # e.g. year 1 -> admitted 2024, year 2 -> 2023
            prog_code = prog.program_code if prog else "GEN"
            seq_key = f"{prog_code}_{admission_year}"
            seq_counter[seq_key] = seq_counter.get(seq_key, 0) + 1
            student_number = f"{admission_year}{prog_code}{seq_counter[seq_key]:03d}"
            if User.objects.filter(username=uname).exists():
                u = User.objects.get(username=uname)
                if not u.check_password("student123"):
                    u.set_password("student123")
                    u.save()
                students.append(StudentProfile.objects.get(user=u))
                continue
            u = User.objects.create_user(
                username=uname, email=email,
            )
            u.set_password("student123")
            u.first_name = fname
            u.last_name = lname
            u.is_student = True
            u.save()
 
            sp = StudentProfile.objects.create(
                user=u,
                student_number=student_number,
                university_email=email,
                program=prog,
                admission_date=date(admission_year, 8, 25),
                expected_graduation_date=date(admission_year + 4, 5, 15),
                current_status="ACTIVE",
                academic_level="UNDERGRADUATE",
                cumulative_gpa=round(random.uniform(2.5, 4.0), 2),
            )
 
            # Find the school this dept belongs to
            school = dept.school
 
            StudentAcademicProfile.objects.create(
                student=sp,
                university=dept.school.university,
                school=school,
                department=dept,
                degree=prog.degree if prog else None,
                program=prog,
                major=dept.department_name,
                catalog_year=admission_year,
            )
 
            # Enroll student in 3-5 courses from their department
            dept_courses = [
                c for c in Course.objects.filter(department=dept)
            ]
            if not dept_courses:
                continue
            num_courses = random.randint(3, min(5, len(dept_courses)))
            chosen_courses = random.sample(dept_courses, num_courses)
 
            for course in chosen_courses:
                sec_key = f"{course.course_code}_{current_sem.semester_code}"
                section = None
                # Find a section for this course in current semester
                section = CourseSection.objects.filter(
                    course=course, semester_id=current_sem
                ).first()
                if not section:
                    continue
                enrollment_status = random.choice(["FULL_TIME", "FULL_TIME", "PART_TIME"])
                standing = random.choice(
                    ["GOOD_STANDING", "GOOD_STANDING", "GOOD_STANDING", "HONOR_ROLL", "DEAN_LIST"]
                )
                StudentEnrollment.objects.get_or_create(
                    student=sp,
                    section_id=section,
                    semester=current_sem,
                    defaults={
                        "enrollment_status": enrollment_status,
                        "credit_load": course.credits,
                        "academic_standing": standing,
                    },
                )
 
            students.append(sp)
            if (i + 1) % 50 == 0:
                self.stdout.write(f"    ... {i+1}/200 students created")
 
        return students
 
    # ── main handle ─────────────────────────────────────────────────
 
    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("Seeding casters demo data..."))
 
        uni = self._seed_university()
        school = self._seed_school(uni)
        degrees = self._seed_degrees()
        departments = self._seed_departments(school)
        self._migrate_legacy_course_codes()
        all_courses = self._seed_courses(departments, degrees)
        programs = self._seed_programs(departments, degrees)
        self._seed_program_curriculum(programs, all_courses)
        semesters = self._seed_semesters()
       
        self._seed_admin()
        faculty = self._seed_faculty(departments)
        staff = self._seed_staff()
        students = self._seed_students(departments, programs, semesters)
 
        self.stdout.write(self.style.SUCCESS(
            f"\nDone! Seeded: 1 admin, {len(staff)} staff, {len(faculty)} faculty, "
            f"{len(students)} students, {len(departments)} departments, "
            f"{len(all_courses)} courses, {len(programs)} programs, "
           
        ))