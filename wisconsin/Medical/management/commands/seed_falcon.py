"""
Idempotent seeder for dynamic form engine metadata.

Safe to run multiple times — uses update-or-create logic everywhere.
Run with:  python manage.py seed_dynamic_forms
"""

from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password

from Admin.models import User, UserRole, Firearm, OlympicAthlete, OlympicPerformance
from Admin.Colleges.models import University, School, Degree, AcademicProgram
from Admin.bela_admin.models import Department
from Admin.Jack.models import Sport, SportClub, Coach, SportsFacility, SportTeamModel, Athletic

from Applicants.models import (
    FormDefinition, FormSection, FormField, FieldChoice, ValidationRule,
    VisibilityRule,
    FormResponse,
    FormAssignment, WorkflowDefinition, DynamicWorkflowStep, StepCondition,
    DocumentRequirement, AdmissionCycle, ApplicantTypeRequirement,
    ApplicationFee,
)
from Faculty.models import FacultyRank, FacultyProfile
from Staff.models import StaffProfile, StaffPosition
from Students.models import StudentProfile


class Command(BaseCommand):
    help = "Seed/update dynamic form engine metadata idempotently"

    FORM_CODES_TO_KEEP = {
        "basic_information", "academic_history", "holistic_background",
    }

    def _seed_admin_user(self):
        if User.objects.filter(username="admin").exists():
            return
        role, _ = UserRole.objects.get_or_create(role_name="System Admin", user_type="admin")
        admin = User.objects.create_superuser(
            username="admin", email="admin@wisconsin.edu",
        )
        admin.set_password("admin")
        admin.first_name = "System"
        admin.last_name = "Administrator"
        admin.is_admin = True
        admin.is_super_admin = True
        admin.role = role
        admin.save()
        self.stdout.write("  Created admin user (admin / admin).")

    def _seed_university_structure(self):
        if University.objects.count() > 0:
            return
        uw = University.objects.create(
            university_name="University of Wisconsin-Madison",
            university_short_name="UW-Madison",
            university_code="UWM",
            official_email="info@wisc.edu",
            phone_number="608-262-2400",
            address_line_1="500 Lincoln Dr",
            city="Madison", state="Wisconsin", country="USA", postal_code="53706",
            website="https://www.wisc.edu", accreditation="HLC",
            established_year=1848,
        )
        ls = School.objects.create(university=uw, school_name="College of Letters & Science",
            school_short_name="L&S", school_code="LS",
            description="The College of Letters & Science is the largest college at UW-Madison.")
        eng = School.objects.create(university=uw, school_name="College of Engineering",
            school_short_name="Engineering", school_code="ENGR",
            description="The College of Engineering at UW-Madison.")
        bus = School.objects.create(university=uw, school_name="Wisconsin School of Business",
            school_short_name="Business", school_code="BUS",
            description="The Wisconsin School of Business.")

        for level in ("UG", "PG", "PHD"):
            label = {"UG": "Undergraduate", "PG": "Postgraduate", "PHD": "Doctorate"}[level]
            Degree.objects.create(
                degree_name=f"Bachelor of {label}" if level == "UG" else
                           f"Master of {label}" if level == "PG" else "Doctor of Philosophy",
                degree_code=level, level=level,
            )

        departments = {
            "CS": ("Computer Sciences", ls, "cs@cs.wisc.edu"),
            "MATH": ("Mathematics", ls, "math@math.wisc.edu"),
            "ME": ("Mechanical Engineering", eng, "me@engr.wisc.edu"),
            "ECE": ("Electrical & Computer Engineering", eng, "ece@engr.wisc.edu"),
            "FIN": ("Finance", bus, "fin@bus.wisc.edu"),
        }
        depts = {}
        for code, (name, school, email) in departments.items():
            depts[code] = Department.objects.create(
                school=school, department_code=code, department_name=name,
                short_name=code, description=f"The {name} department.", email=email,
            )

        ug = Degree.objects.get(degree_code="UG")
        pg = Degree.objects.get(degree_code="PG")
        phd = Degree.objects.get(degree_code="PHD")

        programs = [
            ("BS-CS", depts["CS"], ug, "BS Computer Sciences"),
            ("MS-CS", depts["CS"], pg, "MS Computer Sciences"),
            ("PhD-CS", depts["CS"], phd, "PhD Computer Sciences"),
            ("BS-MATH", depts["MATH"], ug, "BS Mathematics"),
            ("MS-MATH", depts["MATH"], pg, "MS Mathematics"),
            ("BS-ME", depts["ME"], ug, "BS Mechanical Engineering"),
            ("MS-ME", depts["ME"], pg, "MS Mechanical Engineering"),
            ("BS-ECE", depts["ECE"], ug, "BS Electrical Engineering"),
            ("MS-ECE", depts["ECE"], pg, "MS Electrical Engineering"),
            ("BBA-FIN", depts["FIN"], ug, "BBA Finance"),
            ("MBA-FIN", depts["FIN"], pg, "MBA Finance"),
        ]
        for code, dept, deg, name in programs:
            AcademicProgram.objects.create(
                program_code=code, department=dept, degree=deg,
                program_name=name, program_type="FULL_TIME", duration=4, total_credits=120,
            )
        self.stdout.write("  Created university structure  ")

    def _seed_admission_cycles(self):
        today = date.today()
        year = today.year if today.month >= 6 else today.year - 1
        next_year = year + 1

        cycles_data = [
            {
                "name": f"Fall {year} Regular Decision",
                "code": f"FA{year}_RD",
                "academic_year": f"{year}-{next_year}",
                "term": "Fall",
                "application_start": date(year, 1, 1),
                "application_deadline": date(year, 8, 1),
                "deadline_type": "regular",
                "decision_release": date(year, 9, 15),
                "is_active": True,
                "is_open": True,
            },
            {
                "name": f"Fall {year} Early Action",
                "code": f"FA{year}_EA",
                "academic_year": f"{year}-{next_year}",
                "term": "Fall",
                "application_start": date(year, 1, 1),
                "application_deadline": date(year, 6, 1),
                "deadline_type": "early_action",
                "decision_release": date(year, 7, 15),
                "is_active": True,
                "is_open": True,
            },
            {
                "name": f"Fall {year} Early Decision",
                "code": f"FA{year}_ED",
                "academic_year": f"{year}-{next_year}",
                "term": "Fall",
                "application_start": date(year, 1, 1),
                "application_deadline": date(year, 5, 1),
                "deadline_type": "early_decision",
                "decision_release": date(year, 6, 1),
                "is_active": True,
                "is_open": True,
            },
            {
                "name": f"Fall {next_year} Regular Decision",
                "code": f"FA{next_year}_RD",
                "academic_year": f"{next_year}-{next_year + 1}",
                "term": "Fall",
                "application_start": date(next_year, 1, 1),
                "application_deadline": date(next_year, 8, 1),
                "deadline_type": "regular",
                "decision_release": date(next_year, 9, 15),
                "is_active": True,
                "is_open": next_year <= year + 1,
            },
            {
                "name": f"Fall {next_year} Early Action",
                "code": f"FA{next_year}_EA",
                "academic_year": f"{next_year}-{next_year + 1}",
                "term": "Fall",
                "application_start": date(next_year, 1, 1),
                "application_deadline": date(next_year, 6, 1),
                "deadline_type": "early_action",
                "decision_release": date(next_year, 7, 15),
                "is_active": True,
                "is_open": next_year <= year + 1,
            },
            {
                "name": f"Spring {next_year} Transfer",
                "code": f"SP{next_year}_TR",
                "academic_year": f"{year}-{next_year}",
                "term": "Spring",
                "application_start": date(year, 4, 1),
                "application_deadline": date(year, 10, 1),
                "deadline_type": "spring_transfer",
                "decision_release": date(year, 11, 15),
                "is_active": True,
                "is_open": True,
            },
            {
                "name": f"Fall {next_year} Priority Deadline",
                "code": f"FA{next_year}_PD",
                "academic_year": f"{next_year}-{next_year + 1}",
                "term": "Fall",
                "application_start": date(next_year, 1, 1),
                "application_deadline": date(next_year, 4, 1),
                "deadline_type": "priority",
                "decision_release": date(next_year, 5, 15),
                "is_active": True,
                "is_open": next_year <= year + 1,
            },
            {
                "name": f"Summer {next_year} Rolling",
                "code": f"SU{next_year}_RL",
                "academic_year": f"{year}-{next_year}",
                "term": "Summer",
                "application_start": date(year, 9, 1),
                "application_deadline": date(next_year, 5, 1),
                "deadline_type": "rolling",
                "decision_release": date(next_year, 6, 1),
                "is_active": True,
                "is_open": True,
            },
        ]

        for data in cycles_data:
            AdmissionCycle.objects.update_or_create(
                code=data["code"],
                defaults=data,
            )
        self.stdout.write(f"  Seeded/updated {len(cycles_data)} admission cycles.")

    def _seed_sample_users(self):
        if FacultyProfile.objects.count() > 0:
            self.stdout.write("  Sample users already exist, skipping.")
            return

        for role_name, user_type in [("Faculty", "faculty"), ("Staff", "staff"), ("Student", "student"),("is_medical_staff","is_medical_staff")]:
            UserRole.objects.get_or_create(role_name=role_name, user_type=user_type)

        prof, _ = FacultyRank.objects.get_or_create(rank_name="Professor", defaults={"tenure_track": True})
        assoc, _ = FacultyRank.objects.get_or_create(rank_name="Associate Professor", defaults={"tenure_track": True})

        password = "Test@123"

        for username, email, fn, ln, role_name, is_faculty, is_staff, is_student,is_medical_staff in [
            ("faculty", "fac@cs.wisc.edu", "bala", "K", "Faculty", True, False, False,False),
            ("faculty1", "fac1@cs.wisc.edu", "gowtham", "g", "Faculty", True, False, False,False),
            ("staff", "staff@wisc.edu", "prabhu", "B", "Staff", False, True, False,False),
            ("staff1", "staff1@wisc.edu", "kishore", "G", "Staff", False, True, False,False),
            ("medical", "mstaff@wisc.edu", "medical", "B", "Staff", False, True, False,True),

        ]:
            user, _ = User.objects.get_or_create(username=username, defaults=dict(
                email=email, first_name=fn, last_name=ln,
                account_status="ACTIVE",
                role=UserRole.objects.get(role_name=role_name),
                is_faculty=is_faculty, is_staff=is_staff, is_student=is_student,
                is_medical_staff=is_medical_staff,
            ))
           
            user.is_faculty = is_faculty
            user.is_staff = is_staff
            user.is_student = is_student
            user.is_medical_staff = is_medical_staff
            user.set_password(password)
            user.save(update_fields=[
                "password", "is_faculty", "is_staff", "is_student", "is_medical_staff",
            ])

        
        cs_dept = Department.objects.get(department_code="CS")
        uprof = User.objects.get(username="faculty")
        FacultyProfile.objects.get_or_create(user=uprof, defaults=dict(
            employee_id="FAC001", email="fac1@cs.wisc.edu",
            phone="608-262-1001", office_location="CS 1245",
            hire_date=date(2010, 8, 15), faculty_rank=prof,
            employment_status="ACTIVE",
        ))
        usmith = User.objects.get(username="faculty1")
        FacultyProfile.objects.get_or_create(user=usmith, defaults=dict(
            employee_id="FAC002", email="fac2@cs.wisc.edu",
            phone="608-262-1002", office_location="CS 1247",
            hire_date=date(2015, 8, 15), faculty_rank=assoc,
            employment_status="ACTIVE",
        ))

        ustaff = User.objects.get(username="staff")
        sp, _ = StaffProfile.objects.get_or_create(user=ustaff, defaults=dict(
            employee_id="STF001", work_email="staff@wisc.edu",
            hire_date=date(2018, 3, 1),
            employment_status="ACTIVE", employment_type="FULL_TIME",
        ))
        StaffPosition.objects.get_or_create(staff=sp, job_title="Admissions Officer", defaults=dict(
            position_start_date=date(2018, 3, 1), position_status="ACTIVE",
        ))

        ustaff2 = User.objects.get(username="staff1")
        sp2, _ = StaffProfile.objects.get_or_create(user=ustaff2, defaults=dict(
            employee_id="STF002", work_email="staff1@wisc.edu",
            hire_date=date(2019, 6, 1),
            employment_status="ACTIVE", employment_type="FULL_TIME",
        ))
        StaffPosition.objects.get_or_create(staff=sp2, job_title="Registrar", defaults=dict(
            position_start_date=date(2019, 6, 1), position_status="ACTIVE",
        ))


        ustaff3 = User.objects.get(username="medical")
        sp3, _ = StaffProfile.objects.get_or_create(user=ustaff3, defaults=dict(
            employee_id="STF003", work_email="medical@wisc.edu",
            hire_date=date(2019, 6, 1),
            employment_status="ACTIVE", employment_type="FULL_TIME",
        ))
        StaffPosition.objects.get_or_create(staff=sp3, job_title="Medical_staff", defaults=dict(
            position_start_date=date(2019, 6, 1), position_status="ACTIVE",
        ))

        for i in range(1, 6):
            sfirst = ["Jeyakada", "Palani", "Sarav", "Muthu", "Ashwel"][i - 1]
            slast = ["D", "K", "W", "B", "A"][i - 1]
            uname = f"student{i}"
            ustud, _ = User.objects.get_or_create(username=uname, defaults=dict(
                email=f"{uname}@wisc.edu", first_name=sfirst, last_name=slast,
                account_status="ACTIVE",
                role=UserRole.objects.get(role_name="Student"),
                is_student=True,
            ))
            ustud.set_password(password)
            ustud.save(update_fields=["password"])
            StudentProfile.objects.get_or_create(user=ustud, defaults=dict(
                student_number=f"STU{i:05d}",
                university_email=f"{uname}@wisc.edu",
                admission_date=date(2023, 8, 20),
                expected_graduation_date=date(2027, 5, 15),
                academic_level="UNDERGRADUATE",
                cumulative_gpa=Decimal(f"{3.0 + i * 0.2:.2f}"),
                current_status="ACTIVE",
            ))

        self.stdout.write("  Created sample faculty, staff, and student users (password: Test@123).")



    def _seed_sportshub_sample_data(self):
        if Sport.objects.count() > 0:
            self.stdout.write("  SportsHub sample data already exists, skipping.")
            return

        sports_data = [
            ("Cricket", "OUTDOOR", "MALE", True, 11, 15),
            ("Kabaddi", "INDOOR", "MALE", True, 7, 12),
            ("Athletics", "OUTDOOR", "MALE", False, None, None),
        ]
        sports = {}
        for name, sport_type, gender, is_team, min_p, max_p in sports_data:
            sport, _ = Sport.objects.get_or_create(
                sport_name=name,
                defaults=dict(
                    sport_type=sport_type, gender=gender, is_team_sport=is_team,
                    min_players=min_p, max_players=max_p,
                    is_olympic_sport=True, is_active=True,
                ),
            )
            sports[name] = sport

        clubs_data = [
            ("Chennai Super Cricket Club", "Cricket",
             "Premier cricket club based in Chennai."),
            ("Madurai Kabaddi Club", "Kabaddi",
             "Kabaddi club representing the Madurai region."),
            ("Tamil Nadu Athletics Club", "Athletics",
             "Athletics club training track and field athletes."),
        ]
        clubs = {}
        for club_name, sport_name, desc in clubs_data:
            club, _ = SportClub.objects.get_or_create(
                club_name=club_name,
                defaults=dict(sport=sports[sport_name], description=desc, is_active=True),
            )
            clubs[club_name] = club

        coaches_data = [
            ("COACH001", "HEAD", date(2015, 6, 1), "Level 3 Cricket Coaching Certificate"),
            ("COACH002", "HEAD", date(2017, 3, 15), "National Kabaddi Coaching License"),
            ("COACH003", "HEAD", date(2019, 9, 10), "Athletics Federation of India Certified Coach"),
        ]
        coaches = {}
        for staff_id, role, hire_date_, certs in coaches_data:
            coach, _ = Coach.objects.get_or_create(
                staff_id=staff_id,
                defaults=dict(role=role, hire_date=hire_date_, certifications=certs, is_active=True),
            )
            coaches[staff_id] = coach

        facilities_data = [
            ("Nehru Stadium", "Cricket", "STADIUM", 50000, "Chennai, Tamil Nadu"),
            ("Kabaddi Indoor Arena", "Kabaddi", "ARENA", 5000, "Madurai, Tamil Nadu"),
            ("Jawaharlal Nehru Athletics Track", "Athletics", "FIELD", 20000, "Coimbatore, Tamil Nadu"),
        ]
        facilities = {}
        for facility_name, sport_name, ftype, capacity, location in facilities_data:
            facility, _ = SportsFacility.objects.get_or_create(
                facility_name=facility_name,
                defaults=dict(
                    sport=sports[sport_name], facility_type=ftype, capacity=capacity,
                    location=location, status="ACTIVE",
                ),
            )
            facilities[facility_name] = facility

        teams_data = [
            ("TN-CRIC-01", "Tamil Nadu Cricket Team", "Cricket", "MALE", "Division I", "2025-26",
             "COACH001", "Nehru Stadium", 1998, "Chennai Super Cricket Club"),
            ("TN-KAB-01", "Tamil Nadu Kabaddi Team", "Kabaddi", "MALE", "Division I", "2025-26",
             "COACH002", "Kabaddi Indoor Arena", 2005, "Madurai Kabaddi Club"),
            ("TN-ATH-01", "Tamil Nadu Athletics Team", "Athletics", "MALE", "Open", "2025-26",
             "COACH003", "Jawaharlal Nehru Athletics Track", 2010, "Tamil Nadu Athletics Club"),
        ]
        teams = {}
        for code, name, sport_name, gender, division, season, coach_id, facility_name, founded, club_name in teams_data:
            team, _ = SportTeamModel.objects.get_or_create(
                team_code=code,
                defaults=dict(
                    team_name=name, sport_type=sports[sport_name], gender_category=gender,
                    division=division, season=season, head_coach=coaches[coach_id],
                    home_facility=facilities[facility_name], founded_year=founded,
                    status=True, club=clubs[club_name],
                ),
            )
            teams[code] = team

        
        athletes_data = [
            ("arun", "arun@wisc.edu", "Arun", "K", "TN-ATH-01", 101, "Sprinter", 178, 70),
            ("ram", "ram@wisc.edu", "Ram", "P", "TN-ATH-01", 102, "Long Jump", 180, 74),
            ("kali", "karthi@wisc.edu", "Kali", "B", "TN-ATH-01", 103, "Javelin Throw", 182, 80),
        ]
        password = "Test@123"
        athlete_role, _ = UserRole.objects.get_or_create(role_name="Student", user_type="student")
        for username, email, fn, ln, team_code, jersey, position, height, weight in athletes_data:
            user, _ = User.objects.get_or_create(username=username, defaults=dict(
                email=email, first_name=fn, last_name=ln,
                account_status="ACTIVE", role=athlete_role, is_student=True,
            ))
            user.set_password(password)
            user.save(update_fields=["password"])

            athletic, _ = Athletic.objects.get_or_create(
                student=user,
                defaults=dict(
                    team=teams[team_code], jersey_number=jersey, position=position,
                    height=Decimal(str(height)), weight=Decimal(str(weight)),
                    class_year="SOPHOMORE", eligibility_status="ELIGIBLE",
                    scholarship_status=True, is_active=True,
                ),
            )
            athletic.individual_sports.add(sports["Athletics"])

        self.stdout.write("  Seeded SportsHub sample data (3 records per model).")

   

    def _seed_olympic_and_firearm_sample_data(self):
        if OlympicAthlete.objects.count() > 0:
            self.stdout.write("  Firearm/Olympic sample data already exists, skipping.")
            return

        
        medical_user = User.objects.filter(username="medical").first()
        firearms_data = [
            ("Campus Security Sidearm A", "HANDGUN", "Glock", "G19",
             "SN-FA-001", "9mm", "ACTIVE"),
            ("Campus Security Sidearm B", "HANDGUN", "Smith & Wesson", "M&P Shield",
             "SN-FA-002", "9mm", "STORED"),
            ("Campus Security Training Rifle", "TRAINING", "Ruger", "10/22",
             "SN-FA-003", ".22 LR", "ACTIVE"),
        ]
        for name, ftype, manufacturer, model_name, serial, caliber, status in firearms_data:
            Firearm.objects.get_or_create(
                serial_number=serial,
                defaults=dict(
                    user=medical_user, firearm_name=name, firearm_type=ftype,
                    manufacturer=manufacturer, model_name=model_name, caliber=caliber,
                    acquisition_method="PURCHASE", location_name="Campus Security Armory",
                    building_name="Public Safety Building", room_number="B12",
                    security_level="Restricted", current_status=status,
                ),
            )

        
        sport_athletics = Sport.objects.get(sport_name="Athletics")
        coach_athletics = Coach.objects.get(staff_id="COACH003")
        athlete_config = [
            ("arun", "OLY-ARN-001", "100m Sprint", 12, "10.11s"),
            ("ram", "OLY-RAM-001", "Long Jump", 8, "7.85m"),
            ("kali", "OLY-KAR-001", "Javelin Throw", 5, "82.30m"),
        ]
        olympic_athletes = {}
        for username, athlete_number, event_name, ranking, personal_best in athlete_config:
            athletic = Athletic.objects.get(student__username=username)
            oa, _ = OlympicAthlete.objects.get_or_create(
                athlete=athletic,
                defaults=dict(
                    sport=sport_athletics, coach=coach_athletics,
                    athlete_number=athlete_number, nationality="India",
                    olympic_status="SELECTED", target_olympics="Paris 2028",
                    event_name=event_name, event_category="INDIVIDUAL",
                    governing_body="Athletics Federation of India",
                    world_ranking=ranking, qualification_date=date(2026, 3, 1),
                    qualification_status="QUALIFIED", personal_best=personal_best,
                    is_active=True,
                ),
            )
            olympic_athletes[username] = oa

        performance_config = [
            ("arun", "National Athletics Championship", "NATIONAL", "100m Sprint",
             date(2026, 2, 10), "New Delhi", "India", "10.15s", 1, "GOLD"),
            ("ram", "Asian Athletics Championship", "INTERNATIONAL", "Long Jump",
             date(2026, 4, 5), "Bangkok", "Thailand", "7.80m", 2, "SILVER"),
            ("kali", "National Athletics Championship", "NATIONAL", "Javelin Throw",
             date(2026, 2, 12), "New Delhi", "India", "81.50m", 1, "GOLD"),
        ]
        for username, comp_name, level, event_name, comp_date, city, country, score, ranking, medal in performance_config:
            OlympicPerformance.objects.get_or_create(
                olympic_athlete=olympic_athletes[username],
                competition_name=comp_name,
                defaults=dict(
                    competition_level=level, event_name=event_name, competition_date=comp_date,
                    host_city=city, host_country=country, score_time=score,
                    ranking=ranking, medal=medal, participation_status="COMPLETED",
                ),
            )

        self.stdout.write(
            "  Seeded Firearm/OlympicAthlete/OlympicPerformance sample data (3 records per model)."
        )

    def _seed_degrees(self):
        degrees = [
            ("UG", "Undergraduate"),
            ("PG", "Postgraduate"),
            ("PHD", "Doctor of Philosophy"),
        ]

        for code, name in degrees:
            Degree.objects.get_or_create(
                degree_code=code,
                defaults={
                    "degree_name": name
                }
            )
    def handle(self, *args, **options):
        self._seed_admin_user()
        self._seed_university_structure()
        self._seed_admission_cycles()
        self._seed_sample_users()
        self._seed_sportshub_sample_data()
        self._seed_olympic_and_firearm_sample_data()
        self._seed_degrees()
        self._seed_applicant_type_requirements()
        self._seed_forms()
        self._seed_cleanup_old_forms()
        self._seed_cleanup_orphans()
        self._seed_form_assignments()
        self._seed_workflow()
        self._seed_document_requirements()
        self._seed_application_fees()
        self.stdout.write(self.style.SUCCESS("Done."))

    def _seed_application_fees(self):
        """Seed per-campus application fees (idempotent). A fee of 0.00 means no fee."""
        fees = {
            "University of Wisconsin-Madison": "80.00",
            "UW-Madison": "80.00",
            "University of Wisconsin-La Crosse": "25.00",
            "UW-La Crosse": "25.00",
        }
        for university in University.objects.filter(status="ACTIVE"):
            amount = fees.get(university.university_name) or fees.get(university.university_short_name or "", "25.00")
            ApplicationFee.objects.update_or_create(
                university=university,
                defaults={
                    "amount": amount,
                    "currency": "USD",
                    "waiver_available": True,
                },
            )
        self.stdout.write(self.style.SUCCESS(f"  Seeded {ApplicationFee.objects.count()} application fee record(s)."))

    def _seed_cleanup_old_forms(self):
        """Remove forms not in the keep list (reparenting responses first)."""
        FormAssignment.objects.filter(form__isnull=True).delete()
     
        for fr in FormResponse.objects.select_related("section__form", "form").iterator():
            if fr.section and fr.section.form_id != fr.form_id:
                FormResponse.objects.filter(pk=fr.pk).update(form_id=fr.section.form_id)
        removed = FormDefinition.objects.exclude(code__in=self.FORM_CODES_TO_KEEP).delete()
        if removed[0]:
            self.stdout.write(f"  Removed {removed[0]} old form records.")

    def _seed_cleanup_orphans(self):
        """Remove fields not present in any kept form's sections."""
        kept_section_ids = set(FormSection.objects.filter(
            form__code__in=self.FORM_CODES_TO_KEEP,
        ).values_list("id", flat=True))
        extra = FormField.objects.exclude(section_id__in=kept_section_ids)
        fc = extra.count()
        if fc:
            extra.delete()
            self.stdout.write(f"  Removed {fc} orphaned fields.")
        FieldChoice.objects.filter(field__isnull=True).delete()
        ValidationRule.objects.filter(field__isnull=True).delete()
        StepCondition.objects.filter(step__isnull=True).delete()

    def _purge_extra_fields(self):
        """Remove fields within kept sections that are no longer seeded."""
        extra = FormField.objects.exclude(code__in=self._kept_field_codes).filter(
            section__form__code__in=self.FORM_CODES_TO_KEEP,
        )
        fc = extra.count()
        if fc:
            extra.delete()
            self.stdout.write(f"  Removed {fc} extra fields from kept forms.")

   

    def _get_or_create_form(self, code, **defaults):
        obj, created = FormDefinition.objects.update_or_create(
            code=code, defaults=defaults,
        )
        if created:
            self.stdout.write(f"  Created form: {obj.name}")
        return obj

    def _get_basic_info_form(self):
        """The single 'Basic Information' form holding all five sub-sections."""
        return self._get_or_create_form(
            "basic_information",
            name="Basic Information",
            description="Personal, contact, and demographic information",
            icon="user", sort_order=1,
        )

    def _move_section(self, form, code, title, sort_order):
        """Reparent an existing section (by code) onto the given form, then upsert."""
        sec = FormSection.objects.filter(code=code).first()
        if sec and sec.form_id != form.pk:
            sec.form = form
            sec.save()
        return self._get_or_create_section(
            form, code, title=title, sort_order=sort_order,
        )

    def _get_or_create_section(self, form, code, **defaults):
        obj, created = FormSection.objects.update_or_create(
            form=form, code=code, defaults=defaults,
        )
        return obj, created

    def _get_or_create_field(self, section, code, **defaults):
        
        if "layout_width" not in defaults:
            field_type = defaults.get("field_type", "text")
            long_field = (
                field_type in {"textarea", "rich_text", "radio", "checkbox", "file"}
                or "address" in code
                or "description" in code
            )
            defaults["layout_width"] = "full" if long_field else "half"
        obj, created = FormField.objects.update_or_create(
            section=section, code=code, defaults=defaults,
        )
        self._kept_field_codes.add(code)
        return obj, created

    def _add_validation(self, field, validation_type, **defaults):
        defaults.setdefault("value", "")
        defaults.setdefault("value_max", "")
        defaults.setdefault("error_message", "")
        ValidationRule.objects.update_or_create(
            field=field, validation_type=validation_type,
            defaults=defaults,
        )

    def _add_choice(self, field, value, **defaults):
        FieldChoice.objects.update_or_create(
            field=field, value=value,
            defaults=defaults,
        )

    def _add_required(self, field):
        self._add_validation(
            field, "required",
            error_message=f"{field.label} is required",
        )

    def _add_visibility(self, field, target_field, operator, value, logic="AND"):
        VisibilityRule.objects.update_or_create(
            field=field,
            target_field=target_field,
            defaults={
                "operator": operator,
                "value": value,
                "logic_operator": logic,
                "is_active": True,
                "sort_order": 0,
            },
        )

 

    def _seed_applicant_type_requirements(self):
        ug = Degree.objects.get(degree_code="UG")
        pg = Degree.objects.get(degree_code="PG")
        phd = Degree.objects.get(degree_code="PHD")
        configs = [
            ("first_year", ug, True, True, True, False, 24),
            ("transfer", ug, True, True, False, True, None),
            ("reentry", ug, True, False, True, False, None),
            ("second_degree", ug, True, False, True, False, None),
            ("international_first_year", ug, True, True, True, False, 24),
            ("international_transfer", ug, True, True, True, True, None),
            ("first_year", pg, True, True, True, False, None),
            ("transfer", pg, True, True, True, True, None),
            ("international_first_year", pg, True, True, True, False, None),
            ("international_transfer", pg, True, True, True, True, None),
            ("first_year", phd, True, True, True, False, None),
            ("transfer", phd, True, True, True, True, None),
            ("international_first_year", phd, True, True, True, False, None),
            ("international_transfer", phd, True, True, True, True, None),
        ]
        count = 0
        for atype, dl, transcript, essay, test_scores, college_transcript, transfer_credits in configs:
            _, created = ApplicantTypeRequirement.objects.update_or_create(
                applicant_type=atype, degree_level=dl,
                defaults={
                    "requires_transcript": transcript,
                    "requires_essay": essay,
                    "requires_test_scores": test_scores,
                    "requires_college_transcript": college_transcript,
                    "requires_high_school_courses": True,
                    "requires_activities": True,
                    "requires_honors": True,
                    "requires_recommendations": False,
                    "test_optional": True,
                    "requires_resume": False,
                    "min_transfer_credits": transfer_credits,
                    "is_active": True,
                },
            )
            if created:
                count += 1
        if count:
            self.stdout.write(f"  Created {count} applicant type requirements.")

 

    def _seed_forms(self):
        self._kept_field_codes = set()
        self._form_1_personal_information()
        self._form_2_contact_information()
        self._form_3_parent_guardian()
        self._form_4_residency()
        self._form_5_academic_history()
        self._form_6_additional_information()
        self._form_7_holistic_background()
        self._purge_extra_fields()

    def _form_1_personal_information(self):
        form = self._get_basic_info_form()
        sec, _ = self._move_section(form, "personal_info",
            title="Basic Information", sort_order=1)

        required = {"first_name", "last_name", "date_of_birth", "legal_sex", "citizenship_country"}
        encrypted = {"ssn", "confirm_ssn"}
        for code, label, ftype, order, width in [
            ("first_name","First Name","text",1,"half"),
            ("last_name","Last Name","text",2,"half"),
            ("middle_name","Middle Name (Optional)","text",3,"half"),
            ("preferred_name","Preferred Name (Optional)","text",4,"half"),
            ("suffix","Suffix (Optional)","select",5,"half"),
            ("name_changed","Has your name ever changed?","radio",6,"full"),
            ("old_first_name","Previous First Name","text",7,"half"),
            ("old_middle_name","Previous Middle Name","text",8,"half"),
            ("old_last_name","Previous Last Name","text",9,"half"),
            ("legal_sex","Legal Sex","select",13,"half"),
            ("gender","Gender (Optional)","select",14,"half"),
            ("date_of_birth","Date of Birth","date",15,"half"),
            ("identification_type","Which form of identification can you provide?","radio",16,"full"),
            ("ssn","US Social Security Number","text",17,"half"),
            ("confirm_ssn","Confirm Social Security Number","text",18,"half"),
            ("tin","US Tax Identification Number","text",19,"half"),
            ("confirm_tin","Confirm Tax Identification Number","text",20,"half"),
            ("citizenship_country","Citizenship Country","country",21,"half"),
            ("birth_country","Birth Country","country",22,"half"),
            ("birth_city","Birth City","city",23,"half"),
            ("birth_state","Birth State","state",24,"half"),
            ("parent_degree","Have either parent/guardian earned a four-year degree?","radio",25,"full"),
            ("agent_advisor","Are you working with an agent or advisor?","radio",26,"full"),
            ("advisor_name","Advisor Name","text",27,"full"),
        ]:
            fld, _ = self._get_or_create_field(sec, code,
                label=label, field_type=ftype, sort_order=order,
                layout_width=width, is_required=(code in required),
                is_encrypted=(code in encrypted),
            )
            if code in required:
                self._add_required(fld)

      
        dob = FormField.objects.get(section=sec, code="date_of_birth")
        self._add_validation(dob, "max_value", value="today-15y",
            error_message="You must be at least 15 years old to apply.")

        for code, placeholder in [
            ("ssn", "XXX-XX-XXXX"),
            ("confirm_ssn", "XXX-XX-XXXX"),
            ("tin", "XX-XXXXXXX"),
            ("confirm_tin", "XX-XXXXXXX"),
        ]:
            FormField.objects.filter(section=sec, code=code).update(placeholder=placeholder)

       
        name_regex = r"^[a-zA-Z\s'-]{2,50}$"
        name_msg = "Enter valid name."
        first_regex = r"^[a-zA-Z\s'-]{3,50}$"
        first_msg = "Enter valid name."
        last_regex = r"^[a-zA-Z\s'-]{1,50}$"
        last_msg = "Enter valid name."
        for code, regex, msg in [
            ("first_name", first_regex, first_msg),
            ("last_name", last_regex, last_msg),
            ("middle_name", name_regex, name_msg),
            ("preferred_name", name_regex, name_msg),
            ("old_first_name", first_regex, first_msg),
            ("old_last_name", last_regex, last_msg),
            ("old_middle_name", name_regex, name_msg),
        ]:
            f = FormField.objects.get(section=sec, code=code)
            self._add_validation(f, "regex", value=regex, error_message=msg)

        ssn_regex = r"^\d{3}-\d{2}-\d{4}$"
        tin_regex = r"^\d{2}-\d{7}$"
        for code, regex, msg in [
            ("ssn", ssn_regex, "Enter valid SSN."),
            ("tin", tin_regex, "Enter valid TIN."),
        ]:
            f = FormField.objects.get(section=sec, code=code)
            self._add_validation(f, "regex", value=regex, error_message=msg)

        for code, maxlen in [
            ("ssn", 11),
            ("confirm_ssn", 11),
            ("tin", 10),
            ("confirm_tin", 10),
        ]:
            f = FormField.objects.get(section=sec, code=code)
            self._add_validation(f, "max_length", value=str(maxlen))

        advisor_regex = r"^[a-zA-Z\s'-]{2,100}$"
        f = FormField.objects.get(section=sec, code="advisor_name")
        self._add_validation(f, "regex", value=advisor_regex, error_message="Enter valid name.")

        for code, match_target in [
            ("confirm_ssn", "ssn"),
            ("confirm_tin", "tin"),
        ]:
            f = FormField.objects.get(section=sec, code=code)
            self._add_validation(f, "custom", value=f"match:{match_target}", error_message="Values do not match.")

        name_changed_f = FormField.objects.get(section=sec, code="name_changed")
        for target_code in ("old_first_name", "old_middle_name", "old_last_name"):
            target_f = FormField.objects.get(section=sec, code=target_code)
            VisibilityRule.objects.update_or_create(
                field=target_f,
                target_field=name_changed_f,
                defaults={
                    "operator": "eq",
                    "value": "yes",
                    "is_active": True,
                    "sort_order": 0,
                },
            )

        id_type_f = FormField.objects.get(section=sec, code="identification_type")
        citizenship_f = FormField.objects.get(section=sec, code="citizenship_country")
        for target_code, expected_value in [
            ("ssn", "ssn"),
            ("confirm_ssn", "ssn"),
            ("tin", "tin"),
            ("confirm_tin", "tin"),
        ]:
            target_f = FormField.objects.get(section=sec, code=target_code)
            VisibilityRule.objects.update_or_create(
                field=target_f,
                target_field=id_type_f,
                defaults={
                    "operator": "eq",
                    "value": expected_value,
                    "is_active": True,
                    "sort_order": 0,
                },
            )
            VisibilityRule.objects.update_or_create(
                field=target_f,
                target_field=citizenship_f,
                defaults={
                    "operator": "eq",
                    "value": "United States",
                    "is_active": True,
                    "sort_order": 1,
                    "logic_operator": "AND",
                },
            )

        agent_f = FormField.objects.get(section=sec, code="agent_advisor")
        target_f = FormField.objects.get(section=sec, code="advisor_name")
        VisibilityRule.objects.update_or_create(
            field=target_f,
            target_field=agent_f,
            defaults={
                "operator": "eq",
                "value": "yes",
                "is_active": True,
                "sort_order": 0,
            },
        )

        gf = FormField.objects.get(section=sec, code="gender")
        for i, (v, lbl) in enumerate([("male","Male"),("female","Female"),("other","Other"),("prefer_not_to_say","Prefer not to say")]):
            self._add_choice(gf, v, label=lbl, sort_order=i, is_default=False)
        for code, choices in {
            "suffix": [("", "Select Suffix"), ("jr", "Jr."), ("sr", "Sr."), ("ii", "II"), ("iii", "III")],
            "legal_sex": [("female", "Female"), ("male", "Male")],
            "name_changed": [("yes", "Yes"), ("no", "No")],
            "identification_type": [("ssn", "US Social Security Number"), ("tin", "US Tax Identification Number"), ("none", "Do Not Have / Do Not Want to Provide")],
            "parent_degree": [("yes", "Yes"), ("no", "No")],
            "agent_advisor": [("yes", "Yes"), ("no", "No")],
        }.items():
            choice_field = FormField.objects.get(section=sec, code=code)
            for index, (value, label) in enumerate(choices):
                self._add_choice(choice_field, value, label=label, sort_order=index, is_default=(index == 0 and not value))

    def _form_2_contact_information(self):
        form = self._get_basic_info_form()
        sec, _ = self._move_section(form, "contact_info",
            title="Contact Information", sort_order=3)
        required_codes = {"email", "address_line1", "country", "city"}
        for code, label, ftype, order, req in [
            ("email", "Email Address", "email", 1, True),
            ("phone", "Phone Number (Optional)", "phone", 2, False),
            ("phone_type", "Phone Type (Optional)", "select", 3, False),
            ("address_line1", "Address", "text", 4, True),
            ("address_line2", "Address Line 2 (Optional)", "text", 5, False),
            ("country", "Country", "country", 6, True),
            ("city", "City", "text", 7, True),
            ("postal_code", "Zip / Postal Code (Optional)", "text", 8, False),
            ("other_state", "Other State/Province (Optional)", "text", 9, False),
        ]:
            fld, _ = self._get_or_create_field(sec, code,
                label=label, field_type=ftype, sort_order=order,
                is_required=req,
            )
            if req:
                self._add_required(fld)

        address_regex = r"^[\w\s\-'\"\,\.\#\/]{1,200}$"
        address_msg = "Enter valid value."
        for code in ("address_line1", "address_line2"):
            f = FormField.objects.get(section=sec, code=code)
            self._add_validation(f, "regex", value=address_regex, error_message=address_msg)

        city_regex = r"^[a-zA-Z\s\'-]{2,100}$"
        city_msg = "Enter valid city."
        f = FormField.objects.get(section=sec, code="city")
        self._add_validation(f, "regex", value=city_regex, error_message=city_msg)

        zip_regex = r"^\d{5}$"
        zip_msg = "Enter a valid 5-digit ZIP code"
        f = FormField.objects.get(section=sec, code="postal_code")
        self._add_validation(f, "regex", value=zip_regex, error_message=zip_msg)

        state_regex = r"^[a-zA-Z\s\'-]{2,100}$"
        state_msg = "Enter valid state."
        f = FormField.objects.get(section=sec, code="other_state")
        self._add_validation(f, "regex", value=state_regex, error_message=state_msg)

        pf = FormField.objects.get(section=sec, code="phone")
        self._add_validation(pf, "phone", error_message="Enter a valid phone number with country code.")
        phone_type = FormField.objects.get(section=sec, code="phone_type")
        for index, (value, label) in enumerate([("", "Select Type"), ("mobile", "Mobile"), ("home", "Home"), ("work", "Work")]):
            self._add_choice(phone_type, value, label=label, sort_order=index, is_default=(index == 0))

    def _form_3_parent_guardian(self):
        form = self._get_basic_info_form()
        sec, _ = self._move_section(form, "parent_guardian_info",
            title="Parent/Guardian Information", sort_order=4)
        for code, label, ftype, order, required in [
            ("guardian_first_name", "First Name", "text", 1, True),
            ("guardian_last_name", "Last Name", "text", 2, True),
            ("guardian_relationship", "Relationship to Applicant", "select", 3, True),
            ("guardian_phone", "Phone Number", "phone", 4, False),
            ("guardian_same_address", "Same address as applicant?", "radio", 5, True),
            ("guardian_address_line1", "Address", "text", 6, False),
            ("guardian_address_line2", "Address Line 2 (Optional)", "text", 7, False),
            ("guardian_country", "Country", "country", 8, False),
            ("guardian_city", "City", "text", 9, False),
            ("guardian_postal_code", "Zip / Postal Code (Optional)", "text", 10, False),
            ("guardian_other_state", "Other State/Province (Optional)", "text", 11, False),
            ("guardian_email", "Email Address (Optional)", "email", 12, False),
        ]:
            fld, _ = self._get_or_create_field(sec, code, label=label, field_type=ftype,
                                                sort_order=order, is_required=required)
            if required:
                self._add_required(fld)
        first_regex = r"^[a-zA-Z\s'-]{3,50}$"
        first_msg = "Enter valid name."
        last_regex = r"^[a-zA-Z\s'-]{1,50}$"
        last_msg = "Enter valid name."
        for code, regex, msg in [
            ("guardian_first_name", first_regex, first_msg),
            ("guardian_last_name", last_regex, last_msg),
        ]:
            f = FormField.objects.get(section=sec, code=code)
            self._add_validation(f, "regex", value=regex, error_message=msg)

        address_regex = r"^[\w\s\-'\"\,\.\#\/]{1,200}$"
        address_msg = "Enter valid value."
        for code in ("guardian_address_line1", "guardian_address_line2"):
            f = FormField.objects.get(section=sec, code=code)
            self._add_validation(f, "regex", value=address_regex, error_message=address_msg)

        city_regex = r"^[a-zA-Z\s\'-]{2,100}$"
        city_msg = "Enter valid city."
        f = FormField.objects.get(section=sec, code="guardian_city")
        self._add_validation(f, "regex", value=city_regex, error_message=city_msg)

        zip_regex = r"^\d{5}$"
        zip_msg = "Enter a valid 5-digit ZIP code"
        f = FormField.objects.get(section=sec, code="guardian_postal_code")
        self._add_validation(f, "regex", value=zip_regex, error_message=zip_msg)

        state_regex = r"^[a-zA-Z\s\'-]{2,100}$"
        state_msg = "Enter valid state."
        f = FormField.objects.get(section=sec, code="guardian_other_state")
        self._add_validation(f, "regex", value=state_regex, error_message=state_msg)

        same_addr_f = FormField.objects.get(section=sec, code="guardian_same_address")
        for target_code in ("guardian_address_line1", "guardian_address_line2", "guardian_country", "guardian_city", "guardian_postal_code", "guardian_other_state"):
            target_f = FormField.objects.get(section=sec, code=target_code)
            VisibilityRule.objects.update_or_create(
                field=target_f,
                target_field=same_addr_f,
                defaults={
                    "operator": "eq",
                    "value": "no",
                    "is_active": True,
                    "sort_order": 0,
                },
            )

        for code, choices in {
            "guardian_relationship": [("", "Select Relationship"), ("parent", "Parent"), ("legal_guardian", "Legal Guardian"), ("other", "Other")],
            "guardian_same_address": [("yes", "Yes"), ("no", "No")],
        }.items():
            choice_field = FormField.objects.get(section=sec, code=code)
            for index, (value, label) in enumerate(choices):
                self._add_choice(choice_field, value, label=label, sort_order=index, is_default=(index == 0 and not value))

    def _form_4_residency(self):
        form = self._get_basic_info_form()
        sec, _ = self._move_section(form, "residency_info",
            title="Residency Information", sort_order=5)
        FormField.objects.filter(section=sec, is_active=True).delete()
        VisibilityRule.objects.filter(field__section=sec, is_active=True).delete()

        next_order = 1

        self._get_or_create_field(sec, "_residency_desc",
            label="RESIDENCY", field_type="heading",
            sort_order=next_order, is_required=False, is_readonly=True,
            default_value="", layout_width="full")
        next_order += 1

        residency_intro = (
            "The next section will ask questions to determine if you qualify for "
            "Wisconsin resident tuition under state law. The information collected "
            "in the following sections is only used to determine your tuition rate. "
            "Learn more about qualifying for Wisconsin residency.\n\n"
            "Failure to accurately and completely answer the following questions "
            "may result in an incorrect tuition rate."
        )
        self._get_or_create_field(sec, "_residency_intro",
            label=residency_intro, field_type="heading",
            sort_order=next_order, is_required=False, is_readonly=True,
            default_value="", layout_width="full")
        next_order += 1

        in_state, _ = self._get_or_create_field(sec, "in_state_tuition",
            label="Do you believe you may qualify for in-state tuition rate based upon Wisconsin residency?",
            field_type="radio", sort_order=next_order, is_required=True)
        next_order += 1
        self._add_required(in_state)
        for i, (val, lbl) in enumerate([("yes", "Yes"), ("no", "No")]):
            self._add_choice(in_state, val, label=lbl, sort_order=i)

        no_parent, _ = self._get_or_create_field(sec, "_cannot_provide_parent_info",
            label=("I'm not able to provide parent or legal guardian information because "
                   "I'm homeless, in foster care, do not know my parents, or do not have "
                   "a legal guardian, or because my parents are deceased."),
            field_type="checkbox", sort_order=next_order, is_required=False)
        next_order += 1
        self._add_visibility(no_parent, in_state, "eq", "yes", logic="AND")

        def _parent_visible(fld):
            """Add AND rules: in_state_tuition=yes AND _cannot_provide_parent_info != on"""
            self._add_visibility(fld, in_state, "eq", "yes", logic="AND")
            self._add_visibility(fld, no_parent, "neq", "on", logic="AND")

        heading_parent, _ = self._get_or_create_field(sec, "_heading_parent_residency",
            label="PARENT RESIDENCY", field_type="heading",
            sort_order=next_order, is_required=False, is_readonly=True,
            default_value="", layout_width="full")
        next_order += 1
        _parent_visible(heading_parent)

        parent_intro = (
            "Please provide information about your parent/guardian for determining "
            "the Wisconsin resident tuition rate."
        )
        parent_intro_field, _ = self._get_or_create_field(sec, "_parent_relationship_intro",
            label=parent_intro, field_type="heading",
            sort_order=next_order, is_required=False, is_readonly=True,
            default_value="", layout_width="full")
        next_order += 1
        _parent_visible(parent_intro_field)

        chosen_heading_label, _ = self._get_or_create_field(sec, "_parent_chosen_intro",
            label="Chosen Relationship", field_type="heading",
            sort_order=next_order, is_required=False, is_readonly=True,
            default_value="", layout_width="full")
        next_order += 1
        _parent_visible(chosen_heading_label)

        chosen_heading, _ = self._get_or_create_field(sec, "_parent_chosen_heading",
            label="", field_type="heading",
            sort_order=next_order, is_required=False, is_readonly=True,
            default_value="", layout_width="full")
        next_order += 1
        _parent_visible(chosen_heading)

        parent_rel, _ = self._get_or_create_field(sec, "parent_relationship",
            label="Parent/Guardian Relationship",
            field_type="select", sort_order=next_order, is_required=True,
            layout_width="full")
        next_order += 1
        self._add_required(parent_rel)
        _parent_visible(parent_rel)
        for i, (v, lbl) in enumerate([("father", "Father"), ("mother", "Mother"),
                                       ("legal_guardian", "Legal Guardian"),
                                       ("other", "Other")]):
            self._add_choice(parent_rel, v, label=lbl, sort_order=i)

        _pfields = [
            ("parent_us_citizen",
             "Is your {rel_lower} a U.S. citizen?",
             "radio", True,
             [("yes", "Yes"), ("no", "No"), ("prefer_not", "Prefer not to respond at this time")]),
            ("parent_residence_12mo",
             "Has your {rel_lower} physically resided full-time in Wisconsin for the past 12 months?",
             "radio", True,
             [("yes", "Yes"), ("no", "No")]),
            ("parent_employment",
             "Where is your {rel_lower} employed?",
             "radio", True,
             [("wisconsin", "Wisconsin"), ("outside_wi", "Outside of Wisconsin"),
              ("not_working", "Not currently working")]),
            ("parent_tax_return",
             "Has your {rel_lower} filed a Wisconsin resident income tax return for the most recent tax year?",
             "radio", True,
             [("yes", "Yes"), ("no_did_not_file", "No \u2013 did not file"),
              ("no_filed_other", "No \u2013 filed in a different state")]),
            ("parent_vote_registration",
             "Was Wisconsin the last place your {rel_lower} registered to vote or voted?",
             "radio", True,
             [("yes", "Yes"), ("no", "No")]),
            ("parent_drivers_license",
             "Does your {rel_lower} hold a valid Wisconsin driver's license?",
             "radio", True,
             [("yes", "Yes"), ("no", "No")]),
        ]
        for code, label, ftype, req, choices in _pfields:
            fld, _ = self._get_or_create_field(sec, code,
                label=label, field_type=ftype, sort_order=next_order,
                is_required=req)
            next_order += 1
            if req:
                self._add_required(fld)
            _parent_visible(fld)
            if choices:
                for i, (v, lbl) in enumerate(choices):
                    self._add_choice(fld, v, label=lbl, sort_order=i)

        def _applicant_visible(fld):
            """Show when in_state_tuition=yes"""
            self._add_visibility(fld, in_state, "eq", "yes", logic="AND")

        heading_app, _ = self._get_or_create_field(sec, "_heading_applicant_residency",
            label="APPLICANT RESIDENCY", field_type="heading",
            sort_order=next_order, is_required=False, is_readonly=True,
            default_value="", layout_width="full")
        next_order += 1
        _applicant_visible(heading_app)

        _afields = [
            ("applicant_lives_in_wi",
             "Do you live in Wisconsin?",
             "radio", True,
             [("yes", "Yes"), ("no", "No")]),
            ("applicant_employment",
             "Where are you employed?",
             "radio", True,
             [("wisconsin", "Wisconsin"), ("outside_wi", "Outside of Wisconsin"),
              ("not_working", "Not currently working")]),
            ("applicant_tax_return",
             "Have you filed a Wisconsin resident income tax return for the most recent tax year?",
             "radio", True,
             [("yes", "Yes"), ("no_did_not_file", "No \u2013 did not file"),
              ("no_filed_other", "No \u2013 filed in a different state")]),
            ("applicant_vote_registration",
             "Was Wisconsin the last place you registered to vote or voted?",
             "radio", True,
             [("yes", "Yes"), ("no", "No")]),
            ("applicant_drivers_license",
             "Do you hold a valid Wisconsin driver's license?",
             "radio", True,
             [("yes", "Yes"), ("no", "No")]),
            ("applicant_claimed_dependent",
             "Did your parent(s)/guardian(s) claim you as a dependent for the most recent tax year?",
             "radio", True,
             [("yes", "Yes"), ("no", "No")]),
            ("applicant_residence_12mo",
             "Have you physically resided full-time in Wisconsin for the past 12 months?",
             "radio", True,
             [("yes", "Yes"), ("no", "No")]),
            ("applicant_enrolled_before",
             "Have you been enrolled at any institutions of higher education during the twelve months prior to today's date?",
             "radio", True,
             [("yes", "Yes"), ("no", "No")]),
        ]
        for code, label, ftype, req, choices in _afields:
            fld, _ = self._get_or_create_field(sec, code,
                label=label, field_type=ftype, sort_order=next_order,
                is_required=req)
            next_order += 1
            if req:
                self._add_required(fld)
            _applicant_visible(fld)
            if choices:
                for i, (v, lbl) in enumerate(choices):
                    self._add_choice(fld, v, label=lbl, sort_order=i)

        enrolled_field = FormField.objects.get(section=sec, code="applicant_enrolled_before")
        _efields = [
            ("_heading_prior_enrollment", "PRIOR ENROLLMENT INFORMATION", "heading", False),
            ("prior_institution_name", "Institution Name", "text", False),
            ("prior_institution_city", "Institution City", "text", False),
            ("prior_institution_state", "Institution State", "text", False),
            ("prior_institution_dates", "Dates Attended", "text", False),
        ]
        for code, label, ftype, req in _efields:
            fld, _ = self._get_or_create_field(sec, code,
                label=label, field_type=ftype, sort_order=next_order,
                is_required=req)
            next_order += 1
            if req:
                self._add_required(fld)
            self._add_visibility(fld, enrolled_field, "eq", "yes", logic="AND")

        mn_recip, _ = self._get_or_create_field(sec, "_mn_reciprocity",
            label="Minnesota Reciprocity", field_type="heading",
            sort_order=next_order, is_required=False, is_readonly=True,
            default_value="", layout_width="full")
        next_order += 1

        mn_help = (
            "If you believe you qualify for Minnesota tuition reciprocity, that is "
            "determined through a separate process. Learn more about qualifying for "
            "Minnesota Reciprocity."
        )
        self._get_or_create_field(sec, "_mn_reciprocity_info",
            label=mn_help, field_type="heading",
            sort_order=next_order, is_required=False, is_readonly=True,
            default_value="", layout_width="full")

    def _form_5_academic_history(self):
        form = self._get_or_create_form("academic_history",
            name="Academic History", description="High school and college academic history",
            icon="book-open", sort_order=6)
        form.sections.exclude(code__in=["high_school", "higher_education_check", "test_scores"]).delete()
        hs, _ = self._get_or_create_section(form, "high_school",
            title="Academic Background: High School / Secondary School", sort_order=1, is_repeatable=False, max_repeat=1)
        VisibilityRule.objects.filter(field__section=hs, is_active=True).delete()
        ValidationRule.objects.filter(field__section=hs).delete()
        for code, label, ftype, order, req in [
            ("school_name", "High School / Secondary School", "text", 1, True),
            ("school_location", "School Location", "text", 2, True),
            ("currently_attend_school", "Do you currently attend this school?", "radio", 3, True),
            ("graduated_high_school", "Did you graduate from this high school/secondary school?", "radio", 4, False),
            ("graduation_date", "Graduation Date", "date", 5, False),
            ("attend_from", "Attended from", "year", 6, False),
            ("attend_to", "Attended to", "year", 7, False),
            ("anticipated_grad", "Anticipated graduation date", "year", 8, False),
            ("hs_transcript", "High School Transcript", "file", 12, False),
        ]:
            fld, _ = self._get_or_create_field(hs, code,
                label=label, field_type=ftype, sort_order=order,
                is_required=req,
            )
            if req:
                self._add_required(fld)
        hs_attend_from = FormField.objects.get(section=hs, code="attend_from")
        hs_attend_to = FormField.objects.get(section=hs, code="attend_to")
        self._add_validation(hs_attend_from, "custom", value="field_comparison:attend_to:lte",
            error_message="Attended from year cannot be later than attended to year.")
        self._add_validation(hs_attend_to, "max_value", value="2099")
        self._add_validation(hs_attend_to, "custom", value="field_comparison:attend_from:gte",
            error_message="Attended to year cannot be before attended from year.")
        hs_anticipated = FormField.objects.get(section=hs, code="anticipated_grad")
        self._add_validation(hs_anticipated, "custom", value="field_comparison:attend_from:gte",
            error_message="Anticipated graduation year cannot be before attended from year.")
        school_regex = r"^[a-zA-Z\s\-'\.&]{2,200}$"
        school_msg = "Enter a valid school name"
        for code in ("school_name",):
            f = FormField.objects.get(section=hs, code=code)
            self._add_validation(f, "regex", value=school_regex, error_message=school_msg)

        location_regex = r"^[a-zA-Z\s\'-]{2,100}$"
        location_msg = "Enter valid location."
        for code in ("school_location",):
            f = FormField.objects.get(section=hs, code=code)
            self._add_validation(f, "regex", value=location_regex, error_message=location_msg)

        for code in ("currently_attend_school", "graduated_high_school"):
            choice_field = FormField.objects.get(section=hs, code=code)
            for index, (value, label) in enumerate([("yes", "Yes"), ("no", "No")]):
                self._add_choice(choice_field, value, label=label, sort_order=index)

        attend_f = FormField.objects.get(section=hs, code="currently_attend_school")
        ghs = FormField.objects.get(section=hs, code="graduated_high_school")

        VisibilityRule.objects.update_or_create(
            field=ghs, target_field=attend_f,
            defaults={"operator": "neq", "value": "yes", "is_active": True, "sort_order": 0},
        )

        gd = FormField.objects.get(section=hs, code="graduation_date")
        VisibilityRule.objects.update_or_create(
            field=gd, target_field=ghs,
            defaults={"operator": "eq", "value": "yes", "is_active": True, "sort_order": 0},
        )

        tf = FormField.objects.get(section=hs, code="attend_from")
        VisibilityRule.objects.update_or_create(
            field=tf, target_field=attend_f,
            defaults={"operator": "eq", "value": "yes", "is_active": True, "sort_order": 1, "logic_operator": "OR"},
        )
        VisibilityRule.objects.update_or_create(
            field=tf, target_field=ghs,
            defaults={"operator": "eq", "value": "no", "is_active": True, "sort_order": 2, "logic_operator": "OR"},
        )

        tf = FormField.objects.get(section=hs, code="attend_to")
        VisibilityRule.objects.update_or_create(
            field=tf, target_field=ghs,
            defaults={"operator": "eq", "value": "no", "is_active": True, "sort_order": 0},
        )

        tf = FormField.objects.get(section=hs, code="anticipated_grad")
        VisibilityRule.objects.update_or_create(
            field=tf, target_field=attend_f,
            defaults={"operator": "eq", "value": "yes", "is_active": True, "sort_order": 0},
        )
        tf = FormField.objects.get(section=hs, code="hs_transcript")
        VisibilityRule.objects.update_or_create(
            field=tf, target_field=attend_f,
            defaults={"operator": "eq", "value": "yes", "is_active": True, "sort_order": 0},
        )

        higher_ed, _ = self._get_or_create_section(form, "higher_education_check",
            title="Academic Background: College/Post-Secondary Check", sort_order=2)
        FormField.objects.filter(section=higher_ed, is_active=True).exclude(code="college_courses_taken").delete()
        ValidationRule.objects.filter(field__section=higher_ed).delete()
        VisibilityRule.objects.filter(field__section=higher_ed, is_active=True).delete()
        field, _ = self._get_or_create_field(
            higher_ed, "college_courses_taken", label="Have you ever taken any college-level courses?",
            field_type="radio", sort_order=1, is_required=True,
        )
        self._add_required(field)
        for index, (value, label) in enumerate([("yes", "Yes"), ("no", "No")]):
            self._add_choice(field, value, label=label, sort_order=index)

        for code, label, ftype, order, req in [
            ("college_name", "College/University Name", "text", 2, False),
            ("college_location", "College Location", "text", 3, False),
            ("currently_attend_college", "Do you currently attend this college?", "radio", 4, False),
            ("graduated_college", "Did you graduate from this college?", "radio", 5, False),
            ("college_graduation_date", "College Graduation Date", "date", 6, False),
            ("college_attend_from", "Attended from Year", "year", 7, False),
            ("college_attend_to", "Attended to Year", "year", 8, False),
            ("college_anticipated_grad", "Anticipated graduation date", "year", 9, False),
            ("college_transcript", "College Transcript", "file", 10, False),
        ]:
            fld, _ = self._get_or_create_field(higher_ed, code,
                label=label, field_type=ftype, sort_order=order,
                is_required=req,
            )
            if req:
                self._add_required(fld)

        col_attend_from = FormField.objects.get(section=higher_ed, code="college_attend_from")
        col_attend_to = FormField.objects.get(section=higher_ed, code="college_attend_to")
        self._add_validation(col_attend_from, "custom", value="field_comparison:college_attend_to:lte",
            error_message="Attended from year cannot be later than attended to year.")
        self._add_validation(col_attend_to, "custom", value="field_comparison:college_attend_from:gte",
            error_message="Attended to year cannot be before attended from year.")
        col_anticipated = FormField.objects.get(section=higher_ed, code="college_anticipated_grad")
        self._add_validation(col_anticipated, "custom", value="field_comparison:college_attend_from:gte",
            error_message="Anticipated graduation year cannot be before attended from year.")
        for code in ("college_name",):
            f = FormField.objects.get(section=higher_ed, code=code)
            self._add_validation(f, "regex", value=school_regex, error_message=school_msg)

        for code in ("currently_attend_college", "graduated_college"):
            choice_field = FormField.objects.get(section=higher_ed, code=code)
            for index, (value, label) in enumerate([("yes", "Yes"), ("no", "No")]):
                self._add_choice(choice_field, value, label=label, sort_order=index)

        cct = FormField.objects.get(section=higher_ed, code="college_courses_taken")
        cac = FormField.objects.get(section=higher_ed, code="currently_attend_college")
        gc = FormField.objects.get(section=higher_ed, code="graduated_college")

        for fc in ("college_name", "college_location", "currently_attend_college",
                   "graduated_college", "college_graduation_date",
                   "college_attend_from", "college_attend_to",
                   "college_anticipated_grad", "college_transcript"):
            tf = FormField.objects.get(section=higher_ed, code=fc)
            VisibilityRule.objects.update_or_create(
                field=tf, target_field=cct,
                defaults={"operator": "eq", "value": "yes", "is_active": True, "sort_order": 0},
            )

        VisibilityRule.objects.update_or_create(
            field=gc, target_field=cac,
            defaults={"operator": "neq", "value": "yes", "is_active": True, "sort_order": 0},
        )

        cgd = FormField.objects.get(section=higher_ed, code="college_graduation_date")
        VisibilityRule.objects.update_or_create(
            field=cgd, target_field=gc,
            defaults={"operator": "eq", "value": "yes", "is_active": True, "sort_order": 0},
        )

        cf = FormField.objects.get(section=higher_ed, code="college_attend_from")
        VisibilityRule.objects.update_or_create(
            field=cf, target_field=cac,
            defaults={"operator": "eq", "value": "yes", "is_active": True, "sort_order": 1, "logic_operator": "OR"},
        )
        VisibilityRule.objects.update_or_create(
            field=cf, target_field=gc,
            defaults={"operator": "eq", "value": "no", "is_active": True, "sort_order": 2, "logic_operator": "OR"},
        )

        ct = FormField.objects.get(section=higher_ed, code="college_attend_to")
        VisibilityRule.objects.update_or_create(
            field=ct, target_field=gc,
            defaults={"operator": "eq", "value": "no", "is_active": True, "sort_order": 0},
        )

        cag = FormField.objects.get(section=higher_ed, code="college_anticipated_grad")
        VisibilityRule.objects.update_or_create(
            field=cag, target_field=cac,
            defaults={"operator": "eq", "value": "yes", "is_active": True, "sort_order": 0},
        )
        ctran = FormField.objects.get(section=higher_ed, code="college_transcript")
        VisibilityRule.objects.update_or_create(
            field=ctran, target_field=cac,
            defaults={"operator": "eq", "value": "yes", "is_active": True, "sort_order": 0},
        )

        ts, _ = self._get_or_create_section(form, "test_scores",
            title="Academic Background: Test Scores", sort_order=3, is_repeatable=True, max_repeat=5, start_hidden=True)
        FormField.objects.filter(section=ts).delete()
        ValidationRule.objects.filter(field__section=ts).delete()
        VisibilityRule.objects.filter(field__section=ts, is_active=True).delete()
        next_order = 1

        self._get_or_create_field(ts, "_test_scores_intro",
            label=("Please enter test information for exams you have taken. "
                   "Providing this information now may reduce the number of steps "
                   "and costs in applying."),
            field_type="heading", sort_order=next_order, is_required=False, is_readonly=True,
            default_value="", layout_width="full")
        next_order += 1

        test_method, _ = self._get_or_create_field(ts, "test_method",
            label="Select Test Method", field_type="select",
            sort_order=next_order, is_required=False, layout_width="full")
        next_order += 1
        for i, (val, lbl) in enumerate([
            ("", "Select a test"),
            ("ielts", "IELTS"),
            ("toefl", "TOEFL"),
            ("duolingo", "Duolingo English Test"),
        ]):
            self._add_choice(test_method, val, label=lbl, sort_order=i, is_default=(i == 0))

        test_fields = {
            "ielts": [
                ("ielts_exam_date", "IELTS Exam Date", "date", "", "", ""),
                ("ielts_total", "IELTS Total Score", "number", r"^\d\.\d$", "0", "9"),
            ],
            "toefl": [
                ("toefl_exam_date", "TOEFL Exam Date", "date", "", "", ""),
                ("toefl_total", "TOEFL Total Score", "number", r"^\d{1,3}$", "0", "120"),
            ],
            "duolingo": [
                ("duolingo_exam_date", "Duolingo Exam Date", "date", "", "", ""),
                ("duolingo_total", "Duolingo English Test Score", "number", r"^\d{2,3}$", "10", "160"),
            ],
        }

        for test_type, fields in test_fields.items():
            for code, label, ftype, regex, lo, hi in fields:
                fld, _ = self._get_or_create_field(ts, code,
                    label=label, field_type=ftype,
                    sort_order=next_order, is_required=False, layout_width="half")
                next_order += 1
                if regex:
                    self._add_validation(fld, "regex", value=regex,
                        error_message=f"Enter a valid {label}.")
                if lo:
                    self._add_validation(fld, "min_value", value=lo)
                if hi:
                    self._add_validation(fld, "max_value", value=hi)
                VisibilityRule.objects.update_or_create(
                    field=fld, target_field=test_method,
                    defaults={"operator": "eq", "value": test_type,
                              "is_active": True, "sort_order": 0},
                )

    def _form_6_additional_information(self):
        form = self._get_basic_info_form()
        sec, _ = self._move_section(form, "additional_info",
            title="Additional Information", sort_order=2)

        next_order = 1

        self._get_or_create_field(sec, "_heading_family",
            label="FAMILY BACKGROUND", field_type="heading",
            sort_order=next_order, is_required=False, is_readonly=True,
            default_value="", layout_width="full")
        next_order += 1

        serving, _ = self._get_or_create_field(sec, "military_serving",
            label="Are you, or is a parent or spouse, currently serving in the U.S. Military?",
            field_type="radio", sort_order=next_order, is_required=False)
        next_order += 1
        for i, (val, lbl) in enumerate([
            ("self", "Self"), ("parent", "Parent"), ("spouse", "Spouse"), ("none", "None serving"),
        ]):
            self._add_choice(serving, val, label=lbl, sort_order=i)

        veteran, _ = self._get_or_create_field(sec, "military_veteran",
            label="Are you, or is a parent or spouse, a U.S. Military veteran?",
            field_type="radio", sort_order=next_order, is_required=False)
        next_order += 1
        for i, (val, lbl) in enumerate([
            ("self", "Self"), ("parent", "Parent"), ("spouse", "Spouse"), ("none", "None served"),
        ]):
            self._add_choice(veteran, val, label=lbl, sort_order=i)

        self._get_or_create_field(sec, "_heading_ethnicity",
            label="ETHNICITY AND RACE", field_type="heading",
            sort_order=next_order, is_required=False, is_readonly=True,
            default_value="", layout_width="full")
        next_order += 1

        hl, _ = self._get_or_create_field(sec, "hispanic_latino",
            label="Are you of Hispanic or Latino/a origin?",
            field_type="radio", sort_order=next_order, is_required=True)
        next_order += 1
        self._add_required(hl)
        for i, (val, lbl) in enumerate([("yes", "Yes"), ("no", "No")]):
            self._add_choice(hl, val, label=lbl, sort_order=i)

        hl_help = "Which of the option(s) below best describe how you identify yourself? (Check all that apply.)"
        for i, (code, label) in enumerate([
            ("hl_cuban", "Cuban"),
            ("hl_mexican", "Mexican, Mexican American, or Chicano/a"),
            ("hl_puerto_rican", "Puerto Rican"),
            ("hl_other", "Another Hispanic or Latino/a Identity"),
        ], 0):
            hl_field, _ = self._get_or_create_field(sec, code,
                label=label, field_type="checkbox",
                sort_order=next_order + i,
                help_text=hl_help if i == 0 else "")
            VisibilityRule.objects.update_or_create(
                field=hl_field, target_field=hl,
                defaults={
                    "operator": "eq", "value": "yes",
                    "is_active": True, "sort_order": 0,
                },
            )
        next_order += 4

        race_help = "Which of the option(s) below best describe how you identify yourself? (Check all that apply.)"
        for i, (code, label) in enumerate([
            ("race_american_indian", "American Indian or Alaska Native"),
            ("race_asian", "Asian"),
            ("race_black", "Black or African American"),
            ("race_hawaiian", "Native Hawaiian or Other Pacific Islander"),
            ("race_white", "White"),
        ], 0):
            self._get_or_create_field(sec, code,
                label=label, field_type="checkbox",
                sort_order=next_order + i,
                help_text=race_help if i == 0 else "")
        next_order += 5

        self._get_or_create_field(sec, "_heading_financial",
            label="FINANCIAL NEEDS BASED WAIVER", field_type="heading",
            sort_order=next_order, is_required=False, is_readonly=True,
            default_value="", layout_width="full")
        next_order += 1

        fw_help = (
            "Providing this information may waive your application fee "
            "and/or offer you additional assistance on campus."
        )
        fw, _ = self._get_or_create_field(sec, "fee_waiver_eligible",
            label="Do you believe you are eligible for a waived application fee and/or "
                  "additional assistance because of financial need or other circumstances?",
            field_type="radio", sort_order=next_order, is_required=True,
            help_text=fw_help)
        next_order += 1
        self._add_required(fw)
        for i, (val, lbl) in enumerate([("yes", "Yes"), ("no", "No")]):
            self._add_choice(fw, val, label=lbl, sort_order=i)

        fwr_help = (
            "You may be eligible for a waiver of the application fee and/or additional assistance.\n\n"
            "Admissions offices may reach out to confirm your eligibility for an application fee "
            "waiver or additional assistance. Being dishonest on your application can lead to your "
            "application not being considered for admission."
        )
        fwr, _ = self._get_or_create_field(sec, "fee_waiver_reason",
            label='If you chose "yes", choose an option below that best describes your situation:',
            field_type="radio", sort_order=next_order, is_required=True,
            help_text=fwr_help)
        next_order += 1
        self._add_required(fwr)
        for i, (val, lbl) in enumerate([
            ("free_meals", "I qualify for Free and Reduced Price school meals"),
            ("act_sat_waiver", "I qualify for an ACT and/or SAT fee waiver"),
            ("trio", "I am enrolled in a TRIO program, such as Upward Bound"),
            ("counselor_rec", "I have a high school counselor, teacher, principal, financial aid officer, or community leader who can attest to my financial circumstance"),
            ("public_assistance", "My family receives public assistance"),
            ("public_housing", "I live in federally subsidized public housing or a foster home, or I am homeless"),
            ("usda_income", "My family\u2019s income falls within Income Eligibility Guidelines set by USDA Food and Nutrition Services"),
            ("ward_state", "I am a ward of the state or I am an orphan"),
        ]):
            self._add_choice(fwr, val, label=lbl, sort_order=i)

        VisibilityRule.objects.update_or_create(
            field=fwr, target_field=fw,
            defaults={
                "operator": "eq", "value": "yes",
                "is_active": True, "sort_order": 0,
            },
        )

        self._get_or_create_field(sec, "_heading_support",
            label="ADDITIONAL SUPPORT", field_type="heading",
            sort_order=next_order, is_required=False, is_readonly=True,
            default_value="", layout_width="full")
        next_order += 1

        support_help = (
            "Independent students who meet one or more of the following criteria may be eligible "
            "for additional support services:\n\n"
            "\u2022 I am or was in permanent legal guardianship (court-appointed, not with a parent)\n"
            "\u2022 I am or was an emancipated minor\n"
            "\u2022 I am or was in foster care or a ward of the court at any time after I turned 13\n"
            "\u2022 Both of my parents are deceased and I was not adopted\n"
            "\u2022 Both of my parents are currently incarcerated\n"
            "\u2022 I am unaccompanied (not living with or in the physical custody of a parent or "
            "guardian) and homeless; or self-supporting and at risk of homelessness"
        )
        asp, _ = self._get_or_create_field(sec, "additional_support_eligible",
            label="Do any of the above apply to you?",
            field_type="radio", sort_order=next_order, is_required=True,
            help_text=support_help)
        self._add_required(asp)
        for i, (val, lbl) in enumerate([
            ("yes", "Yes"), ("no", "No"), ("prefer_not", "Prefer not to answer"),
        ]):
            self._add_choice(asp, val, label=lbl, sort_order=i)

    def _form_7_holistic_background(self):
        form = self._get_or_create_form("holistic_background",
            name="Holistic Background",
            description="Extracurricular activities, work experience, and personal essay",
            icon="clipboard", sort_order=7)
        form.sections.exclude(code__in=["activities", "work_experience", "essay"]).delete()

        sec, _ = self._get_or_create_section(form, "activities",
            title="Activities", sort_order=1,
            is_repeatable=False, max_repeat=1)

        next_order = 1

        cat, _ = self._get_or_create_field(sec, "activity_category",
            label="Activity Category", field_type="select",
            sort_order=next_order, is_required=True)
        next_order += 1
        for i, (val, lbl) in enumerate([
            ("athletics", "Athletics"),
            ("academic", "Academic / Educational"),
            ("arts", "Arts / Music"),
            ("community_service", "Community Service / Volunteer"),
            ("employment", "Employment / Internship"),
            ("student_governance", "Student Governance / Leadership"),
            ("religious", "Religious / Spiritual"),
            ("other", "Other"),
        ]):
            self._add_choice(cat, val, label=lbl, sort_order=i)

        self._get_or_create_field(sec, "activity_name",
            label="Activity Name", field_type="text",
            sort_order=next_order, is_required=True)
        next_order += 1

        grade_multi, _ = self._get_or_create_field(sec, "activity_grades",
            label="Participation grade levels", field_type="multi_select",
            sort_order=next_order, is_required=False)
        next_order += 1
        for i, (val, lbl) in enumerate([
            ("9", "9th Grade"),
            ("10", "10th Grade"),
            ("11", "11th Grade"),
            ("12", "12th Grade"),
            ("post_hs", "After High School"),
        ]):
            self._add_choice(grade_multi, val, label=lbl, sort_order=i)

        lvl, _ = self._get_or_create_field(sec, "activity_level",
            label="Level of participation", field_type="select",
            sort_order=next_order, is_required=True)
        next_order += 1
        for i, (val, lbl) in enumerate([
            ("low", "Low (Up to 2 hours per week)"),
            ("medium", "Medium (3-4 hours per week)"),
            ("high", "High (5 or more hours per week)"),
        ]):
            self._add_choice(lvl, val, label=lbl, sort_order=i)

        self._get_or_create_field(sec, "activity_role",
            label="Position / Leadership Role and/or Awards Received, if applicable",
            field_type="textarea",
            sort_order=next_order, is_required=False)
        next_order += 1

        intend, _ = self._get_or_create_field(sec, "activity_intend_college",
            label="I intend to participate in a similar activity in college",
            field_type="radio",
            sort_order=next_order, is_required=True)
        next_order += 1
        for i, (val, lbl) in enumerate([("yes", "Yes"), ("no", "No")]):
            self._add_choice(intend, val, label=lbl, sort_order=i)

        sec2, _ = self._get_or_create_section(form, "work_experience",
            title="Work Experience", sort_order=2,
            is_repeatable=False, max_repeat=1, start_hidden=False)

        VisibilityRule.objects.filter(field__section=sec2, is_active=True).delete()
        ValidationRule.objects.filter(field__section=sec2).delete()

        next_order = 1

        self._get_or_create_field(sec2, "_work_intro",
            label="Like activities, listing your work experience can help us understand "
                  "your life outside the classroom better. Your work experience can include "
                  "summer jobs, part or full-time jobs, and internships (paid or unpaid).",
            field_type="heading", sort_order=next_order, is_required=False,
            is_readonly=True, default_value="", layout_width="full")
        next_order += 1

        no_exp, _ = self._get_or_create_field(sec2, "work_no_experience",
            label="I have no work experience to report.",
            field_type="checkbox", sort_order=next_order, is_required=False)
        next_order += 1

        method, _ = self._get_or_create_field(sec2, "work_method",
            label="Please select the method you wish to provide employment",
            field_type="radio", sort_order=next_order, is_required=False)
        next_order += 1
        for i, (val, lbl) in enumerate([
            ("upload_resume", "Upload Resume"),
            ("manual_enter", "Manually Enter Employment"),
        ]):
            self._add_choice(method, val, label=lbl, sort_order=i)
        VisibilityRule.objects.update_or_create(
            field=method, target_field=no_exp,
            defaults={"operator": "not_checked", "value": "",
                      "is_active": True, "sort_order": 0},
        )

        resume, _ = self._get_or_create_field(sec2, "work_resume_upload",
            label="Upload your resume (PDF only, 2MB limit)",
            field_type="file", sort_order=next_order, is_required=False)
        next_order += 1
        VisibilityRule.objects.update_or_create(
            field=resume, target_field=method,
            defaults={"operator": "eq", "value": "upload_resume",
                      "is_active": True, "sort_order": 0},
        )
        VisibilityRule.objects.update_or_create(
            field=resume, target_field=no_exp,
            defaults={"operator": "not_checked", "value": "",
                      "is_active": True, "sort_order": 1},
        )

        manual_fields = [
            ("work_self_employed", "Are/were you self-employed?", "radio", True, [("yes", "Yes"), ("no", "No")]),
            ("work_employer_country", "Employer Country", "country", True, None),
            ("work_employer_city", "Employer City", "city", True, None),
            ("work_job_title", "Job Title", "text", True, None),
            ("work_currently_employed", "Are you currently employed here?", "radio", True, [("yes", "Yes"), ("no", "No")]),
            ("work_start_date", "Date Employment Started", "year", True, None),
            ("work_hours_week", "Hours Per Week", "number", False, None),
            ("work_summer_only", "Did you work this job only over summers?", "radio", True, [("yes", "Yes"), ("no", "No")]),
        ]
        for code, label, ftype, req, choices in manual_fields:
            fld, _ = self._get_or_create_field(sec2, code,
                label=label, field_type=ftype,
                sort_order=next_order, is_required=req)
            next_order += 1
            if req:
                self._add_required(fld)
            if choices:
                for i, (v, lbl) in enumerate(choices):
                    self._add_choice(fld, v, label=lbl, sort_order=i)
            VisibilityRule.objects.update_or_create(
                field=fld, target_field=method,
                defaults={"operator": "eq", "value": "manual_enter",
                          "is_active": True, "sort_order": 0},
            )
            VisibilityRule.objects.update_or_create(
                field=fld, target_field=no_exp,
                defaults={"operator": "not_checked", "value": "",
                          "is_active": True, "sort_order": 1},
            )

        essay_section, _ = self._get_or_create_section(
            form, "essay", title="Essay", sort_order=3,
            is_repeatable=False, max_repeat=1,
        )
        ValidationRule.objects.filter(field__section=essay_section).delete()

        self._get_or_create_field(
            essay_section, "_essay_guidance",
            label="Share the life experiences, talents, commitments, or interests "
                  "that you will bring to our campus.",
            field_type="heading", sort_order=1, is_required=False,
            is_readonly=True, default_value="", layout_width="full",
        )
        personal_essay, _ = self._get_or_create_field(
            essay_section, "personal_essay",
            label="Personal Essay",
            help_text="Write 250 to 650 words. Draft your response elsewhere if you prefer, "
                      "then paste it here.",
            placeholder="Tell us about an experience that has shaped you.",
            field_type="textarea", sort_order=2, is_required=True,
            rows=14, layout_width="full",
        )
        self._add_required(personal_essay)
        self._add_validation(
            personal_essay, "word_count", value="250", value_max="650",
            error_message="Your personal essay must be between 250 and 650 words.",
        )


    def _seed_form_assignments(self):
        forms = FormDefinition.objects.all().order_by("sort_order")
        count = 0
        for form in forms:
            for applicant_type in [None, "first_year", "transfer"]:
                _, created = FormAssignment.objects.update_or_create(
                    form=form, university=None, degree_level=None,
                    applicant_type=applicant_type, program=None,
                    defaults={"sort_order": form.sort_order, "is_required": True},
                )
                if created:
                    count += 1
        if count:
            self.stdout.write(f"  Created {count} form assignments.")


    def _seed_workflow(self):
        wf, _ = WorkflowDefinition.objects.update_or_create(
            code="standard_application_process",
            defaults={
                "name": "Standard Application Process",
                "description": "Default workflow covering all applicant types.",
                "is_default": True,
            },
        )

        forms_by_code = {f.code: f for f in FormDefinition.objects.all()}

        steps_data = [
            ("personal_info", "Basic Information", "form", "basic_information", 1, None, None),
            ("additional_info", "Additional Information", "form", "basic_information", 2, None, [
                ("applicant_type", "not_in", "international_first_year,international_transfer"),
            ]),
            ("contact_info", "Contact Information", "form", "basic_information", 3, None, None),
            ("parent_guardian_info", "Parent/Guardian Information", "form", "basic_information", 4, None, None),
            ("residency_info", "Residency Information", "form", "basic_information", 5, None, None),
            ("high_school", "Academic Background: High School", "form", "academic_history", 6, None, None),
            ("higher_education_check", "Academic Background: Higher Education ", "form", "academic_history", 6, None, None),
            ("test_scores", "Academic Background: Test Scores", "form", "academic_history", 7, None, None),
            ("activities", "Holistic Background: Activities", "form", "holistic_background", 8, None, None),
            ("work_experience", "Holistic Background: Work Experience", "form", "holistic_background", 9, None, None),
            ("essay", "Holistic Background: Essay", "form", "holistic_background", 10, None, None),
        ]

        step_codes = []
        for code, name, step_type, form_code, sort_order, conditions, step_conditions in steps_data:
            step, _ = DynamicWorkflowStep.objects.update_or_create(
                workflow=wf, code=code,
                defaults={
                    "name": name, "step_type": step_type,
                    "form": forms_by_code.get(form_code),
                    "sort_order": sort_order, "is_required": True,
                },
            )
            step_codes.append(code)
            StepCondition.objects.filter(step=step).delete()
            if conditions:
                StepCondition.objects.update_or_create(
                    step=step, target_field=conditions[0][0],
                    operator=conditions[0][1], value=conditions[0][2],
                    defaults={"logic_operator": "AND"},
                )
            if step_conditions:
                for tf, op, val in step_conditions:
                    StepCondition.objects.update_or_create(
                        step=step, target_field=tf, operator=op, value=val,
                        defaults={"logic_operator": "AND"},
                    )

        removed = DynamicWorkflowStep.objects.filter(workflow=wf).exclude(code__in=step_codes).delete()
        if removed[0]:
            self.stdout.write(f"  Removed {removed[0]} stale workflow steps.")

        self.stdout.write(f"  Workflow '{wf.name}' ready with {len(steps_data)} steps.")


    def _seed_document_requirements(self):
        docs = [
            ("transcript_hs","High School Transcript","academic","Official high school transcript",True),
            ("transcript_college","College Transcript(s)","academic","Official transcripts from all post-secondary institutions",False),
            ("resume_cv","Resume / CV","other","Current resume or curriculum vitae",False),
            ("passport_copy","Passport Copy","identification","Copy of passport identification page",False),
            ("visa_documents","Visa Documents","legal","Current visa and immigration documents",False),
            ("financial_statement","Financial Statement","financial","Proof of financial support",False),
            ("english_proficiency","English Proficiency Score","test_score","TOEFL, IELTS, PTE, or Duolingo score report",False),
            ("portfolio","Portfolio","portfolio","Portfolio of work (if applicable)",False),
            ("military_dd214","Military DD-214","military","Certificate of Release or Discharge from Active Duty",False),
            ("green_card_copy","Green Card Copy","legal","Copy of Permanent Resident Card",False),
        ]
        for code, name, category, desc, req in docs:
            DocumentRequirement.objects.update_or_create(
                code=code, university=None, degree_level=None,
                defaults={"name": name, "description": desc, "category": category, "is_required": req},
            )
        self.stdout.write(f"  {len(docs)} document requirements ready.")