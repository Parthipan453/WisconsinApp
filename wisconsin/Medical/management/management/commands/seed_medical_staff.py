import random
from datetime import date, time, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from Admin.models import User
from Staff.models import StaffProfile
from Medical.models import (
    MedicalDepartment,
    MedicalStaffProfile,
    StaffSchedule,
    MedicalService,
    PatientProfile,
    Appointment,
    MedicalVisit,
    LaboratoryTest,
)
from Medical.Dominic.models import MedicalStaffRole


FIRST_NAMES = [
    "Aravind", "Praveen", "Harini", "Nithya", "Suresh", "Keerthana",
    "Aarthi", "Anitha", "Bhavani", "Haritha", "Arun", "Karthik",
    "Rahul", "Vignesh", "Naveen", "Divya", "Priya", "Kavya",
    "Swathi", "Meena"
]

LAST_NAMES = [
    "Rajan", "Kumar", "Selvaraj", "Balakrishnan", "Kumar", "Murugan",
    "Ramesh", "Devi", "Krishnan", "Murugan", "Kumar", "Raj",
    "Prakash", "Iyer", "Nair", "Reddy", "Pillai", "Menon",
    "Krishnan", "Varma"
]


DEPARTMENTS = [
    dict(
        department_code="GEN-MED",
        department_name="General Medicine",
        short_name="GenMed",
        department_type="Outpatient",
        location="Block A - Ground Floor",
        opening_time=time(8, 0),
        closing_time=time(20, 0),
        is_emergency=False,
    ),
    dict(
        department_code="SPORTS-MED",
        department_name="Sports Medicine",
        short_name="SportsMed",
        department_type="Specialty",
        location="Athletic Complex - Wing B",
        opening_time=time(7, 0),
        closing_time=time(19, 0),
        is_emergency=False,
    ),
    dict(
        department_code="PHYSIO",
        department_name="Physiotherapy",
        short_name="Physio",
        department_type="Rehabilitation",
        location="Block C - 1st Floor",
        opening_time=time(8, 0),
        closing_time=time(18, 0),
        is_emergency=False,
    ),
    dict(
        department_code="EMERGENCY",
        department_name="Emergency Care",
        short_name="ER",
        department_type="Emergency",
        location="Block A - Ground Floor Wing 2",
        opening_time=time(0, 0),
        closing_time=time(23, 59),
        is_emergency=True,
    ),
    dict(
        department_code="DENTAL",
        department_name="Dental Care",
        short_name="Dental",
        department_type="Specialty",
        location="Block D - 2nd Floor",
        opening_time=time(9, 0),
        closing_time=time(17, 0),
        is_emergency=False,
    ),
]


ROLES = [
    dict(name="Doctor", category="DOCTOR"),
    dict(name="Staff Nurse", category="NURSE"),
    dict(name="Physiotherapist", category="PHYSIO"),
    dict(name="Lab Technician", category="LAB"),
    dict(name="Pharmacist", category="PHARMACY"),
    dict(name="Front Desk Executive", category="FRONT_DESK"),
    dict(name="Sports Medicine Specialist", category="DOCTOR"),

    # Director role
    dict(name="Director", category="DIRECTOR"),
]


QUALIFICATIONS = [
    "MBBS, MD",
    "MBBS, MS (Ortho)",
    "B.Sc Nursing",
    "BPT, MPT",
    "D.Pharm",
    "B.Pharm",
    "DMLT",
    "B.Sc MLT",
    "BDS",
    "MDS",
]


SPECIALIZATIONS = [
    "General Medicine",
    "Orthopedics",
    "Sports Injury",
    "Cardiology",
    "Physiotherapy",
    "Dental Surgery",
    "Emergency Medicine",
    "",
]


SHIFT_TIMES = {
    "MORNING": (time(7, 0), time(13, 0)),
    "AFTERNOON": (time(13, 0), time(19, 0)),
    "EVENING": (time(17, 0), time(21, 0)),
}


DAYS = [
    "MON",
    "TUE",
    "WED",
    "THU",
    "FRI",
    "SAT",
]


class Command(BaseCommand):
    help = (
        "Seed dummy Department / Role / Staff / Schedule data "
        "for the Medical Staff Dashboard."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--staff-count",
            type=int,
            default=15,
            help=(
                "How many medical staff profiles to create "
                "(bounded by available Staff users)."
            ),
        )

    @transaction.atomic
    def handle(self, *args, **options):
        staff_count = options["staff_count"]

        # --------------------------------------------------------------
        # Departments
        # --------------------------------------------------------------
        departments = self._seed_departments()

        # --------------------------------------------------------------
        # Medical Staff Roles
        # --------------------------------------------------------------
        roles = self._seed_roles()

        # --------------------------------------------------------------
        # Medical Staff
        # --------------------------------------------------------------
        medical_staff = self._seed_medical_staff(
            departments,
            roles,
            staff_count,
        )

        # --------------------------------------------------------------
        # Director
        # --------------------------------------------------------------
        self._ensure_director(
            medical_staff,
            departments,
            roles,
        )

        # --------------------------------------------------------------
        # Staff Schedules
        # --------------------------------------------------------------
        self._seed_schedules(medical_staff)

        # --------------------------------------------------------------
        # Medical Services
        # --------------------------------------------------------------
        services = self._seed_services(departments)

        # --------------------------------------------------------------
        # Patients
        # --------------------------------------------------------------
        patients = self._seed_patients()

        # --------------------------------------------------------------
        # Appointments
        # --------------------------------------------------------------
        self._seed_appointments(
            patients,
            medical_staff,
            services,
        )

        # --------------------------------------------------------------
        # Visits + Laboratory Tests
        # --------------------------------------------------------------
        self._seed_visits_and_labs(
            patients,
            medical_staff,
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Medical staff dashboard dummy data seeded successfully."
            )
        )

    # ==================================================================
    # DEPARTMENTS
    # ==================================================================

    def _seed_departments(self):
        created = []

        for d in DEPARTMENTS:
            dept, _ = MedicalDepartment.objects.get_or_create(
                department_code=d["department_code"],
                defaults=d,
            )

            created.append(dept)

        self.stdout.write(
            f"Departments ready: {len(created)}"
        )

        return created

    # ==================================================================
    # ROLES
    # ==================================================================

    def _seed_roles(self):
        created = []

        for r in ROLES:
            role, _ = MedicalStaffRole.objects.get_or_create(
                name=r["name"],
                defaults={
                    "category": r["category"],
                },
            )

            # If the role already exists but category is different,
            # update it to the expected category.
            if role.category != r["category"]:
                role.category = r["category"]
                role.save(update_fields=["category"])

            created.append(role)

        self.stdout.write(
            f"Medical staff roles ready: {len(created)}"
        )

        return created

    # ==================================================================
    # MEDICAL STAFF
    # ==================================================================

    def _seed_medical_staff(
        self,
        departments,
        roles,
        staff_count,
    ):
        eligible_users = list(
            User.objects.filter(
                is_staff=True,
                medical_staff_profile__isnull=True,
            ).select_related(
                "staff_profile"
            )
        )

        random.shuffle(eligible_users)

        eligible_users = eligible_users[:staff_count]

        if not eligible_users:
            self.stdout.write(
                self.style.WARNING(
                    "No eligible Staff users found "
                    "(is_staff=True, no medical_staff_profile yet). "
                    "Create a few Staff users/StaffProfiles first, "
                    "then re-run this command."
                )
            )

            return list(
                MedicalStaffProfile.objects.all()
            )

        created = []

        for i, user in enumerate(eligible_users):
            sp = getattr(
                user,
                "staff_profile",
                None,
            )

            dept = departments[
                i % len(departments)
            ]

            role = roles[
                i % len(roles)
            ]

            # Don't randomly assign Director here.
            # Director is explicitly handled by _ensure_director().
            if role.name == "Director":
                non_director_roles = [
                    r for r in roles
                    if r.name != "Director"
                ]

                if non_director_roles:
                    role = non_director_roles[
                        i % len(non_director_roles)
                    ]

            employee_id = (
                (sp.employee_id if sp else None)
                or f"MED-{1000 + i}"
            )

            work_email = (
                (sp.work_email if sp else None)
                or f"medstaff{i}@campus.edu"
            )

            profile, is_new = (
                MedicalStaffProfile.objects.get_or_create(
                    user=user,
                    defaults=dict(
                        employee_id=employee_id,
                        department=dept,
                        work_email=work_email,
                        personal_email=(
                            (sp.personal_email if sp else None)
                            or ""
                        ),
                        phone=(
                            user.mobile_number
                            or "9000000000"
                        ),
                        preferred_name=(
                            (sp.preferred_name if sp else None)
                            or user.full_name
                        ),
                        role=role,
                        qualification=random.choice(
                            QUALIFICATIONS
                        ),
                        specialization=random.choice(
                            SPECIALIZATIONS
                        ),
                        medical_license_number=(
                            f"LIC-{random.randint(10000, 99999)}"
                        ),
                        years_of_experience=random.randint(
                            1,
                            20,
                        ),
                        hire_date=(
                            date.today()
                            - timedelta(
                                days=random.randint(
                                    100,
                                    3000,
                                )
                            )
                        ),
                        employment_type=random.choice(
                            [
                                "FULL_TIME",
                                "FULL_TIME",
                                "PART_TIME",
                                "CONTRACT",
                            ]
                        ),
                        status=random.choice(
                            [
                                "ACTIVE",
                                "ACTIVE",
                                "ACTIVE",
                                "ON_LEAVE",
                            ]
                        ),
                        emergency_contact_name=(
                            f"{random.choice(FIRST_NAMES)} "
                            f"{random.choice(LAST_NAMES)}"
                        ),
                        emergency_contact_phone=(
                            f"9{random.randint(100000000, 999999999)}"
                        ),
                    ),
                )
            )

            if is_new:
                user.is_medical_staff = True
                user.save(
                    update_fields=[
                        "is_medical_staff"
                    ]
                )

            created.append(profile)

        self.stdout.write(
            f"Medical staff profiles ready: {len(created)}"
        )

        return created

    # ==================================================================
    # DIRECTOR
    # ==================================================================

    def _ensure_director(
        self,
        medical_staff,
        departments,
        roles,
    ):
        """
        Ensure at least one MedicalStaffProfile has the Director role.

        Existing Director:
            - Reuses it.
            - Does not create another Director.

        No Director:
            - Selects one seeded medical staff profile.
            - Changes that profile's role to Director.
        """

        director_role = next(
            (
                role
                for role in roles
                if role.name == "Director"
            ),
            None,
        )

        if not director_role:
            self.stdout.write(
                self.style.WARNING(
                    "Director role was not found."
                )
            )
            return None

        # --------------------------------------------------------------
        # Check if Director already exists
        # --------------------------------------------------------------
        existing_director = (
            MedicalStaffProfile.objects.filter(
                role=director_role
            )
            .select_related("user", "department")
            .first()
        )

        if existing_director:
            self.stdout.write(
                self.style.SUCCESS(
                    "Director already exists: "
                    f"{existing_director.preferred_name}"
                )
            )

            return existing_director

        # --------------------------------------------------------------
        # Find General Medicine department
        # --------------------------------------------------------------
        director_department = next(
            (
                dept
                for dept in departments
                if dept.department_code == "GEN-MED"
            ),
            None,
        )

        if director_department is None:
            director_department = departments[0]

        # --------------------------------------------------------------
        # Select one medical staff
        # --------------------------------------------------------------
        director_profile = None

        if medical_staff:
            director_profile = medical_staff[0]

        if director_profile is None:
            director_profile = (
                MedicalStaffProfile.objects
                .select_related("user")
                .first()
            )

        if director_profile is None:
            self.stdout.write(
                self.style.WARNING(
                    "No medical staff profile available "
                    "to assign as Director."
                )
            )

            return None

        # --------------------------------------------------------------
        # Assign Director role
        # --------------------------------------------------------------
        director_profile.role = director_role
        director_profile.department = director_department
        director_profile.specialization = (
            "Hospital Administration"
        )
        director_profile.status = "ACTIVE"

        director_profile.save(
            update_fields=[
                "role",
                "department",
                "specialization",
                "status",
            ]
        )

        # Make sure linked User is marked as medical staff.
        user = getattr(
            director_profile,
            "user",
            None,
        )

        if user and not user.is_medical_staff:
            user.is_medical_staff = True
            user.save(
                update_fields=[
                    "is_medical_staff"
                ]
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Director seeded successfully: "
                f"{director_profile.preferred_name}"
            )
        )

        return director_profile

    # ==================================================================
    # SCHEDULES
    # ==================================================================

    def _seed_schedules(self, medical_staff):
        count = 0

        for profile in medical_staff:
            assigned_days = random.sample(
                DAYS,
                k=random.randint(3, 5),
            )

            for d in assigned_days:
                shift = random.choice(
                    list(SHIFT_TIMES.keys())
                )

                start, end = SHIFT_TIMES[shift]

                _, is_new = (
                    StaffSchedule.objects.get_or_create(
                        medical_staff=profile,
                        day_of_week=d,
                        shift=shift,
                        start_time=start,
                        defaults=dict(
                            department=profile.department,
                            end_time=end,
                            room_number=(
                                f"R-{random.randint(100, 320)}"
                            ),
                        ),
                    )
                )

                if is_new:
                    count += 1

        self.stdout.write(
            f"Staff schedule entries created: {count}"
        )

    # ==================================================================
    # SERVICES
    # ==================================================================

    def _seed_services(self, departments):
        service_defs = [
            (
                "CONS-GEN",
                "General Consultation",
                "CONSULTATION",
                20,
            ),
            (
                "CONS-SPORTS",
                "Sports Injury Consultation",
                "SPORTS",
                30,
            ),
            (
                "PHYSIO-SESS",
                "Physiotherapy Session",
                "PHYSIOTHERAPY",
                45,
            ),
            (
                "LAB-BASIC",
                "Basic Lab Panel",
                "LABORATORY",
                15,
            ),
            (
                "DENTAL-CHECK",
                "Dental Checkup",
                "DENTAL",
                25,
            ),
        ]

        created = []

        for i, (
            code,
            name,
            category,
            duration,
        ) in enumerate(service_defs):

            dept = departments[
                i % len(departments)
            ]

            service, _ = (
                MedicalService.objects.get_or_create(
                    service_code=code,
                    defaults=dict(
                        department=dept,
                        service_name=name,
                        service_category=category,
                        estimated_duration=duration,
                    ),
                )
            )

            created.append(service)

        self.stdout.write(
            f"Medical services ready: {len(created)}"
        )

        return created

    # ==================================================================
    # PATIENTS
    # ==================================================================

    def _seed_patients(self):
        """
        Reuse whichever real Student/Faculty/Staff profiles
        already exist.

        We only need a handful of PatientProfile rows to power
        the small "Appointments Today / Pending Labs" numbers
        on the dashboard.
        """

        try:
            from Students.models import StudentProfile
        except Exception:
            StudentProfile = None

        try:
            from Faculty.models import FacultyProfile
        except Exception:
            FacultyProfile = None

        patients = []

        # --------------------------------------------------------------
        # Student Patients
        # --------------------------------------------------------------
        if StudentProfile is not None:
            for sp in StudentProfile.objects.all()[:6]:
                p, _ = PatientProfile.objects.get_or_create(
                    student=sp,
                    defaults=dict(
                        patient_number=(
                            f"PT-STU-{sp.pk}"
                        ),
                        patient_type="STUDENT",
                        blood_group=random.choice(
                            [
                                "A+",
                                "B+",
                                "O+",
                                "AB+",
                            ]
                        ),
                    ),
                )

                patients.append(p)

        # --------------------------------------------------------------
        # Faculty Patients
        # --------------------------------------------------------------
        if FacultyProfile is not None:
            for fp in FacultyProfile.objects.all()[:3]:
                p, _ = PatientProfile.objects.get_or_create(
                    faculty=fp,
                    defaults=dict(
                        patient_number=(
                            f"PT-FAC-{fp.pk}"
                        ),
                        patient_type="FACULTY",
                        blood_group=random.choice(
                            [
                                "A+",
                                "B+",
                                "O+",
                                "AB+",
                            ]
                        ),
                    ),
                )

                patients.append(p)

        # --------------------------------------------------------------
        # Staff Patients
        # --------------------------------------------------------------
        for sfp in StaffProfile.objects.all()[:3]:
            p, _ = PatientProfile.objects.get_or_create(
                staff=sfp,
                defaults=dict(
                    patient_number=(
                        f"PT-STF-{sfp.pk}"
                    ),
                    patient_type="STAFF",
                    blood_group=random.choice(
                        [
                            "A+",
                            "B+",
                            "O+",
                            "AB+",
                        ]
                    ),
                ),
            )

            patients.append(p)

        if not patients:
            self.stdout.write(
                self.style.WARNING(
                    "No Student/Faculty/Staff profiles found — "
                    "skipping PatientProfile/Appointment/"
                    "Lab/Visit seeding."
                )
            )
        else:
            self.stdout.write(
                f"Patient profiles ready: {len(patients)}"
            )

        return patients

    # ==================================================================
    # APPOINTMENTS
    # ==================================================================

    def _seed_appointments(
        self,
        patients,
        medical_staff,
        services,
    ):
        if not patients or not medical_staff or not services:
            return

        today = timezone.localdate()
        count = 0

        for i in range(12):
            patient = random.choice(
                patients
            )

            staff = random.choice(
                medical_staff
            )

            service = random.choice(
                services
            )

            appt_date = (
                today
                + timedelta(
                    days=random.randint(-2, 3)
                )
            )

            priority = random.choices(
                [
                    "NORMAL",
                    "HIGH",
                    "EMERGENCY",
                    "LOW",
                ],
                weights=[
                    6,
                    2,
                    1,
                    1,
                ],
            )[0]

            status = random.choice(
                [
                    "PENDING",
                    "CONFIRMED",
                    "CHECKED_IN",
                    "IN_PROGRESS",
                    "COMPLETED",
                ]
            )

            _, is_new = (
                Appointment.objects.get_or_create(
                    appointment_number=f"APT-{2000 + i}",
                    defaults=dict(
                        patient=patient,
                        medical_staff=staff,
                        department=staff.department,
                        service=service,
                        appointment_date=appt_date,
                        appointment_time=time(
                            random.randint(8, 17),
                            random.choice(
                                [
                                    0,
                                    15,
                                    30,
                                    45,
                                ]
                            ),
                        ),
                        priority=priority,
                        status=status,
                        reason=(
                            "Routine checkup / "
                            "follow-up (seed data)"
                        ),
                    ),
                )
            )

            if is_new:
                count += 1

        self.stdout.write(
            f"Appointments created: {count}"
        )

    # ==================================================================
    # VISITS + LABS
    # ==================================================================

    def _seed_visits_and_labs(
        self,
        patients,
        medical_staff,
    ):
        if not patients or not medical_staff:
            return

        today = timezone.localdate()

        visit_count = 0
        lab_count = 0

        for i in range(8):
            patient = random.choice(
                patients
            )

            staff = random.choice(
                medical_staff
            )

            visit, is_new = (
                MedicalVisit.objects.get_or_create(
                    visit_number=f"VIS-{3000 + i}",
                    defaults=dict(
                        patient=patient,
                        attending_staff=staff,
                        department=staff.department,
                        visit_type=random.choice(
                            [
                                "CONSULTATION",
                                "FOLLOW_UP",
                                "HEALTH_CHECK",
                            ]
                        ),
                        visit_date=(
                            today
                            - timedelta(
                                days=random.randint(
                                    0,
                                    5,
                                )
                            )
                        ),
                        visit_time=time(
                            random.randint(8, 17),
                            0,
                        ),
                        chief_complaint=(
                            "Seed data visit for "
                            "dashboard testing."
                        ),
                        visit_status=random.choice(
                            [
                                "OPEN",
                                "COMPLETED",
                            ]
                        ),
                    ),
                )
            )

            if is_new:
                visit_count += 1

            _, is_new_lab = (
                LaboratoryTest.objects.get_or_create(
                    test_number=f"LAB-{4000 + i}",
                    defaults=dict(
                        patient=patient,
                        medical_visit=visit,
                        requested_by=staff,
                        test_name=random.choice(
                            [
                                "CBC",
                                "Blood Sugar",
                                "X-Ray Knee",
                                "ECG",
                                "Urine Routine",
                            ]
                        ),
                        test_category=random.choice(
                            [
                                "BLOOD",
                                "URINE",
                                "ECG",
                                "XRAY",
                            ]
                        ),
                        requested_date=(
                            today
                            - timedelta(
                                days=random.randint(
                                    0,
                                    4,
                                )
                            )
                        ),
                        status=random.choice(
                            [
                                "REQUESTED",
                                "COLLECTED",
                                "PROCESSING",
                                "COMPLETED",
                            ]
                        ),
                    ),
                )
            )

            if is_new_lab:
                lab_count += 1

        self.stdout.write(
            "Medical visits created: "
            f"{visit_count}, "
            "Lab tests created: "
            f"{lab_count}"
        )