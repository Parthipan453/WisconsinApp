import secrets
import string
import re
import logging
from datetime import date, timezone

from django.contrib.auth.hashers import make_password
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.template.loader import render_to_string
from django.conf import settings

from Admin.models import User
from Applicants.models import Applicant, Application, ApplicantProfile
from Students.models import StudentProfile, StudentAcademicProfile, StudentAddress

logger = logging.getLogger(__name__)


def generate_student_number(admission_year=None) -> str:
    """STU<year><seq> — e.g. STU2026001."""
    year = admission_year or date.today().year
    prefix = f"STU{year}"

    existing = (
        StudentProfile.objects
        .filter(student_number__startswith=prefix)
        .values_list("student_number", flat=True)
    )
    max_seq = 0
    pattern = re.compile(rf"^{prefix}(\d+)$")
    for num in existing:
        m = pattern.match(num)
        if m:
            seq = int(m.group(1))
            if seq > max_seq:
                max_seq = seq

    return f"{prefix}{max_seq + 1:03d}"


def generate_temp_password(length=12) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%"
    while True:
        pw = "".join(secrets.choice(alphabet) for _ in range(length))
        if (any(c.islower() for c in pw) and any(c.isupper() for c in pw)
                and any(c.isdigit() for c in pw) and any(c in "!@#$%" for c in pw)):
            return pw


def generate_university_email(first_name: str, last_name: str) -> str:
    """first.last@wisc.edu — dedup with a numeric suffix if needed."""
    base = re.sub(r"[^a-z]", "", first_name.lower().strip())
    slug = re.sub(r"[^a-z]", "", last_name.lower().strip())
    email = f"{base}.{slug}@wisc.edu"

    if not User.objects.filter(email=email).exists():
        return email

    for i in range(2, 100):
        email = f"{base}.{slug}{i}@wisc.edu"
        if not User.objects.filter(email=email).exists():
            return email

    return f"{base}.{slug}{secrets.randbelow(900)+100}@wisc.edu"


def _map_citizenship(applicant_type: str, immigration_status: str = "") -> tuple:
    """Returns (citizenship_status, country_of_citizenship)."""
    t = (applicant_type or "").lower()
    imm = (immigration_status or "").lower()
    if "international" in t or "f1" in t or "j1" in t:
        return "INTERNATIONAL", None
    if "permanent" in imm or "pr" in imm:
        return "PERMANENT_RESIDENT", None
    if "citizen" in imm or not imm:
        return "CITIZEN", None
    return "OTHER", None


def _map_academic_level(admission_level: str, applicant_type: str = "") -> str:
    al = (admission_level or "").lower()
    t = (applicant_type or "").lower()
    if "phd" in al or "doctoral" in al or "phd" in t:
        return "PHD"
    if "master" in al or "graduate" in al or "certificate" in al:
        return "GRADUATE"
    if "master" in t or "graduate" in t:
        return "GRADUATE"
    return "UNDERGRADUATE"


def _get_profile_field(profile: ApplicantProfile, *field_names, default=""):
    """Safely read from ApplicantProfile, trying each field name."""
    if profile is None:
        return default
    for name in field_names:
        val = getattr(profile, name, None)
        if val:
            return val
    return default


def create_student_from_application(application_id: int, created_by=None) -> dict:
    """
    Convert an offer-accepted Application into a full student account.

    Returns:
        {
            "user": <User>,
            "student_profile": <StudentProfile>,
            "temp_password": str,
            "university_email": str,
            "student_number": str,
        }

    Raises ValueError if application is not in a valid state or already converted.
    """
    app = (
        Application.objects
        .select_related("applicant", "program", "university", "school",
                        "department", "degree_level", "admission_cycle")
        .get(application_id=application_id)
    )
    applicant = app.applicant

    if app.status not in ("offer_accepted", "enrolled"):
        raise ValueError(f"Application must be 'offer_accepted' (current: {app.status}).")

    if applicant.converted_to_user_id:
        raise ValueError(
            f"This applicant is already linked to user account "
            f"(#{applicant.converted_to_user_id})."
        )

    profile = ApplicantProfile.objects.filter(applicant=applicant).first()

    temp_password = generate_temp_password()
    university_email = generate_university_email(applicant.first_name, applicant.last_name)
    admission_year = app.deposit_paid_at.year if app.deposit_paid_at else date.today().year
    student_number = generate_student_number(admission_year)

    with transaction.atomic():
        # ── 1. Create User ──
        user = User.objects.create(
            username=university_email.split("@")[0],
            email=university_email,
            first_name=applicant.first_name,
            last_name=applicant.last_name,
            middle_name=_get_profile_field(profile, "middle_name"),
            date_of_birth=profile.date_of_birth if profile else applicant.date_of_birth,
            gender=_get_profile_field(profile, "gender"),
            mobile_number=_get_profile_field(profile, "phone", "alternate_phone",
                                             default=applicant.mobile_number),
            password=make_password(temp_password),
            is_student=True,
            is_active=True,
            email_verified=False,
            account_status="ACTIVE",
        )

        # ── 2. Link Applicant → User ──
        applicant.converted_to_user = user
        applicant.save(update_fields=["converted_to_user"])

        # ── 3. Citizenship mapping ──
        cit_status, cit_country = _map_citizenship(
            app.applicant_type,
            _get_profile_field(profile, "nationality"),
        )

        # ── 4. Create StudentProfile ──
        student_profile = StudentProfile.objects.create(
            user=user,
            student_number=student_number,
            preferred_name=_get_profile_field(profile, "middle_name") or applicant.first_name,
            university_email=university_email,
            personal_email=applicant.email,
            citizenship_status=cit_status,
            country_of_citizenship=cit_country,
            admission_date=app.deposit_paid_at or date.today(),
            current_status="ACTIVE",
            academic_level=_map_academic_level(app.admission_level, app.applicant_type),
        )

        # ── 5. Create StudentAcademicProfile ──
        major_name = _get_profile_field(profile, "major")
        if not major_name and app.program:
            major_name = app.program.program_name

        StudentAcademicProfile.objects.create(
            student=student_profile,
            university=app.university,
            school=app.school,
            department=app.department,
            degree=app.degree_level,
            program=app.program,
            major=major_name or "",
            catalog_year=date.today().year,
        )

        # ── 6. Create StudentAddress (if profile has address) ──
        addr_line1 = _get_profile_field(profile, "address_line1")
        if addr_line1:
            StudentAddress.objects.create(
                student=student_profile,
                address_type="PERMANENT",
                address_line_1=addr_line1,
                address_line_2=_get_profile_field(profile, "address_line2"),
                city=_get_profile_field(profile, "city"),
                state=_get_profile_field(profile, "state"),
                postal_code=_get_profile_field(profile, "postal_code"),
                country=_get_profile_field(profile, "country", default="US"),
            )

        # ── 7. Application log ──
        from Applicants.models import ApplicationLog
        ApplicationLog.objects.create(
            application=app,
            field_name="student_created",
            old_value="",
            new_value=(
                f"Student account created -- {student_number}, "
                f"{university_email}"
            ),
            actor=created_by or "System",
        )

        # ── 8. Mark application as enrolled ──
        app.status = "enrolled"
        app.save(update_fields=["status"])

    # ── 9. Send welcome email ──
    _send_student_welcome_email(user, student_profile, temp_password, app)

    return {
        "user": user,
        "student_profile": student_profile,
        "temp_password": temp_password,
        "university_email": university_email,
        "student_number": student_number,
    }


def _send_student_welcome_email(user, student_profile, temp_password, app):
    """Send welcome email with login credentials to the new student's personal email."""
    contact_email = getattr(settings, "APPLICANT_CONTACT_EMAIL", "contact@go.wisconsin.edu")
    site_url = getattr(settings, "SITE_URL", "http://127.0.0.1:8000")
    program_name = app.program.program_name if app.program else "your program"

    ctx = {
        "student_name": user.get_full_name() or user.first_name,
        "username": user.username,
        "student_number": student_profile.student_number,
        "university_email": user.email,
        "temp_password": temp_password,
        "program_name": program_name,
        "portal_url": site_url,
        "contact_email": contact_email,
    }

    subject = f"Welcome to the University of Wisconsin–Madison — Your Student Account"
    html_body = render_to_string("eric/emails/student_welcome.html", ctx)

    txt_body = render_to_string("eric/emails/student_welcome.txt", ctx)
    to_email = app.applicant.email
    msg = EmailMultiAlternatives(
        subject=subject,
        body=txt_body,
        from_email=contact_email,
        to=[to_email],
    )
    msg.attach_alternative(html_body, "text/html")
    msg.send(fail_silently=True)
