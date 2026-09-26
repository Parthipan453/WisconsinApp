"""
Idempotent seeder for dynamic form engine metadata.

Safe to run multiple times — uses update-or-create logic everywhere.
Run with:  python manage.py seed_dynamic_forms
"""

from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password

from Admin.models import User, UserRole
from Admin.Colleges.models import University, School, Degree, AcademicProgram
from Admin.bela_admin.models import Department

from Applicants.models import (
    FormDefinition, FormSection, FormField, FieldChoice, ValidationRule,
    VisibilityRule,
    FormAssignment, WorkflowDefinition, DynamicWorkflowStep, StepCondition,
    DocumentRequirement, EssayPrompt, AdmissionCycle, ApplicantTypeRequirement,
)
from Faculty.models import FacultyRank, FacultyProfile
from Staff.models import StaffProfile, StaffPosition
from Students.models import StudentProfile


class Command(BaseCommand):
    help = "Seed/update dynamic form engine metadata idempotently"

    FORM_CODES_TO_KEEP = {
        "personal_information", "contact_information", "parent_guardian",
        "residency", "academic_history",
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
        uw_system = University.objects.create(
            university_name="University of Wisconsin System",
            university_short_name="UW System",
            university_code="UWS",
            official_email="info@uwsys.wisconsin.edu",
            phone_number="608-263-2400",
            address_line_1="1220 Linden Dr",
            city="Madison", state="Wisconsin", country="USA", postal_code="53706",
            website="https://www.wisconsin.edu", accreditation="HLC",
            established_year=1848,
        )
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
        ls, _ = School.objects.get_or_create(
            university=uw, school_code="LS",
            defaults=dict(
                school_name="College of Letters & Science",
                school_short_name="L&S", school_type="ACADEMIC",
                description="The College of Letters & Science is the largest college at UW-Madison.",
            ),
        )
        eng, _ = School.objects.get_or_create(
            university=uw, school_code="ENG",
            defaults=dict(
                school_name="College of Engineering",
                school_short_name="ENGR", school_type="ACADEMIC",
                description="The College of Engineering at UW-Madison.",
            ),
        )
        bus, _ = School.objects.get_or_create(
            university=uw, school_code="BUS",
            defaults=dict(
                school_name="Wisconsin School of Business",
                school_short_name="BUS", school_type="PROFESSIONAL",
                description="The Wisconsin School of Business.",
            ),
        )

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
        self.stdout.write("  Created university structure (UWM, schools, degrees, departments, programs).")

    def _seed_admission_cycles(self):
        if AdmissionCycle.objects.count() > 0:
            return
        today = date.today()
        year = today.year if today.month >= 6 else today.year - 1
        AdmissionCycle.objects.create(
            name=f"Fall {year} Regular Decision", code=f"FA{year}_RD",
            academic_year=f"{year}-{year+1}", term="Fall",
            application_start=date(year - 1, 9, 1),
            application_deadline=date(year, 3, 1),
            deadline_type="regular", decision_release=date(year, 4, 15),
            is_active=True, is_open=today < date(year, 3, 1),
        )
        AdmissionCycle.objects.create(
            name=f"Fall {year} Early Action", code=f"FA{year}_EA",
            academic_year=f"{year}-{year+1}", term="Fall",
            application_start=date(year - 1, 9, 1),
            application_deadline=date(year - 1, 11, 15),
            deadline_type="early_action", decision_release=date(year - 1, 12, 15),
            is_active=True, is_open=today < date(year - 1, 11, 15),
        )
        self.stdout.write("  Created admission cycles.")

    def _seed_sample_users(self):
        if FacultyProfile.objects.count() > 0:
            self.stdout.write("  Sample users already exist, skipping.")
            return

        for role_name, user_type in [("Faculty", "faculty"), ("Staff", "staff"), ("Student", "student")]:
            UserRole.objects.get_or_create(role_name=role_name, user_type=user_type)

        prof, _ = FacultyRank.objects.get_or_create(rank_name="Professor", defaults={"tenure_track": True})
        assoc, _ = FacultyRank.objects.get_or_create(rank_name="Associate Professor", defaults={"tenure_track": True})

        password = "Test@123"

        for username, email, fn, ln, role_name, is_faculty, is_staff, is_student in [
            ("jdoe", "jdoe@cs.wisc.edu", "John", "Doe", "Faculty", True, False, False),
            ("asmith", "asmith@cs.wisc.edu", "Alice", "Smith", "Faculty", True, False, False),
            ("jwilson", "jwilson@wisc.edu", "Jane", "Wilson", "Staff", False, True, False),
            ("brownr", "rbrown@wisc.edu", "Robert", "Brown", "Staff", False, True, False),
        ]:
            user, _ = User.objects.get_or_create(username=username, defaults=dict(
                email=email, first_name=fn, last_name=ln,
                account_status="ACTIVE",
                role=UserRole.objects.get(role_name=role_name),
                is_faculty=is_faculty, is_staff=is_staff, is_student=is_student,
            ))
            user.set_password(password)
            user.save(update_fields=["password"])

        # Faculty profiles
        uprof = User.objects.get(username="jdoe")
        FacultyProfile.objects.get_or_create(user=uprof, defaults=dict(
            employee_id="FAC001", email="jdoe@cs.wisc.edu",
            phone="608-262-1001", office_location="CS 1245",
            hire_date=date(2010, 8, 15), faculty_rank=prof,
            employment_status="ACTIVE",
        ))
        usmith = User.objects.get(username="asmith")
        FacultyProfile.objects.get_or_create(user=usmith, defaults=dict(
            employee_id="FAC002", email="asmith@cs.wisc.edu",
            phone="608-262-1002", office_location="CS 1247",
            hire_date=date(2015, 8, 15), faculty_rank=assoc,
            employment_status="ACTIVE",
        ))

        # Staff profiles + positions
        ustaff = User.objects.get(username="jwilson")
        sp, _ = StaffProfile.objects.get_or_create(user=ustaff, defaults=dict(
            employee_id="STF001", work_email="jwilson@wisc.edu",
            hire_date=date(2018, 3, 1),
            employment_status="ACTIVE", employment_type="FULL_TIME",
        ))
        StaffPosition.objects.get_or_create(staff=sp, job_title="Admissions Officer", defaults=dict(
            position_start_date=date(2018, 3, 1), position_status="ACTIVE",
        ))

        ustaff2 = User.objects.get(username="brownr")
        sp2, _ = StaffProfile.objects.get_or_create(user=ustaff2, defaults=dict(
            employee_id="STF002", work_email="rbrown@wisc.edu",
            hire_date=date(2019, 6, 1),
            employment_status="ACTIVE", employment_type="FULL_TIME",
        ))
        StaffPosition.objects.get_or_create(staff=sp2, job_title="Registrar", defaults=dict(
            position_start_date=date(2019, 6, 1), position_status="ACTIVE",
        ))

        # Students
        for i in range(1, 6):
            sfirst = ["Emily", "Michael", "Sophia", "James", "Olivia"][i - 1]
            slast = ["Davis", "Miller", "Wilson", "Taylor", "Anderson"][i - 1]
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

    def handle(self, *args, **options):
        self._seed_admin_user()
        self._seed_university_structure()
        self._seed_admission_cycles()
        self._seed_sample_users()
        self._seed_applicant_type_requirements()
        self._seed_forms()
        self._seed_cleanup_old_forms()
        self._seed_cleanup_orphans()
        self._seed_form_assignments()
        self._seed_workflow()
        self._seed_document_requirements()
        self._seed_essay_prompts()
        self.stdout.write(self.style.SUCCESS("Done."))

    def _seed_cleanup_old_forms(self):
        """Remove forms not in the keep list."""
        FormAssignment.objects.filter(form__isnull=True).delete()
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

    # ------------------------------------------------------------------
    # Helpers — idempotent upsert
    # ------------------------------------------------------------------

    def _get_or_create_form(self, code, **defaults):
        obj, created = FormDefinition.objects.update_or_create(
            code=code, defaults=defaults,
        )
        if created:
            self.stdout.write(f"  Created form: {obj.name}")
        return obj

    def _get_or_create_section(self, form, code, **defaults):
        obj, created = FormSection.objects.update_or_create(
            form=form, code=code, defaults=defaults,
        )
        return obj, created

    def _get_or_create_field(self, section, code, **defaults):
        # Give common short answers a practical two-column layout by default.
        # Long answers and choice groups remain full width for readability.
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

    # ------------------------------------------------------------------
    # Applicant Type Requirements
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Form Definitions
    # ------------------------------------------------------------------

    def _seed_forms(self):
        self._kept_field_codes = set()
        self._form_1_personal_information()
        self._form_2_contact_information()
        self._form_3_parent_guardian()
        self._form_4_residency()
        self._form_5_academic_history()
        self._purge_extra_fields()

    def _form_1_personal_information(self):
        form = self._get_or_create_form(
            "personal_information",
            name="Personal Information",
            description="Basic personal and demographic information",
            icon="user", sort_order=1,
        )
        sec, _ = self._get_or_create_section(form, "personal_info",
            title="Personal Information", sort_order=1)

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
            ("legal_sex","Legal Gender","select",13,"half"),
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

        for code, placeholder in [
            ("ssn", "XXX-XX-XXXX"),
            ("confirm_ssn", "XXX-XX-XXXX"),
            ("tin", "XX-XXXXXXX"),
            ("confirm_tin", "XX-XXXXXXX"),
        ]:
            FormField.objects.filter(section=sec, code=code).update(placeholder=placeholder)

        # ── Field-level regex validations ────────────────────────────
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

        # ── Visibility rules ─────────────────────────────────────────────
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

        # Show SSN/TIN fields based on identification_type selection
        id_type_f = FormField.objects.get(section=sec, code="identification_type")
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

        # Show advisor_name when agent_advisor=yes
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
        form = self._get_or_create_form("contact_information",
            name="Contact Information", description="Contact details and mailing address",
            icon="mail", sort_order=2)
        sec, _ = self._get_or_create_section(form, "contact_info",
            title="Contact Information", sort_order=1)
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

        # ── Field-level regex validations ────────────────────────────
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

        # Add international phone validation
        pf = FormField.objects.get(section=sec, code="phone")
        self._add_validation(pf, "phone", error_message="Enter a valid phone number with country code.")
        phone_type = FormField.objects.get(section=sec, code="phone_type")
        for index, (value, label) in enumerate([("", "Select Type"), ("mobile", "Mobile"), ("home", "Home"), ("work", "Work")]):
            self._add_choice(phone_type, value, label=label, sort_order=index, is_default=(index == 0))

    def _form_3_parent_guardian(self):
        form = self._get_or_create_form("parent_guardian",
            name="Parent/Guardian", description="Parent and guardian information",
            icon="users", sort_order=3)
        sec, _ = self._get_or_create_section(form, "parent_guardian_info",
            title="Parent/Guardian Information", sort_order=1)
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
        # ── Field-level regex validations ────────────────────────────
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

        # ── Visibility: show address fields when guardian_same_address=no ──
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
        form = self._get_or_create_form("residency",
            name="Residency", description="Residency and citizenship information",
            icon="map-pin", sort_order=4)
        sec, _ = self._get_or_create_section(form, "residency_info",
            title="Residency Information", sort_order=1)
        for code, label, ftype, order, req in [
            ("residency_status","Residency Status","select",1,False),
            ("state_of_residence","State of Residence","state",2,False),
            ("years_in_state","Years in State","number",3,False),
            ("visa_status","Visa Status","text",4,False),
            ("us_permanent_resident","U.S. Permanent Resident","checkbox",5,False),
            ("passport_number","Passport Number","text",6,False),
            ("passport_country","Passport Country","country",7,False),
            ("green_card","Green Card Holder","checkbox",8,False),
        ]:
            fld, _ = self._get_or_create_field(sec, code,
                label=label, field_type=ftype, sort_order=order,
                is_required=req,
            )
            if req:
                self._add_required(fld)
        # ── Field-level regex validations ────────────────────────────
        visa_regex = r"^[a-zA-Z\s\'-]{2,100}$"
        visa_msg = "Enter valid value."
        f = FormField.objects.get(section=sec, code="visa_status")
        self._add_validation(f, "regex", value=visa_regex, error_message=visa_msg)

        passport_regex = r"^[A-Za-z0-9]{6,20}$"
        passport_msg = "Enter a valid passport number (6-20 alphanumeric characters)"
        f = FormField.objects.get(section=sec, code="passport_number")
        self._add_validation(f, "regex", value=passport_regex, error_message=passport_msg)

        sf = FormField.objects.get(section=sec, code="residency_status")
        for i, (v, lbl) in enumerate([
            ("","Select Residency Status"), ("wisconsin_resident","Wisconsin Resident"),
            ("non_resident","Non-Resident"), ("midwest_exchange","Midwest Exchange"),
            ("international","International"), ("military_residency","Military Residency"),
            ("tribal_residency","Tribal Residency"),
        ]):
            self._add_choice(sf, v, label=lbl, sort_order=i, is_default=(i==0))

    def _form_5_academic_history(self):
        form = self._get_or_create_form("academic_history",
            name="Academic History", description="High school and college academic history",
            icon="book-open", sort_order=5)
        form.sections.exclude(code__in=["high_school", "higher_education_check"]).delete()
        hs, _ = self._get_or_create_section(form, "high_school",
            title="Academic Background: High School / Secondary School", sort_order=1, is_repeatable=False, max_repeat=1)
        # wipe stale visibility rules for this section
        VisibilityRule.objects.filter(field__section=hs, is_active=True).delete()
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
            ("hs_grades", "Grade Sheet / Marksheet for Classes 9–12", "file", 13, False),
        ]:
            fld, _ = self._get_or_create_field(hs, code,
                label=label, field_type=ftype, sort_order=order,
                is_required=req,
            )
            if req:
                self._add_required(fld)
        # ── Field-level regex validations ────────────────────────────
        school_regex = r"^[a-zA-Z0-9\s\-'\.\,\(\)\&\/]{2,200}$"
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

        # ── Visibility rules ──────────────────────────────────────────
        attend_f = FormField.objects.get(section=hs, code="currently_attend_school")
        grad_f = FormField.objects.get(section=hs, code="graduated_high_school")

        # Hide graduated_high_school when currently_attend_school=yes
        ghs = FormField.objects.get(section=hs, code="graduated_high_school")
        VisibilityRule.objects.update_or_create(
            field=ghs, target_field=attend_f,
            defaults={"operator": "neq", "value": "yes", "is_active": True, "sort_order": 0},
        )
        # Show graduation_date when graduated_high_school=yes
        gd = FormField.objects.get(section=hs, code="graduation_date")
        VisibilityRule.objects.update_or_create(
            field=gd, target_field=grad_f,
            defaults={"operator": "eq", "value": "yes", "is_active": True, "sort_order": 0},
        )

        # attend_from: show when currently_attend_school=yes OR graduated_high_school=no
        tf = FormField.objects.get(section=hs, code="attend_from")
        VisibilityRule.objects.update_or_create(
            field=tf, target_field=attend_f,
            defaults={"operator": "eq", "value": "yes", "is_active": True, "sort_order": 0, "logic_operator": "OR"},
        )
        VisibilityRule.objects.update_or_create(
            field=tf, target_field=grad_f,
            defaults={"operator": "eq", "value": "no", "is_active": True, "sort_order": 1, "logic_operator": "OR"},
        )

        # attend_to: show when graduated_high_school=no
        tf = FormField.objects.get(section=hs, code="attend_to")
        VisibilityRule.objects.update_or_create(
            field=tf, target_field=grad_f,
            defaults={"operator": "eq", "value": "no", "is_active": True, "sort_order": 0},
        )

        # anticipated_grad: show when currently_attend_school=yes
        tf = FormField.objects.get(section=hs, code="anticipated_grad")
        VisibilityRule.objects.update_or_create(
            field=tf, target_field=attend_f,
            defaults={"operator": "eq", "value": "yes", "is_active": True, "sort_order": 0},
        )

        # hs_transcript & hs_grades: show when graduated_high_school=yes
        for code in ("hs_transcript", "hs_grades"):
            tf = FormField.objects.get(section=hs, code=code)
            VisibilityRule.objects.update_or_create(
                field=tf, target_field=grad_f,
                defaults={"operator": "eq", "value": "yes", "is_active": True, "sort_order": 0},
            )

        higher_ed, _ = self._get_or_create_section(form, "higher_education_check",
            title="Academic Background: College/Post-Secondary Check", sort_order=2)
        # wipe stale fields and visibility for this section
        FormField.objects.filter(section=higher_ed, is_active=True).exclude(code="college_courses_taken").delete()
        VisibilityRule.objects.filter(field__section=higher_ed, is_active=True).delete()
        field, _ = self._get_or_create_field(
            higher_ed, "college_courses_taken", label="Have you ever taken any college-level courses?",
            field_type="radio", sort_order=1, is_required=True,
        )
        self._add_required(field)
        for index, (value, label) in enumerate([("yes", "Yes"), ("no", "No")]):
            self._add_choice(field, value, label=label, sort_order=index)

        # ── College detail fields (shown when college_courses_taken=yes) ──
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

        # ── College radio choices ──────────────────────────────────────
        for code in ("currently_attend_college", "graduated_college"):
            choice_field = FormField.objects.get(section=higher_ed, code=code)
            for index, (value, label) in enumerate([("yes", "Yes"), ("no", "No")]):
                self._add_choice(choice_field, value, label=label, sort_order=index)

        # ── College visibility rules ───────────────────────────────────
        cct = FormField.objects.get(section=higher_ed, code="college_courses_taken")
        cac = FormField.objects.get(section=higher_ed, code="currently_attend_college")
        gc = FormField.objects.get(section=higher_ed, code="graduated_college")

        # All college fields hidden unless college_courses_taken=yes
        for fc in ("college_name", "college_location", "currently_attend_college",
                   "graduated_college", "college_graduation_date",
                   "college_attend_from", "college_attend_to",
                   "college_anticipated_grad", "college_transcript"):
            tf = FormField.objects.get(section=higher_ed, code=fc)
            VisibilityRule.objects.update_or_create(
                field=tf, target_field=cct,
                defaults={"operator": "eq", "value": "yes", "is_active": True, "sort_order": 0},
            )

        # Hide graduated_college when currently_attend_college=yes
        VisibilityRule.objects.update_or_create(
            field=gc, target_field=cac,
            defaults={"operator": "neq", "value": "yes", "is_active": True, "sort_order": 0},
        )

        # Show college_graduation_date when graduated_college=yes
        cgd = FormField.objects.get(section=higher_ed, code="college_graduation_date")
        VisibilityRule.objects.update_or_create(
            field=cgd, target_field=gc,
            defaults={"operator": "eq", "value": "yes", "is_active": True, "sort_order": 0},
        )

        # college_attend_from: show when currently_attend_college=yes OR graduated_college=no
        cf = FormField.objects.get(section=higher_ed, code="college_attend_from")
        VisibilityRule.objects.update_or_create(
            field=cf, target_field=cac,
            defaults={"operator": "eq", "value": "yes", "is_active": True, "sort_order": 1},
        )
        VisibilityRule.objects.update_or_create(
            field=cf, target_field=gc,
            defaults={"operator": "eq", "value": "no", "is_active": True, "sort_order": 2},
        )

        # college_attend_to: show when graduated_college=no
        ct = FormField.objects.get(section=higher_ed, code="college_attend_to")
        VisibilityRule.objects.update_or_create(
            field=ct, target_field=gc,
            defaults={"operator": "eq", "value": "no", "is_active": True, "sort_order": 0},
        )

        # college_anticipated_grad & college_transcript: show when currently_attend_college=yes
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

    # ------------------------------------------------------------------
    # Form Assignments — scoped properly (NOT every form to every app)
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Workflow — using correct applicant_type values and FK references
    # ------------------------------------------------------------------

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

        # Step codes deliberately match FormSection codes: the applicant portal
        # renders and validates one dynamic section per step.
        steps_data = [
            ("personal_info", "Personal Information", "form", "personal_information", 1, None, None),
            ("contact_info", "Contact Information", "form", "contact_information", 2, None, None),
            ("parent_guardian_info", "Parent/Guardian Information", "form", "parent_guardian", 3, None, None),
            ("high_school", "Academic Background: High School", "form", "academic_history", 4, None, None),
            ("higher_education_check", "Academic Background: Higher Education Check", "form", "academic_history", 4, None, None),
            ("review", "Review & Submit", "review", None, 6, None, None),
            ("payment", "Payment", "payment", None, 7, None, None),
            ("submit", "Submit", "submit", None, 8, None, None),
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
            # Remove all conditions and recreate
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

        # Remove steps no longer in the data
        removed = DynamicWorkflowStep.objects.filter(workflow=wf).exclude(code__in=step_codes).delete()
        if removed[0]:
            self.stdout.write(f"  Removed {removed[0]} stale workflow steps.")

        self.stdout.write(f"  Workflow '{wf.name}' ready with {len(steps_data)} steps.")

    # ------------------------------------------------------------------
    # Document Requirements
    # ------------------------------------------------------------------

    def _seed_document_requirements(self):
        docs = [
            ("transcript_hs","High School Transcript","academic","Official high school transcript",True),
            ("transcript_college","College Transcript(s)","academic","Official transcripts from all post-secondary institutions",False),
            ("resume_cv","Resume / CV","other","Current resume or curriculum vitae",False),
            ("personal_statement","Personal Statement","essay","Personal statement or statement of purpose",True),
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

    # ------------------------------------------------------------------
    # Essay Prompts
    # ------------------------------------------------------------------

    def _seed_essay_prompts(self):
        prompts = [
            ("personal_statement","Personal Statement","Tell us about yourself and your journey...",250,650,True),
            ("statement_of_purpose","Statement of Purpose","Describe your academic and research interests...",500,1000,False),
            ("diversity_statement","Diversity Statement","How would you contribute to the diversity of our campus community?",250,500,False),
        ]
        for essay_type, title, prompt_text, min_w, max_w, req in prompts:
            EssayPrompt.objects.update_or_create(
                code=essay_type, university=None, degree_level=None,
                defaults={
                    "essay_type": essay_type, "title": title,
                    "prompt_text": prompt_text,
                    "min_words": min_w, "max_words": max_w,
                    "is_required": req,
                },
            )
        self.stdout.write(f"  {len(prompts)} essay prompts ready.")