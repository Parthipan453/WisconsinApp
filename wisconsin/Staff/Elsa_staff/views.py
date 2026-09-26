from django.shortcuts import render
from Faculty.Elsa_Faculty.models import CourseGrade
from Faculty.models import FacultyProfile, FacultyCourseAssignment
from Admin.Colleges.models import AcademicTerm, ProgramCourse
from Students.models import Semester
from Admin.Elsa_admin.models import GradeScale
from Students.models import CourseSection
from django.utils import timezone

TERM_TYPE_MAP = {
    "FALL": "FA",
    "SPRING": "SP",
    "SUMMER": "SU",
    "WINTER": "WI",
}

def _get_current_semester():
    today = timezone.localdate()

    current_term = (
        AcademicTerm.objects
        .filter(status="ACTIVE", start_date__lte=today, end_date__gte=today)
        .order_by("start_date")
        .first()
    )
    if current_term:
        semester_type = TERM_TYPE_MAP.get(current_term.term_name)
        academic_year = int(current_term.academic_year.split("-")[0])
        semester = Semester.objects.filter(
            semester_type=semester_type,
            academic_year=academic_year,
        ).first()
        if semester:
            return semester
    current = Semester.objects.filter(is_current=True).first()
    if current:
        return current
    current = (
        Semester.objects
        .filter(start_date__lte=today, end_date__gte=today)
        .first()
    )
    if current:
        return current
    return Semester.objects.order_by("-start_date").first()


def gradebook(request, staff_uuid):

    current_semester = _get_current_semester()
    current_semester_id = str(current_semester.pk) if current_semester else ""
    current_semester_label = (
        f"{current_semester.semester_type} {current_semester.academic_year}"
        if current_semester else ""
    )

    grade_scales_json = [
        {
            "letter": g.letter_grade,
            "points": float(g.grade_points) if g.grade_points is not None else None,
        }
        for g in GradeScale.objects.order_by("-grade_points")
    ]

    grades_qs = (
        CourseGrade.objects
        .select_related(
            "student", "student__user",
            "student__academic_profile", "student__academic_profile__program",
            "course", "course__department",
            "semester", "grade_scale",
        )
        .order_by("course__course_code", "student__student_number")
    )

    groups = {}
    for grade in grades_qs:
        key = (grade.course_id, grade.instructor_id, grade.semester_id)
        if key not in groups:
            groups[key] = {
                "course": grade.course,
                "instructor_id": grade.instructor_id,
                "semester": grade.semester,
                "grades": [],
            }
        groups[key]["grades"].append(grade)

    instructor_ids = {g["instructor_id"] for g in groups.values() if g["instructor_id"]}
    faculty_by_id = {
        f.employee_id: f
        for f in FacultyProfile.objects
        .filter(employee_id__in=instructor_ids)
        .select_related("user")
    }

    faculty_objs = list(faculty_by_id.values())

    assignment_pairs = list(
        FacultyCourseAssignment.objects
        .filter(faculty__in=faculty_objs)
        .values_list("faculty__employee_id", "course_section_id")
    )

    section_ids = {
        str(section_id)
        for _, section_id in assignment_pairs
        if section_id
    }

    sections_by_id = {
        s.section_id: s
        for s in CourseSection.objects
        .filter(section_id__in=section_ids)
        .select_related("course", "semester_id")
    }

    section_lookup = {}
    for employee_id, section_id in assignment_pairs:
        section = sections_by_id.get(section_id)
        if not section or not section.course:
            continue
        semester_pk = section.semester_id_id if section.semester_id else None
        key = (employee_id, section.course_id, semester_pk)
        section_lookup.setdefault(key, set()).add(str(section.section_number))
    # ---------------------------------------------------------------------------------

    program_ids = set()
    course_ids = set()
    for grade in grades_qs:
        academic_profile = getattr(grade.student, "academic_profile", None)
        program = academic_profile.program if academic_profile else None
        if program:
            program_ids.add(program.pk)
        if grade.course:
            course_ids.add(grade.course.pk)

    program_course_map = {
        (pc.program_id, pc.course_id): pc.study_year
        for pc in ProgramCourse.objects.filter(
            program_id__in=program_ids, course_id__in=course_ids
        ).values_list("program_id", "course_id", "study_year", named=False)
        for pc in [type("_", (), {"program_id": pc[0], "course_id": pc[1], "study_year": pc[2]})]
    } if program_ids and course_ids else {}

    courses_payload = []
    for group in groups.values():
        course = group["course"]
        semester = group["semester"]

        faculty = faculty_by_id.get(group["instructor_id"])
        faculty_name = faculty.user.get_full_name() if faculty else "Not assigned"
        faculty_id = str(group["instructor_id"]) if group["instructor_id"] else ""

        department = course.department if course else None
        department_name = department.department_name if department else "Not assigned"
        department_id = str(department.pk) if department else ""

        semester_name = (
            f"{semester.semester_type} {semester.academic_year}" if semester else "Not assigned"
        )
        semester_id = str(semester.pk) if semester else ""

        # ---------------- Section label ----------------
        section_key = (
            group["instructor_id"],
            course.pk if course else None,
            semester.pk if semester else None,
        )
        section_numbers = section_lookup.get(section_key, set())
        section_label = ", ".join(sorted(section_numbers)) if section_numbers else "Not assigned"
        # -------------------------------------------------

        students_payload = []
        for grade in group["grades"]:
            student = grade.student
            name = student.preferred_name or student.user.get_full_name()

            academic_profile = getattr(student, "academic_profile", None)
            program = academic_profile.program if academic_profile else None
            program_name = program.program_name if program else "Not assigned"
            program_id = str(program.pk) if program else ""

            study_year = None
            if program and course:
                study_year = program_course_map.get((program.pk, course.pk))

            students_payload.append({
                "id": student.id,
                "name": name,
                "rollNo": student.student_number,
                "score": float(grade.numeric_score) if grade.numeric_score is not None else None,
                "grade": grade.grade_scale.letter_grade if grade.grade_scale else "",
                "finalized": bool(grade.is_finalized),
                "program": program_name,
                "programId": program_id,
                "year": study_year,
            })

        courses_payload.append({
            "id": f"{course.course_id if course else 'x'}-{group['instructor_id']}-{semester_id}",
            "name": course.course_name if course else "Unknown Course",
            "code": course.course_code if course else "",
            "subject": course.course_code if course else "",
            "faculty": faculty_name,
            "facultyId": faculty_id,
            "department": department_name,
            "departmentId": department_id,
            "semester": semester_name,
            "semesterId": semester_id,
            "section": section_label,
            "students": students_payload,
        })

    context = {
        "staff_uuid": staff_uuid,
        "courses_json": courses_payload,
        "current_semester_id": current_semester_id,
        "current_semester_label": current_semester_label,
        "grade_scales_json": grade_scales_json,
    }
    return render(request, "Elsa/gradebook.html", context)