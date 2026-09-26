## Leo's Code Start ##
import csv

############################################################
# Standard Library Imports
############################################################
from datetime import date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation

############################################################
# Django Core Imports
############################################################
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Avg, Count, Max, OuterRef, Prefetch, Q, Subquery, Sum
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.text import Truncator
from django.views.decorators.http import require_POST

############################################################
# Admin App Imports
############################################################
from Admin.bela_admin.models import Department

############################################################
# Faculty App Imports
############################################################
from Faculty.models import FacultyCourseAssignment, FacultyProfile
from Faculty.leo.forms import (
    AdvisorResearchAdviceForm,
    AnnualProgressReviewForm,
    CommitteeMemberForm,
    CourseworkEvaluationForm,
    CourseworkForm,
    CourseworkSubmissionForm,
    DissertationDefenseChairFinalizationForm,
    DissertationDefenseEvaluationForm,
    DissertationDefenseScheduleForm,
    DissertationEvaluationForm,
    DissertationProposalAdvisorReviewForm,
    DoctoralCandidacyForm,
    FacultyCourseworkForm,
    FacultyCourseworkUpdateForm,
    FinalDissertationAdvisorEvaluationForm,
    FinalDissertationChairFinalizationForm,
    PreliminaryExaminationForm,
    PreliminaryExamEvaluationForm,
    ResearchMilestoneEvaluationForm,
    ResearchMilestoneForm,
    DissertationDefenseScheduleForm,
    ResearchMilestoneEvaluationForm,
)
from Faculty.leo.models import (
    AdvisorResearchAdvice,
    AdvisorStudentMessage,
    AdvisorStudentMessageAttachment,
    Attendance,
    AttendanceSession,
    Coursework,
    CourseworkEvaluation,
    CourseworkSubmission,
    DissertationAdvisorAdvice,
    DissertationAdvisorFeedback,
    DissertationApproval,
    DissertationChairReplyFeedback,
    DissertationEvaluation,
    FacultyCoursework,
    FinalDissertationAdvisorEvaluation,
    FinalDissertationCommitteeEvaluation,
    PreliminaryExamEvaluation,
    ResearchMilestone,
    ResearchMilestoneEvaluation,
    ResearchMilestoneSubmission,
)

############################################################
# Students App Imports
############################################################
from Students.models import (
    AnnualProgressReview,
    CommitteeMember,
    CourseSection,
    DefenseLocation,
    Dissertation,
    DissertationDefense,
    DissertationDefenseEvaluation,
    DissertationProposal,
    DissertationProposalEvaluation,
    DissertationProposalResubmissionRequest,
    DoctoralCandidacy,
    DoctoralCommittee,
    FinalDissertationSubmission,
    Graduation,
    PhDStudent,
    PhDMilestone,
    PreliminaryExamination,
    ResearchPublication,
    Schedule,
    StudentEnrollment,
)
from Students.Leo_Student.forms import DissertationProposalForm
from Students.Leo_Student.models import (
    PhD,
    PhDVideoEvidence,
)

from Staff.models import Notification
from notifications.utils import send_notification

############################################################
# ATTENDANCE MODULE FOR STUDENT IN FACULTY DASHBOARD
############################################################

# ======== ELSA CODE START ==========
from django.contrib.auth import get_user_model
from Staff.models import Notification
def _notify_staff_attendance_taken(faculty, session, present_count, absent_count):
    faculty_name = faculty.user.get_full_name() or faculty.user.username
    course_label = session.course.course_code if session.course else "the course"
    message = (
        f"{faculty_name} recorded attendance for {course_label} on "
        f"{session.attendance_date.strftime('%d %b %Y')} "
        f"({present_count} present, {absent_count} absent)."
    )
    for staff_user in get_user_model().objects.filter(is_staff=True):
        link = reverse("student_attendance_record", args=[staff_user.uuid])

        Notification.objects.create(
            user=staff_user,
            title="Attendance Recorded",
            message=message,
            notification_type="INFO",
            link=link,
        )
@login_required
def student_attendance_list(request):
    faculty = get_object_or_404(FacultyProfile, user=request.user)
    today = timezone.localdate()

    date_param = request.GET.get("date")
    if date_param:
        try:
            selected_date = datetime.strptime(date_param, "%Y-%m-%d").date()
        except ValueError:
            selected_date = today
    else:
        selected_date = today

    selected_date_string = selected_date.isoformat()

    assignments = FacultyCourseAssignment.objects.filter(faculty=faculty)
    section_ids = assignments.values_list("course_section_id", flat=True)

    sections = (
        CourseSection.objects.filter(section_id__in=section_ids)
        .select_related("course", "course__department", "semester_id")
        .annotate(student_count=Count("enrollments"))
    )
    section_dict = {section.section_id: section for section in sections}

    selected_sessions = {
        (session.section_id, session.schedule_id): session
        for session in AttendanceSession.objects.filter(
            faculty=faculty, attendance_date=selected_date
        )
    }

    attendance_sessions = []
    classes_count = 0
    total_students = 0
    pending_classes_count = 0
    completed_classes_count = 0

    for assignment in assignments:
        section = section_dict.get(assignment.course_section_id)
        if not section or not section.course:
            continue

        schedules = Schedule.objects.filter(section_id=section.section_id)

        # collect ALL slots scheduled on this date, don't stop at the first
        matched_schedules = [
            item for item in schedules if selected_date_string in (item.dates or [])
        ]

        if not matched_schedules:
            continue

        for schedule in matched_schedules:
            session = selected_sessions.get((section.section_id, schedule.pk))

            attendance_sessions.append(
                {
                    "id": session.id if session else None,
                    "section": section,
                    "course": section.course,
                    "schedule": schedule,
                    "student_count": section.student_count,
                    "attendance_date": selected_date,
                    "status": (session.status if session else None),
                    "has_session": session is not None,
                }
            )

            classes_count += 1
            total_students += section.student_count

            if session and session.status == "CLOSED":
                completed_classes_count += 1
            else:
                pending_classes_count += 1

    context = {
        "attendance_sessions": attendance_sessions,
        "todays_classes_count": classes_count,
        "total_students_today": total_students,
        "pending_classes_count": pending_classes_count,
        "completed_today_count": completed_classes_count,
        "selected_date": selected_date,
        "today": today,
    }
    return render(request, "leo/Attendance/Attendance_list.html", context)


@login_required
def student_attendance_start(request, section_id, schedule_id):
    faculty = get_object_or_404(FacultyProfile, user=request.user)
    section = get_object_or_404(CourseSection, section_id=section_id)
    schedule = get_object_or_404(
        Schedule, pk=schedule_id, section_id=section.section_id
    )

    today = timezone.localdate()
    date_param = request.GET.get("date")
    if date_param:
        try:
            selected_date = datetime.strptime(date_param, "%Y-%m-%d").date()
        except ValueError:
            selected_date = today
    else:
        selected_date = today

    selected_date_string = selected_date.isoformat()

    assigned = FacultyCourseAssignment.objects.filter(
        faculty=faculty, course_section_id=section.section_id
    ).exists()
    if not assigned:
        return redirect("student_attendance_list")

    scheduled_dates = schedule.dates or []
    if selected_date_string not in scheduled_dates:
        messages.error(
            request,
            f"{selected_date.strftime('%d %b %Y')} is not a scheduled class date.",
        )
        return redirect(
            f"{reverse('student_attendance_list')}?date={selected_date_string}"
        )

    session, created = AttendanceSession.objects.get_or_create(
        faculty=faculty,
        course=section.course,
        section=section,
        schedule=schedule,
        attendance_date=selected_date,
        defaults={"status": "OPEN"},
    )

    return redirect("student_attendance_take", session_id=session.id)


# ======== ELSA CODE END ===============


def student_attendance_take(request, session_id):
    """
    Take attendance for a specific session.

    Purpose:
        Allow faculty to mark attendance for all students in a session.

    Parameters:
        request: HTTP request object
        session_id: ID of the attendance session

    Returns:
        Rendered template with form for taking attendance

    Workflow:
        1. Get attendance session and related schedule
        2. Check if attendance already taken
        3. Get enrolled students
        4. Handle POST request - save attendance records
        5. Handle GET request - display attendance form
    """
    # Get attendance session
    session = get_object_or_404(
        AttendanceSession,
        id=session_id,
    )
    # Get schedule for THIS attendance date
    selected_date_string = session.attendance_date.isoformat()

    schedule = None

    for item in Schedule.objects.filter(section_id=session.section):
        scheduled_dates = item.dates or []

        if selected_date_string in scheduled_dates:
            schedule = item
            break

    # Check for duplicate attendance
    if Attendance.objects.filter(attendance_session=session).exists():
        messages.warning(
            request,
            "Attendance already taken for this session.",
        )
        return redirect(
            "student_attendance_view",
            session.id,
        )

    # Get enrolled students
    enrollments = (
        StudentEnrollment.objects.filter(section_id=session.section)
        .select_related(
            "student",
            "student__user",
        )
        .order_by("student__student_number")
    )

    # Process POST request
    if request.method == "POST":
        for enrollment in enrollments:
            student = enrollment.student

            status = request.POST.get(
                f"status_{student.id}",
                "PRESENT",
            )

            remarks = request.POST.get(
                f"remarks_{student.id}",
                "",
            )

            Attendance.objects.create(
                attendance_session=session,
                student=student,
                status=status,
                remarks=remarks,
            )

        # Close attendance session
        session.status = "CLOSED"
        session.save()
    # ======== ELSA CODE START =================================
        present_count = Attendance.objects.filter(
            attendance_session=session, status="PRESENT"
        ).count()
        absent_count = Attendance.objects.filter(
            attendance_session=session, status="ABSENT"
        ).count()
        _notify_staff_attendance_taken(session.faculty, session, present_count, absent_count)
    # ======== ELSA CODE END ====================================
        messages.success(
            request,
            "Attendance saved successfully.",
        )

        return redirect(
            "student_attendance_view",
            session.id,
        )

    # Render GET request
    context = {
        "session": session,
        "schedule": schedule,
        "enrollments": enrollments,
        "total_students": enrollments.count(),
    }

    return render(
        request,
        "leo/Attendance/Attendance_take.html",
        context,
    )


def student_attendance_view(request, session_id):
    """
    View attendance records for a specific session.

    Purpose:
        Display attendance records with statistics for a session.

    Parameters:
        request: HTTP request object
        session_id: ID of the attendance session

    Returns:
        Rendered template with attendance data and statistics

    Workflow:
        1. Get attendance session
        2. Get schedule
        3. Get attendance records
        4. Calculate statistics
        5. Render view template
    """
    # Get attendance session
    session = get_object_or_404(
        AttendanceSession,
        id=session_id,
    )

    # Get schedule for THIS attendance date
    selected_date_string = session.attendance_date.isoformat()

    schedule = None

    for item in Schedule.objects.filter(section_id=session.section):
        scheduled_dates = item.dates or []

        if selected_date_string in scheduled_dates:
            schedule = item
            break

    # Get attendance records
    attendances = (
        Attendance.objects.filter(attendance_session=session)
        .select_related(
            "student",
            "student__user",
        )
        .order_by("student__student_number")
    )

    # Calculate statistics
    total_students = StudentEnrollment.objects.filter(
        section_id=session.section
    ).count()

    present_count = attendances.filter(status="PRESENT").count()
    absent_count = attendances.filter(status="ABSENT").count()
    late_count = attendances.filter(status="LATE").count()
    leave_count = attendances.filter(status="LEAVE").count()
    half_day_count = attendances.filter(status="HALF_DAY").count()
    permission_count = attendances.filter(status="PERMISSION").count()

    context = {
        "session": session,
        "schedule": schedule,
        "attendances": attendances,
        "total_students": total_students,
        "present_count": present_count,
        "absent_count": absent_count,
        "late_count": late_count,
        "leave_count": leave_count,
        "half_day_count": half_day_count,
        "permission_count": permission_count,
    }

    return render(
        request,
        "leo/Attendance/Attendance_view.html",
        context,
    )


def student_attendance_edit(request, session_id):
    """
    Edit attendance records for a specific session.

    Purpose:
        Allow faculty to modify existing attendance records.

    Parameters:
        request: HTTP request object
        session_id: ID of the attendance session

    Returns:
        Rendered template with edit form and statistics

    Workflow:
        1. Get attendance session
        2. Get schedule
        3. Get existing attendance records
        4. Handle POST request - update records
        5. Calculate statistics
        6. Render edit template
    """
    # Get attendance session
    session = get_object_or_404(
        AttendanceSession,
        id=session_id,
    )

    # Get schedule for THIS attendance date
    selected_date_string = session.attendance_date.isoformat()

    schedule = None

    for item in Schedule.objects.filter(section_id=session.section):
        scheduled_dates = item.dates or []

        if selected_date_string in scheduled_dates:
            schedule = item
            break

    # Get existing attendance records
    attendances = (
        Attendance.objects.filter(attendance_session=session)
        .select_related(
            "student",
            "student__user",
        )
        .order_by("student__student_number")
    )

    # Process POST request
    if request.method == "POST":
        for attendance in attendances:
            status = request.POST.get(
                f"status_{attendance.id}",
                attendance.status,
            )

            remarks = request.POST.get(
                f"remarks_{attendance.id}",
                "",
            )

            attendance.status = status
            attendance.remarks = remarks
            attendance.save()

        messages.success(
            request,
            "Attendance updated successfully.",
        )

        return redirect(
            "student_attendance_view",
            session.id,
        )

    # Calculate statistics
    total_students = StudentEnrollment.objects.filter(
        section_id=session.section
    ).count()

    present_count = attendances.filter(status="PRESENT").count()
    absent_count = attendances.filter(status="ABSENT").count()
    late_count = attendances.filter(status="LATE").count()
    leave_count = attendances.filter(status="LEAVE").count()
    half_day_count = attendances.filter(status="HALF_DAY").count()
    permission_count = attendances.filter(status="PERMISSION").count()

    context = {
        "session": session,
        "schedule": schedule,
        "attendances": attendances,
        "total_students": total_students,
        "present_count": present_count,
        "absent_count": absent_count,
        "late_count": late_count,
        "leave_count": leave_count,
        "half_day_count": half_day_count,
        "permission_count": permission_count,
    }

    return render(
        request,
        "leo/Attendance/Attendance_edit.html",
        context,
    )


def faculty_phd_management(request, uuid):
    faculty = get_object_or_404(
        FacultyProfile,
        user__uuid=uuid,
    )

    today = date.today()

    def to_datetime(value):
        if value is None:
            return datetime.min

        if isinstance(value, datetime):
            if value.tzinfo is not None:
                return value.replace(tzinfo=None)
            return value

        if isinstance(value, date):
            return datetime.combine(
                value,
                datetime.min.time(),
            )

        return datetime.min

    def safe_date(value):
        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        return None

    def display_date(value):
        value = safe_date(value)

        if value:
            return value.strftime("%b %d, %Y")

        return "—"

    committee_list = (
        DoctoralCommittee.objects.filter(
            Q(chair_faculty=faculty) | Q(committee_members__faculty=faculty)
        )
        .distinct()
        .select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__phd_program",
            "phd_student__advisor",
            "chair_faculty",
        )
        .prefetch_related(
            "committee_members",
        )
        .order_by(
            "-formation_date",
        )
    )

    phd_student_ids = list(
        committee_list.values_list(
            "phd_student_id",
            flat=True,
        )
    )

    advisee_ids = list(
        PhDStudent.objects.filter(
            advisor=faculty,
            current_status="ACTIVE",
        ).values_list(
            "phd_student_id",
            flat=True,
        )
    )

    managed_student_ids = list(set(phd_student_ids + advisee_ids))

    total_committees = committee_list.count()

    total_advisees = PhDStudent.objects.filter(
        advisor=faculty,
        current_status="ACTIVE",
    ).count()

    active_students = PhDStudent.objects.filter(
        pk__in=managed_student_ids,
        current_status="ACTIVE",
    ).count()

    completed_students = PhDStudent.objects.filter(
        pk__in=managed_student_ids,
        current_status="COMPLETED",
    ).count()

    on_hold_students = PhDStudent.objects.filter(
        pk__in=managed_student_ids,
        current_status="ON_HOLD",
    ).count()

    withdrawn_students = PhDStudent.objects.filter(
        pk__in=managed_student_ids,
        current_status="WITHDRAWN",
    ).count()

    approved_committees = committee_list.filter(
        approval_status="APPROVED",
    ).count()

    pending_committees = committee_list.filter(
        approval_status="PENDING",
    ).count()

    rejected_committees = committee_list.filter(
        approval_status="REJECTED",
    ).count()

    completed_committees = approved_committees

    chair_committees = committee_list.filter(
        chair_faculty=faculty,
    ).count()

    committee_member_committees = (
        committee_list.filter(
            committee_members__faculty=faculty,
        )
        .distinct()
        .count()
    )

    if total_committees:
        committee_progress = round((completed_committees / total_committees) * 100)

        approved_percentage = round((approved_committees / total_committees) * 100)

        pending_percentage = round((pending_committees / total_committees) * 100)

        rejected_percentage = round((rejected_committees / total_committees) * 100)
    else:
        committee_progress = 0
        approved_percentage = 0
        pending_percentage = 0
        rejected_percentage = 0

    managed_students = PhDStudent.objects.filter(
        pk__in=managed_student_ids,
    ).select_related(
        "student",
        "phd_program",
        "advisor",
    )

    faculty_courseworks = FacultyCoursework.objects.filter(
        phd_student_id__in=managed_student_ids,
    ).select_related(
        "phd_student",
        "phd_student__student",
        "phd_student__phd_program",
        "coursework",
        "program",
    )

    total_courseworks = faculty_courseworks.count()

    completed_courseworks = faculty_courseworks.filter(
        status="COMPLETED",
    ).count()

    in_progress_courseworks = faculty_courseworks.filter(
        status="IN_PROGRESS",
    ).count()

    failed_courseworks = faculty_courseworks.filter(
        status="FAILED",
    ).count()

    not_started_courseworks = faculty_courseworks.filter(
        status="NOT_STARTED",
    ).count()

    coursework_progress_values = list(
        faculty_courseworks.values_list(
            "progress_percentage",
            flat=True,
        )
    )

    coursework_progress_values = [
        float(value or 0) for value in coursework_progress_values
    ]

    if coursework_progress_values:
        coursework_completion = round(
            sum(coursework_progress_values) / len(coursework_progress_values)
        )
    else:
        coursework_completion = 0

    coursework_completion_percentage = coursework_completion

    coursework_submissions = CourseworkSubmission.objects.filter(
        coursework__phd_student_id__in=managed_student_ids,
    ).select_related(
        "coursework",
        "coursework__phd_student",
        "coursework__phd_student__student",
        "coursework__coursework",
    )

    total_submissions = coursework_submissions.count()

    pending_coursework_reviews = coursework_submissions.filter(
        status__in=[
            "SUBMITTED",
            "UNDER_REVIEW",
        ],
    ).count()

    approved_coursework_submissions = coursework_submissions.filter(
        status="APPROVED",
    ).count()

    rejected_coursework_submissions = coursework_submissions.filter(
        status="REJECTED",
    ).count()

    coursework_evaluations = CourseworkEvaluation.objects.filter(
        submission__coursework__phd_student_id__in=managed_student_ids,
    ).select_related(
        "submission",
        "submission__coursework",
        "submission__coursework__coursework",
        "evaluated_by",
    )

    total_coursework_evaluations = coursework_evaluations.count()

    preliminary_examinations = (
        PreliminaryExamination.objects.filter(
            phd_student_id__in=managed_student_ids,
        )
        .select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__phd_program",
        )
        .order_by(
            "-exam_date",
            "-start_time",
        )
    )

    total_examinations = preliminary_examinations.count()

    scheduled_examinations = preliminary_examinations.filter(
        status="SCHEDULED",
    ).count()

    completed_examinations = preliminary_examinations.filter(
        status="COMPLETED",
    ).count()

    cancelled_examinations = preliminary_examinations.filter(
        status="CANCELLED",
    ).count()

    passed_examinations = preliminary_examinations.filter(
        result="PASS",
    ).count()

    failed_examinations = preliminary_examinations.filter(
        result="FAIL",
    ).count()

    pending_exam_results = preliminary_examinations.filter(
        result="PENDING",
    ).count()

    if total_examinations:
        qualifying_progress = round((completed_examinations / total_examinations) * 100)
    else:
        qualifying_progress = 0

    preliminary_evaluations = PreliminaryExamEvaluation.objects.filter(
        examination__phd_student_id__in=managed_student_ids,
    ).select_related(
        "examination",
        "examination__phd_student",
        "faculty",
    )

    submitted_preliminary_evaluations = preliminary_evaluations.filter(
        is_submitted=True,
    ).count()

    pending_preliminary_evaluations = (
        preliminary_examinations.filter(
            status="SCHEDULED",
            is_published=True,
            result="PENDING",
        )
        .exclude(
            evaluations__faculty=faculty,
        )
        .count()
    )

    dissertation_proposals = (
        DissertationProposal.objects.filter(
            phd_student_id__in=managed_student_ids,
        )
        .select_related(
            "phd_student",
            "phd_student__student",
            "approved_by",
        )
        .order_by(
            "-submission_date",
        )
    )

    total_proposals = dissertation_proposals.count()

    approved_proposals = dissertation_proposals.filter(
        result="APPROVED",
    ).count()

    pending_proposals = dissertation_proposals.filter(
        result="PENDING",
    ).count()

    rejected_proposals = dissertation_proposals.filter(
        result="REJECTED",
    ).count()

    if total_proposals:
        proposal_progress = round((approved_proposals / total_proposals) * 100)
    else:
        proposal_progress = 0

    doctoral_candidacies = (
        DoctoralCandidacy.objects.filter(
            phd_student_id__in=managed_student_ids,
        )
        .select_related(
            "phd_student",
            "phd_student__student",
        )
        .order_by(
            "-candidacy_date",
        )
    )

    total_candidacies = doctoral_candidacies.count()

    approved_candidacies = doctoral_candidacies.filter(
        candidacy_status="APPROVED",
    ).count()

    pending_candidacies = doctoral_candidacies.filter(
        candidacy_status="PENDING",
    ).count()

    rejected_candidacies = doctoral_candidacies.filter(
        candidacy_status="REJECTED",
    ).count()

    if total_candidacies:
        candidacy_progress = round((approved_candidacies / total_candidacies) * 100)
    else:
        candidacy_progress = 0

    milestones = PhDMilestone.objects.filter(
        phd_student_id__in=managed_student_ids,
    )

    total_milestones = milestones.count()

    completed_milestones = milestones.filter(
        status="COMPLETED",
    ).count()

    in_progress_milestones = milestones.filter(
        status="IN_PROGRESS",
    ).count()

    pending_milestones = milestones.filter(
        status="PENDING",
    ).count()

    if total_milestones:
        research_progress = round((completed_milestones / total_milestones) * 100)
    else:
        research_progress = 0

    annual_reviews = AnnualProgressReview.objects.filter(
        phd_student_id__in=managed_student_ids,
    )

    total_annual_reviews = annual_reviews.count()

    research_score_values = list(
        annual_reviews.values_list(
            "progress_score",
            flat=True,
        )
    )

    research_score_values = [float(value or 0) for value in research_score_values]

    if research_score_values:
        research_score = round(sum(research_score_values) / len(research_score_values))
    else:
        research_score = 0

    research_publications = ResearchPublication.objects.filter(
        phd_student_id__in=managed_student_ids,
    )

    publications_count = research_publications.count()

    indexed_publications = research_publications.filter(
        indexed_status="INDEXED",
    ).count()

    publications_under_review = research_publications.filter(
        indexed_status="UNDER_REVIEW",
    ).count()

    non_indexed_publications = research_publications.filter(
        indexed_status="NOT_INDEXED",
    ).count()

    if publications_count:
        publications_progress = round((indexed_publications / publications_count) * 100)
    else:
        publications_progress = 0

    dissertations = (
        Dissertation.objects.filter(
            phd_student_id__in=managed_student_ids,
        )
        .select_related(
            "phd_student",
            "phd_student__student",
        )
        .order_by(
            "-submission_date",
        )
    )

    total_dissertations = dissertations.count()

    submitted_dissertations = dissertations.filter(
        status="SUBMITTED",
    ).count()

    dissertations_under_review = dissertations.filter(
        status="UNDER_REVIEW",
    ).count()

    approved_dissertations = dissertations.filter(
        status="APPROVED",
    ).count()

    rejected_dissertations = dissertations.filter(
        status="REJECTED",
    ).count()

    draft_dissertations = dissertations.filter(
        status="DRAFT",
    ).count()

    dissertation_status_weights = {
        "DRAFT": 20,
        "SUBMITTED": 50,
        "UNDER_REVIEW": 75,
        "APPROVED": 100,
        "REJECTED": 0,
    }

    dissertation_progress_values = [
        dissertation_status_weights.get(
            status,
            0,
        )
        for status in dissertations.values_list(
            "status",
            flat=True,
        )
    ]

    if dissertation_progress_values:
        dissertation_progress = round(
            sum(dissertation_progress_values) / len(dissertation_progress_values)
        )
    else:
        dissertation_progress = 0

    dissertation_evaluations = DissertationEvaluation.objects.filter(
        dissertation__phd_student_id__in=managed_student_ids,
    ).select_related(
        "dissertation",
        "committee_member",
        "committee_member__faculty",
    )

    total_dissertation_evaluations = dissertation_evaluations.count()

    pending_dissertation_evaluations = dissertation_evaluations.filter(
        is_submitted=False,
    ).count()

    submitted_dissertation_evaluations = dissertation_evaluations.filter(
        is_submitted=True,
    ).count()

    dissertation_approvals = DissertationApproval.objects.filter(
        dissertation__phd_student_id__in=managed_student_ids,
    ).select_related(
        "dissertation",
        "chair_faculty",
    )

    total_dissertation_approvals = dissertation_approvals.count()

    pending_dissertation_approvals = dissertation_approvals.filter(
        decision="PENDING",
    ).count()

    approved_dissertation_approvals = dissertation_approvals.filter(
        decision="APPROVED",
    ).count()

    revision_dissertation_approvals = dissertation_approvals.filter(
        decision__in=[
            "MINOR_REVISION",
            "MAJOR_REVISION",
        ],
    ).count()

    rejected_dissertation_approvals = dissertation_approvals.filter(
        decision="REJECTED",
    ).count()

    dissertation_defenses = (
        DissertationDefense.objects.filter(
            phd_student_id__in=managed_student_ids,
        )
        .select_related(
            "phd_student",
            "phd_student__student",
        )
        .order_by(
            "-defense_date",
        )
    )

    total_defenses = dissertation_defenses.count()

    completed_defenses = dissertation_defenses.filter(
        result="PASS",
    ).count()

    pending_defenses = dissertation_defenses.filter(
        result="PENDING",
    ).count()

    failed_defenses = dissertation_defenses.filter(
        result="FAIL",
    ).count()

    if total_defenses:
        defense_progress = round((completed_defenses / total_defenses) * 100)
    else:
        defense_progress = 0

    graduations = (
        Graduation.objects.filter(
            phd_student_id__in=managed_student_ids,
        )
        .select_related(
            "phd_student",
            "phd_student__student",
        )
        .order_by(
            "-graduation_date",
        )
    )

    total_graduations = graduations.count()

    dissertation_accepted_graduations = graduations.filter(
        dissertation_accepted=True,
    ).count()

    if total_graduations:
        graduation_progress = round(
            (dissertation_accepted_graduations / total_graduations) * 100
        )
    else:
        graduation_progress = 0

    synopsis_progress = proposal_progress

    stage_progress_values = [
        committee_progress,
        coursework_completion,
        qualifying_progress,
        proposal_progress,
        research_progress,
        dissertation_progress,
    ]

    overall_progress = round(sum(stage_progress_values) / len(stage_progress_values))

    if chair_committees and total_advisees:
        dashboard_role = "Chair Faculty & Advisor"
        role_code = "chair_advisor"

    elif chair_committees:
        dashboard_role = "Chair Faculty"
        role_code = "chair"

    elif total_advisees:
        dashboard_role = "Advisor"
        role_code = "advisor"

    else:
        dashboard_role = "Committee Member"
        role_code = "committee_member"

    if pending_committees > 3:
        workload_status = "High"
        workload_level = "high"

    elif pending_committees > 0:
        workload_status = "Moderate"
        workload_level = "moderate"

    else:
        workload_status = "Low"
        workload_level = "low"

    pending_actions = []

    if pending_committees:
        pending_actions.append(
            (
                pending_committees,
                "doctoral committee approval",
                "bi-diagram-3",
            )
        )

    if pending_coursework_reviews:
        pending_actions.append(
            (
                pending_coursework_reviews,
                "coursework review",
                "bi-journal-check",
            )
        )

    if pending_preliminary_evaluations:
        pending_actions.append(
            (
                pending_preliminary_evaluations,
                "preliminary examination evaluation",
                "bi-clipboard-check",
            )
        )

    if pending_proposals:
        pending_actions.append(
            (
                pending_proposals,
                "dissertation proposal",
                "bi-file-earmark-text",
            )
        )

    if pending_candidacies:
        pending_actions.append(
            (
                pending_candidacies,
                "doctoral candidacy",
                "bi-person-check",
            )
        )

    if pending_dissertation_evaluations:
        pending_actions.append(
            (
                pending_dissertation_evaluations,
                "dissertation evaluation",
                "bi-file-earmark-check",
            )
        )

    if pending_dissertation_approvals:
        pending_actions.append(
            (
                pending_dissertation_approvals,
                "dissertation approval",
                "bi-patch-check",
            )
        )

    if pending_defenses:
        pending_actions.append(
            (
                pending_defenses,
                "dissertation defense",
                "bi-mortarboard",
            )
        )

    if pending_actions:
        pending_actions.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        next_action_count = pending_actions[0][0]
        next_action_label = pending_actions[0][1]
        next_action_icon = pending_actions[0][2]

        next_action = (
            f"Review {next_action_count} pending "
            f"{next_action_label}"
            f"{'s' if next_action_count != 1 else ''}"
        )

    elif total_advisees:
        next_action = (
            f"Continue monitoring {total_advisees} active "
            f"PhD advisee"
            f"{'s' if total_advisees != 1 else ''}"
        )

        next_action_icon = "bi-eye"

    elif total_committees:
        next_action = "Monitor current doctoral committee activities"

        next_action_icon = "bi-activity"

    else:
        next_action = "No immediate action required"
        next_action_icon = "bi-check-circle"

    recent_activities = []

    for committee in committee_list[:10]:
        student_name = str(committee.phd_student)

        status_map = {
            "APPROVED": (
                "check-circle-fill",
                "approved",
                "Doctoral Committee Approved",
            ),
            "PENDING": (
                "clock-fill",
                "pending",
                "Doctoral Committee Awaiting Approval",
            ),
            "REJECTED": (
                "x-circle-fill",
                "rejected",
                "Doctoral Committee Rejected",
            ),
        }

        (
            icon,
            activity_status,
            title,
        ) = status_map.get(
            committee.approval_status,
            (
                "activity",
                "pending",
                "Doctoral Committee Updated",
            ),
        )

        activity_date = safe_date(committee.formation_date)

        recent_activities.append(
            {
                "icon": icon,
                "title": title,
                "description": (f"Committee activity for " f"{student_name}."),
                "status": activity_status,
                "date": activity_date,
                "sort_date": activity_date,
            }
        )

    for coursework in faculty_courseworks.order_by("-updated_at")[:10]:
        activity_date = safe_date(coursework.updated_at)

        recent_activities.append(
            {
                "icon": "journal-text",
                "title": "Coursework Updated",
                "description": (
                    f"{coursework.coursework.coursework_name} "
                    f"for {coursework.phd_student} "
                    f"is "
                    f"{coursework.status.replace('_', ' ').title()}."
                ),
                "status": (
                    "completed" if coursework.status == "COMPLETED" else "pending"
                ),
                "date": activity_date,
                "sort_date": coursework.updated_at,
            }
        )

    for submission in coursework_submissions.order_by("-submitted_at")[:10]:
        submitted_at = submission.submitted_at

        activity_date = safe_date(submitted_at)

        recent_activities.append(
            {
                "icon": "file-earmark-arrow-up",
                "title": "Coursework Submission",
                "description": (
                    f"{submission.coursework.coursework.coursework_name} "
                    f"submitted by "
                    f"{submission.coursework.phd_student}."
                ),
                "status": (
                    submission.status.lower() if submission.status else "pending"
                ),
                "date": activity_date,
                "sort_date": submitted_at,
            }
        )

    for examination in preliminary_examinations[:10]:
        activity_date = safe_date(examination.exam_date)

        exam_result = examination.result.lower() if examination.result else "pending"

        recent_activities.append(
            {
                "icon": "mortarboard-fill",
                "title": (f"{examination.get_exam_type_display()} " f"Examination"),
                "description": (
                    f"Examination for "
                    f"{examination.phd_student} "
                    f"is currently "
                    f"{examination.status.replace('_', ' ').title()}."
                ),
                "status": exam_result,
                "date": activity_date,
                "sort_date": examination.exam_date,
            }
        )

    for proposal in dissertation_proposals[:10]:
        activity_date = safe_date(proposal.submission_date)

        proposal_result = proposal.result.title() if proposal.result else "Pending"

        recent_activities.append(
            {
                "icon": "file-earmark-text-fill",
                "title": "Dissertation Proposal",
                "description": (
                    f"{proposal.proposal_title} "
                    f"for {proposal.phd_student} "
                    f"is {proposal_result}."
                ),
                "status": (proposal.result.lower() if proposal.result else "pending"),
                "date": activity_date,
                "sort_date": proposal.submission_date,
            }
        )

    for dissertation in dissertations[:10]:
        activity_date = safe_date(
            dissertation.submission_date or dissertation.phd_student.admission_date
        )

        recent_activities.append(
            {
                "icon": "file-earmark-richtext-fill",
                "title": "Dissertation Updated",
                "description": (
                    f"Dissertation for "
                    f"{dissertation.phd_student} "
                    f"is "
                    f"{dissertation.status.replace('_', ' ').title()}."
                ),
                "status": (
                    dissertation.status.lower() if dissertation.status else "pending"
                ),
                "date": activity_date,
                "sort_date": activity_date,
            }
        )

    for publication in research_publications[:10]:
        activity_date = safe_date(publication.publication_date)

        publication_status = (
            publication.indexed_status.lower()
            if publication.indexed_status
            else "pending"
        )

        recent_activities.append(
            {
                "icon": "journal-bookmark-fill",
                "title": "Research Publication",
                "description": (
                    f"{publication.title} "
                    f"for {publication.phd_student} "
                    f"is "
                    f"{publication.indexed_status.replace('_', ' ').title()}."
                    if publication.indexed_status
                    else (
                        f"{publication.title} "
                        f"for {publication.phd_student} "
                        f"is pending."
                    )
                ),
                "status": publication_status,
                "date": activity_date,
                "sort_date": publication.publication_date,
            }
        )

    recent_activities.sort(
        key=lambda item: to_datetime(item.get("sort_date")),
        reverse=True,
    )

    recent_activities = recent_activities[:8]

    upcoming_schedule = []

    upcoming_examinations = preliminary_examinations.filter(
        exam_date__gte=today,
        status="SCHEDULED",
    ).order_by("exam_date", "start_time",)[:5]

    for examination in upcoming_examinations:
        if not examination.exam_date:
            continue

        time_value = (
            examination.start_time.strftime("%I:%M %p")
            if examination.start_time
            else "All day"
        )

        upcoming_schedule.append(
            {
                "day": examination.exam_date.strftime("%d"),
                "month": examination.exam_date.strftime("%b"),
                "title": (f"{examination.get_exam_type_display()} " f"Examination"),
                "description": str(examination.phd_student),
                "time": time_value,
                "date": examination.exam_date,
                "sort_datetime": examination.exam_date,
            }
        )

    upcoming_proposals = dissertation_proposals.filter(
        hearing_date__gte=today,
        hearing_date__isnull=False,
    ).order_by("hearing_date",)[:5]

    for proposal in upcoming_proposals:
        if not proposal.hearing_date:
            continue

        upcoming_schedule.append(
            {
                "day": proposal.hearing_date.strftime("%d"),
                "month": proposal.hearing_date.strftime("%b"),
                "title": "Dissertation Proposal Hearing",
                "description": str(proposal.phd_student),
                "time": "Scheduled",
                "date": proposal.hearing_date,
                "sort_datetime": proposal.hearing_date,
            }
        )

    upcoming_courseworks = faculty_courseworks.filter(
        expected_completion_date__gte=today,
        status__in=[
            "NOT_STARTED",
            "IN_PROGRESS",
        ],
    ).order_by("expected_completion_date",)[:5]

    for coursework in upcoming_courseworks:
        if not coursework.expected_completion_date:
            continue

        upcoming_schedule.append(
            {
                "day": coursework.expected_completion_date.strftime("%d"),
                "month": coursework.expected_completion_date.strftime("%b"),
                "title": "Coursework Completion",
                "description": (
                    f"{coursework.coursework.coursework_name} "
                    f"· "
                    f"{coursework.phd_student}"
                ),
                "time": "Due",
                "date": coursework.expected_completion_date,
                "sort_datetime": coursework.expected_completion_date,
            }
        )

    upcoming_defenses = dissertation_defenses.filter(
        defense_date__gte=today,
        result="PENDING",
    ).order_by("defense_date",)[:5]

    for defense in upcoming_defenses:
        if not defense.defense_date:
            continue

        upcoming_schedule.append(
            {
                "day": defense.defense_date.strftime("%d"),
                "month": defense.defense_date.strftime("%b"),
                "title": "Dissertation Defense",
                "description": str(defense.phd_student),
                "time": "Scheduled",
                "date": defense.defense_date,
                "sort_datetime": defense.defense_date,
            }
        )

    upcoming_students = managed_students.filter(
        expected_graduation_date__gte=today,
        expected_graduation_date__isnull=False,
    ).order_by("expected_graduation_date",)[:5]

    for student in upcoming_students:
        if not student.expected_graduation_date:
            continue

        upcoming_schedule.append(
            {
                "day": student.expected_graduation_date.strftime("%d"),
                "month": student.expected_graduation_date.strftime("%b"),
                "title": "Expected Graduation",
                "description": str(student),
                "time": "Expected",
                "date": student.expected_graduation_date,
                "sort_datetime": student.expected_graduation_date,
            }
        )

    upcoming_schedule.sort(key=lambda item: to_datetime(item.get("sort_datetime")))

    upcoming_schedule = upcoming_schedule[:8]

    upcoming_activities = len(upcoming_schedule)

    context = {
        "uuid": faculty.user.uuid,
        "faculty": faculty,
        "committee_list": committee_list,
        "dashboard_role": dashboard_role,
        "role_code": role_code,
        "total_committees": total_committees,
        "total_advisees": total_advisees,
        "total_active_students": active_students,
        "completed_students": completed_students,
        "on_hold_students": on_hold_students,
        "withdrawn_students": withdrawn_students,
        "approved_committees": approved_committees,
        "pending_committees": pending_committees,
        "rejected_committees": rejected_committees,
        "completed_committees": completed_committees,
        "chair_committees": chair_committees,
        "committee_member_committees": (committee_member_committees),
        "committee_progress": committee_progress,
        "overall_progress": overall_progress,
        "approved_percentage": approved_percentage,
        "pending_percentage": pending_percentage,
        "rejected_percentage": rejected_percentage,
        "total_courseworks": total_courseworks,
        "completed_courseworks": completed_courseworks,
        "in_progress_courseworks": in_progress_courseworks,
        "failed_courseworks": failed_courseworks,
        "not_started_courseworks": not_started_courseworks,
        "coursework_completion": coursework_completion,
        "coursework_completion_percentage": (coursework_completion_percentage),
        "total_submissions": total_submissions,
        "pending_coursework_reviews": (pending_coursework_reviews),
        "approved_coursework_submissions": (approved_coursework_submissions),
        "rejected_coursework_submissions": (rejected_coursework_submissions),
        "total_coursework_evaluations": (total_coursework_evaluations),
        "total_examinations": total_examinations,
        "scheduled_examinations": (scheduled_examinations),
        "completed_examinations": (completed_examinations),
        "cancelled_examinations": (cancelled_examinations),
        "passed_examinations": passed_examinations,
        "failed_examinations": failed_examinations,
        "pending_exam_results": pending_exam_results,
        "qualifying_progress": qualifying_progress,
        "submitted_preliminary_evaluations": (submitted_preliminary_evaluations),
        "pending_preliminary_evaluations": (pending_preliminary_evaluations),
        "total_proposals": total_proposals,
        "approved_proposals": approved_proposals,
        "pending_proposals": pending_proposals,
        "rejected_proposals": rejected_proposals,
        "proposal_progress": proposal_progress,
        "synopsis_progress": synopsis_progress,
        "total_candidacies": total_candidacies,
        "approved_candidacies": approved_candidacies,
        "pending_candidacies": pending_candidacies,
        "rejected_candidacies": rejected_candidacies,
        "candidacy_progress": candidacy_progress,
        "total_milestones": total_milestones,
        "completed_milestones": completed_milestones,
        "in_progress_milestones": in_progress_milestones,
        "pending_milestones": pending_milestones,
        "research_progress": research_progress,
        "research_score": research_score,
        "total_annual_reviews": total_annual_reviews,
        "publications_count": publications_count,
        "indexed_publications": indexed_publications,
        "publications_under_review": (publications_under_review),
        "non_indexed_publications": (non_indexed_publications),
        "publications_progress": publications_progress,
        "total_dissertations": total_dissertations,
        "draft_dissertations": draft_dissertations,
        "submitted_dissertations": (submitted_dissertations),
        "dissertations_under_review": (dissertations_under_review),
        "approved_dissertations": (approved_dissertations),
        "rejected_dissertations": (rejected_dissertations),
        "dissertation_progress": dissertation_progress,
        "total_dissertation_evaluations": (total_dissertation_evaluations),
        "pending_dissertation_evaluations": (pending_dissertation_evaluations),
        "submitted_dissertation_evaluations": (submitted_dissertation_evaluations),
        "total_dissertation_approvals": (total_dissertation_approvals),
        "pending_dissertation_approvals": (pending_dissertation_approvals),
        "approved_dissertation_approvals": (approved_dissertation_approvals),
        "revision_dissertation_approvals": (revision_dissertation_approvals),
        "rejected_dissertation_approvals": (rejected_dissertation_approvals),
        "total_defenses": total_defenses,
        "completed_defenses": completed_defenses,
        "pending_defenses": pending_defenses,
        "failed_defenses": failed_defenses,
        "defense_progress": defense_progress,
        "total_graduations": total_graduations,
        "dissertation_accepted_graduations": (dissertation_accepted_graduations),
        "graduation_progress": graduation_progress,
        "workload_status": workload_status,
        "workload_level": workload_level,
        "next_action": next_action,
        "next_action_icon": next_action_icon,
        "upcoming_activities": upcoming_activities,
        "recent_activities": recent_activities,
        "upcoming_schedule": upcoming_schedule,
    }

    return render(
        request,
        "leo/PhD/phd_management.html",
        context,
    )


###############################################################
# DOCTORAL COMMITTEE MODULE MANAGEMENT IN FACULTY DASHBOARD
###############################################################


@login_required
def faculty_doctoral_committee(
    request,
    uuid,
):
    faculty = get_object_or_404(
        FacultyProfile,
        user__uuid=uuid,
    )

    committee_list = (
        DoctoralCommittee.objects.filter(
            Q(chair_faculty=faculty) | Q(committee_members__faculty=faculty),
        )
        .distinct()
        .select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "chair_faculty",
            "chair_faculty__user",
        )
        .prefetch_related(
            Prefetch(
                "committee_members",
                queryset=CommitteeMember.objects.select_related(
                    "faculty",
                    "faculty__user",
                    "department",
                ).order_by(
                    "role",
                ),
            ),
        )
        .order_by(
            "formation_date",
        )
    )

    search_query = request.GET.get(
        "search",
        "",
    ).strip()

    status_filter = request.GET.get(
        "status",
        "",
    ).strip()

    department_filter = request.GET.get(
        "department",
        "",
    ).strip()

    if search_query:
        committee_list = committee_list.filter(
            Q(phd_student__student__student_number__icontains=search_query)
            | Q(phd_student__student__user__first_name__icontains=search_query)
            | Q(phd_student__student__user__last_name__icontains=search_query)
        )

    if status_filter:
        committee_list = committee_list.filter(
            approval_status=status_filter,
        )

    if department_filter:
        committee_list = committee_list.filter(
            committee_members__department_id=department_filter,
        ).distinct()

    approved_committees = committee_list.filter(
        approval_status="APPROVED",
    ).count()

    pending_committees = committee_list.filter(
        approval_status="PENDING",
    ).count()

    rejected_committees = committee_list.filter(
        approval_status="REJECTED",
    ).count()

    total_members = 0

    for committee in committee_list:
        committee.member_form = CommitteeMemberForm(
            committee=committee,
        )

        committee.total_members = committee.committee_members.count() + 1

        total_members += committee.total_members

    context = {
        "faculty": faculty,
        "committee_list": committee_list,
        "total_committees": committee_list.count(),
        "total_members": total_members,
        "approved_committees": approved_committees,
        "pending_committees": pending_committees,
        "rejected_committees": rejected_committees,
        "search_query": search_query,
        "status_filter": status_filter,
        "department_filter": department_filter,
    }

    return render(
        request,
        "leo/PhD/doctoral_committee.html",
        context,
    )


def committee_member_create(
    request,
    uuid,
    committee_id,
):
    """
    Add a new member to a doctoral committee.

    Purpose:
        Allow chair faculty to add committee members.

    Parameters:
        request: HTTP request object
        uuid: UUID of the faculty member
        committee_id: ID of the committee

    Returns:
        Rendered template with member creation form

    Workflow:
        1. Get committee and faculty
        2. Verify chair faculty authorization
        3. Handle POST - create member
        4. Handle GET - display form
        5. Render template
    """
    committee = get_object_or_404(
        DoctoralCommittee,
        committee_id=committee_id,
    )

    faculty = get_object_or_404(
        FacultyProfile,
        user__uuid=uuid,
    )

    # Verify chair faculty authorization
    if committee.chair_faculty != faculty:
        return HttpResponse(
            "Unauthorized",
            status=403,
        )

    # Process POST request
    if request.method == "POST":
        form = CommitteeMemberForm(
            request.POST,
            committee=committee,
        )

        if form.is_valid():
            member = form.save(
                commit=False,
            )
            member.committee = committee
            member.save()

            messages.success(
                request,
                "Committee member added successfully.",
            )

            return redirect(
                "committee_detail",
                uuid=faculty.user.uuid,
                committee_id=committee.committee_id,
            )

        messages.error(
            request,
            "Please correct the errors below and try again.",
        )

    # Process GET request
    else:
        form = CommitteeMemberForm(
            committee=committee,
        )

    context = {
        "faculty": faculty,
        "committee": committee,
        "form": form,
    }

    return render(
        request,
        "leo/PhD/committee_member_create.html",
        context,
    )


def committee_member_update(
    request,
    uuid,
    committee_id,
    member_id,
):
    """
    Update an existing committee member.

    Purpose:
        Allow chair faculty to modify committee member details.

    Parameters:
        request: HTTP request object
        uuid: UUID of the faculty member
        committee_id: ID of the committee
        member_id: ID of the committee member

    Returns:
        Rendered template with member update form

    Workflow:
        1. Get committee, faculty, and member
        2. Verify chair faculty authorization
        3. Handle POST - update member
        4. Handle GET - display form
        5. Render template
    """
    committee = get_object_or_404(
        DoctoralCommittee,
        committee_id=committee_id,
    )

    faculty = get_object_or_404(
        FacultyProfile,
        user__uuid=uuid,
    )

    # Verify chair faculty authorization
    if committee.chair_faculty != faculty:
        return HttpResponse(
            "Unauthorized",
            status=403,
        )

    member = get_object_or_404(
        CommitteeMember,
        member_id=member_id,
        committee=committee,
    )

    # Process POST request
    if request.method == "POST":
        form = CommitteeMemberForm(
            request.POST,
            instance=member,
            committee=committee,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Committee member updated successfully.",
            )

            return redirect(
                "faculty_doctoral_committee",
                uuid=faculty.user.uuid,
            )

        messages.error(
            request,
            "Please correct the errors below and try again.",
        )

    # Process GET request
    else:
        form = CommitteeMemberForm(
            instance=member,
            committee=committee,
        )

    context = {
        "faculty": faculty,
        "committee": committee,
        "member": member,
        "form": form,
    }

    return render(
        request,
        "leo/PhD/committee_member_update.html",
        context,
    )


def committee_member_delete(
    request,
    uuid,
    committee_id,
    member_id,
):
    """
    Delete a committee member.

    Purpose:
        Allow chair faculty to remove committee members.

    Parameters:
        request: HTTP request object
        uuid: UUID of the faculty member
        committee_id: ID of the committee
        member_id: ID of the committee member

    Returns:
        Redirect to committee detail page

    Workflow:
        1. Get committee, faculty, and member
        2. Verify chair faculty authorization
        3. Validate request method
        4. Delete member
        5. Redirect with success message
    """
    committee = get_object_or_404(
        DoctoralCommittee,
        committee_id=committee_id,
    )

    faculty = get_object_or_404(
        FacultyProfile,
        user__uuid=uuid,
    )

    # Verify chair faculty authorization
    if committee.chair_faculty != faculty:
        return HttpResponse(
            "Unauthorized",
            status=403,
        )

    member = get_object_or_404(
        CommitteeMember,
        committee=committee,
        member_id=member_id,
    )

    # Validate request method
    if request.method != "POST":
        messages.warning(
            request,
            "Invalid request.",
        )
        return redirect(
            "faculty_doctoral_committee",
            uuid=faculty.user.uuid,
        )

    # Delete member
    member.delete()

    messages.success(
        request,
        "Committee member deleted successfully.",
    )

    return redirect(
        "committee_detail",
        uuid=faculty.user.uuid,
        committee_id=committee.committee_id,
    )


@login_required
def committee_detail(
    request,
    uuid,
    committee_id,
):
    faculty = get_object_or_404(
        FacultyProfile,
        user__uuid=uuid,
    )

    committee = get_object_or_404(
        DoctoralCommittee.objects.select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "phd_student__phd_program",
            "phd_student__phd_program__department",
            "chair_faculty",
            "chair_faculty__user",
        ).prefetch_related(
            Prefetch(
                "committee_members",
                queryset=CommitteeMember.objects.select_related(
                    "faculty",
                    "faculty__user",
                    "department",
                ).order_by(
                    "role",
                ),
            ),
        ),
        committee_id=committee_id,
    )

    is_chair = committee.chair_faculty == faculty

    is_committee_member = committee.committee_members.filter(
        faculty=faculty,
    ).exists()

    if not (is_chair or is_committee_member):
        return HttpResponse(
            "Unauthorized",
            status=403,
        )

    committee_members = committee.committee_members.exclude(
        faculty=committee.chair_faculty,
    )

    internal_members = committee_members.filter(
        role="INTERNAL_MEMBER",
    ).count()

    external_members = committee_members.filter(
        role="EXTERNAL_MEMBER",
    ).count()

    chair_department = Department.objects.filter(
        department_id=committee.chair_faculty.department_id,
    ).first()

    total_members = committee_members.count() + 1

    context = {
        "faculty": faculty,
        "committee": committee,
        "committee_members": committee_members,
        "internal_members": internal_members,
        "external_members": external_members,
        "total_members": total_members,
        "chair_department": chair_department,
        "can_manage_committee": is_chair,
    }

    return render(
        request,
        "leo/PhD/committee_detail.html",
        context,
    )


###############################################################
# COURSEWORK MODULE
###############################################################
def _create_coursework_notification(
    user,
    title,
    message,
    notification_type="INFO",
    link="",
):
    if not user:
        return

    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link or "",
        is_read=False,
    )

    payload = {
        "id": notification.pk,
        "title": notification.title,
        "message": notification.message,
        "type": notification.notification_type,
        "link": notification.link,
        "is_read": notification.is_read,
        "created_at": notification.created_at.isoformat(),
    }

    transaction.on_commit(
        lambda user_id=user.pk, payload=payload: send_notification(
            user_id,
            payload,
            event="coursework_update",
        )
    )


def faculty_coursework_list(request, uuid):

    faculty = get_object_or_404(
        FacultyProfile,
        user__uuid=uuid,
    )

    search = request.GET.get(
        "q",
        "",
    ).strip()

    program_id = request.GET.get(
        "program",
        "",
    ).strip()

    status = request.GET.get(
        "status",
        "",
    ).strip()

    all_assignments = (
        FacultyCoursework.objects.filter(
            phd_student__advisor=faculty,
        )
        .select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__phd_program",
            "phd_student__phd_program__department",
            "coursework",
            "program",
        )
        .prefetch_related(
            "submission__evaluation",
        )
        .order_by(
            "-faculty_coursework_id",
        )
    )

    assignments = all_assignments

    if search:
        assignments = assignments.filter(
            Q(
                phd_student__student__user__first_name__icontains=search,
            )
            | Q(
                phd_student__student__user__last_name__icontains=search,
            )
            | Q(
                phd_student__student__student_number__icontains=search,
            )
            | Q(
                coursework__coursework_name__icontains=search,
            )
            | Q(
                program__program_name__icontains=search,
            )
            | Q(
                academic_year__icontains=search,
            )
            | Q(
                status__icontains=search,
            )
            | Q(
                grade__icontains=search,
            )
        )

    if program_id:
        assignments = assignments.filter(
            program_id=program_id,
        )

    if status:
        assignments = assignments.filter(
            status=status,
        )

    all_assignments = (
        FacultyCoursework.objects.filter(
            phd_student__advisor=faculty,
        )
        .select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__phd_program",
            "phd_student__phd_program__department",
            "coursework",
            "program",
        )
        .prefetch_related(
            "submission__evaluation",
        )
        .order_by(
            "-faculty_coursework_id",
        )
    )

    assignments = all_assignments

    if search:
        assignments = assignments.filter(
            Q(
                phd_student__student__user__first_name__icontains=search,
            )
            | Q(
                phd_student__student__user__last_name__icontains=search,
            )
            | Q(
                phd_student__student__student_number__icontains=search,
            )
            | Q(
                coursework__coursework_name__icontains=search,
            )
            | Q(
                program__program_name__icontains=search,
            )
            | Q(
                academic_year__icontains=search,
            )
            | Q(
                status__icontains=search,
            )
            | Q(
                grade__icontains=search,
            )
        )

    if program_id:
        assignments = assignments.filter(
            program_id=program_id,
        )

    if status:
        assignments = assignments.filter(
            status=status,
        )

    total_courseworks = all_assignments.count()

    completed_courseworks = all_assignments.filter(
        status="COMPLETED",
    ).count()

    in_progress_courseworks = all_assignments.filter(
        status="IN_PROGRESS",
    ).count()

    pending_courseworks = all_assignments.filter(
        status="NOT_STARTED",
    ).count()

    failed_courseworks = all_assignments.filter(
        status="FAILED",
    ).count()

    active_courses = all_assignments.exclude(
        status__in=[
            "COMPLETED",
            "FAILED",
        ],
    ).count()

    advisees_queryset = (
        PhDStudent.objects.filter(
            advisor=faculty,
            current_status="ACTIVE",
        )
        .select_related(
            "student",
            "student__user",
            "phd_program",
            "phd_program__department",
        )
        .order_by(
            "student__user__first_name",
            "student__user__last_name",
        )
    )

    if search:
        advisees_queryset = advisees_queryset.filter(
            Q(
                student__user__first_name__icontains=search,
            )
            | Q(
                student__user__last_name__icontains=search,
            )
            | Q(
                student__student_number__icontains=search,
            )
            | Q(
                phd_program__program_name__icontains=search,
            )
        )

    if program_id:
        advisees_queryset = advisees_queryset.filter(
            phd_program_id=program_id,
        )

    advisee_data = []

    for advisee in advisees_queryset:

        all_advisee_courseworks = list(
            FacultyCoursework.objects.filter(
                phd_student=advisee,
            )
            .select_related(
                "coursework",
                "program",
            )
            .prefetch_related(
                "submission__evaluation",
            )
            .order_by(
                "-faculty_coursework_id",
            )
        )

        display_courseworks = all_advisee_courseworks

        if status:
            display_courseworks = [
                coursework
                for coursework in all_advisee_courseworks
                if coursework.status == status
            ]

        coursework_count = len(
            display_courseworks,
        )

        assigned_credits = sum(
            coursework.coursework.credits
            for coursework in all_advisee_courseworks
            if coursework.coursework
        )

        completed_credits = sum(
            coursework.coursework.credits
            for coursework in all_advisee_courseworks
            if (coursework.coursework and coursework.status == "COMPLETED")
        )

        required_credits = advisee.phd_program.total_credits_required or 0

        remaining_credits = max(
            required_credits - completed_credits,
            0,
        )

        if required_credits > 0:
            progress_percentage = round((completed_credits / required_credits) * 100)
        else:
            progress_percentage = 0

        progress_percentage = min(
            max(
                progress_percentage,
                0,
            ),
            100,
        )

        progress_credits = completed_credits

        advisee_data.append(
            {
                "student": advisee.student,
                "program": advisee.phd_program,
                "courseworks": display_courseworks,
                "coursework_count": coursework_count,
                "assigned_credits": assigned_credits,
                "completed_credits": completed_credits,
                "required_credits": required_credits,
                "remaining_credits": remaining_credits,
                "progress_percentage": progress_percentage,
                "progress_credits": progress_credits,
            }
        )

    paginator = Paginator(
        advisee_data,
        10,
    )

    page_obj = paginator.get_page(
        request.GET.get("page"),
    )

    recent_courseworks = all_assignments[:5]

    advisees = len(
        advisee_data,
    )

    total_assigned_credits = (
        all_assignments.aggregate(
            total=Sum(
                "coursework__credits",
            ),
        )["total"]
        or 0
    )

    completed_credits = (
        all_assignments.filter(
            status="COMPLETED",
        ).aggregate(
            total=Sum(
                "coursework__credits",
            ),
        )["total"]
        or 0
    )

    avg_progress = round(
        all_assignments.aggregate(
            avg=Avg(
                "progress_percentage",
            ),
        )["avg"]
        or 0
    )

    completion_rate = (
        round((completed_courseworks / total_courseworks) * 100)
        if total_courseworks
        else 0
    )

    programs = (
        PhDStudent.objects.filter(
            advisor=faculty,
            current_status="ACTIVE",
        )
        .values(
            "phd_program_id",
            "phd_program__program_name",
        )
        .distinct()
        .order_by(
            "phd_program__program_name",
        )
    )

    today = date.today()

    if today.month >= 7:
        academic_year = f"{today.year}-" f"{str(today.year + 1)[2:]}"
    else:
        academic_year = f"{today.year - 1}-" f"{str(today.year)[2:]}"

    context = {
        "faculty": faculty,
        "coursework_list": assignments,
        "advisee_coursework": page_obj.object_list,
        "page_obj": page_obj,
        "is_paginated": page_obj.has_other_pages(),
        "recent_courseworks": recent_courseworks,
        "search": search,
        "program_id": program_id,
        "status": status,
        "programs": programs,
        "total_courseworks": total_courseworks,
        "completed_courseworks": completed_courseworks,
        "in_progress_courseworks": in_progress_courseworks,
        "pending_courseworks": pending_courseworks,
        "failed_courseworks": failed_courseworks,
        "active_courses": active_courses,
        "advisees": advisees,
        "total_assigned_credits": total_assigned_credits,
        "completed_credits": completed_credits,
        "avg_progress": avg_progress,
        "completion_rate": completion_rate,
        "academic_year": academic_year,
    }

    return render(
        request,
        "leo/Coursework/coursework_list.html",
        context,
    )


@login_required
def faculty_coursework_evaluate(
    request,
    uuid,
    coursework_id,
):
    faculty = get_object_or_404(
        FacultyProfile,
        user__uuid=uuid,
    )

    coursework = get_object_or_404(
        FacultyCoursework.objects.select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__phd_program",
            "phd_student__phd_program__department",
            "coursework",
            "program",
        ),
        faculty_coursework_id=coursework_id,
        phd_student__advisor=faculty,
    )

    submission = get_object_or_404(
        CourseworkSubmission.objects.select_related(
            "coursework",
        ),
        coursework=coursework,
    )

    existing_evaluation = getattr(
        submission,
        "evaluation",
        None,
    )

    if request.method == "POST":
        if existing_evaluation:
            messages.info(
                request,
                "This coursework has already been evaluated.",
            )

            return redirect(
                "faculty_coursework_evaluate",
                uuid=faculty.user.uuid,
                coursework_id=coursework.faculty_coursework_id,
            )

        form = CourseworkEvaluationForm(
            request.POST,
            faculty=faculty,
            submission=submission,
        )

        if form.is_valid():
            with transaction.atomic():
                evaluation = form.save(
                    commit=True,
                )

                student_user = None

                if (
                    coursework.phd_student.student_id
                    and coursework.phd_student.student.user_id
                ):
                    student_user = coursework.phd_student.student.user

                coursework_name = (
                    coursework.coursework.coursework_name
                    if coursework.coursework
                    else "Coursework"
                )

                _create_coursework_notification(
                    user=student_user,
                    title="Coursework Evaluation Completed",
                    message=(
                        f"Your coursework "
                        f"'{coursework_name}' "
                        f"has been evaluated."
                    ),
                    notification_type="SUCCESS",
                )

            messages.success(
                request,
                "Coursework evaluation submitted successfully.",
            )

            return redirect(
                "faculty_coursework_list",
                uuid=faculty.user.uuid,
            )

        messages.error(
            request,
            "Please correct the errors below and try again.",
        )

    else:
        form = CourseworkEvaluationForm(
            faculty=faculty,
            submission=submission,
        )

    context = {
        "faculty": faculty,
        "coursework": coursework,
        "submission": submission,
        "evaluation": existing_evaluation,
        "form": form,
    }

    return render(
        request,
        "leo/Coursework/coursework_evaluate.html",
        context,
    )


@login_required
def faculty_coursework_assign_data(
    request,
    uuid,
):
    faculty = get_object_or_404(
        FacultyProfile,
        user__uuid=uuid,
    )

    student_id = request.GET.get(
        "student",
    )

    if not student_id:
        return JsonResponse(
            {
                "success": False,
                "message": "Student is required.",
            },
            status=400,
        )

    student = get_object_or_404(
        PhDStudent.objects.select_related(
            "phd_program",
            "doctoral_committee",
        ),
        pk=student_id,
        advisor=faculty,
        current_status="ACTIVE",
    )

    committee = getattr(
        student,
        "doctoral_committee",
        None,
    )

    if committee is None:
        return JsonResponse(
            {
                "success": False,
                "message": (
                    "Coursework cannot be assigned because "
                    "the doctoral committee has not been created."
                ),
            },
            status=403,
        )

    if committee.approval_status != "APPROVED":
        return JsonResponse(
            {
                "success": False,
                "message": (
                    "Coursework cannot be assigned because "
                    "the doctoral committee is not approved."
                ),
            },
            status=403,
        )

    program = student.phd_program

    assigned_coursework_ids = FacultyCoursework.objects.filter(
        phd_student=student,
    ).values_list(
        "coursework_id",
        flat=True,
    )

    available_courseworks = (
        Coursework.objects.filter(
            program=program,
            is_active=True,
        )
        .exclude(
            coursework_id__in=assigned_coursework_ids,
        )
        .order_by(
            "coursework_name",
        )
    )

    assigned_credits = (
        FacultyCoursework.objects.filter(
            phd_student=student,
        ).aggregate(
            total=Sum(
                "coursework__credits",
            ),
        )["total"]
        or 0
    )

    required_credits = (
        getattr(
            program,
            "coursework_credits_required",
            0,
        )
        or 0
    )

    remaining_credits = max(
        required_credits - assigned_credits,
        0,
    )

    coursework_data = [
        {
            "id": coursework.coursework_id,
            "name": coursework.coursework_name,
            "credits": coursework.credits,
            "description": coursework.description or "",
        }
        for coursework in available_courseworks
    ]

    return JsonResponse(
        {
            "success": True,
            "committee_approved": True,
            "program": {
                "id": program.pk,
                "name": program.program_name,
                "required_credits": required_credits,
            },
            "assigned_credits": assigned_credits,
            "remaining_credits": remaining_credits,
            "courseworks": coursework_data,
        }
    )


@login_required
def faculty_coursework_create(
    request,
    uuid,
):
    faculty = get_object_or_404(
        FacultyProfile,
        user__uuid=uuid,
    )

    if request.method == "POST":
        form = FacultyCourseworkForm(
            request.POST,
            faculty=faculty,
        )

        if form.is_valid():
            assignment = form.save(
                commit=False,
            )

            phd_student = assignment.phd_student

            committee = getattr(
                phd_student,
                "doctoral_committee",
                None,
            )

            if committee is None:
                messages.error(
                    request,
                    (
                        "Coursework cannot be assigned because "
                        "the doctoral committee has not been created."
                    ),
                )

                return redirect(
                    "faculty_coursework_list",
                    uuid=faculty.user.uuid,
                )

            if committee.approval_status != "APPROVED":
                messages.error(
                    request,
                    (
                        "Coursework cannot be assigned because "
                        "the doctoral committee is not approved."
                    ),
                )

                return redirect(
                    "faculty_coursework_list",
                    uuid=faculty.user.uuid,
                )

            assignment.program = phd_student.phd_program

            if assignment.start_date.month >= 7:
                assignment.academic_year = (
                    f"{assignment.start_date.year}-" f"{assignment.start_date.year + 1}"
                )
            else:
                assignment.academic_year = (
                    f"{assignment.start_date.year - 1}-" f"{assignment.start_date.year}"
                )

            with transaction.atomic():
                assignment.save()

                student_user = None

                if phd_student.student_id and phd_student.student.user_id:
                    student_user = phd_student.student.user

                _create_coursework_notification(
                    user=student_user,
                    title="Coursework Assigned",
                    message=(
                        f"New coursework has been assigned to you: "
                        f"{assignment.coursework.coursework_name}."
                    ),
                    notification_type="INFO",
                )

            messages.success(
                request,
                "Coursework assigned successfully.",
            )

            return redirect(
                "faculty_coursework_list",
                uuid=faculty.user.uuid,
            )

        error_messages = []

        for field, errors in form.errors.items():
            for error in errors:
                if field == "__all__":
                    error_messages.append(
                        str(error),
                    )
                else:
                    field_label = form.fields[field].label

                    error_messages.append(
                        f"{field_label}: {error}",
                    )

        for error_message in error_messages:
            messages.error(
                request,
                error_message,
            )

        return redirect(
            "faculty_coursework_list",
            uuid=faculty.user.uuid,
        )

    form = FacultyCourseworkForm(
        faculty=faculty,
    )

    context = {
        "faculty": faculty,
        "form": form,
    }

    return render(
        request,
        "leo/Coursework/coursework_create.html",
        context,
    )


def faculty_coursework_update(
    request,
    uuid,
    coursework_id,
):
    faculty = get_object_or_404(
        FacultyProfile,
        user__uuid=uuid,
    )

    assignment = get_object_or_404(
        FacultyCoursework.objects.select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__phd_program",
            "phd_student__phd_program__department",
            "coursework",
            "program",
        ),
        faculty_coursework_id=coursework_id,
        phd_student__advisor=faculty,
    )

    if request.method == "POST":
        form = FacultyCourseworkUpdateForm(
            request.POST,
            instance=assignment,
            faculty=faculty,
        )

        if form.is_valid():
            updated_assignment = form.save(
                commit=False,
            )

            updated_assignment.phd_student = assignment.phd_student
            updated_assignment.coursework = assignment.coursework
            updated_assignment.program = assignment.phd_student.phd_program

            if updated_assignment.start_date.month >= 7:
                updated_assignment.academic_year = (
                    f"{updated_assignment.start_date.year}-"
                    f"{updated_assignment.start_date.year + 1}"
                )
            else:
                updated_assignment.academic_year = (
                    f"{updated_assignment.start_date.year - 1}-"
                    f"{updated_assignment.start_date.year}"
                )

            updated_assignment.save()

            messages.success(
                request,
                "Coursework updated successfully.",
            )

            return redirect(
                "faculty_coursework_list",
                uuid=faculty.user.uuid,
            )

        for field, errors in form.errors.items():
            for error in errors:
                if field == "__all__":
                    messages.error(
                        request,
                        str(error),
                    )
                else:
                    messages.error(
                        request,
                        f"{form.fields[field].label}: {error}",
                    )

    else:
        form = FacultyCourseworkUpdateForm(
            instance=assignment,
            faculty=faculty,
        )

    context = {
        "faculty": faculty,
        "coursework": assignment,
        "form": form,
    }

    return render(
        request,
        "leo/Coursework/coursework_update.html",
        context,
    )


def faculty_coursework_delete(
    request,
    uuid,
    coursework_id,
):
    faculty = get_object_or_404(
        FacultyProfile,
        user__uuid=uuid,
    )

    assignment = get_object_or_404(
        FacultyCoursework,
        faculty_coursework_id=coursework_id,
        phd_student__advisor=faculty,
    )

    if request.method != "POST":
        messages.warning(
            request,
            "Invalid request.",
        )

        return redirect(
            "faculty_coursework_list",
            uuid=faculty.user.uuid,
        )

    if CourseworkSubmission.objects.filter(
        coursework=assignment,
    ).exists():
        messages.error(
            request,
            "Coursework cannot be deleted because a submission already exists.",
        )

        return redirect(
            "faculty_coursework_list",
            uuid=faculty.user.uuid,
        )

    assignment.delete()

    messages.success(
        request,
        "Coursework assignment deleted successfully.",
    )

    return redirect(
        "faculty_coursework_list",
        uuid=faculty.user.uuid,
    )


def faculty_coursework_view(
    request,
    uuid,
    coursework_id,
):
    faculty = get_object_or_404(
        FacultyProfile,
        user__uuid=uuid,
    )

    assignment = get_object_or_404(
        FacultyCoursework.objects.select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__phd_program",
            "program",
            "coursework",
        ),
        faculty_coursework_id=coursework_id,
        phd_student__advisor=faculty,
    )

    submission = (
        CourseworkSubmission.objects.select_related(
            "coursework",
        )
        .filter(
            coursework=assignment,
        )
        .first()
    )

    file_size = None

    if submission and submission.submission_file:
        try:
            file_size = submission.submission_file.size
        except (ValueError, OSError):
            file_size = None

    program_required_credits = (
        getattr(
            assignment.program,
            "coursework_credits_required",
            0,
        )
        or 0
    )

    assigned_credits = (
        FacultyCoursework.objects.filter(
            phd_student=assignment.phd_student,
        )
        .exclude(
            pk=assignment.pk,
        )
        .aggregate(
            total=Sum("coursework__credits"),
        )["total"]
        or 0
    )

    assigned_credits += assignment.coursework.credits or 0

    remaining_credits = max(
        program_required_credits - assigned_credits,
        0,
    )

    faculty_feedback = (
        getattr(
            assignment,
            "remarks",
        )
        or ""
    )

    context = {
        "faculty": faculty,
        "coursework": assignment,
        "submission": submission,
        "file_size": file_size,
        "program_required_credits": program_required_credits,
        "assigned_credits": assigned_credits,
        "remaining_credits": remaining_credits,
        "faculty_feedback": faculty_feedback,
    }

    return render(
        request,
        "leo/Coursework/coursework_view.html",
        context,
    )


def faculty_coursework_assign_data(
    request,
    uuid,
):
    faculty = get_object_or_404(
        FacultyProfile,
        user__uuid=uuid,
    )

    student_id = request.GET.get(
        "student",
    )

    if not student_id:
        return JsonResponse(
            {
                "success": False,
                "message": "Student is required.",
            },
            status=400,
        )

    student = get_object_or_404(
        PhDStudent.objects.select_related(
            "phd_program",
        ),
        pk=student_id,
        advisor=faculty,
        current_status="ACTIVE",
    )

    program = student.phd_program

    assigned_coursework_ids = FacultyCoursework.objects.filter(
        phd_student=student,
    ).values_list(
        "coursework_id",
        flat=True,
    )

    available_courseworks = (
        Coursework.objects.filter(
            program=program,
            is_active=True,
        )
        .exclude(
            coursework_id__in=assigned_coursework_ids,
        )
        .order_by(
            "coursework_name",
        )
    )

    assigned_credits = (
        FacultyCoursework.objects.filter(
            phd_student=student,
        ).aggregate(
            total=Sum("coursework__credits"),
        )["total"]
        or 0
    )

    required_credits = (
        getattr(
            program,
            "coursework_credits_required",
            0,
        )
        or 0
    )

    remaining_credits = max(
        required_credits - assigned_credits,
        0,
    )

    coursework_data = [
        {
            "id": coursework.coursework_id,
            "name": coursework.coursework_name,
            "credits": coursework.credits,
            "description": coursework.description or "",
        }
        for coursework in available_courseworks
    ]

    return JsonResponse(
        {
            "success": True,
            "program": {
                "id": program.pk,
                "name": program.program_name,
                "required_credits": required_credits,
            },
            "assigned_credits": assigned_credits,
            "remaining_credits": remaining_credits,
            "courseworks": coursework_data,
        }
    )


@login_required
def faculty_coursework_create_master(
    request,
    uuid,
):
    faculty = get_object_or_404(
        FacultyProfile,
        user__uuid=uuid,
    )

    if request.method == "POST":
        form = CourseworkForm(
            request.POST,
            faculty=faculty,
        )

        if form.is_valid():
            program = form.cleaned_data["program"]
            credits = form.cleaned_data["credits"]

            required_credits = (
                getattr(
                    program,
                    "total_credits_required",
                    0,
                )
                or 0
            )

            existing_credits = (
                Coursework.objects.filter(
                    program=program,
                    is_active=True,
                ).aggregate(
                    total=Sum("credits"),
                )["total"]
                or 0
            )

            remaining_credits = max(
                required_credits - existing_credits,
                0,
            )

            if credits > remaining_credits:
                form.add_error(
                    "credits",
                    (
                        f"Program credit limit exceeded. "
                        f"Remaining credits: {remaining_credits} credits. "
                        f"This coursework requires {credits} credits."
                    ),
                )
            else:
                coursework = form.save()

                messages.success(
                    request,
                    "Master coursework created successfully.",
                )

                return redirect(
                    "faculty_coursework_master_list",
                    uuid=faculty.user.uuid,
                )

        if form.errors:
            error_messages = []

            for field_name, errors in form.errors.items():
                if field_name == "__all__":
                    for error in errors:
                        error_messages.append(str(error))
                    continue

                field = form.fields.get(field_name)

                if field:
                    field_label = (
                        field.label
                        or field_name.replace(
                            "_",
                            " ",
                        ).title()
                    )
                else:
                    field_label = field_name.replace(
                        "_",
                        " ",
                    ).title()

                for error in errors:
                    error_messages.append(f"{field_label}: {error}")

            messages.error(
                request,
                "Please correct the following errors: " + " | ".join(error_messages),
            )

    else:
        form = CourseworkForm(
            faculty=faculty,
        )

    programs = (
        form.fields["program"].queryset
        if "program" in form.fields
        else PhD.objects.none()
    )

    program_credit_data = {}

    for program in programs:
        existing_credits = (
            Coursework.objects.filter(
                program=program,
                is_active=True,
            ).aggregate(
                total=Sum("credits"),
            )["total"]
            or 0
        )

        required_credits = (
            getattr(
                program,
                "total_credits_required",
                0,
            )
            or 0
        )

        remaining_credits = max(
            required_credits - existing_credits,
            0,
        )

        program_credit_data[str(program.pk)] = {
            "required": required_credits,
            "existing": existing_credits,
            "remaining": remaining_credits,
        }

    field_errors = {}

    for field_name, errors in form.errors.items():
        if field_name == "__all__":
            continue

        field = form.fields.get(field_name)

        field_label = (
            field.label
            if field
            else field_name.replace(
                "_",
                " ",
            ).title()
        )

        field_errors[field_name] = {
            "label": field_label,
            "messages": [str(error) for error in errors],
        }

    non_field_errors = [str(error) for error in form.non_field_errors()]

    error_summary = []

    for field_name, error_data in field_errors.items():
        for error in error_data["messages"]:
            error_summary.append(
                {
                    "field": error_data["label"],
                    "message": error,
                }
            )

    for error in non_field_errors:
        error_summary.append(
            {
                "field": "Form",
                "message": error,
            }
        )

    context = {
        "faculty": faculty,
        "form": form,
        "programs": programs,
        "program_credit_data": program_credit_data,
        "field_errors": field_errors,
        "non_field_errors": non_field_errors,
        "error_summary": error_summary,
        "has_form_errors": form.errors,
        "form_error_count": len(error_summary),
    }

    return render(
        request,
        "leo/Coursework/coursework_master_create.html",
        context,
    )


def faculty_coursework_master_list(
    request,
    uuid,
):
    faculty = get_object_or_404(
        FacultyProfile,
        user__uuid=uuid,
    )

    search = request.GET.get(
        "search",
        "",
    ).strip()

    selected_program = request.GET.get(
        "program",
        "",
    ).strip()

    selected_status = request.GET.get(
        "status",
        "",
    ).strip()

    base_courseworks = Coursework.objects.filter(
        created_by=faculty,
    )

    total_courseworks = base_courseworks.count()

    active_courseworks = base_courseworks.filter(
        is_active=True,
    ).count()

    inactive_courseworks = base_courseworks.filter(
        is_active=False,
    ).count()

    total_programs = base_courseworks.values("program").distinct().count()

    courseworks = base_courseworks.select_related(
        "program",
        "created_by",
    ).order_by(
        "program__program_name",
        "coursework_name",
    )

    if search:
        courseworks = courseworks.filter(
            Q(
                coursework_name__icontains=search,
            )
            | Q(
                description__icontains=search,
            )
            | Q(
                program__program_name__icontains=search,
            )
        )

    if selected_program:
        courseworks = courseworks.filter(
            program_id=selected_program,
        )

    if selected_status == "active":
        courseworks = courseworks.filter(
            is_active=True,
        )

    elif selected_status == "inactive":
        courseworks = courseworks.filter(
            is_active=False,
        )

    program_list = PhD.objects.filter(
        status="ACTIVE",
    ).order_by(
        "program_name",
    )

    paginator = Paginator(
        courseworks,
        10,
    )

    coursework_list = paginator.get_page(
        request.GET.get("page"),
    )

    context = {
        "faculty": faculty,
        "coursework_list": coursework_list,
        "search": search,
        "selected_program": selected_program,
        "selected_status": selected_status,
        "program_list": program_list,
        "total_courseworks": total_courseworks,
        "active_courseworks": active_courseworks,
        "inactive_courseworks": inactive_courseworks,
        "total_programs": total_programs,
    }

    return render(
        request,
        "leo/Coursework/coursework_master_list.html",
        context,
    )


def faculty_coursework_master_update(
    request,
    uuid,
    coursework_id,
):
    faculty = get_object_or_404(
        FacultyProfile,
        user__uuid=uuid,
    )

    coursework = get_object_or_404(
        Coursework,
        coursework_id=coursework_id,
        created_by=faculty,
    )

    program_credit_data = {}

    programs = PhD.objects.filter(
        status="ACTIVE",
    ).order_by(
        "program_name",
    )

    for program in programs:
        required_credits = (
            getattr(
                program,
                "total_credits_required",
                0,
            )
            or 0
        )

        existing_credits = (
            Coursework.objects.filter(
                program=program,
                is_active=True,
            )
            .exclude(
                pk=coursework.pk,
            )
            .aggregate(
                total=Sum("credits"),
            )["total"]
            or 0
        )

        remaining_credits = max(
            required_credits - existing_credits,
            0,
        )

        program_credit_data[str(program.pk)] = {
            "required": required_credits,
            "existing": existing_credits,
            "remaining": remaining_credits,
        }

    if request.method == "POST":
        form = CourseworkForm(
            request.POST,
            instance=coursework,
            faculty=faculty,
        )

        if form.is_valid():
            program = form.cleaned_data["program"]
            credits = form.cleaned_data["credits"]

            required_credits = (
                getattr(
                    program,
                    "total_credits_required",
                    0,
                )
                or 0
            )

            existing_credits = (
                Coursework.objects.filter(
                    program=program,
                    is_active=True,
                )
                .exclude(
                    pk=coursework.pk,
                )
                .aggregate(
                    total=Sum("credits"),
                )["total"]
                or 0
            )

            assigned_coursework = FacultyCoursework.objects.filter(
                coursework=coursework,
            ).first()

            assigned_credits = (
                assigned_coursework.coursework.credits if assigned_coursework else 0
            )

            if required_credits > 0 and existing_credits + credits > required_credits:
                remaining_credits = max(
                    required_credits - existing_credits,
                    0,
                )

                form.add_error(
                    "credits",
                    (
                        f"Program credit limit exceeded. "
                        f"Remaining credits: {remaining_credits}."
                    ),
                )

            elif assigned_coursework and credits < assigned_credits:
                form.add_error(
                    "credits",
                    (
                        "Credits cannot be reduced below the "
                        "credits already used by assigned students."
                    ),
                )

            else:
                form.save()

                messages.success(
                    request,
                    "Coursework updated successfully.",
                )

                return redirect(
                    "faculty_coursework_master_list",
                    uuid=faculty.user.uuid,
                )

        messages.error(
            request,
            "Please correct the errors below and try again.",
        )

    else:
        form = CourseworkForm(
            instance=coursework,
            faculty=faculty,
        )

    context = {
        "faculty": faculty,
        "coursework": coursework,
        "form": form,
        "program_credit_data": program_credit_data,
    }

    return render(
        request,
        "leo/Coursework/coursework_master_update.html",
        context,
    )


def faculty_coursework_master_delete(
    request,
    uuid,
    coursework_id,
):
    faculty = get_object_or_404(
        FacultyProfile,
        user__uuid=uuid,
    )

    coursework = get_object_or_404(
        Coursework,
        coursework_id=coursework_id,
        created_by=faculty,
    )

    if request.method != "POST":
        messages.warning(
            request,
            "Invalid request.",
        )

        return redirect(
            "faculty_coursework_master_list",
            uuid=faculty.user.uuid,
        )

    if FacultyCoursework.objects.filter(
        coursework=coursework,
    ).exists():
        messages.error(
            request,
            "This coursework cannot be deleted because it has already been assigned to students.",
        )

        return redirect(
            "faculty_coursework_master_list",
            uuid=faculty.user.uuid,
        )

    coursework.delete()

    messages.success(
        request,
        "Coursework deleted successfully.",
    )

    return redirect(
        "faculty_coursework_master_list",
        uuid=faculty.user.uuid,
    )


def faculty_coursework_by_program(request, uuid):

    faculty = get_object_or_404(
        FacultyProfile,
        user__uuid=uuid,
    )

    program_id = request.GET.get(
        "program_id",
    )

    student_id = request.GET.get(
        "student_id",
    )

    if not program_id:
        return JsonResponse(
            {
                "success": False,
                "courseworks": [],
                "message": "Program is required.",
            },
            status=400,
        )

    courseworks = Coursework.objects.filter(
        program_id=program_id,
        is_active=True,
        created_by=faculty,
    )

    if student_id:

        student = get_object_or_404(
            PhDStudent,
            pk=student_id,
            advisor=faculty,
            current_status="ACTIVE",
        )

        assigned_coursework_ids = FacultyCoursework.objects.filter(
            phd_student=student,
        ).values_list(
            "coursework_id",
            flat=True,
        )

        courseworks = courseworks.exclude(
            coursework_id__in=assigned_coursework_ids,
        )

    courseworks = courseworks.order_by(
        "coursework_name",
    )

    return JsonResponse(
        {
            "success": True,
            "courseworks": [
                {
                    "id": coursework.coursework_id,
                    "name": coursework.coursework_name,
                    "credits": coursework.credits,
                    "description": coursework.description or "",
                }
                for coursework in courseworks
            ],
        }
    )

############################################################
# Preliminary Examination Module
############################################################


class ExamAuthorization:
    """
    Authorization helper for preliminary examination access control.

    This class centralizes all permission checks for examinations including:
    - Viewing permissions
    - Editing permissions
    - Publishing permissions
    - Evaluation permissions
    - Result declaration permissions
    """

    def __init__(self, faculty, examination):
        """
        Initialize authorization object.

        Parameters:
            faculty: FacultyProfile instance
            examination: PreliminaryExamination instance
        """
        self.faculty = faculty
        self.examination = examination
        self.phd_student = examination.phd_student
        self._committee = None
        self._committee_members = None
        self._my_evaluation = None
        self._evaluation_status = None
        self._required_evaluator_ids = None
        self._roles_calculated = False
        self._calculate_roles()

    def _calculate_roles(self):
        """
        Calculate faculty's roles for the examination.

        Sets: is_chair, is_committee_member, is_advisor
        """
        if self._roles_calculated:
            return

        self.is_chair = False
        self.is_committee_member = False
        self.is_advisor = False

        committee = self.phd_student.doctoral_committee
        if committee:
            self._committee = committee
            if committee.chair_faculty_id == self.faculty.pk:
                self.is_chair = True
            if committee.committee_members.filter(faculty=self.faculty).exists():
                self.is_committee_member = True

        if self.phd_student.advisor_id == self.faculty.pk:
            self.is_advisor = True

        self._roles_calculated = True

    def get_committee_members(self):
        """Get list of committee members."""
        if self._committee is None:
            return []
        if self._committee_members is None:
            self._committee_members = list(
                self._committee.committee_members.select_related(
                    "faculty",
                    "faculty__user",
                    "department",
                ).order_by("role")
            )
        return self._committee_members

    def get_my_evaluation(self):
        """Get faculty's evaluation for the examination."""
        if self._my_evaluation is None:
            self._my_evaluation = (
                PreliminaryExamEvaluation.objects.filter(
                    examination=self.examination,
                    faculty=self.faculty,
                )
                .select_related(
                    "faculty",
                    "faculty__user",
                )
                .first()
            )
        return self._my_evaluation

    def has_submitted_evaluation(self):
        """Check if faculty has submitted an evaluation."""
        my_eval = self.get_my_evaluation()
        return my_eval is not None and my_eval.is_submitted

    def get_required_evaluators(self):
        if self._required_evaluator_ids is not None:
            return self._required_evaluator_ids

        evaluator_ids = set()
        committee = self._committee

        if committee:
            for member in committee.committee_members.all():
                if (
                    member.faculty_id
                    and member.faculty_id != committee.chair_faculty_id
                ):
                    evaluator_ids.add(member.faculty_id)

        advisor_id = self.phd_student.advisor_id

        if (
            advisor_id
            and (
                not committee
                or advisor_id != committee.chair_faculty_id
            )
        ):
            evaluator_ids.add(advisor_id)

        self._required_evaluator_ids = list(evaluator_ids)
        return self._required_evaluator_ids

    def get_evaluation_status(self):
        """Get evaluation submission status."""
        if self._evaluation_status is None:
            required_ids = self.get_required_evaluators()
            submitted_count = PreliminaryExamEvaluation.objects.filter(
                examination=self.examination,
                faculty_id__in=required_ids,
                is_submitted=True,
            ).count()

            total = len(required_ids)
            self._evaluation_status = {
                "total": total,
                "submitted": submitted_count,
                "pending": total - submitted_count,
                "all_submitted": total > 0 and submitted_count == total,
                "has_submitted": self.has_submitted_evaluation(),
            }
        return self._evaluation_status

    def _is_exam_not_completed_or_cancelled(self):
        """Check if exam is not completed or cancelled."""
        return self.examination.status not in ["COMPLETED", "CANCELLED"]

    def _is_exam_published_and_pending(self):
        """Check if exam is published and pending result."""
        return (
            self.examination.is_published
            and self.examination.result == "PENDING"
            and self.examination.status == "SCHEDULED"
        )

    def can_view(self):
        """Check if faculty can view the examination."""
        self._calculate_roles()
        return self.is_chair or self.is_committee_member or self.is_advisor

    def can_edit(self):
        """Check if faculty can edit the examination."""
        self._calculate_roles()
        if not self.is_chair:
            return False
        return self._is_exam_not_completed_or_cancelled()

    def can_publish(self):
        """Check if faculty can publish the examination."""
        self._calculate_roles()
        if not self.is_chair:
            return False
        if self.examination.is_published or self.examination.status == "CANCELLED":
            return False
        if not all(
            [
                self.examination.title,
                self.examination.venue,
                self.examination.exam_date,
                self.examination.start_time,
                self.examination.end_time,
            ]
        ):
            return False
        return True

    def can_delete(self):
        """Check if faculty can delete the examination."""
        self._calculate_roles()
        if not self.is_chair:
            return False
        if self.examination.is_published or self.examination.status == "COMPLETED":
            return False
        return True

    def can_declare_result(self):
        """Check if faculty can declare result."""
        self._calculate_roles()
        if not self.is_chair:
            return False
        if not self._is_exam_not_completed_or_cancelled():
            return False
        if not self.examination.is_published:
            return False
        if self.examination.result != "PENDING":
            return False
        return self.get_evaluation_status()["all_submitted"]

    def can_evaluate(self):
        """Check if faculty can evaluate the examination."""
        self._calculate_roles()
        if self.is_chair:
            return False
        if not (self.is_committee_member or self.is_advisor):
            return False
        if not self._is_exam_published_and_pending():
            return False
        if self.has_submitted_evaluation():
            return False
        return True

    def can_view_evaluation(self):
        """Check if faculty can view their evaluation."""
        self._calculate_roles()
        if self.is_chair:
            return False
        if not (self.is_committee_member or self.is_advisor):
            return False
        return self.has_submitted_evaluation()


def get_faculty_or_404(uuid, request_user=None):
    """
    Get faculty profile by UUID with active status.

    Parameters:
        uuid: UUID of the faculty user
        request_user: Optional user to filter by

    Returns:
        FacultyProfile instance or 404

    Workflow:
        1. Build queryset with user relation
        2. Filter by request_user if provided
        3. Get faculty with ACTIVE employment status
    """
    queryset = FacultyProfile.objects.select_related("user")
    if request_user:
        queryset = queryset.filter(user=request_user)
    return get_object_or_404(
        queryset,
        user__uuid=uuid,
        employment_status="ACTIVE",
    )


def get_examination_with_all_data(exam_id):
    """
    Get preliminary examination with all related data prefetched.

    Parameters:
        exam_id: ID of the preliminary examination

    Returns:
        PreliminaryExamination instance with all relations
    """
    return get_object_or_404(
        PreliminaryExamination.objects.select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "phd_student__phd_program",
            "phd_student__doctoral_committee",
            "phd_student__doctoral_committee__chair_faculty",
            "phd_student__doctoral_committee__chair_faculty__user",
        ).prefetch_related(
            Prefetch(
                "evaluations",
                queryset=PreliminaryExamEvaluation.objects.select_related(
                    "faculty",
                    "faculty__user",
                ),
            ),
            Prefetch(
                "phd_student__doctoral_committee__committee_members",
                queryset=CommitteeMember.objects.select_related(
                    "faculty",
                    "faculty__user",
                    "department",
                ),
            ),
        ),
        prelim_exam_id=exam_id,
    )


def get_authorized_examination_or_404(faculty, exam_id):
    """
    Get examination with authorization check.

    Parameters:
        faculty: FacultyProfile instance
        exam_id: ID of the preliminary examination

    Returns:
        Tuple of (examination, auth) or 404

    Workflow:
        1. Get examination with all data
        2. Create authorization object
        3. Verify view permission
        4. Return examination and auth
    """
    examination = get_examination_with_all_data(exam_id)
    auth = ExamAuthorization(faculty, examination)

    if not auth.can_view():
        raise Http404("You are not authorized to view this examination.")

    return examination, auth


def get_chair_examination_or_404(faculty, exam_id):
    """
    Get examination with chair authorization check.

    Parameters:
        faculty: FacultyProfile instance
        exam_id: ID of the preliminary examination

    Returns:
        Tuple of (examination, auth) or 404

    Workflow:
        1. Get examination with all data
        2. Create authorization object
        3. Verify chair permission
        4. Return examination and auth
    """
    examination = get_examination_with_all_data(exam_id)
    auth = ExamAuthorization(faculty, examination)

    if not auth.is_chair:
        raise Http404("Only the Chair Faculty can access this.")

    return examination, auth


@login_required
def faculty_preliminary_exam_list(request, uuid):
    """
    Display list of preliminary examinations.

    Purpose:
        Show all examinations with filters and statistics.

    Parameters:
        request: HTTP request object
        uuid: UUID of the faculty member

    Returns:
        Rendered template with examination list

    Workflow:
        1. Get faculty profile
        2. Get examinations with filters
        3. Calculate roles and permissions for each
        4. Apply pagination
        5. Calculate statistics
        6. Render template
    """
    faculty = get_faculty_or_404(uuid, request.user)

    search = request.GET.get("search", "")
    status_filter = request.GET.get("status", "")
    exam_type_filter = request.GET.get("exam_type", "")
    role_filter = request.GET.get("role", "")
    result_filter = request.GET.get("result", "")

    examinations = (
        PreliminaryExamination.objects.select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "phd_student__phd_program",
            "phd_student__doctoral_committee",
            "phd_student__doctoral_committee__chair_faculty",
            "phd_student__doctoral_committee__chair_faculty__user",
        )
        .prefetch_related(
            Prefetch(
                "evaluations",
                queryset=PreliminaryExamEvaluation.objects.select_related(
                    "faculty",
                    "faculty__user",
                ),
            ),
            Prefetch(
                "phd_student__doctoral_committee__committee_members",
                queryset=CommitteeMember.objects.select_related(
                    "faculty",
                    "faculty__user",
                ),
            ),
        )
        .filter(
            Q(phd_student__doctoral_committee__chair_faculty=faculty)
            | Q(phd_student__doctoral_committee__committee_members__faculty=faculty)
            | Q(phd_student__advisor=faculty)
        )
        .distinct()
        .order_by("-exam_date", "-start_time")
    )

    if search:
        examinations = examinations.filter(
            Q(phd_student__student__user__first_name__icontains=search)
            | Q(phd_student__student__user__last_name__icontains=search)
            | Q(phd_student__student__student_number__icontains=search)
            | Q(phd_student__phd_program__program_name__icontains=search)
            | Q(title__icontains=search)
            | Q(venue__icontains=search)
        )
    if status_filter:
        examinations = examinations.filter(status=status_filter)
    if exam_type_filter:
        examinations = examinations.filter(exam_type=exam_type_filter)
    if result_filter:
        examinations = examinations.filter(result=result_filter)

    exam_list = []
    for exam in examinations:
        auth = ExamAuthorization(faculty, exam)

        if auth.is_chair:
            role = "CHAIR"
        elif auth.is_committee_member:
            role = "MEMBER"
        elif auth.is_advisor:
            role = "ADVISOR"
        else:
            continue

        exam.faculty_role = role
        exam.can_edit = auth.can_edit()
        exam.can_publish = auth.can_publish()
        exam.can_delete = auth.can_delete()
        exam.can_declare_result = auth.can_declare_result()
        exam.can_evaluate = auth.can_evaluate()
        exam.can_view_evaluation = auth.can_view_evaluation()
        exam.has_submitted_evaluation = auth.has_submitted_evaluation()

        evaluations = list(exam.evaluations.all())
        exam.evaluation_total = len(evaluations)
        exam.evaluation_submitted = sum(
            1 for evaluation in evaluations if evaluation.is_submitted
        )
        exam.evaluation_pending = exam.evaluation_total - exam.evaluation_submitted
        exam.all_evaluations_submitted = (
            exam.evaluation_total > 0
            and exam.evaluation_submitted == exam.evaluation_total
        )

        exam_list.append(exam)

    if role_filter:
        exam_list = [e for e in exam_list if e.faculty_role == role_filter]

    paginator = Paginator(exam_list, 10)
    page_number = request.GET.get("page")
    examination_list = paginator.get_page(page_number)

    total_exams = len(exam_list)
    chair_exams = sum(1 for e in exam_list if e.faculty_role == "CHAIR")
    member_exams = sum(1 for e in exam_list if e.faculty_role == "MEMBER")
    advisor_exams = sum(1 for e in exam_list if e.faculty_role == "ADVISOR")

    draft_exams = sum(1 for e in exam_list if e.status == "DRAFT")
    scheduled_exams = sum(1 for e in exam_list if e.status == "SCHEDULED")
    completed_exams = sum(1 for e in exam_list if e.status == "COMPLETED")
    cancelled_exams = sum(1 for e in exam_list if e.status == "CANCELLED")

    published_exams = sum(1 for e in exam_list if e.is_published)
    unpublished_exams = sum(1 for e in exam_list if not e.is_published)

    pass_count = sum(1 for e in exam_list if e.result == "PASS")
    fail_count = sum(1 for e in exam_list if e.result == "FAIL")
    pending_results = sum(1 for e in exam_list if e.result == "PENDING")

    pending_evaluations = sum(1 for e in exam_list if e.can_evaluate)
    submitted_evaluations = sum(1 for e in exam_list if e.has_submitted_evaluation)

    context = {
        "faculty": faculty,
        "examination_list": examination_list,
        "search": search,
        "status_filter": status_filter,
        "exam_type_filter": exam_type_filter,
        "role_filter": role_filter,
        "result_filter": result_filter,
        "total_exams": total_exams,
        "chair_exams": chair_exams,
        "member_exams": member_exams,
        "advisor_exams": advisor_exams,
        "draft_exams": draft_exams,
        "scheduled_exams": scheduled_exams,
        "completed_exams": completed_exams,
        "cancelled_exams": cancelled_exams,
        "published_exams": published_exams,
        "unpublished_exams": unpublished_exams,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "pending_results": pending_results,
        "pending_evaluations": pending_evaluations,
        "submitted_evaluations": submitted_evaluations,
    }

    return render(
        request,
        "leo/PreliminaryExam/exam_list.html",
        context,
    )


@login_required
def faculty_my_preliminary_examinations(request, uuid):
    """
    Display examinations where faculty is a committee member or advisor.

    Purpose:
        Show examinations available for evaluation.

    Parameters:
        request: HTTP request object
        uuid: UUID of the faculty member

    Returns:
        Rendered template with examination list

    Workflow:
        1. Get faculty profile
        2. Get examinations where faculty is member or advisor
        3. Calculate evaluation permissions for each
        4. Apply pagination
        5. Calculate statistics
        6. Render template
    """
    faculty = get_faculty_or_404(uuid, request.user)

    search = request.GET.get("search", "")
    status_filter = request.GET.get("status", "")
    exam_type_filter = request.GET.get("exam_type", "")
    result_filter = request.GET.get("result", "")

    committee_ids = CommitteeMember.objects.filter(faculty=faculty).values_list(
        "committee_id", flat=True
    )
    phd_student_ids = PhDStudent.objects.filter(advisor=faculty).values_list(
        "phd_student_id", flat=True
    )

    examinations = (
        PreliminaryExamination.objects.filter(
            Q(phd_student_id__in=phd_student_ids)
            | Q(phd_student__doctoral_committee__committee_id__in=committee_ids)
        )
        .select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "phd_student__phd_program",
            "phd_student__doctoral_committee",
            "phd_student__doctoral_committee__chair_faculty",
            "phd_student__doctoral_committee__chair_faculty__user",
        )
        .prefetch_related(
            Prefetch(
                "evaluations",
                queryset=PreliminaryExamEvaluation.objects.select_related(
                    "faculty",
                    "faculty__user",
                ),
            ),
            Prefetch(
                "phd_student__doctoral_committee__committee_members",
                queryset=CommitteeMember.objects.select_related(
                    "faculty",
                    "faculty__user",
                ),
            ),
        )
        .distinct()
        .order_by("-exam_date", "-start_time")
    )

    if search:
        examinations = examinations.filter(
            Q(phd_student__student__user__first_name__icontains=search)
            | Q(phd_student__student__user__last_name__icontains=search)
            | Q(phd_student__student__student_number__icontains=search)
            | Q(phd_student__phd_program__program_name__icontains=search)
            | Q(title__icontains=search)
            | Q(venue__icontains=search)
        )
    if status_filter:
        examinations = examinations.filter(status=status_filter)
    if exam_type_filter:
        examinations = examinations.filter(exam_type=exam_type_filter)
    if result_filter:
        examinations = examinations.filter(result=result_filter)

    exam_list = []
    for exam in examinations:
        auth = ExamAuthorization(faculty, exam)

        if not (auth.is_committee_member or auth.is_advisor):
            continue

        exam.faculty_role = "MEMBER" if auth.is_committee_member else "ADVISOR"
        exam.can_evaluate = auth.can_evaluate()
        exam.can_view_evaluation = auth.can_view_evaluation()
        exam.has_submitted_evaluation = auth.has_submitted_evaluation()
        exam.my_evaluation = auth.get_my_evaluation()

        exam_list.append(exam)

    paginator = Paginator(exam_list, 10)
    page_number = request.GET.get("page")
    examination_list = paginator.get_page(page_number)

    total_exams = len(exam_list)
    scheduled_exams = sum(1 for e in exam_list if e.status == "SCHEDULED")
    completed_exams = sum(1 for e in exam_list if e.status == "COMPLETED")
    cancelled_exams = sum(1 for e in exam_list if e.status == "CANCELLED")
    pass_count = sum(1 for e in exam_list if e.result == "PASS")
    fail_count = sum(1 for e in exam_list if e.result == "FAIL")
    pending_results = sum(1 for e in exam_list if e.result == "PENDING")
    pending_evaluations = sum(1 for e in exam_list if e.can_evaluate)
    submitted_evaluations = sum(1 for e in exam_list if e.has_submitted_evaluation)

    context = {
        "faculty": faculty,
        "examination_list": examination_list,
        "search": search,
        "status_filter": status_filter,
        "exam_type_filter": exam_type_filter,
        "result_filter": result_filter,
        "total_exams": total_exams,
        "scheduled_exams": scheduled_exams,
        "completed_exams": completed_exams,
        "cancelled_exams": cancelled_exams,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "pending_results": pending_results,
        "pending_evaluations": pending_evaluations,
        "submitted_evaluations": submitted_evaluations,
    }

    return render(
        request,
        "leo/PreliminaryExam/exam_list.html",
        context,
    )


@login_required
def faculty_preliminary_exam_create(
    request,
    uuid,
):
    faculty = get_faculty_or_404(
        uuid,
        request.user,
    )

    if request.method == "POST":
        form = PreliminaryExaminationForm(
            request.POST,
            faculty=faculty,
        )

        if form.is_valid():
            examination_student = form.cleaned_data.get(
                "phd_student",
            )

            exam_date = form.cleaned_data.get(
                "exam_date",
            )

            start_time = form.cleaned_data.get(
                "start_time",
            )

            end_time = form.cleaned_data.get(
                "end_time",
            )

            now = timezone.localtime()
            current_date = now.date()
            current_time = now.time()

            if exam_date < current_date:
                messages.error(
                    request,
                    "Preliminary examination cannot be scheduled for a past date.",
                )

                return redirect(
                    "faculty_preliminary_exam_list",
                    uuid=faculty.user.uuid,
                )

            if exam_date == current_date:
                if start_time <= current_time:
                    messages.error(
                        request,
                        "Preliminary examination start time must be in the future.",
                    )

                    return redirect(
                        "faculty_preliminary_exam_list",
                        uuid=faculty.user.uuid,
                    )

            if start_time >= end_time:
                messages.error(
                    request,
                    "Preliminary examination end time must be after the start time.",
                )

                return redirect(
                    "faculty_preliminary_exam_list",
                    uuid=faculty.user.uuid,
                )

            if not examination_student:
                messages.error(
                    request,
                    "PhD student is required.",
                )

                return redirect(
                    "faculty_preliminary_exam_list",
                    uuid=faculty.user.uuid,
                )

            committee = getattr(
                examination_student,
                "doctoral_committee",
                None,
            )

            if committee is None:
                messages.error(
                    request,
                    (
                        "Preliminary examination cannot be created "
                        "because the doctoral committee has not been created."
                    ),
                )

                return redirect(
                    "faculty_preliminary_exam_list",
                    uuid=faculty.user.uuid,
                )

            if committee.approval_status != "APPROVED":
                messages.error(
                    request,
                    (
                        "Preliminary examination cannot be created "
                        "because the doctoral committee is not approved."
                    ),
                )

                return redirect(
                    "faculty_preliminary_exam_list",
                    uuid=faculty.user.uuid,
                )

            phd_program = getattr(
                examination_student,
                "phd_program",
                None,
            )

            if phd_program is None:
                messages.error(
                    request,
                    (
                        "Preliminary examination cannot be created "
                        "because the PhD program has not been assigned."
                    ),
                )

                return redirect(
                    "faculty_preliminary_exam_list",
                    uuid=faculty.user.uuid,
                )

            required_credits = (
                getattr(
                    phd_program,
                    "total_credits_required",
                    0,
                )
                or 0
            )

            completed_credits = (
                FacultyCoursework.objects.filter(
                    phd_student=examination_student,
                    status="COMPLETED",
                ).aggregate(
                    total=Sum(
                        "coursework__credits",
                    ),
                )[
                    "total"
                ]
                or 0
            )

            remaining_credits = max(
                required_credits - completed_credits,
                0,
            )

            if completed_credits < required_credits:
                messages.error(
                    request,
                    (
                        "Preliminary examination cannot be created "
                        "because the required coursework has not been completed. "
                        f"Required credits: {required_credits}. "
                        f"Completed credits: {completed_credits}. "
                        f"Remaining credits: {remaining_credits}."
                    ),
                )

                return redirect(
                    "faculty_preliminary_exam_list",
                    uuid=faculty.user.uuid,
                )

            try:
                with transaction.atomic():
                    examination = form.save()

                    evaluators = {}

                    committee_members = CommitteeMember.objects.filter(
                        committee=committee,
                    ).select_related(
                        "faculty",
                    )

                    for member in committee_members:
                        if member.faculty and member.faculty != committee.chair_faculty:
                            evaluators[member.faculty.pk] = member.faculty

                    advisor = getattr(
                        examination_student,
                        "advisor",
                        None,
                    )

                    if advisor and advisor != committee.chair_faculty:
                        evaluators[advisor.pk] = advisor

                    for evaluator in evaluators.values():
                        PreliminaryExamEvaluation.objects.get_or_create(
                            examination=examination,
                            faculty=evaluator,
                            defaults={
                                "knowledge_score": 0,
                                "research_aptitude_score": 0,
                                "presentation_score": 0,
                                "technical_score": 0,
                                "comments": "",
                                "recommendation": "PASS",
                                "is_submitted": False,
                            },
                        )

                    if examination.is_published:
                        student_user = None

                        if (
                            examination_student
                            and examination_student.student_id
                            and examination_student.student.user_id
                        ):
                            student_user = examination_student.student.user

                        exam_title = examination.title or "Preliminary Examination"

                        exam_date_text = examination.exam_date.strftime("%B %d, %Y")

                        start_time_text = examination.start_time.strftime("%I:%M %p")

                        end_time_text = examination.end_time.strftime("%I:%M %p")

                        exam_message = (
                            f"Your {exam_title} has been scheduled for "
                            f"{exam_date_text} from {start_time_text} "
                            f"to {end_time_text} at {examination.venue}."
                        )

                        if student_user:
                            _create_preliminary_exam_notification(
                                user=student_user,
                                title="Preliminary Examination Scheduled",
                                message=exam_message,
                                notification_type="INFO",
                            )

                        advisor_user = (
                            getattr(
                                advisor,
                                "user",
                                None,
                            )
                            if advisor
                            else None
                        )

                        if advisor_user:
                            advisor_message = (
                                f"The {exam_title} for "
                                f"{student_user.get_full_name()} "
                                f"has been scheduled for "
                                f"{exam_date_text} from {start_time_text} "
                                f"to {end_time_text} at {examination.venue}."
                            )

                            _create_preliminary_exam_notification(
                                user=advisor_user,
                                title="Preliminary Examination Scheduled",
                                message=advisor_message,
                                notification_type="INFO",
                            )

                messages.success(
                    request,
                    "Preliminary examination created successfully.",
                )

                return redirect(
                    "faculty_preliminary_exam_list",
                    uuid=faculty.user.uuid,
                )

            except Exception as e:
                messages.error(
                    request,
                    f"Error creating examination: {e}",
                )

                return redirect(
                    "faculty_preliminary_exam_list",
                    uuid=faculty.user.uuid,
                )

        messages.error(
            request,
            "Please correct the errors below.",
        )

        return redirect(
            "faculty_preliminary_exam_list",
            uuid=faculty.user.uuid,
        )

    form = PreliminaryExaminationForm(
        faculty=faculty,
    )

    students = list(form.fields["phd_student"].queryset)

    committee_ids = [
        student.doctoral_committee.pk
        for student in students
        if getattr(
            student,
            "doctoral_committee",
            None,
        )
    ]

    committee_members = (
        CommitteeMember.objects.filter(
            committee_id__in=committee_ids,
        )
        .select_related(
            "faculty",
            "faculty__user",
        )
        .order_by(
            "faculty__user__first_name",
            "faculty__user__last_name",
        )
    )

    members_by_committee = {}

    for member in committee_members:
        members_by_committee.setdefault(
            member.committee_id,
            [],
        ).append(member)

    committee_data = {}

    for student in students:
        committee = getattr(
            student,
            "doctoral_committee",
            None,
        )

        if committee is None:
            continue

        chair = committee.chair_faculty

        data = {
            "chair": (chair.user.get_full_name() if chair else "—"),
            "co_chair": "—",
            "internal": [],
            "external": [],
        }

        for member in members_by_committee.get(
            committee.pk,
            [],
        ):
            if not member.faculty:
                continue

            member_name = member.faculty.user.get_full_name()

            if member.role == "CO_CHAIR":
                data["co_chair"] = member_name

            elif member.role == "INTERNAL_MEMBER":
                data["internal"].append(member_name)

            elif member.role == "EXTERNAL_MEMBER":
                data["external"].append(member_name)

        committee_data[str(student.phd_student_id)] = data

    context = {
        "faculty": faculty,
        "form": form,
        "committee_data": committee_data,
    }

    return render(
        request,
        "leo/PreliminaryExam/exam_create.html",
        context,
    )


@login_required
def faculty_preliminary_exam_detail(request, uuid, exam_id):
    """
    Display detailed view of a preliminary examination.

    Purpose:
        Show examination details with evaluations and permission info.

    Parameters:
        request: HTTP request object
        uuid: UUID of the faculty member
        exam_id: ID of the preliminary examination

    Returns:
        Rendered template with examination details

    Workflow:
        1. Get faculty and authorized examination
        2. Get committee members and evaluations
        3. Calculate averages for submitted evaluations
        4. Render template
    """
    faculty = get_faculty_or_404(uuid, request.user)
    examination, auth = get_authorized_examination_or_404(faculty, exam_id)

    committee_members = auth.get_committee_members()
    my_evaluation = auth.get_my_evaluation()

    evaluations = examination.evaluations.select_related(
        "faculty",
        "faculty__user",
    ).order_by("faculty__user__first_name")

    submitted_evaluations = evaluations.filter(is_submitted=True)

    knowledge_avg = submitted_evaluations.aggregate(avg=Avg("knowledge_score"))["avg"]
    research_aptitude_avg = submitted_evaluations.aggregate(
        avg=Avg("research_aptitude_score")
    )["avg"]
    presentation_avg = submitted_evaluations.aggregate(avg=Avg("presentation_score"))[
        "avg"
    ]
    technical_avg = submitted_evaluations.aggregate(avg=Avg("technical_score"))["avg"]

    examination_content_type = ContentType.objects.get_for_model(examination)

    video_evidence = (
        PhDVideoEvidence.objects.filter(
            phd_student=examination.phd_student,
            evidence_type="PRELIMINARY_EXAMINATION",
            target_content_type=examination_content_type,
            target_object_id=examination.pk,
        )
        .select_related("uploaded_by")
        .first()
    )

    context = {
        "faculty": faculty,
        "examination": examination,
        "committee_members": committee_members,
        "evaluations": evaluations,
        "my_evaluation": my_evaluation,
        "is_chair": auth.is_chair,
        "is_committee_member": auth.is_committee_member,
        "is_advisor": auth.is_advisor,
        "can_publish": auth.can_publish(),
        "can_enter_result": auth.can_declare_result(),
        "can_evaluate": auth.can_evaluate(),
        "evaluation_submitted": auth.has_submitted_evaluation(),
        "can_view_evaluation": auth.can_view_evaluation(),
        "total_evaluations": evaluations.count(),
        "knowledge_avg": knowledge_avg,
        "research_aptitude_avg": research_aptitude_avg,
        "presentation_avg": presentation_avg,
        "technical_avg": technical_avg,
        "video_evidence": video_evidence,
    }

    return render(
        request,
        "leo/PreliminaryExam/exam_detail.html",
        context,
    )

@login_required
def faculty_preliminary_exam_update(request, uuid, exam_id):
    """
    Update an existing preliminary examination.

    Purpose:
        Allow chair faculty to modify examination details.

    Parameters:
        request: HTTP request object
        uuid: UUID of the faculty member
        exam_id: ID of the preliminary examination

    Returns:
        Rendered template with examination update form

    Workflow:
        1. Get faculty and chair-authorized examination
        2. Verify edit permission
        3. Handle POST - update examination
        4. Handle GET - display form
        5. Render template
    """
    faculty = get_faculty_or_404(uuid, request.user)
    examination, auth = get_chair_examination_or_404(faculty, exam_id)

    if not auth.can_edit():
        messages.warning(
            request,
            f"{examination.get_status_display()} examinations cannot be edited.",
        )
        return redirect(
            "faculty_preliminary_exam_detail",
            uuid=faculty.user.uuid,
            exam_id=examination.prelim_exam_id,
        )

    if request.method == "POST":
        form = PreliminaryExaminationForm(
            request.POST,
            instance=examination,
            faculty=faculty,
        )

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Preliminary examination updated successfully.",
            )
            return redirect(
                "faculty_preliminary_exam_list",
                uuid=faculty.user.uuid,
            )

        messages.error(
            request,
            "Please correct the errors below and try again.",
        )

    else:
        form = PreliminaryExaminationForm(
            instance=examination,
            faculty=faculty,
        )

    context = {
        "faculty": faculty,
        "examination": examination,
        "form": form,
    }

    return render(
        request,
        "leo/PreliminaryExam/exam_update.html",
        context,
    )


@login_required
def faculty_preliminary_exam_delete(request, uuid, exam_id):
    """
    Delete a preliminary examination.

    Purpose:
        Allow chair faculty to delete examinations that haven't been published or completed.

    Parameters:
        request: HTTP request object
        uuid: UUID of the faculty member
        exam_id: ID of the preliminary examination

    Returns:
        Redirect to examination list

    Workflow:
        1. Validate request method
        2. Get faculty and chair-authorized examination
        3. Verify delete permission
        4. Delete examination
        5. Redirect with success message
    """
    faculty = get_faculty_or_404(uuid, request.user)

    if request.method != "POST":
        messages.warning(request, "Invalid request.")
        return redirect(
            "faculty_preliminary_exam_list",
            uuid=faculty.user.uuid,
        )

    examination, auth = get_chair_examination_or_404(faculty, exam_id)

    if not auth.can_delete():
        if examination.is_published:
            messages.warning(request, "Published examinations cannot be deleted.")
        elif examination.status == "COMPLETED":
            messages.warning(request, "Completed examinations cannot be deleted.")
        else:
            messages.warning(request, "This examination cannot be deleted.")
        return redirect(
            "faculty_preliminary_exam_detail",
            uuid=faculty.user.uuid,
            exam_id=examination.prelim_exam_id,
        )

    examination.delete()
    messages.success(request, "Preliminary examination deleted successfully.")

    return redirect(
        "faculty_preliminary_exam_list",
        uuid=faculty.user.uuid,
    )


def _create_preliminary_exam_notification(
    user,
    title,
    message,
    notification_type="INFO",
    link="",
):
    if not user:
        return

    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link or "",
        is_read=False,
    )

    payload = {
        "id": notification.pk,
        "title": notification.title,
        "message": notification.message,
        "type": notification.notification_type,
        "link": notification.link,
        "is_read": notification.is_read,
        "created_at": notification.created_at.isoformat(),
    }

    transaction.on_commit(
        lambda user_id=user.pk, payload=payload: send_notification(
            user_id,
            payload,
            event="preliminary_exam_update",
        )
    )


@login_required
def faculty_preliminary_exam_publish(request, uuid, exam_id):
    faculty = get_faculty_or_404(
        uuid,
        request.user,
    )

    if request.method != "POST":
        messages.warning(
            request,
            "Invalid request method.",
        )
        return redirect(
            "faculty_preliminary_exam_list",
            uuid=faculty.user.uuid,
        )

    examination, auth = get_chair_examination_or_404(
        faculty,
        exam_id,
    )

    if not auth.can_publish():
        if examination.is_published:
            messages.warning(
                request,
                "This examination has already been published.",
            )
        elif examination.status == "CANCELLED":
            messages.error(
                request,
                "Cancelled examinations cannot be published.",
            )
        elif examination.status == "COMPLETED":
            messages.error(
                request,
                "Completed examinations cannot be published.",
            )
        else:
            messages.error(
                request,
                "Please complete all mandatory examination details before publishing.",
            )

        return redirect(
            "faculty_preliminary_exam_detail",
            uuid=faculty.user.uuid,
            exam_id=examination.prelim_exam_id,
        )

    try:
        with transaction.atomic():
            examination.is_published = True

            if examination.status == "DRAFT":
                examination.status = "SCHEDULED"

            examination.save(
                update_fields=[
                    "is_published",
                    "status",
                ]
            )

            phd_student = examination.phd_student

            student_user = None

            if phd_student and phd_student.student_id and phd_student.student.user_id:
                student_user = phd_student.student.user

            advisor_user = None

            advisor = getattr(
                phd_student,
                "advisor",
                None,
            )

            if advisor and advisor.user_id:
                advisor_user = advisor.user

            student_name = (
                phd_student.student.user.get_full_name()
                if (
                    phd_student
                    and phd_student.student_id
                    and phd_student.student.user_id
                )
                else "the PhD student"
            )

            exam_date = examination.exam_date.strftime("%B %d, %Y")

            start_time = examination.start_time.strftime("%I:%M %p")

            end_time = examination.end_time.strftime("%I:%M %p")

            venue = examination.venue or "the scheduled venue"

            exam_schedule = (
                f"{exam_date} from {start_time} to {end_time} " f"at {venue}"
            )

            recipients = {}

            if student_user:
                recipients[student_user.pk] = (
                    student_user,
                    "Your Preliminary Examination has been scheduled.",
                    (
                        f"Your preliminary examination "
                        f"'{examination.title}' has been scheduled for "
                        f"{exam_schedule}."
                    ),
                )

            if advisor_user:
                recipients[advisor_user.pk] = (
                    advisor_user,
                    "Preliminary Examination Scheduled",
                    (
                        f"The preliminary examination for "
                        f"{student_name} has been scheduled for "
                        f"{exam_schedule}."
                    ),
                )

            for (
                recipient_user,
                notification_title,
                notification_message,
            ) in recipients.values():
                _create_preliminary_exam_notification(
                    user=recipient_user,
                    title=notification_title,
                    message=notification_message,
                    notification_type="INFO",
                )

        messages.success(
            request,
            "Preliminary examination published successfully.",
        )

    except Exception as e:
        messages.error(
            request,
            f"Unable to publish examination. {e}",
        )

    return redirect(
        "faculty_preliminary_exam_detail",
        uuid=faculty.user.uuid,
        exam_id=examination.prelim_exam_id,
    )


@login_required
def faculty_preliminary_exam_result(
    request,
    uuid,
    exam_id,
):
    faculty = get_faculty_or_404(
        uuid,
        request.user,
    )

    examination, auth = get_chair_examination_or_404(
        faculty,
        exam_id,
    )

    if not auth.can_declare_result():
        if examination.status == "COMPLETED":
            messages.warning(
                request,
                "Result has already been declared for this examination.",
            )
        else:
            messages.error(
                request,
                (
                    "Result cannot be declared at this time. "
                    "All evaluators must submit."
                ),
            )

        return redirect(
            "faculty_preliminary_exam_detail",
            uuid=faculty.user.uuid,
            exam_id=examination.prelim_exam_id,
        )

    evaluations = examination.evaluations.select_related(
        "faculty",
        "faculty__user",
    ).order_by(
        "faculty__user__first_name",
    )

    required_evaluator_ids = auth.get_required_evaluators()

    required_count = len(required_evaluator_ids)

    submitted_evals = evaluations.filter(
        faculty_id__in=required_evaluator_ids,
        is_submitted=True,
    )

    if request.method == "POST":
        result = request.POST.get(
            "result",
        )

        remarks = request.POST.get(
            "remarks",
            "",
        )

        if not result:
            messages.error(
                request,
                "Please select a result.",
            )

            return redirect(
                "faculty_preliminary_exam_result",
                uuid=faculty.user.uuid,
                exam_id=examination.prelim_exam_id,
            )

        if submitted_evals.count() != required_count:
            messages.error(
                request,
                (
                    "Cannot declare result. "
                    "Some evaluators have not submitted "
                    "their evaluations."
                ),
            )

            return redirect(
                "faculty_preliminary_exam_result",
                uuid=faculty.user.uuid,
                exam_id=examination.prelim_exam_id,
            )

        if submitted_evals.filter(
            recommendation__isnull=True,
        ).exists():
            messages.error(
                request,
                (
                    "Cannot declare result. "
                    "Some evaluators have not provided "
                    "a recommendation."
                ),
            )

            return redirect(
                "faculty_preliminary_exam_result",
                uuid=faculty.user.uuid,
                exam_id=examination.prelim_exam_id,
            )

        try:
            with transaction.atomic():
                examination.result = result
                examination.remarks = remarks
                examination.status = "COMPLETED"

                examination.save(
                    update_fields=[
                        "result",
                        "remarks",
                        "status",
                    ]
                )

                transaction.on_commit(
                    lambda examination_id=examination.prelim_exam_id: _notify_preliminary_exam_result(
                        examination=PreliminaryExamination.objects.select_related(
                            "phd_student",
                            "phd_student__student",
                            "phd_student__student__user",
                            "phd_student__advisor",
                            "phd_student__advisor__user",
                        ).get(
                            pk=examination_id,
                        )
                    )
                )

            messages.success(
                request,
                "Examination result declared successfully.",
            )

        except Exception as e:
            messages.error(
                request,
                f"Unable to declare examination result. {e}",
            )

        return redirect(
            "faculty_preliminary_exam_detail",
            uuid=faculty.user.uuid,
            exam_id=examination.prelim_exam_id,
        )

    recommendations = submitted_evals.values_list(
        "recommendation",
        flat=True,
    )

    pass_recommendations = sum(
        1
        for recommendation in recommendations
        if recommendation == "PASS"
    )

    fail_recommendations = sum(
        1
        for recommendation in recommendations
        if recommendation == "FAIL"
    )

    revision_recommendations = sum(
        1
        for recommendation in recommendations
        if recommendation == "REVISION"
    )

    context = {
        "faculty": faculty,
        "examination": examination,
        "evaluations": evaluations,
        "total_evaluations": evaluations.count(),
        "submitted_evaluations": submitted_evals.count(),
        "pass_recommendations": pass_recommendations,
        "fail_recommendations": fail_recommendations,
        "revision_recommendations": revision_recommendations,
        "required_evaluators_count": required_count,
        "can_submit_result": True,
        "all_submitted": (
            submitted_evals.count() == required_count
        ),
    }

    return render(
        request,
        "leo/PreliminaryExam/exam_result.html",
        context,
    )

@login_required
def faculty_preliminary_exam_evaluation_ready(
    request,
    uuid,
    exam_id,
):
    faculty = get_faculty_or_404(
        uuid,
        request.user,
    )

    examination, auth = get_authorized_examination_or_404(
        faculty,
        exam_id,
    )

    if request.method != "GET":
        return JsonResponse(
            {
                "success": False,
                "message": "Invalid request method.",
            },
            status=405,
        )

    if not examination.is_published:
        return JsonResponse(
            {
                "success": False,
                "message": "This examination has not been published.",
            },
            status=400,
        )

    if examination.status != "SCHEDULED":
        return JsonResponse(
            {
                "success": False,
                "message": "This examination is not scheduled.",
            },
            status=400,
        )

    if examination.result != "PENDING":
        return JsonResponse(
            {
                "success": False,
                "message": "This examination is no longer pending.",
            },
            status=400,
        )

    if not examination.exam_date or not examination.end_time:
        return JsonResponse(
            {
                "success": False,
                "message": "Examination date or end time is not configured.",
            },
            status=400,
        )

    now = timezone.localtime()

    examination_end = timezone.make_aware(
        datetime.combine(
            examination.exam_date,
            examination.end_time,
        ),
        timezone.get_current_timezone(),
    )

    if now < examination_end:
        return JsonResponse(
            {
                "success": False,
                "ready": False,
                "message": "The examination has not ended yet.",
            }
        )

    _notify_preliminary_exam_ready_for_evaluation(
        examination=examination,
    )

    return JsonResponse(
        {
            "success": True,
            "ready": True,
            "message": "Examination is ready for evaluation.",
        }
    )

@login_required
def faculty_submit_preliminary_evaluation(
    request,
    uuid,
    exam_id,
):
    faculty = get_faculty_or_404(
        uuid,
        request.user,
    )

    examination, auth = get_authorized_examination_or_404(
        faculty,
        exam_id,
    )

    if not auth.can_evaluate():
        if auth.is_chair:
            messages.error(
                request,
                "Chair Faculty cannot evaluate examinations.",
            )
        elif examination.is_published and examination.status != "SCHEDULED":
            messages.error(
                request,
                (
                    "Evaluations can only be submitted for "
                    "scheduled examinations. "
                    f"Status: {examination.get_status_display()}"
                ),
            )
        elif not examination.is_published:
            messages.error(
                request,
                "This examination has not been published yet.",
            )
        elif examination.result != "PENDING":
            messages.error(
                request,
                "Evaluation is closed for this examination.",
            )
        elif auth.has_submitted_evaluation():
            messages.info(
                request,
                "You have already submitted your evaluation.",
            )
            return redirect(
                "faculty_view_preliminary_evaluation",
                uuid=faculty.user.uuid,
                exam_id=examination.prelim_exam_id,
            )
        else:
            messages.error(
                request,
                "You are not authorized to evaluate this examination.",
            )

        return redirect(
            "faculty_my_preliminary_examinations",
            uuid=faculty.user.uuid,
        )

    existing_evaluation, created = (
        PreliminaryExamEvaluation.objects.get_or_create(
            examination=examination,
            faculty=faculty,
            defaults={
                "knowledge_score": 0,
                "research_aptitude_score": 0,
                "presentation_score": 0,
                "technical_score": 0,
                "comments": "",
                "recommendation": "PASS",
                "is_submitted": False,
            },
        )
    )

    if existing_evaluation.is_submitted:
        messages.info(
            request,
            "You have already submitted your evaluation.",
        )
        return redirect(
            "faculty_view_preliminary_evaluation",
            uuid=faculty.user.uuid,
            exam_id=examination.prelim_exam_id,
        )

    if request.method == "POST":
        form = PreliminaryExamEvaluationForm(
            request.POST,
            instance=existing_evaluation,
            faculty=faculty,
            examination=examination,
        )

        if form.is_valid():
            with transaction.atomic():
                evaluation = form.save(
                    commit=False,
                )

                evaluation.examination = examination
                evaluation.faculty = faculty
                evaluation.is_submitted = True
                evaluation.save()

                required_evaluator_ids = (
                    auth.get_required_evaluators()
                )

                required_count = len(
                    required_evaluator_ids
                )

                submitted_count = (
                    PreliminaryExamEvaluation.objects.filter(
                        examination=examination,
                        faculty_id__in=required_evaluator_ids,
                        is_submitted=True,
                    ).count()
                )

                if (
                    required_count > 0
                    and submitted_count == required_count
                ):
                    committee = (
                        examination
                        .phd_student
                        .doctoral_committee
                    )

                    chair_user = None

                    if (
                        committee
                        and committee.chair_faculty
                        and committee.chair_faculty.user_id
                    ):
                        chair_user = (
                            committee
                            .chair_faculty
                            .user
                        )

                    if chair_user:
                        transaction.on_commit(
                            lambda examination_id=examination.prelim_exam_id,
                            chair_user=chair_user: _notify_chair_preliminary_exam_decision_ready(
                                examination=PreliminaryExamination.objects.select_related(
                                    "phd_student",
                                    "phd_student__student",
                                    "phd_student__student__user",
                                ).get(
                                    pk=examination_id,
                                ),
                                chair_user=chair_user,
                            )
                        )

            messages.success(
                request,
                "Your evaluation has been submitted successfully.",
            )

            return redirect(
                "faculty_view_preliminary_evaluation",
                uuid=faculty.user.uuid,
                exam_id=examination.prelim_exam_id,
            )

        messages.error(
            request,
            "Please correct the errors below.",
        )

    else:
        form = PreliminaryExamEvaluationForm(
            instance=existing_evaluation,
            faculty=faculty,
            examination=examination,
        )

    context = {
        "faculty": faculty,
        "examination": examination,
        "form": form,
        "evaluation": existing_evaluation,
        "is_advisor": auth.is_advisor,
        "is_committee_member": auth.is_committee_member,
    }

    return render(
        request,
        "leo/PreliminaryExam/exam_evaluate.html",
        context,
    )


def _notify_preliminary_exam_ready_for_evaluation(
    examination,
):
    title = "Preliminary Examination Ready for Review"

    exam_title = (
        examination.title
        or "Preliminary Examination"
    )

    exam_date = examination.exam_date.strftime(
        "%B %d, %Y"
    )

    start_time = (
        examination.start_time.strftime("%I:%M %p")
        if examination.start_time
        else ""
    )

    end_time = (
        examination.end_time.strftime("%I:%M %p")
        if examination.end_time
        else ""
    )

    venue = (
        examination.venue
        or "the scheduled venue"
    )

    message = (
        f"Your assigned examination "
        f"'{exam_title}' is ready for review. "
        f"The examination was scheduled on "
        f"{exam_date} from {start_time} to "
        f"{end_time} at {venue}."
    )

    phd_student = examination.phd_student

    if not phd_student:
        return

    committee = getattr(
        phd_student,
        "doctoral_committee",
        None,
    )

    if not committee:
        return

    recipients = {}

    committee_members = (
        committee.committee_members
        .select_related(
            "faculty",
            "faculty__user",
        )
    )

    for member in committee_members:
        evaluator = member.faculty

        if not evaluator:
            continue

        if (
            committee.chair_faculty_id
            and evaluator.pk == committee.chair_faculty_id
        ):
            continue

        if not evaluator.user_id:
            continue

        recipients[evaluator.user_id] = (
            evaluator.user
        )

    advisor = getattr(
        phd_student,
        "advisor",
        None,
    )

    if (
        advisor
        and advisor.pk != committee.chair_faculty_id
        and advisor.user_id
    ):
        recipients[advisor.user_id] = (
            advisor.user
        )

    for user in recipients.values():
        already_notified = (
            Notification.objects.filter(
                user=user,
                title=title,
                message=message,
            ).exists()
        )

        if already_notified:
            continue

        _create_preliminary_exam_notification(
            user=user,
            title=title,
            message=message,
            notification_type="INFO",
        )


def _notify_chair_preliminary_exam_decision_ready(
    examination,
    chair_user,
):
    if not chair_user:
        return

    title = (
        "Preliminary Examination Ready "
        "for Result Declaration"
    )

    student = examination.phd_student

    student_user = None

    if (
        student
        and student.student_id
        and student.student.user_id
    ):
        student_user = student.student.user

    student_name = (
        student_user.get_full_name()
        if student_user
        else "the PhD student"
    )

    exam_title = (
        examination.title
        or "Preliminary Examination"
    )

    message = (
        f"All required evaluations for the "
        f"preliminary examination "
        f"'{exam_title}' for "
        f"{student_name} have been completed. "
        f"The examination is ready for you "
        f"to declare the final result."
    )

    already_notified = (
        Notification.objects.filter(
            user=chair_user,
            title=title,
            message=message,
        ).exists()
    )

    if already_notified:
        return

    _create_preliminary_exam_notification(
        user=chair_user,
        title=title,
        message=message,
        notification_type="SUCCESS",
    )


def _notify_preliminary_exam_result(
    examination,
):
    student = examination.phd_student

    if not student:
        return

    recipients = {}

    student_user = None

    if (
        student.student_id
        and student.student.user_id
    ):
        student_user = student.student.user

    if student_user:
        recipients[student_user.pk] = (
            student_user
        )

    advisor = getattr(
        student,
        "advisor",
        None,
    )

    if (
        advisor
        and advisor.user_id
    ):
        recipients[advisor.user_id] = (
            advisor.user
        )

    if not recipients:
        return

    title = (
        "Preliminary Examination Results Published"
    )

    exam_title = (
        examination.title
        or "Preliminary Examination"
    )

    result_display = (
        examination.get_result_display()
        if examination.result
        else "Pending"
    )

    message = (
        f"The preliminary examination "
        f"'{exam_title}' has been completed. "
        f"The final result has been published: "
        f"{result_display}."
    )

    if examination.remarks:
        message = (
            f"{message} "
            f"Remarks: {examination.remarks}"
        )

    notification_type = "INFO"

    if examination.result == "PASS":
        notification_type = "SUCCESS"

    elif examination.result == "FAIL":
        notification_type = "ERROR"

    for user in recipients.values():
        already_notified = (
            Notification.objects.filter(
                user=user,
                title=title,
                message=message,
            ).exists()
        )

        if already_notified:
            continue

        _create_preliminary_exam_notification(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
        )


@login_required
def faculty_view_preliminary_evaluation(
    request,
    uuid,
    exam_id,
):
    faculty = get_faculty_or_404(
        uuid,
        request.user,
    )

    examination, auth = get_authorized_examination_or_404(
        faculty,
        exam_id,
    )

    evaluation = (
        PreliminaryExamEvaluation.objects.filter(
            examination=examination,
            faculty=faculty,
            is_submitted=True,
        )
        .select_related(
            "faculty",
            "faculty__user",
        )
        .first()
    )

    if evaluation is None:
        messages.error(
            request,
            "You have not submitted an evaluation for this examination.",
        )

        return redirect(
            "faculty_my_preliminary_examinations",
            uuid=faculty.user.uuid,
        )

    evaluations = (
        PreliminaryExamEvaluation.objects.filter(
            examination=examination,
            is_submitted=True,
        )
        .select_related(
            "faculty",
            "faculty__user",
        )
        .order_by(
            "submitted_at",
        )
    )

    average_score = round(
        (
            float(evaluation.knowledge_score or 0)
            + float(evaluation.research_aptitude_score or 0)
            + float(evaluation.presentation_score or 0)
            + float(evaluation.technical_score or 0)
        )
        / 4,
        2,
    )

    submitted_count = evaluations.count()

    context = {
        "faculty": faculty,
        "examination": examination,
        "evaluation": evaluation,
        "evaluations": evaluations,
        "average_score": average_score,
        "submitted_count": submitted_count,
        "auth": auth,
        "is_chair": auth.is_chair,
        "is_committee_member": auth.is_committee_member,
        "is_advisor": auth.is_advisor,
    }

    return render(
        request,
        "leo/PreliminaryExam/view_evaluation.html",
        context,
    )

###############################################################
# EXAM MODULE ENDS HERE
###############################################################

###############################################################
# DISSERTATION PROPOSAL MODULE IN FACULTY DASHBOARD
###############################################################


def _get_current_submission_number(proposal):
    return (
        getattr(
            proposal,
            "resubmission_count",
            0,
        )
        or 0
    ) + 1


# ============================================================
# Advisor Dissertation proposal list, detail and review
# ============================================================


@login_required
def faculty_advisor_dissertation_proposal_list(
    request,
    uuid,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
            "faculty_rank",
            "department",
        ),
        user__uuid=uuid,
        user=request.user,
    )

    proposals = (
        DissertationProposal.objects.select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__phd_program",
            "phd_student__doctoral_committee",
            "finalized_by",
            "finalized_by__user",
        )
        .filter(
            phd_student__advisor=faculty,
        )
        .order_by(
            "-submission_date",
            "-proposal_id",
        )
    )

    search = request.GET.get(
        "search",
        "",
    ).strip()

    if search:
        proposals = proposals.filter(
            Q(
                proposal_title__icontains=search,
            )
            | Q(
                phd_student__student__user__first_name__icontains=search,
            )
            | Q(
                phd_student__student__user__last_name__icontains=search,
            )
            | Q(
                phd_student__student__student_number__icontains=search,
            )
            | Q(
                phd_student__phd_program__program_name__icontains=search,
            )
        )

    proposal_list = list(proposals)

    for proposal in proposal_list:
        proposal.can_review = (
            proposal.status == "ADVISOR_REVIEW"
            and proposal.advisor_review_status == "PENDING"
        )

        proposal.review_completed = (
            proposal.advisor_review_status != "PENDING"
        )

        proposal.is_finalized = proposal.result != "PENDING"

        proposal.final_approved = proposal.result == "APPROVED"

        proposal.final_rejected = proposal.result == "REJECTED"

        proposal.final_revision_required = (
            proposal.result == "REVISION_REQUIRED"
        )

        proposal.final_result_label = {
            "APPROVED": "Approved",
            "REJECTED": "Rejected",
            "REVISION_REQUIRED": "Revision Required",
        }.get(
            proposal.result,
            "Pending Final Decision",
        )

    total_proposals = len(proposal_list)

    pending_review_count = sum(
        1
        for proposal in proposal_list
        if proposal.advisor_review_status == "PENDING"
    )

    reviewed_count = sum(
        1
        for proposal in proposal_list
        if proposal.advisor_review_status != "PENDING"
    )

    final_approved_count = sum(
        1
        for proposal in proposal_list
        if proposal.result == "APPROVED"
    )

    final_rejected_count = sum(
        1
        for proposal in proposal_list
        if proposal.result == "REJECTED"
    )

    final_revision_count = sum(
        1
        for proposal in proposal_list
        if proposal.result == "REVISION_REQUIRED"
    )

    attention_count = sum(
        1
        for proposal in proposal_list
        if (
            proposal.advisor_review_status == "REJECTED"
            or proposal.result == "REJECTED"
            or proposal.result == "REVISION_REQUIRED"
        )
    )

    context = {
        "faculty": faculty,
        "proposals": proposal_list,
        "search": search,
        "total_proposals": total_proposals,
        "pending_review_count": pending_review_count,
        "reviewed_count": reviewed_count,
        "attention_count": attention_count,
        "final_approved_count": final_approved_count,
        "final_rejected_count": final_rejected_count,
        "final_revision_count": final_revision_count,
    }

    return render(
        request,
        "leo/dissertation/advisor_dissertation_proposal_list.html",
        context,
    )


@login_required
def faculty_advisor_dissertation_proposal_detail(
    request,
    uuid,
    proposal_id,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
            "faculty_rank",
            "department",
        ),
        user__uuid=uuid,
        user=request.user,
    )

    proposal = get_object_or_404(
        DissertationProposal.objects.select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "phd_student__phd_program",
            "phd_student__doctoral_committee",
            "phd_student__doctoral_committee__chair_faculty",
            "phd_student__doctoral_committee__chair_faculty__user",
        ),
        proposal_id=proposal_id,
        phd_student__advisor=faculty,
    )

    committee = getattr(
        proposal.phd_student,
        "doctoral_committee",
        None,
    )

    committee_members = (
        CommitteeMember.objects.select_related(
            "faculty",
            "faculty__user",
            "faculty__faculty_rank",
            "faculty__department",
            "department",
        )
        .filter(
            committee=committee,
        )
        .exclude(
            role="CHAIR",
        )
        .order_by(
            "role",
            "faculty__user__first_name",
            "faculty__user__last_name",
        )
        if committee
        else CommitteeMember.objects.none()
    )

    current_submission_number = _get_current_submission_number(
        proposal,
    )

    evaluations = (
        DissertationProposalEvaluation.objects.filter(
            proposal=proposal,
            submission_number=current_submission_number,
            committee_member__committee=committee,
            is_submitted=True,
        )
        .select_related(
            "committee_member",
            "committee_member__faculty",
            "committee_member__faculty__user",
            "committee_member__faculty__faculty_rank",
            "committee_member__faculty__department",
            "committee_member__department",
        )
        .order_by(
            "-submitted_at",
            "evaluation_id",
        )
        if committee
        else DissertationProposalEvaluation.objects.none()
    )

    evaluations_required = committee_members.count() if committee else 0

    evaluations_completed = evaluations.count()

    evaluations_pending = max(
        evaluations_required - evaluations_completed,
        0,
    )

    evaluation_percentage = (
        int((evaluations_completed / evaluations_required) * 100)
        if evaluations_required > 0
        else 0
    )

    evaluation_ready_for_chair = (
        evaluations_required > 0
        and evaluations_completed >= evaluations_required
    )

    advisor_review_status = proposal.advisor_review_status or "PENDING"

    advisor_review_remarks = proposal.advisor_review_remarks or ""

    can_review = (
        advisor_review_status == "PENDING"
        and proposal.status == "ADVISOR_REVIEW"
    )

    review_completed = advisor_review_status != "PENDING"

    committee_evaluation_started = (
        proposal.status == "COMMITTEE_EVALUATION"
    )

    committee_evaluation_completed = evaluation_ready_for_chair

    final_decision_available = (
        proposal.status == "APPROVED"
        or proposal.status == "REJECTED"
        or proposal.status == "REVISION_REQUIRED"
    )

    proposal_content_type = ContentType.objects.get_for_model(
        proposal,
    )

    video_evidence = (
        PhDVideoEvidence.objects.filter(
            phd_student=proposal.phd_student,
            evidence_type="DISSERTATION_PROPOSAL",
            target_content_type=proposal_content_type,
            target_object_id=proposal.pk,
        )
        .select_related(
            "uploaded_by",
        )
        .first()
    )

    student = proposal.phd_student

    context = {
        "faculty": faculty,
        "proposal": proposal,
        "student": student,
        "committee": committee,
        "committee_members": committee_members,
        "advisor_review_status": advisor_review_status,
        "advisor_review_remarks": advisor_review_remarks,
        "can_review": can_review,
        "review_completed": review_completed,
        "evaluations": evaluations,
        "faculty_feedback": evaluations,
        "faculty_feedback_count": evaluations_completed,
        "evaluations_required": evaluations_required,
        "evaluations_completed": evaluations_completed,
        "evaluations_pending": evaluations_pending,
        "evaluation_percentage": evaluation_percentage,
        "evaluation_ready_for_chair": evaluation_ready_for_chair,
        "committee_evaluation_started": committee_evaluation_started,
        "committee_evaluation_completed": committee_evaluation_completed,
        "final_decision_available": final_decision_available,
        "current_submission_number": current_submission_number,
        "video_evidence": video_evidence,
    }

    return render(
        request,
        "leo/dissertation/advisor_dissertation_proposal_detail.html",
        context,
    )

def _create_dissertation_proposal_notification(
    user,
    title,
    message,
    notification_type="INFO",
    link="",
):
    if not user:
        return

    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link or "",
        is_read=False,
    )

    payload = {
        "id": notification.pk,
        "title": notification.title,
        "message": notification.message,
        "type": notification.notification_type,
        "link": notification.link,
        "is_read": notification.is_read,
        "created_at": notification.created_at.isoformat(),
    }

    transaction.on_commit(
        lambda user_id=user.pk, payload=payload: send_notification(
            user_id,
            payload,
            event="dissertation_proposal_update",
        )
    )

@login_required
def faculty_advisor_dissertation_proposal_review(
    request,
    uuid,
    proposal_id,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
            "faculty_rank",
            "department",
        ),
        user__uuid=uuid,
        user=request.user,
    )

    proposal = get_object_or_404(
        DissertationProposal.objects.select_related(
            "phd_student",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__phd_program",
            "phd_student__doctoral_committee",
            "phd_student__doctoral_committee__chair_faculty",
            "phd_student__doctoral_committee__chair_faculty__user",
        ),
        proposal_id=proposal_id,
        phd_student__advisor=faculty,
    )

    if proposal.status != "ADVISOR_REVIEW":
        messages.warning(
            request,
            "This proposal is not currently awaiting advisor review.",
        )

        return redirect(
            "faculty_advisor_dissertation_proposal_detail",
            uuid=uuid,
            proposal_id=proposal_id,
        )

    if proposal.advisor_review_status != "PENDING":
        messages.warning(
            request,
            "This proposal has already been reviewed.",
        )

        return redirect(
            "faculty_advisor_dissertation_proposal_detail",
            uuid=uuid,
            proposal_id=proposal_id,
        )

    if request.method == "GET":
        form = DissertationProposalAdvisorReviewForm(
            instance=proposal,
            faculty=faculty,
        )

        context = {
            "faculty": faculty,
            "proposal": proposal,
            "form": form,
        }

        return render(
            request,
            "leo/dissertation/advisor_dissertation_proposal_review.html",
            context,
        )

    form = DissertationProposalAdvisorReviewForm(
        request.POST,
        instance=proposal,
        faculty=faculty,
    )

    if not form.is_valid():
        context = {
            "faculty": faculty,
            "proposal": proposal,
            "form": form,
        }

        return render(
            request,
            "leo/dissertation/advisor_dissertation_proposal_review.html",
            context,
        )

    proposal = form.save(
        commit=False,
    )

    if proposal.advisor_review_status == "APPROVED":
        proposal.status = "COMMITTEE_EVALUATION"
        proposal.result = "PENDING"

    elif proposal.advisor_review_status == "REVISION_REQUIRED":
        proposal.status = "REVISION_REQUIRED"
        proposal.result = "REVISION_REQUIRED"

    elif proposal.advisor_review_status == "REJECTED":
        proposal.status = "REJECTED"
        proposal.result = "REJECTED"

    student_name = (
        proposal.phd_student.student.user.get_full_name().strip()
        or proposal.phd_student.student.user.username
    )

    advisor_name = (
        proposal.phd_student.advisor.user.get_full_name().strip()
        or proposal.phd_student.advisor.user.username
    )

    proposal_title = proposal.proposal_title.strip()

    with transaction.atomic():
        proposal.save(
            update_fields=[
                "advisor_review_status",
                "advisor_review_remarks",
                "advisor_reviewed_at",
                "status",
                "result",
            ]
        )

        if proposal.advisor_review_status == "APPROVED":
            committee = proposal.phd_student.doctoral_committee

            if committee:
                chair_faculty = committee.chair_faculty

                if chair_faculty and chair_faculty.user:
                    chair_name = (
                        chair_faculty.user.get_full_name().strip()
                        or chair_faculty.user.username
                    )

                    _create_dissertation_proposal_notification(
                        user=chair_faculty.user,
                        title="Dissertation Proposal Awaiting Committee Evaluation",
                        message=(
                            f"Dissertation proposal submitted by {student_name} "
                            f"has been approved by Advisor {advisor_name} "
                            f"and is now awaiting evaluation from the committee members. "
                            f"Proposal: {proposal_title}. "
                            f"Please wait for all committee evaluations to be completed "
                            f"before proceeding with the final approval."
                        ),
                        notification_type="INFO",
                    )

                committee_members = (
                    committee.committee_members
                    .select_related(
                        "faculty",
                        "faculty__user",
                    )
                    .exclude(
                        role="CHAIR",
                    )
                )

                for committee_member in committee_members:
                    if (
                        committee_member.faculty
                        and committee_member.faculty.user
                    ):
                        committee_member_name = (
                            committee_member.faculty.user.get_full_name().strip()
                            or committee_member.faculty.user.username
                        )

                        _create_dissertation_proposal_notification(
                            user=committee_member.faculty.user,
                            title="Dissertation Proposal Ready for Your Evaluation",
                            message=(
                                f"Dear {committee_member_name}, "
                                f"the dissertation proposal submitted by {student_name} "
                                f"has been approved by Advisor {advisor_name} "
                                f"and is now ready for your committee evaluation. "
                                f"Proposal: {proposal_title}. "
                                f"Please complete your evaluation to allow the committee "
                                f"to proceed with the final review."
                            ),
                            notification_type="INFO",
                        )

    if proposal.advisor_review_status == "APPROVED":
        messages.success(
            request,
            "Proposal approved successfully and moved to committee evaluation.",
        )

    elif proposal.advisor_review_status == "REVISION_REQUIRED":
        messages.warning(
            request,
            "Revision has been requested for this proposal.",
        )

    elif proposal.advisor_review_status == "REJECTED":
        messages.error(
            request,
            "Dissertation proposal has been rejected.",
        )

    return redirect(
        "faculty_advisor_dissertation_proposal_detail",
        uuid=uuid,
        proposal_id=proposal_id,
    )


# ============================================================
# Committee Dissertation proposal list
# ============================================================


@login_required
def faculty_committee_dissertation_proposal_list(
    request,
    uuid,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
            "faculty_rank",
            "department",
        ),
        user__uuid=uuid,
        user=request.user,
    )

    committee_memberships = (
        CommitteeMember.objects.select_related(
            "committee",
            "faculty",
        )
        .filter(
            faculty=faculty,
        )
        .exclude(
            role="CHAIR",
        )
    )

    chair_committees = DoctoralCommittee.objects.filter(
        chair_faculty=faculty,
    )

    is_committee_member = committee_memberships.exists()
    is_chair = chair_committees.exists()

    # if not is_committee_member and not is_chair:
    #     messages.error(
    #         request,
    #         "You are not authorized to access dissertation proposals.",
    #     )
    #     return redirect(
    #         "faculty_phd_management",
    #         uuid=uuid,
    #     )

    if is_chair:
        proposals = (
            DissertationProposal.objects.select_related(
                "phd_student",
                "phd_student__student",
                "phd_student__student__user",
                "phd_student__advisor",
                "phd_student__advisor__user",
                "phd_student__phd_program",
                "phd_student__doctoral_committee",
                "phd_student__doctoral_committee__chair_faculty",
                "phd_student__doctoral_committee__chair_faculty__user",
            )
            .filter(
                phd_student__doctoral_committee__chair_faculty=faculty,
            )
            .distinct()
            .order_by(
                "-submission_date",
                "-proposal_id",
            )
        )

    else:
        proposals = (
            DissertationProposal.objects.select_related(
                "phd_student",
                "phd_student__student",
                "phd_student__student__user",
                "phd_student__advisor",
                "phd_student__advisor__user",
                "phd_student__phd_program",
                "phd_student__doctoral_committee",
            )
            .filter(
                phd_student__doctoral_committee__committee_members__faculty=faculty,
                phd_student__doctoral_committee__committee_members__role__in=[
                    "CO_CHAIR",
                    "MEMBER",
                ],
            )
            .distinct()
            .order_by(
                "-submission_date",
                "-proposal_id",
            )
        )

    search = request.GET.get(
        "search",
        "",
    ).strip()

    status_filter = (
        request.GET.get(
            "status",
            "",
        )
        .strip()
        .upper()
    )

    if search:
        proposals = proposals.filter(
            Q(
                proposal_title__icontains=search,
            )
            | Q(
                phd_student__student__user__first_name__icontains=search,
            )
            | Q(
                phd_student__student__user__last_name__icontains=search,
            )
            | Q(
                phd_student__student__student_number__icontains=search,
            )
            | Q(
                status__icontains=search,
            )
        )

    total_proposals = proposals.count()

    pending_advisor_review = 0
    pending_committee_evaluation = 0
    completed_evaluations = 0
    revision_required = 0
    rejected_proposals = 0
    final_review_proposals = 0
    approved_proposals = 0

    for proposal in proposals:
        committee = getattr(
            proposal.phd_student,
            "doctoral_committee",
            None,
        )

        proposal.is_chair = is_chair

        proposal.is_committee_member = (
            not is_chair
            and committee_memberships.filter(
                committee=committee,
            ).exists()
        )

        proposal.current_submission_number = (
            _get_current_submission_number(
                proposal,
            )
        )

        proposal.evaluation = None

        proposal.can_evaluate = False

        proposal.evaluation_completed = False

        proposal.committee_role = (
            "Chair Faculty" if is_chair else "Committee Member"
        )

        proposal.total_members = 0

        proposal.submitted_members = 0

        proposal.pending_members = 0

        proposal.advisor_review_completed = (
            proposal.advisor_review_status != "PENDING"
        )

        proposal.advisor_approved = (
            proposal.advisor_review_status == "APPROVED"
        )

        proposal.is_waiting_for_advisor = (
            proposal.advisor_review_status == "PENDING"
            and proposal.status
            in [
                "DRAFT",
                "SUBMITTED",
                "ADVISOR_REVIEW",
            ]
        )

        proposal.is_waiting_for_committee = (
            proposal.status == "COMMITTEE_EVALUATION"
        )

        proposal.is_final_review = proposal.status == "FINAL_REVIEW"

        proposal.is_revision_required = (
            proposal.status == "REVISION_REQUIRED"
        )

        proposal.is_rejected = proposal.status == "REJECTED"

        proposal.is_approved = proposal.status == "APPROVED"

        if proposal.is_waiting_for_advisor:
            pending_advisor_review += 1

        if proposal.is_revision_required:
            revision_required += 1

        if proposal.is_rejected:
            rejected_proposals += 1

        if proposal.is_final_review:
            final_review_proposals += 1

        if proposal.is_approved:
            approved_proposals += 1

        if committee:
            evaluation_members = committee.committee_members.exclude(
                role="CHAIR",
            )

            proposal.total_members = evaluation_members.count()

            proposal.submitted_members = (
                DissertationProposalEvaluation.objects.filter(
                    proposal=proposal,
                    submission_number=proposal.current_submission_number,
                    committee_member__in=evaluation_members,
                    is_submitted=True,
                )
                .values(
                    "committee_member_id",
                )
                .distinct()
                .count()
            )

            proposal.pending_members = max(
                proposal.total_members - proposal.submitted_members,
                0,
            )

        if proposal.is_committee_member:
            committee_member = committee_memberships.filter(
                committee=committee,
            ).first()

            if committee_member:
                proposal.committee_role = (
                    committee_member.get_role_display()
                )

                proposal.evaluation = (
                    DissertationProposalEvaluation.objects.filter(
                        proposal=proposal,
                        submission_number=proposal.current_submission_number,
                        committee_member=committee_member,
                    )
                    .order_by(
                        "-evaluation_id",
                    )
                    .first()
                )

                proposal.evaluation_completed = bool(
                    proposal.evaluation
                    and proposal.evaluation.is_submitted
                )

                proposal.can_evaluate = (
                    proposal.status == "COMMITTEE_EVALUATION"
                    and proposal.advisor_review_status == "APPROVED"
                    and not proposal.evaluation_completed
                )

                if proposal.can_evaluate:
                    pending_committee_evaluation += 1

                if proposal.evaluation_completed:
                    completed_evaluations += 1

        elif is_chair:
            proposal.committee_evaluation_completed = (
                proposal.total_members > 0
                and proposal.submitted_members == proposal.total_members
            )

            if proposal.committee_evaluation_completed:
                completed_evaluations += 1

            elif (
                proposal.status == "COMMITTEE_EVALUATION"
                and proposal.pending_members > 0
            ):
                pending_committee_evaluation += 1

    if status_filter == "PENDING_ADVISOR":
        proposals = [
            proposal
            for proposal in proposals
            if proposal.is_waiting_for_advisor
        ]

    elif status_filter == "PENDING_COMMITTEE":
        proposals = [
            proposal
            for proposal in proposals
            if (
                proposal.is_waiting_for_committee
                and (
                    (
                        proposal.is_committee_member
                        and not proposal.evaluation_completed
                    )
                    or (
                        proposal.is_chair
                        and proposal.pending_members > 0
                    )
                )
            )
        ]

    elif status_filter == "COMPLETED":
        proposals = [
            proposal
            for proposal in proposals
            if proposal.evaluation_completed
        ]

    elif status_filter == "FINAL_REVIEW":
        proposals = [
            proposal
            for proposal in proposals
            if proposal.is_final_review
        ]

    elif status_filter == "REVISION_REQUIRED":
        proposals = [
            proposal
            for proposal in proposals
            if proposal.is_revision_required
        ]

    elif status_filter == "REJECTED":
        proposals = [
            proposal
            for proposal in proposals
            if proposal.is_rejected
        ]

    elif status_filter == "APPROVED":
        proposals = [
            proposal
            for proposal in proposals
            if proposal.is_approved
        ]

    filtered_total = len(proposals)

    context = {
        "faculty": faculty,
        "proposals": proposals,
        "search": search,
        "status_filter": status_filter,
        "total_proposals": total_proposals,
        "filtered_total": filtered_total,
        "pending_advisor_review": pending_advisor_review,
        "pending_committee_evaluation": pending_committee_evaluation,
        "completed_evaluations": completed_evaluations,
        "revision_required": revision_required,
        "rejected_proposals": rejected_proposals,
        "final_review_proposals": final_review_proposals,
        "approved_proposals": approved_proposals,
        "is_chair": is_chair,
        "is_committee_member": is_committee_member,
    }

    return render(
        request,
        "leo/dissertation/committee_dissertation_proposal_list.html",
        context,
    )


# ============================================================
# Committee Dissertation proposal Detail and Evaluation
# ============================================================


@login_required
def faculty_committee_dissertation_proposal_detail(
    request,
    uuid,
    proposal_id,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
        ),
        user__uuid=uuid,
        user=request.user,
    )

    proposal = get_object_or_404(
        DissertationProposal.objects.select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__phd_program",
            "phd_student__phd_program__department",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "phd_student__doctoral_committee",
            "phd_student__doctoral_committee__chair_faculty",
            "phd_student__doctoral_committee__chair_faculty__user",
        ),
        proposal_id=proposal_id,
    )

    committee = getattr(
        proposal.phd_student,
        "doctoral_committee",
        None,
    )

    if not committee:
        messages.error(
            request,
            "No doctoral committee is associated with this dissertation proposal.",
        )
        return redirect(
            "faculty_committee_dissertation_proposal_list",
            uuid=uuid,
        )

    if committee.approval_status != "APPROVED":
        messages.error(
            request,
            "The doctoral committee has not been approved.",
        )
        return redirect(
            "faculty_committee_dissertation_proposal_list",
            uuid=uuid,
        )

    is_chair = committee.chair_faculty == faculty

    committee_member = (
        CommitteeMember.objects.select_related(
            "faculty",
            "faculty__user",
            "faculty__faculty_rank",
            "faculty__department",
        )
        .filter(
            committee=committee,
            faculty=faculty,
        )
        .first()
    )

    is_committee_member = (
        committee_member is not None
        and committee_member.role != "CHAIR"
    )

    if not is_chair and not is_committee_member:
        messages.error(
            request,
            "You are not authorized to access this dissertation proposal.",
        )
        return redirect(
            "faculty_committee_dissertation_proposal_list",
            uuid=uuid,
        )

    if is_chair:
        committee_member = None
        is_committee_member = False

    latest_resubmission_request = (
        DissertationProposalResubmissionRequest.objects.filter(
            proposal=proposal,
        )
        .select_related(
            "reviewed_by",
            "reviewed_by__user",
        )
        .order_by(
            "-requested_at",
            "-request_id",
        )
        .first()
    )

    pending_resubmission_request = (
        DissertationProposalResubmissionRequest.objects.filter(
            proposal=proposal,
            status="PENDING",
        )
        .order_by(
            "-requested_at",
            "-request_id",
        )
        .first()
    )

    if request.method == "POST":
        action = request.POST.get(
            "action",
            "",
        ).strip()

        if action == "approve_resubmission":
            if not is_chair:
                messages.error(
                    request,
                    "Only the Chair Faculty can grant a second chance.",
                )
                return redirect(
                    "faculty_committee_dissertation_proposal_detail",
                    uuid=uuid,
                    proposal_id=proposal_id,
                )

            with transaction.atomic():
                locked_proposal = get_object_or_404(
                    DissertationProposal.objects.select_for_update(),
                    proposal_id=proposal_id,
                )

                locked_committee = getattr(
                    locked_proposal.phd_student,
                    "doctoral_committee",
                    None,
                )

                if (
                    not locked_committee
                    or locked_committee.chair_faculty_id != faculty.pk
                ):
                    messages.error(
                        request,
                        "Only the Chair Faculty can grant a second chance.",
                    )
                    return redirect(
                        "faculty_committee_dissertation_proposal_detail",
                        uuid=uuid,
                        proposal_id=proposal_id,
                    )

                request_record = (
                    DissertationProposalResubmissionRequest.objects.select_for_update()
                    .filter(
                        proposal=locked_proposal,
                        status="PENDING",
                    )
                    .order_by(
                        "-requested_at",
                        "-request_id",
                    )
                    .first()
                )

                if not request_record:
                    messages.info(
                        request,
                        "There is no pending resubmission request to approve.",
                    )
                    return redirect(
                        "faculty_committee_dissertation_proposal_detail",
                        uuid=uuid,
                        proposal_id=proposal_id,
                    )

                review_remarks = request.POST.get(
                    "review_remarks",
                    "",
                ).strip()

                request_record.status = "APPROVED"
                request_record.reviewed_by = faculty
                request_record.review_remarks = review_remarks
                request_record.reviewed_at = timezone.now()

                request_record.save(
                    update_fields=[
                        "status",
                        "reviewed_by",
                        "review_remarks",
                        "reviewed_at",
                        "updated_at",
                    ]
                )

                locked_proposal.status = "REVISION_REQUIRED"

                locked_proposal.save(
                    update_fields=[
                        "status",
                    ]
                )

            messages.success(
                request,
                "Second chance granted successfully. The student can now "
                "revise and resubmit the dissertation proposal.",
            )

            return redirect(
                "faculty_committee_dissertation_proposal_detail",
                uuid=uuid,
                proposal_id=proposal_id,
            )

        messages.error(
            request,
            "Invalid academic action.",
        )

        return redirect(
            "faculty_committee_dissertation_proposal_detail",
            uuid=uuid,
            proposal_id=proposal_id,
        )

    current_submission_number = _get_current_submission_number(
        proposal,
    )

    proposal_content_type = ContentType.objects.get_for_model(
        proposal,
    )

    video_evidence = (
        PhDVideoEvidence.objects.filter(
            phd_student=proposal.phd_student,
            evidence_type="DISSERTATION_PROPOSAL",
            target_content_type=proposal_content_type,
            target_object_id=proposal.pk,
        )
        .select_related(
            "uploaded_by",
        )
        .first()
    )

    evaluation_members = committee.committee_members.exclude(
        role="CHAIR",
    )

    evaluations = (
        DissertationProposalEvaluation.objects.filter(
            proposal=proposal,
            submission_number=current_submission_number,
            committee_member__in=evaluation_members,
        )
        .select_related(
            "committee_member",
            "committee_member__faculty",
            "committee_member__faculty__user",
            "committee_member__faculty__faculty_rank",
            "committee_member__faculty__department",
        )
        .order_by(
            "-submitted_at",
            "evaluation_id",
        )
    )

    evaluations_required = evaluation_members.count()

    submitted_evaluations = list(
        evaluations.filter(
            is_submitted=True,
        )
    )

    evaluations_completed = len(
        submitted_evaluations,
    )

    evaluations_pending = max(
        evaluations_required - evaluations_completed,
        0,
    )

    evaluation_percentage = (
        int((evaluations_completed / evaluations_required) * 100)
        if evaluations_required
        else 0
    )

    evaluation_ready_for_chair = (
        proposal.status == "FINAL_REVIEW"
        and evaluations_required > 0
        and evaluations_completed == evaluations_required
    )

    my_evaluation = None
    my_evaluation_submitted = False

    if committee_member:
        my_evaluation = evaluations.filter(
            committee_member=committee_member,
        ).first()

        my_evaluation_submitted = bool(
            my_evaluation and my_evaluation.is_submitted
        )

    committee_evaluation_allowed = (
        is_committee_member
        and proposal.status == "COMMITTEE_EVALUATION"
        and proposal.advisor_review_status == "APPROVED"
        and not my_evaluation_submitted
    )

    student = proposal.phd_student

    student_name = str(
        student.student,
    )

    student_id = getattr(
        student.student,
        "student_number",
        None,
    )

    program_name = (
        str(student.phd_program) if student.phd_program else None
    )

    department_name = None

    if student.phd_program:
        department = getattr(
            student.phd_program,
            "department",
            None,
        )

        if department:
            department_name = str(
                department,
            )

    advisor = student.advisor

    advisor_name = str(advisor) if advisor else "Advisor"

    advisor_review_status = (
        getattr(
            proposal,
            "advisor_review_status",
            None,
        )
        or "PENDING"
    )

    advisor_review_comments = (
        getattr(
            proposal,
            "advisor_review_comments",
            "",
        )
        or ""
    )

    can_grant_second_chance = (
        is_chair
        and proposal.status == "REJECTED"
        and pending_resubmission_request is not None
    )

    final_result = (
        getattr(
            proposal,
            "result",
            "PENDING",
        )
        or "PENDING"
    )

    finalised = final_result != "PENDING"

    context = {
        "uuid": uuid,
        "faculty": faculty,
        "video_evidence": video_evidence,
        "proposal": proposal,
        "committee": committee,
        "committee_member": committee_member,
        "student": student,
        "student_name": student_name,
        "student_id": student_id,
        "program_name": program_name,
        "department_name": department_name,
        "advisor_name": advisor_name,
        "advisor_review_status": advisor_review_status,
        "advisor_review_comments": advisor_review_comments,
        "my_evaluation": my_evaluation,
        "my_evaluation_submitted": my_evaluation_submitted,
        "committee_evaluation_allowed": committee_evaluation_allowed,
        "evaluations": evaluations,
        "submitted_evaluations": submitted_evaluations,
        "faculty_feedback": submitted_evaluations,
        "faculty_feedback_count": len(
            submitted_evaluations,
        ),
        "evaluations_required": evaluations_required,
        "evaluations_completed": evaluations_completed,
        "evaluations_pending": evaluations_pending,
        "evaluation_percentage": evaluation_percentage,
        "evaluation_ready_for_chair": evaluation_ready_for_chair,
        "is_chair": is_chair,
        "is_committee_member": is_committee_member,
        "latest_resubmission_request": latest_resubmission_request,
        "pending_resubmission_request": pending_resubmission_request,
        "can_grant_second_chance": can_grant_second_chance,
        "current_submission_number": current_submission_number,
        "finalised": finalised,
        "final_result": final_result,
    }

    return render(
        request,
        "leo/dissertation/committee_dissertation_proposal_detail.html",
        context,
    )

@login_required
def faculty_committee_dissertation_proposal_evaluate(
    request,
    uuid,
    proposal_id,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
        ),
        user__uuid=uuid,
        user=request.user,
    )

    proposal = get_object_or_404(
        DissertationProposal.objects.select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "phd_student__phd_program",
            "phd_student__doctoral_committee",
            "phd_student__doctoral_committee__chair_faculty",
            "phd_student__doctoral_committee__chair_faculty__user",
        ),
        proposal_id=proposal_id,
        status="COMMITTEE_EVALUATION",
        phd_student__doctoral_committee__committee_members__faculty=faculty,
        phd_student__doctoral_committee__approval_status="APPROVED",
    )

    committee = proposal.phd_student.doctoral_committee

    current_submission_number = _get_current_submission_number(
        proposal,
    )

    committee_member = get_object_or_404(
        CommitteeMember.objects.select_related(
            "faculty",
            "faculty__user",
        ).exclude(
            role="CHAIR",
        ),
        committee=committee,
        faculty=faculty,
    )

    evaluation = (
        DissertationProposalEvaluation.objects.filter(
            proposal=proposal,
            committee_member=committee_member,
            submission_number=current_submission_number,
        )
        .order_by(
            "-evaluation_id",
        )
        .first()
    )

    if evaluation and evaluation.is_submitted:
        messages.info(
            request,
            "Your evaluation has already been submitted for this submission.",
        )

        return redirect(
            "faculty_committee_dissertation_proposal_detail",
            uuid=uuid,
            proposal_id=proposal_id,
        )

    if request.method != "POST":
        return render(
            request,
            "leo/dissertation/committee_dissertation_proposal_review.html",
            {
                "uuid": uuid,
                "faculty": faculty,
                "proposal": proposal,
                "committee": committee,
                "committee_member": committee_member,
                "evaluation": evaluation,
                "current_submission_number": current_submission_number,
            },
        )

    score = request.POST.get(
        "score",
    )

    recommendation = request.POST.get(
        "recommendation",
        "",
    ).strip()

    comments = request.POST.get(
        "comments",
        "",
    ).strip()

    try:
        score = float(
            score,
        )
    except (
        TypeError,
        ValueError,
    ):
        messages.error(
            request,
            "Please enter a valid evaluation score.",
        )

        return redirect(
            "faculty_committee_dissertation_proposal_evaluate",
            uuid=uuid,
            proposal_id=proposal_id,
        )

    if score < 0 or score > 100:
        messages.error(
            request,
            "Evaluation score must be between 0 and 100.",
        )

        return redirect(
            "faculty_committee_dissertation_proposal_evaluate",
            uuid=uuid,
            proposal_id=proposal_id,
        )

    if not recommendation:
        messages.error(
            request,
            "Please select a recommendation.",
        )

        return redirect(
            "faculty_committee_dissertation_proposal_evaluate",
            uuid=uuid,
            proposal_id=proposal_id,
        )

    if len(comments) < 20:
        messages.error(
            request,
            "Evaluation comments must contain at least 20 characters.",
        )

        return redirect(
            "faculty_committee_dissertation_proposal_evaluate",
            uuid=uuid,
            proposal_id=proposal_id,
        )

    if len(comments) > 5000:
        messages.error(
            request,
            "Evaluation comments cannot exceed 5000 characters.",
        )

        return redirect(
            "faculty_committee_dissertation_proposal_evaluate",
            uuid=uuid,
            proposal_id=proposal_id,
        )

    all_evaluations_completed = False

    with transaction.atomic():
        locked_proposal = (
            DissertationProposal.objects.select_for_update()
            .select_related(
                "phd_student",
                "phd_student__student",
                "phd_student__student__user",
                "phd_student__advisor",
                "phd_student__advisor__user",
                "phd_student__doctoral_committee",
                "phd_student__doctoral_committee__chair_faculty",
                "phd_student__doctoral_committee__chair_faculty__user",
            )
            .get(
                proposal_id=proposal_id,
            )
        )

        if locked_proposal.status != "COMMITTEE_EVALUATION":
            messages.error(
                request,
                "This dissertation proposal is no longer open for committee evaluation.",
            )

            return redirect(
                "faculty_committee_dissertation_proposal_detail",
                uuid=uuid,
                proposal_id=proposal_id,
            )

        current_submission_number = _get_current_submission_number(
            locked_proposal,
        )

        evaluation = (
            DissertationProposalEvaluation.objects.select_for_update()
            .filter(
                proposal=locked_proposal,
                committee_member=committee_member,
                submission_number=current_submission_number,
            )
            .order_by(
                "-evaluation_id",
            )
            .first()
        )

        if evaluation and evaluation.is_submitted:
            messages.info(
                request,
                "Your evaluation has already been submitted for this submission.",
            )

            return redirect(
                "faculty_committee_dissertation_proposal_detail",
                uuid=uuid,
                proposal_id=proposal_id,
            )

        if evaluation is None:
            evaluation = DissertationProposalEvaluation(
                proposal=locked_proposal,
                committee_member=committee_member,
                submission_number=current_submission_number,
            )

        evaluation.score = score
        evaluation.recommendation = recommendation
        evaluation.comments = comments
        evaluation.is_submitted = True
        evaluation.submitted_at = timezone.now()

        evaluation.save(
            force_insert=evaluation.pk is None,
        )

        evaluation_members = (
            locked_proposal.phd_student.doctoral_committee.committee_members.exclude(
                role="CHAIR",
            )
        )

        total_members = evaluation_members.count()

        submitted_members = (
            DissertationProposalEvaluation.objects.filter(
                proposal=locked_proposal,
                submission_number=current_submission_number,
                committee_member__in=evaluation_members,
                is_submitted=True,
            )
            .values(
                "committee_member_id",
            )
            .distinct()
            .count()
        )

        if total_members > 0 and submitted_members == total_members:
            locked_proposal.status = "FINAL_REVIEW"

            locked_proposal.save(
                update_fields=[
                    "status",
                ]
            )

            all_evaluations_completed = True

            student_user = locked_proposal.phd_student.student.user
            advisor_user = locked_proposal.phd_student.advisor.user
            chair_faculty = (
                locked_proposal.phd_student.doctoral_committee.chair_faculty
            )

            student_name = (
                student_user.get_full_name().strip()
                or student_user.username
            )

            advisor_name = (
                advisor_user.get_full_name().strip()
                or advisor_user.username
            )

            proposal_title = (
                locked_proposal.proposal_title.strip()
            )

            if chair_faculty and chair_faculty.user:
                chair_user = chair_faculty.user

                _create_dissertation_proposal_notification(
                    user=chair_user,
                    title="Dissertation Proposal Ready for Final Evaluation",
                    message=(
                        f"Dissertation proposal submitted by {student_name} "
                        f"has completed all required committee evaluations "
                        f"and is now awaiting your final evaluation and decision. "
                        f"Advisor: {advisor_name}. "
                        f"Proposal: {proposal_title}. "
                        f"Please review the committee evaluations and proceed "
                        f"with the final decision."
                    ),
                    notification_type="INFO",
                )

    messages.success(
        request,
        (
            "Dissertation proposal evaluation submitted successfully "
            f"for Submission #{current_submission_number}."
        ),
    )

    if all_evaluations_completed:
        messages.info(
            request,
            "All committee evaluations are complete. The proposal is now awaiting Chair final evaluation.",
        )

    return redirect(
        "faculty_committee_dissertation_proposal_detail",
        uuid=uuid,
        proposal_id=proposal_id,
    )

@login_required
def faculty_chair_dissertation_proposal_finalize(
    request,
    uuid,
    proposal_id,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
        ),
        user__uuid=uuid,
        user=request.user,
    )

    proposal = get_object_or_404(
        DissertationProposal.objects.select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__phd_program",
            "phd_student__phd_program__department",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "phd_student__doctoral_committee",
            "phd_student__doctoral_committee__chair_faculty",
            "phd_student__doctoral_committee__chair_faculty__user",
        ),
        proposal_id=proposal_id,
        phd_student__doctoral_committee__chair_faculty=faculty,
        phd_student__doctoral_committee__approval_status="APPROVED",
    )

    committee = proposal.phd_student.doctoral_committee

    current_submission_number = _get_current_submission_number(
        proposal,
    )

    evaluation_members = committee.committee_members.exclude(
        role="CHAIR",
    )

    total_members = evaluation_members.count()

    evaluations = (
        DissertationProposalEvaluation.objects.select_related(
            "committee_member",
            "committee_member__faculty",
            "committee_member__faculty__user",
        )
        .filter(
            proposal=proposal,
            submission_number=current_submission_number,
            committee_member__in=evaluation_members,
            is_submitted=True,
        )
        .order_by(
            "committee_member__role",
            "committee_member__faculty__user__first_name",
        )
    )

    submitted_count = evaluations.count()

    pending_count = max(
        total_members - submitted_count,
        0,
    )

    evaluation_percentage = (
        int((submitted_count / total_members) * 100)
        if total_members
        else 0
    )

    all_evaluations_completed = (
        total_members > 0
        and submitted_count == total_members
    )

    average_score = 0

    if submitted_count > 0:
        average_score = round(
            sum(
                float(
                    evaluation.score or 0,
                )
                for evaluation in evaluations
            )
            / submitted_count,
            2,
        )

    student = proposal.phd_student

    student_name = (
        student.student.user.get_full_name().strip()
        or student.student.user.username
    )

    student_id = getattr(
        student.student,
        "student_number",
        None,
    )

    program_name = (
        str(student.phd_program)
        if student.phd_program
        else None
    )

    department_name = None

    if student.phd_program:
        department = getattr(
            student.phd_program,
            "department",
            None,
        )

        if department:
            department_name = str(
                department,
            )

    advisor_name = (
        student.advisor.user.get_full_name().strip()
        or student.advisor.user.username
        if student.advisor and student.advisor.user
        else "Advisor"
    )

    final_result = (
        getattr(
            proposal,
            "result",
            "PENDING",
        )
        or "PENDING"
    )

    finalised = final_result != "PENDING"

    if request.method == "GET":
        if proposal.status != "FINAL_REVIEW" and not finalised:
            messages.warning(
                request,
                "This proposal is not ready for final review.",
            )

            return redirect(
                "faculty_committee_dissertation_proposal_detail",
                uuid=uuid,
                proposal_id=proposal_id,
            )

        context = {
            "uuid": uuid,
            "faculty": faculty,
            "proposal": proposal,
            "committee": committee,
            "evaluations": evaluations,
            "total_members": total_members,
            "submitted_count": submitted_count,
            "pending_count": pending_count,
            "evaluation_percentage": evaluation_percentage,
            "all_evaluations_completed": all_evaluations_completed,
            "average_score": average_score,
            "student": student,
            "student_name": student_name,
            "student_id": student_id,
            "program_name": program_name,
            "department_name": department_name,
            "advisor_name": advisor_name,
            "finalised": finalised,
            "final_result": final_result,
            "final_remarks": getattr(
                proposal,
                "final_remarks",
                "",
            ) or "",
            "finalized_by": getattr(
                proposal,
                "finalized_by",
                None,
            ),
            "finalized_at": getattr(
                proposal,
                "finalized_at",
                None,
            ),
            "current_submission_number": current_submission_number,
        }

        return render(
            request,
            "leo/dissertation/chair_dissertation_proposal_finalize.html",
            context,
        )

    if finalised:
        messages.warning(
            request,
            "This dissertation proposal has already been finalized.",
        )

        return redirect(
            "faculty_chair_dissertation_proposal_finalize",
            uuid=uuid,
            proposal_id=proposal_id,
        )

    if proposal.status != "FINAL_REVIEW":
        messages.error(
            request,
            "This dissertation proposal is not ready for Chair finalization.",
        )

        return redirect(
            "faculty_committee_dissertation_proposal_detail",
            uuid=uuid,
            proposal_id=proposal_id,
        )

    if not all_evaluations_completed:
        messages.error(
            request,
            "All committee members must submit their evaluations before finalization.",
        )

        return redirect(
            "faculty_committee_dissertation_proposal_detail",
            uuid=uuid,
            proposal_id=proposal_id,
        )

    decision = request.POST.get(
        "result",
        "",
    ).strip()

    final_remarks = request.POST.get(
        "final_remarks",
        "",
    ).strip()

    allowed_results = {
        "APPROVED",
        "REJECTED",
        "REVISION_REQUIRED",
    }

    if decision not in allowed_results:
        messages.error(
            request,
            "Please select a valid final decision.",
        )

        return redirect(
            "faculty_chair_dissertation_proposal_finalize",
            uuid=uuid,
            proposal_id=proposal_id,
        )

    if len(final_remarks) < 20:
        messages.error(
            request,
            "Final remarks must contain at least 20 characters.",
        )

        return redirect(
            "faculty_chair_dissertation_proposal_finalize",
            uuid=uuid,
            proposal_id=proposal_id,
        )

    if len(final_remarks) > 5000:
        messages.error(
            request,
            "Final remarks cannot exceed 5000 characters.",
        )

        return redirect(
            "faculty_chair_dissertation_proposal_finalize",
            uuid=uuid,
            proposal_id=proposal_id,
        )

    with transaction.atomic():
        locked_proposal = (
            DissertationProposal.objects.select_for_update()
            .select_related(
                "phd_student",
                "phd_student__student",
                "phd_student__student__user",
                "phd_student__advisor",
                "phd_student__advisor__user",
                "phd_student__doctoral_committee",
                "phd_student__doctoral_committee__chair_faculty",
                "phd_student__doctoral_committee__chair_faculty__user",
            )
            .get(
                proposal_id=proposal_id,
            )
        )

        if locked_proposal.result != "PENDING":
            messages.warning(
                request,
                "This dissertation proposal has already been finalized.",
            )

            return redirect(
                "faculty_chair_dissertation_proposal_finalize",
                uuid=uuid,
                proposal_id=proposal_id,
            )

        locked_committee = (
            locked_proposal.phd_student.doctoral_committee
        )

        if (
            not locked_committee
            or locked_committee.chair_faculty_id != faculty.pk
        ):
            messages.error(
                request,
                "Only the Chair Faculty can finalize this dissertation proposal.",
            )

            return redirect(
                "faculty_committee_dissertation_proposal_detail",
                uuid=uuid,
                proposal_id=proposal_id,
            )

        if locked_proposal.status != "FINAL_REVIEW":
            messages.error(
                request,
                "This dissertation proposal is not ready for finalization.",
            )

            return redirect(
                "faculty_committee_dissertation_proposal_detail",
                uuid=uuid,
                proposal_id=proposal_id,
            )

        locked_submission_number = _get_current_submission_number(
            locked_proposal,
        )

        locked_evaluation_members = (
            locked_committee.committee_members.exclude(
                role="CHAIR",
            )
        )

        locked_total_members = locked_evaluation_members.count()

        locked_submitted_count = (
            DissertationProposalEvaluation.objects.filter(
                proposal=locked_proposal,
                submission_number=locked_submission_number,
                committee_member__in=locked_evaluation_members,
                is_submitted=True,
            )
            .values(
                "committee_member_id",
            )
            .distinct()
            .count()
        )

        if (
            locked_total_members == 0
            or locked_submitted_count != locked_total_members
        ):
            messages.error(
                request,
                "All committee members must submit their evaluations before finalization.",
            )

            return redirect(
                "faculty_committee_dissertation_proposal_detail",
                uuid=uuid,
                proposal_id=proposal_id,
            )

        locked_proposal.result = decision
        locked_proposal.final_remarks = final_remarks
        locked_proposal.finalized_by = faculty
        locked_proposal.finalized_at = timezone.now()

        if decision == "APPROVED":
            locked_proposal.status = "APPROVED"
        elif decision == "REJECTED":
            locked_proposal.status = "REJECTED"
        else:
            locked_proposal.status = "REVISION_REQUIRED"

        locked_proposal.save(
            update_fields=[
                "result",
                "final_remarks",
                "finalized_by",
                "finalized_at",
                "status",
            ]
        )

        student_user = locked_proposal.phd_student.student.user
        advisor_user = locked_proposal.phd_student.advisor.user

        student_name = (
            student_user.get_full_name().strip()
            or student_user.username
        )

        advisor_name = (
            advisor_user.get_full_name().strip()
            or advisor_user.username
        )

        proposal_title = (
            locked_proposal.proposal_title.strip()
        )

        chair_name = (
            faculty.user.get_full_name().strip()
            or faculty.user.username
        )

        if decision == "APPROVED":
            notification_title = (
                "Dissertation Proposal Approved - Research May Begin"
            )

            notification_message = (
                f"The dissertation proposal submitted by {student_name} "
                f"has been approved by Chair {chair_name} "
                f"after completion of all required committee evaluations. "
                f"Proposal: {proposal_title}. "
                f"Advisor: {advisor_name}. "
                f"Final decision: APPROVED. "
                f"The student may now proceed with the research work."
            )

            notification_type = "SUCCESS"

        elif decision == "REJECTED":
            notification_title = (
                "Dissertation Proposal Rejected"
            )

            notification_message = (
                f"The dissertation proposal submitted by {student_name} "
                f"has been rejected by Chair {chair_name} "
                f"after completion of the committee evaluation process. "
                f"Proposal: {proposal_title}. "
                f"Advisor: {advisor_name}. "
                f"Final decision: REJECTED. "
                f"Chair remarks: {final_remarks}"
            )

            notification_type = "ERROR"

        else:
            notification_title = (
                "Dissertation Proposal Revision Required"
            )

            notification_message = (
                f"The dissertation proposal submitted by {student_name} "
                f"requires revision following the final review by Chair "
                f"{chair_name}. "
                f"Proposal: {proposal_title}. "
                f"Advisor: {advisor_name}. "
                f"Final decision: REVISION REQUIRED. "
                f"Chair remarks: {final_remarks}"
            )

            notification_type = "WARNING"

        _create_dissertation_proposal_notification(
            user=student_user,
            title=notification_title,
            message=notification_message,
            notification_type=notification_type,
        )

        _create_dissertation_proposal_notification(
            user=advisor_user,
            title=notification_title,
            message=notification_message,
            notification_type=notification_type,
        )

    messages.success(
        request,
        "Dissertation proposal has been finalized successfully.",
    )

    return redirect(
        "faculty_chair_dissertation_proposal_finalize",
        uuid=uuid,
        proposal_id=proposal_id,
    )


### DISSERTATION PROPOSALS ENDs HERE ####

###############################################################
# DOCTORAL CANDIDACY MODULE MANAGEMENT IN FACULTY DASHBOARD
###############################################################

def _create_doctoral_candidacy_notification(
    user,
    title,
    message,
    notification_type="INFO",
):
    if not user:
        return

    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        link="",
        is_read=False,
    )

    payload = {
        "id": notification.pk,
        "title": notification.title,
        "message": notification.message,
        "type": notification.notification_type,
        "link": notification.link,
        "is_read": notification.is_read,
        "created_at": notification.created_at.isoformat(),
    }

    transaction.on_commit(
        lambda user_id=user.pk, payload=payload: send_notification(
            user_id,
            payload,
            event="doctoral_candidacy_update",
        )
    )

def get_doctoral_candidacy_status(phd_student):

    committee = getattr(
        phd_student,
        "doctoral_committee",
        None,
    )

    advisor_assigned = phd_student.advisor_id is not None

    committee_approved = bool(committee and committee.approval_status == "APPROVED")

    phd_program = getattr(
        phd_student,
        "phd_program",
        None,
    )

    required_credits = (
        getattr(
            phd_program,
            "total_credits_required",
            0,
        )
        or 0
    )

    coursework_queryset = FacultyCoursework.objects.filter(
        phd_student=phd_student,
    )

    completed_credits = (
        coursework_queryset.filter(
            status="COMPLETED",
        ).aggregate(
            total=Sum(
                "coursework__credits",
            )
        )["total"]
        or 0
    )

    coursework_completed = (
        required_credits > 0 and completed_credits >= required_credits
    )

    passed_exam = PreliminaryExamination.objects.filter(
        phd_student=phd_student,
        result="PASS",
    ).exists()

    proposal_approved = DissertationProposal.objects.filter(
        phd_student=phd_student,
        result="APPROVED",
    ).exists()

    candidacy = getattr(
        phd_student,
        "doctoral_candidacy",
        None,
    )

    candidacy_approved = bool(candidacy and candidacy.candidacy_status == "APPROVED")

    dissertation = getattr(
        phd_student,
        "dissertation",
        None,
    )

    dissertation_completed = bool(dissertation and dissertation.status == "APPROVED")

    student_active = phd_student.current_status == "ACTIVE"

    eligibility_checks = [
        advisor_assigned,
        committee_approved,
        coursework_completed,
        passed_exam,
        proposal_approved,
    ]

    eligible_for_candidacy = all(eligibility_checks)

    return {
        "eligible_for_candidacy": eligible_for_candidacy,
        "student_active": student_active,
        "advisor_assigned": advisor_assigned,
        "committee_approved": committee_approved,
        "coursework_completed": coursework_completed,
        "required_credits": required_credits,
        "completed_credits": completed_credits,
        "remaining_credits": max(
            required_credits - completed_credits,
            0,
        ),
        "preliminary_exam_passed": passed_exam,
        "dissertation_proposal_approved": proposal_approved,
        "doctoral_candidacy_approved": candidacy_approved,
        "dissertation_completed": dissertation_completed,
    }


@login_required
def faculty_doctoral_candidacy_list(
    request,
    uuid,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
        ),
        user__uuid=uuid,
    )

    search = request.GET.get(
        "search",
        "",
    ).strip()

    status_filter = request.GET.get(
        "status",
        "",
    ).strip()

    chair_candidacy_ids = DoctoralCandidacy.objects.filter(
        phd_student__doctoral_committee__chair_faculty=faculty,
    ).values_list(
        "candidacy_id",
        flat=True,
    )

    committee_candidacy_ids = DoctoralCandidacy.objects.filter(
        phd_student__doctoral_committee__committee_members__faculty=faculty,
    ).values_list(
        "candidacy_id",
        flat=True,
    )

    candidacy_ids = set(chair_candidacy_ids).union(set(committee_candidacy_ids))

    candidacies = (
        DoctoralCandidacy.objects.filter(
            candidacy_id__in=candidacy_ids,
        )
        .select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "phd_student__phd_program",
            "phd_student__doctoral_committee",
            "phd_student__doctoral_committee__chair_faculty",
            "phd_student__doctoral_committee__chair_faculty__user",
        )
        .prefetch_related(
            "phd_student__doctoral_committee__committee_members",
        )
        .order_by(
            "-candidacy_date",
        )
        .distinct()
    )

    total_candidacies = candidacies.count()

    pending_candidacies = candidacies.filter(
        candidacy_status="PENDING",
    ).count()

    approved_candidacies = candidacies.filter(
        candidacy_status="APPROVED",
    ).count()

    rejected_candidacies = candidacies.filter(
        candidacy_status="REJECTED",
    ).count()

    on_hold_candidacies = candidacies.filter(
        candidacy_status="ON_HOLD",
    ).count()

    if search:
        candidacies = candidacies.filter(
            Q(
                phd_student__student__user__first_name__icontains=search,
            )
            | Q(
                phd_student__student__user__last_name__icontains=search,
            )
            | Q(
                phd_student__student__student_number__icontains=search,
            )
            | Q(
                phd_student__phd_program__program_name__icontains=search,
            )
        )

    if status_filter and status_filter.lower() != "all":
        candidacies = candidacies.filter(
            candidacy_status=status_filter.upper(),
        )

    filtered_candidacies = candidacies.count()

    is_chair = False
    is_committee_member = False

    for candidacy in candidacies:

        status_data = get_doctoral_candidacy_status(
            candidacy.phd_student,
        )

        candidacy.status_data = status_data

        candidacy.advisor_assigned = status_data.get(
            "advisor_assigned",
            False,
        )

        candidacy.committee_approved = status_data.get(
            "committee_approved",
            False,
        )

        candidacy.coursework_completed = status_data.get(
            "coursework_completed",
            False,
        )

        candidacy.preliminary_exam_passed = status_data.get(
            "preliminary_exam_passed",
            False,
        )

        candidacy.dissertation_proposal_approved = status_data.get(
            "dissertation_proposal_approved",
            False,
        )

        candidacy.dissertation_completed = status_data.get(
            "dissertation_completed",
            False,
        )

        candidacy.candidacy_approved = candidacy.candidacy_status == "APPROVED"

        advisor = getattr(
            candidacy.phd_student,
            "advisor",
            None,
        )

        if advisor:
            candidacy.advisor_name = str(
                advisor,
            )
        else:
            candidacy.advisor_name = ""

        committee = getattr(
            candidacy.phd_student,
            "doctoral_committee",
            None,
        )

        candidacy.is_chair = False
        candidacy.is_committee_member = False
        candidacy.can_hold = False
        candidacy.committee_chair = ""

        if committee:

            chair_faculty = getattr(
                committee,
                "chair_faculty",
                None,
            )

            if chair_faculty:

                candidacy.committee_chair = str(
                    chair_faculty,
                )

                candidacy.is_chair = chair_faculty.pk == faculty.pk

            candidacy.is_committee_member = committee.committee_members.filter(
                faculty=faculty,
            ).exists()

        candidacy.can_hold = candidacy.is_chair

        eligibility_items = [
            candidacy.advisor_assigned,
            candidacy.committee_approved,
            candidacy.coursework_completed,
            candidacy.preliminary_exam_passed,
            candidacy.dissertation_proposal_approved,
        ]

        candidacy.eligibility_completed = sum(bool(item) for item in eligibility_items)

        candidacy.eligibility_total = len(eligibility_items)

        candidacy.progress_percentage = round(
            (candidacy.eligibility_completed / candidacy.eligibility_total) * 100
        )

        if candidacy.progress_percentage >= 100:
            candidacy.readiness_label = "Ready"
            candidacy.readiness_status = "complete"
            candidacy.next_step = "Dissertation"
        elif not candidacy.advisor_assigned:
            candidacy.readiness_label = "Advisor Pending"
            candidacy.readiness_status = "pending"
            candidacy.next_step = "Advisor Assignment"
        elif not candidacy.committee_approved:
            candidacy.readiness_label = "Committee Pending"
            candidacy.readiness_status = "pending"
            candidacy.next_step = "Committee Approval"
        elif not candidacy.coursework_completed:
            candidacy.readiness_label = "Coursework Pending"
            candidacy.readiness_status = "pending"
            candidacy.next_step = "Coursework"
        elif not candidacy.preliminary_exam_passed:
            candidacy.readiness_label = "Exam Pending"
            candidacy.readiness_status = "pending"
            candidacy.next_step = "Preliminary Exam"
        else:
            candidacy.readiness_label = "Proposal Pending"
            candidacy.readiness_status = "pending"
            candidacy.next_step = "Dissertation Proposal"

        if candidacy.is_chair:
            is_chair = True

        if candidacy.is_committee_member:
            is_committee_member = True

    can_create = is_chair

    paginator = Paginator(
        candidacies,
        10,
    )

    page_number = request.GET.get(
        "page",
    )

    candidacy_list = paginator.get_page(
        page_number,
    )

    context = {
        "faculty": faculty,
        "candidacy_list": candidacy_list,
        "search": search,
        "status_filter": status_filter,
        "total_candidacies": total_candidacies,
        "pending_candidacies": pending_candidacies,
        "approved_candidacies": approved_candidacies,
        "rejected_candidacies": rejected_candidacies,
        "on_hold_candidacies": on_hold_candidacies,
        "filtered_candidacies": filtered_candidacies,
        "is_chair": is_chair,
        "is_committee_member": is_committee_member,
        "can_create": can_create,
    }

    return render(
        request,
        "leo/DoctoralCandidacy/candidacy_list.html",
        context,
    )


@login_required
def faculty_doctoral_candidacy_create(
    request,
    uuid,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
        ),
        user__uuid=uuid,
        user=request.user,
    )

    eligible_students = (
        PhDStudent.objects.filter(
            doctoral_committee__chair_faculty=faculty,
            doctoral_committee__approval_status="APPROVED",
            current_status="ACTIVE",
        )
        .select_related(
            "student",
            "student__user",
            "advisor",
            "advisor__user",
            "phd_program",
            "doctoral_committee",
        )
        .exclude(
            doctoral_candidacy__isnull=False,
        )
        .order_by(
            "student__user__first_name",
            "student__user__last_name",
        )
        .distinct()
    )

    if request.method == "POST":
        form = DoctoralCandidacyForm(
            request.POST,
            faculty=faculty,
        )

        if form.is_valid():
            phd_student = form.cleaned_data["phd_student"]

            committee = (
                DoctoralCommittee.objects.filter(
                    phd_student=phd_student,
                    chair_faculty=faculty,
                    approval_status="APPROVED",
                )
                .select_related(
                    "chair_faculty",
                )
                .first()
            )

            if not committee:
                form.add_error(
                    "phd_student",
                    (
                        "The selected student does not have "
                        "an approved doctoral committee assigned "
                        "to this Chair Faculty."
                    ),
                )

            elif phd_student.current_status != "ACTIVE":
                form.add_error(
                    "phd_student",
                    (
                        "Only active PhD students can be "
                        "initiated for doctoral candidacy."
                    ),
                )

            elif DoctoralCandidacy.objects.filter(
                phd_student=phd_student,
            ).exists():
                form.add_error(
                    "phd_student",
                    "This student already has a doctoral candidacy record.",
                )

            else:
                status_data = get_doctoral_candidacy_status(
                    phd_student,
                )

                if not status_data.get(
                    "eligible_for_candidacy",
                    False,
                ):
                    form.add_error(
                        "phd_student",
                        (
                            "The selected student has not "
                            "completed all doctoral candidacy "
                            "requirements."
                        ),
                    )

                else:
                    candidacy = form.save(
                        commit=False,
                    )

                    candidacy.phd_student = phd_student
                    candidacy.candidacy_status = "APPROVED"
                    candidacy.approval_date = timezone.now().date()

                    with transaction.atomic():
                        candidacy.save()

                        student_user = phd_student.student.user

                        advisor_user = (
                            phd_student.advisor.user
                            if phd_student.advisor
                            and phd_student.advisor.user
                            else None
                        )

                        student_name = (
                            student_user.get_full_name().strip()
                            or student_user.username
                        )

                        chair_name = (
                            faculty.user.get_full_name().strip()
                            or faculty.user.username
                        )

                        advisor_name = (
                            advisor_user.get_full_name().strip()
                            or advisor_user.username
                            if advisor_user
                            else "Advisor"
                        )

                        program_name = (
                            str(phd_student.phd_program)
                            if phd_student.phd_program
                            else "PhD Program"
                        )

                        candidacy_date = (
                            candidacy.candidacy_date.strftime("%d %B %Y")
                            if candidacy.candidacy_date
                            else "Not specified"
                        )

                        _create_doctoral_candidacy_notification(
                            user=student_user,
                            title="Doctoral Candidacy Approved",
                            message=(
                                f"Your doctoral candidacy has been created "
                                f"and approved by Chair {chair_name}. "
                                f"Student: {student_name}. "
                                f"Program: {program_name}. "
                                f"Advisor: {advisor_name}. "
                                f"Candidacy Date: {candidacy_date}. "
                                f"Your doctoral candidacy status is now APPROVED "
                                f"and you may proceed to the dissertation stage."
                            ),
                            notification_type="SUCCESS",
                        )

                        if advisor_user:
                            _create_doctoral_candidacy_notification(
                                user=advisor_user,
                                title="Doctoral Candidacy Approved",
                                message=(
                                    f"Doctoral candidacy for {student_name} "
                                    f"has been created and approved by Chair "
                                    f"{chair_name}. "
                                    f"Program: {program_name}. "
                                    f"You are listed as the student's Advisor. "
                                    f"Candidacy Date: {candidacy_date}. "
                                    f"The doctoral candidacy status is now APPROVED "
                                    f"and the student may proceed to the dissertation stage."
                                ),
                                notification_type="SUCCESS",
                            )

                    messages.success(
                        request,
                        (
                            "Doctoral candidacy created and approved "
                            "successfully. The student can now proceed "
                            "to the dissertation stage."
                        ),
                    )

                    return redirect(
                        "faculty_doctoral_candidacy_list",
                        uuid=faculty.user.uuid,
                    )

        if form.errors:
            messages.error(
                request,
                "Please correct the errors below and try again.",
            )

    else:
        form = DoctoralCandidacyForm(
            faculty=faculty,
        )

    context = {
        "faculty": faculty,
        "form": form,
        "eligible_students": eligible_students,
    }

    return render(
        request,
        "leo/DoctoralCandidacy/candidacy_create.html",
        context,
    )


@login_required
def faculty_doctoral_candidacy_check_status(
    request,
    uuid,
):

    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
        ),
        user__uuid=uuid,
        user=request.user,
    )

    if request.method != "GET":

        return JsonResponse(
            {
                "success": False,
                "message": "Invalid request.",
            },
            status=400,
        )

    student_id = request.GET.get(
        "student_id",
    )

    if not student_id:

        return JsonResponse(
            {
                "success": False,
                "message": "PhD student is required.",
            },
            status=400,
        )

    phd_student = get_object_or_404(
        PhDStudent.objects.select_related(
            "student",
            "student__user",
            "advisor",
            "phd_program",
            "doctoral_committee",
            "doctoral_candidacy",
            "dissertation",
        ),
        pk=student_id,
        doctoral_committee__chair_faculty=faculty,
    )

    status_data = get_doctoral_candidacy_status(
        phd_student,
    )

    advisor_assigned = bool(
        status_data.get(
            "advisor_assigned",
            False,
        )
    )

    committee_approved = bool(
        status_data.get(
            "committee_approved",
            False,
        )
    )

    coursework_completed = bool(
        status_data.get(
            "coursework_completed",
            False,
        )
    )

    preliminary_exam_passed = bool(
        status_data.get(
            "preliminary_exam_passed",
            False,
        )
    )

    dissertation_proposal_approved = bool(
        status_data.get(
            "dissertation_proposal_approved",
            False,
        )
    )

    doctoral_candidacy_approved = bool(
        status_data.get(
            "doctoral_candidacy_approved",
            False,
        )
    )

    dissertation_completed = bool(
        status_data.get(
            "dissertation_completed",
            False,
        )
    )

    eligible = bool(
        status_data.get(
            "eligible_for_candidacy",
            False,
        )
    )

    required_credits = int(
        status_data.get(
            "required_credits",
            0,
        )
        or 0
    )

    completed_credits = int(
        status_data.get(
            "completed_credits",
            0,
        )
        or 0
    )

    remaining_credits = int(
        status_data.get(
            "remaining_credits",
            max(
                required_credits - completed_credits,
                0,
            ),
        )
        or 0
    )

    return JsonResponse(
        {
            "success": True,
            "eligible": eligible,
            "student_active": (phd_student.current_status == "ACTIVE"),
            "advisor_assigned": advisor_assigned,
            "committee_approved": committee_approved,
            "coursework_completed": coursework_completed,
            "preliminary_exam_passed": preliminary_exam_passed,
            "dissertation_proposal_approved": (dissertation_proposal_approved),
            "doctoral_candidacy_approved": (doctoral_candidacy_approved),
            "dissertation_completed": (dissertation_completed),
            "required_credits": required_credits,
            "completed_credits": completed_credits,
            "remaining_credits": remaining_credits,
            "checks": {
                "advisor_assigned": {
                    "label": "Advisor Assigned",
                    "completed": advisor_assigned,
                },
                "committee_approved": {
                    "label": "Doctoral Committee Approved",
                    "completed": committee_approved,
                },
                "coursework_completed": {
                    "label": "Coursework Credits Completed",
                    "completed": coursework_completed,
                    "required": required_credits,
                    "completed_credits": completed_credits,
                    "remaining": remaining_credits,
                },
                "preliminary_exam_passed": {
                    "label": ("Preliminary / Qualifying " "Examination Passed"),
                    "completed": preliminary_exam_passed,
                },
                "dissertation_proposal_approved": {
                    "label": "Dissertation Proposal Approved",
                    "completed": dissertation_proposal_approved,
                },
                "doctoral_candidacy_approved": {
                    "label": "Doctoral Candidacy",
                    "completed": doctoral_candidacy_approved,
                },
                "dissertation_completed": {
                    "label": "Dissertation Completed",
                    "completed": dissertation_completed,
                },
            },
        }
    )


@login_required
def faculty_doctoral_candidacy_detail(
    request,
    uuid,
    candidacy_id,
):

    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
            "faculty_rank",
            "department",
        ),
        user__uuid=uuid,
        user=request.user,
    )

    candidacy = get_object_or_404(
        DoctoralCandidacy.objects.select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "phd_student__phd_program",
            "phd_student__phd_program__department",
            "phd_student__doctoral_committee",
            "phd_student__doctoral_committee__chair_faculty",
            "phd_student__doctoral_committee__chair_faculty__user",
        ),
        candidacy_id=candidacy_id,
    )

    phd_student = candidacy.phd_student

    committee = getattr(
        phd_student,
        "doctoral_committee",
        None,
    )

    if not committee:
        return HttpResponse(
            "Doctoral committee not found.",
            status=404,
        )

    chair_faculty = getattr(
        committee,
        "chair_faculty",
        None,
    )

    is_chair = bool(
        chair_faculty and chair_faculty.pk == faculty.pk
    )

    is_committee_member = CommitteeMember.objects.filter(
        committee=committee,
        faculty=faculty,
    ).exists()

    if not is_chair and not is_committee_member:
        return HttpResponse(
            "You are not authorized to access this doctoral candidacy.",
            status=403,
        )

    can_approve = (
        is_chair
        and candidacy.candidacy_status == "PENDING"
    )

    can_reject = (
        is_chair
        and candidacy.candidacy_status == "PENDING"
    )

    if request.method == "POST":

        if not is_chair:
            messages.error(
                request,
                (
                    "Only the Doctoral Committee Chair "
                    "can process this candidacy."
                ),
            )

            return redirect(
                "faculty_doctoral_candidacy_detail",
                uuid=faculty.user.uuid,
                candidacy_id=candidacy.candidacy_id,
            )

        action = (
            request.POST.get(
                "action",
                "",
            )
            .strip()
            .lower()
        )

        if candidacy.candidacy_status != "PENDING":
            messages.error(
                request,
                "This doctoral candidacy has already been processed.",
            )

            return redirect(
                "faculty_doctoral_candidacy_detail",
                uuid=faculty.user.uuid,
                candidacy_id=candidacy.candidacy_id,
            )

        status_data = get_doctoral_candidacy_status(
            phd_student,
        )

        eligible_for_candidacy = status_data.get(
            "eligible_for_candidacy",
            False,
        )

        student_user = getattr(
            getattr(
                phd_student,
                "student",
                None,
            ),
            "user",
            None,
        )

        advisor_user = getattr(
            getattr(
                phd_student,
                "advisor",
                None,
            ),
            "user",
            None,
        )

        student_name = (
            student_user.get_full_name().strip()
            or student_user.username
            if student_user
            else "Student"
        )

        advisor_name = (
            advisor_user.get_full_name().strip()
            or advisor_user.username
            if advisor_user
            else "Advisor"
        )

        chair_user = getattr(
            getattr(
                committee,
                "chair_faculty",
                None,
            ),
            "user",
            None,
        )

        chair_name = (
            chair_user.get_full_name().strip()
            or chair_user.username
            if chair_user
            else (
                faculty.user.get_full_name().strip()
                or faculty.user.username
            )
        )

        program_name = getattr(
            getattr(
                phd_student,
                "phd_program",
                None,
            ),
            "program_name",
            "Doctoral Program",
        )

        if action == "approve":

            if not eligible_for_candidacy:
                messages.error(
                    request,
                    (
                        "This student does not meet all "
                        "doctoral candidacy requirements. "
                        "The dissertation proposal must be "
                        "approved before candidacy approval."
                    ),
                )

                return redirect(
                    "faculty_doctoral_candidacy_detail",
                    uuid=faculty.user.uuid,
                    candidacy_id=candidacy.candidacy_id,
                )

            candidacy.candidacy_status = "APPROVED"
            candidacy.approval_date = timezone.now().date()

            candidacy.save(
                update_fields=[
                    "candidacy_status",
                    "approval_date",
                ],
            )

            notification_title = (
                "Doctoral Candidacy Approved"
            )

            notification_message = (
                f"Doctoral candidacy for {student_name} "
                f"has been approved by Committee Chair "
                f"{chair_name}. "
                f"Advisor: {advisor_name}. "
                f"Program: {program_name}. "
                "The student has successfully advanced "
                "to doctoral candidacy and may proceed "
                "to the dissertation stage."
            )

            _create_doctoral_candidacy_notification(
                student_user,
                notification_title,
                notification_message,
                "SUCCESS",
            )

            _create_doctoral_candidacy_notification(
                advisor_user,
                notification_title,
                notification_message,
                "SUCCESS",
            )

            messages.success(
                request,
                "Doctoral candidacy has been approved successfully.",
            )

            return redirect(
                "faculty_doctoral_candidacy_detail",
                uuid=faculty.user.uuid,
                candidacy_id=candidacy.candidacy_id,
            )

        if action == "reject":

            candidacy.candidacy_status = "REJECTED"
            candidacy.approval_date = None

            candidacy.save(
                update_fields=[
                    "candidacy_status",
                    "approval_date",
                ],
            )

            notification_title = (
                "Doctoral Candidacy Rejected"
            )

            notification_message = (
                f"Doctoral candidacy for {student_name} "
                f"has been rejected by Committee Chair "
                f"{chair_name}. "
                f"Advisor: {advisor_name}. "
                f"Program: {program_name}. "
                "The doctoral candidacy application has "
                "not been approved."
            )

            _create_doctoral_candidacy_notification(
                student_user,
                notification_title,
                notification_message,
                "ERROR",
            )

            _create_doctoral_candidacy_notification(
                advisor_user,
                notification_title,
                notification_message,
                "ERROR",
            )

            messages.success(
                request,
                "Doctoral candidacy has been rejected.",
            )

            return redirect(
                "faculty_doctoral_candidacy_detail",
                uuid=faculty.user.uuid,
                candidacy_id=candidacy.candidacy_id,
            )

        messages.error(
            request,
            "Invalid candidacy action.",
        )

        return redirect(
            "faculty_doctoral_candidacy_detail",
            uuid=faculty.user.uuid,
            candidacy_id=candidacy.candidacy_id,
        )

    status_data = get_doctoral_candidacy_status(
        phd_student,
    )

    advisor_assigned = status_data.get(
        "advisor_assigned",
        bool(phd_student.advisor_id),
    )

    committee_approved = status_data.get(
        "committee_approved",
        committee.approval_status == "APPROVED",
    )

    coursework_completed = status_data.get(
        "coursework_completed",
        False,
    )

    preliminary_exam_passed = status_data.get(
        "preliminary_exam_passed",
        False,
    )

    proposal_approved = status_data.get(
        "dissertation_proposal_approved",
        False,
    )

    completed_credits = status_data.get(
        "completed_credits",
        0,
    )

    required_credits = status_data.get(
        "required_credits",
        0,
    )

    eligible_for_candidacy = status_data.get(
        "eligible_for_candidacy",
        False,
    )

    academic_requirements_completed = all(
        [
            advisor_assigned,
            committee_approved,
            coursework_completed,
            preliminary_exam_passed,
            proposal_approved,
        ]
    )

    completed_stages = sum(
        [
            advisor_assigned,
            committee_approved,
            coursework_completed,
            preliminary_exam_passed,
            proposal_approved,
            candidacy.candidacy_status == "APPROVED",
        ]
    )

    total_stages = 6

    overall_progress = round(
        (completed_stages / total_stages) * 100
    )

    coursework_progress = 0

    if required_credits:
        coursework_progress = min(
            round(
                (completed_credits / required_credits) * 100
            ),
            100,
        )

    coursework_list = (
        FacultyCoursework.objects.filter(
            phd_student=phd_student,
        )
        .select_related(
            "coursework",
        )
        .order_by(
            "coursework__coursework_name",
        )
    )

    preliminary_examinations = (
        PreliminaryExamination.objects.filter(
            phd_student=phd_student,
        )
        .order_by(
            "-exam_date",
        )
    )

    dissertation_proposal = (
        DissertationProposal.objects.filter(
            phd_student=phd_student,
        )
        .order_by(
            "-pk",
        )
        .first()
    )

    dissertation = (
        Dissertation.objects.filter(
            phd_student=phd_student,
        )
        .order_by(
            "-pk",
        )
        .first()
    )

    candidacy_content_type = ContentType.objects.get_for_model(
        candidacy,
    )

    video_evidence = (
        PhDVideoEvidence.objects.filter(
            phd_student=phd_student,
            evidence_type="DOCTORAL_CANDIDACY",
            target_content_type=candidacy_content_type,
            target_object_id=candidacy.pk,
        )
        .select_related(
            "uploaded_by",
        )
        .first()
    )

    context = {
        "faculty": faculty,
        "candidacy": candidacy,
        "phd_student": phd_student,
        "committee": committee,
        "status_data": status_data,
        "is_chair": is_chair,
        "is_committee_member": is_committee_member,
        "advisor_assigned": advisor_assigned,
        "committee_approved": committee_approved,
        "coursework_completed": coursework_completed,
        "preliminary_exam_passed": preliminary_exam_passed,
        "proposal_approved": proposal_approved,
        "eligible_for_candidacy": eligible_for_candidacy,
        "completed_credits": completed_credits,
        "required_credits": required_credits,
        "coursework_progress": coursework_progress,
        "academic_requirements_completed": (
            academic_requirements_completed
        ),
        "overall_progress": overall_progress,
        "coursework_list": coursework_list,
        "preliminary_examinations": preliminary_examinations,
        "dissertation_proposal": dissertation_proposal,
        "dissertation": dissertation,
        "video_evidence": video_evidence,
        "can_approve": can_approve,
        "can_reject": can_reject,
    }

    return render(
        request,
        "leo/DoctoralCandidacy/candidacy_detail.html",
        context,
    )

@login_required
def faculty_doctoral_candidacy_update(
    request,
    uuid,
    candidacy_id,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
        ),
        user__uuid=uuid,
        user=request.user,
    )

    candidacy = get_object_or_404(
        DoctoralCandidacy.objects.select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "phd_student__phd_program",
            "phd_student__doctoral_committee",
        ),
        candidacy_id=candidacy_id,
        phd_student__doctoral_committee__chair_faculty=faculty,
    )

    if candidacy.candidacy_status != "PENDING":
        messages.error(
            request,
            "Only pending doctoral candidacies can be edited.",
        )

        return redirect(
            "faculty_doctoral_candidacy_detail",
            uuid=faculty.user.uuid,
            candidacy_id=candidacy.candidacy_id,
        )

    if request.method == "POST":
        form = DoctoralCandidacyForm(
            request.POST,
            instance=candidacy,
            faculty=faculty,
        )

        if form.is_valid():
            status_data = get_doctoral_candidacy_status(
                candidacy.phd_student,
            )

            if not status_data.get(
                "eligible_for_candidacy",
                False,
            ):
                messages.error(
                    request,
                    (
                        "This doctoral candidacy cannot be "
                        "updated because the student has not "
                        "completed the required academic "
                        "milestones, including an approved "
                        "dissertation proposal."
                    ),
                )

                return render(
                    request,
                    "leo/DoctoralCandidacy/candidacy_update.html",
                    {
                        "faculty": faculty,
                        "candidacy": candidacy,
                        "phd_student": candidacy.phd_student,
                        "form": form,
                    },
                )

            updated_candidacy = form.save(
                commit=False,
            )

            updated_candidacy.candidacy_status = "PENDING"
            updated_candidacy.approval_date = None

            with transaction.atomic():
                updated_candidacy.save()

                student_user = candidacy.phd_student.student.user
                advisor_user = (
                    candidacy.phd_student.advisor.user
                    if candidacy.phd_student.advisor
                    and candidacy.phd_student.advisor.user
                    else None
                )

                student_name = (
                    student_user.get_full_name().strip()
                    or student_user.username
                )

                advisor_name = (
                    advisor_user.get_full_name().strip()
                    or advisor_user.username
                    if advisor_user
                    else "Advisor"
                )

                _create_doctoral_candidacy_notification(
                    user=student_user,
                    title="Doctoral Candidacy Updated",
                    message=(
                        f"Your doctoral candidacy record has been updated "
                        f"by Chair {faculty.user.get_full_name().strip() or faculty.user.username}. "
                        f"Student: {student_name}. "
                        f"Advisor: {advisor_name}. "
                        f"The candidacy has been returned to Pending status "
                        f"and is awaiting Chair approval."
                    ),
                    notification_type="INFO",
                )

                if advisor_user:
                    _create_doctoral_candidacy_notification(
                        user=advisor_user,
                        title="Doctoral Candidacy Updated",
                        message=(
                            f"The doctoral candidacy record for {student_name} "
                            f"has been updated by Chair "
                            f"{faculty.user.get_full_name().strip() or faculty.user.username}. "
                            f"Advisor: {advisor_name}. "
                            f"The candidacy has been returned to Pending status "
                            f"and is awaiting Chair approval."
                        ),
                        notification_type="INFO",
                    )

            messages.success(
                request,
                "Doctoral candidacy updated successfully.",
            )

            return redirect(
                "faculty_doctoral_candidacy_detail",
                uuid=faculty.user.uuid,
                candidacy_id=candidacy.candidacy_id,
            )

        messages.error(
            request,
            "Please correct the errors below and try again.",
        )

    else:
        form = DoctoralCandidacyForm(
            instance=candidacy,
            faculty=faculty,
        )

    context = {
        "faculty": faculty,
        "candidacy": candidacy,
        "phd_student": candidacy.phd_student,
        "form": form,
    }

    return render(
        request,
        "leo/DoctoralCandidacy/candidacy_update.html",
        context,
    )

@login_required
@transaction.atomic
def faculty_doctoral_candidacy_approve(
    request,
    uuid,
    candidacy_id,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
        ),
        user__uuid=uuid,
        user=request.user,
    )

    if request.method != "POST":
        messages.warning(
            request,
            "Invalid request.",
        )

        return redirect(
            "faculty_doctoral_candidacy_list",
            uuid=faculty.user.uuid,
        )

    candidacy = get_object_or_404(
        DoctoralCandidacy.objects.select_for_update().select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "phd_student__doctoral_committee",
        ),
        candidacy_id=candidacy_id,
        phd_student__doctoral_committee__chair_faculty=faculty,
    )

    committee = getattr(
        candidacy.phd_student,
        "doctoral_committee",
        None,
    )

    if not committee:
        messages.error(
            request,
            "Doctoral committee has not been created.",
        )

        return redirect(
            "faculty_doctoral_candidacy_list",
            uuid=faculty.user.uuid,
        )

    if committee.approval_status != "APPROVED":
        messages.error(
            request,
            "The doctoral committee must be approved before approving candidacy.",
        )

        return redirect(
            "faculty_doctoral_candidacy_detail",
            uuid=faculty.user.uuid,
            candidacy_id=candidacy.candidacy_id,
        )

    if candidacy.candidacy_status != "PENDING":
        messages.error(
            request,
            "Only pending doctoral candidacies can be approved.",
        )

        return redirect(
            "faculty_doctoral_candidacy_detail",
            uuid=faculty.user.uuid,
            candidacy_id=candidacy.candidacy_id,
        )

    status_data = get_doctoral_candidacy_status(
        candidacy.phd_student,
    )

    if not status_data.get(
        "eligible_for_candidacy",
        False,
    ):
        messages.error(
            request,
            (
                "Doctoral candidacy cannot be approved. "
                "The student must complete the required "
                "academic milestones, including an "
                "approved dissertation proposal."
            ),
        )

        return redirect(
            "faculty_doctoral_candidacy_detail",
            uuid=faculty.user.uuid,
            candidacy_id=candidacy.candidacy_id,
        )

    candidacy.candidacy_status = "APPROVED"
    candidacy.approval_date = timezone.now().date()

    candidacy.save(
        update_fields=[
            "candidacy_status",
            "approval_date",
        ],
    )

    student_user = candidacy.phd_student.student.user
    advisor_user = (
        candidacy.phd_student.advisor.user
        if candidacy.phd_student.advisor
        and candidacy.phd_student.advisor.user
        else None
    )

    student_name = (
        student_user.get_full_name().strip()
        or student_user.username
    )

    advisor_name = (
        advisor_user.get_full_name().strip()
        or advisor_user.username
        if advisor_user
        else "Advisor"
    )

    chair_name = (
        faculty.user.get_full_name().strip()
        or faculty.user.username
    )

    _create_doctoral_candidacy_notification(
        user=student_user,
        title="Doctoral Candidacy Approved",
        message=(
            f"Your doctoral candidacy has been officially approved "
            f"by Chair {chair_name}. "
            f"Student: {student_name}. "
            f"Advisor: {advisor_name}. "
            f"The required doctoral candidacy milestones have been completed. "
            f"You may now proceed to the dissertation stage."
        ),
        notification_type="SUCCESS",
    )

    if advisor_user:
        _create_doctoral_candidacy_notification(
            user=advisor_user,
            title="Doctoral Candidacy Approved",
            message=(
                f"The doctoral candidacy of {student_name} "
                f"has been approved by Chair {chair_name}. "
                f"Advisor: {advisor_name}. "
                f"The student has completed the required doctoral candidacy "
                f"milestones and may now proceed to the dissertation stage."
            ),
            notification_type="SUCCESS",
        )

    messages.success(
        request,
        (
            "Doctoral candidacy approved successfully. "
            "The student can now proceed to the dissertation stage."
        ),
    )

    return redirect(
        "faculty_doctoral_candidacy_detail",
        uuid=faculty.user.uuid,
        candidacy_id=candidacy.candidacy_id,
    )


@login_required
@transaction.atomic
def faculty_doctoral_candidacy_reject(
    request,
    uuid,
    candidacy_id,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
        ),
        user__uuid=uuid,
        user=request.user,
    )

    if request.method != "POST":
        messages.warning(
            request,
            "Invalid request.",
        )

        return redirect(
            "faculty_doctoral_candidacy_list",
            uuid=faculty.user.uuid,
        )

    candidacy = get_object_or_404(
        DoctoralCandidacy.objects.select_for_update().select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "phd_student__doctoral_committee",
        ),
        candidacy_id=candidacy_id,
        phd_student__doctoral_committee__chair_faculty=faculty,
    )

    committee = getattr(
        candidacy.phd_student,
        "doctoral_committee",
        None,
    )

    if not committee:
        messages.error(
            request,
            "Doctoral committee has not been created.",
        )

        return redirect(
            "faculty_doctoral_candidacy_list",
            uuid=faculty.user.uuid,
        )

    if candidacy.candidacy_status != "PENDING":
        messages.error(
            request,
            "Only pending doctoral candidacies can be rejected.",
        )

        return redirect(
            "faculty_doctoral_candidacy_detail",
            uuid=faculty.user.uuid,
            candidacy_id=candidacy.candidacy_id,
        )

    candidacy.candidacy_status = "REJECTED"
    candidacy.approval_date = None

    candidacy.save(
        update_fields=[
            "candidacy_status",
            "approval_date",
        ],
    )

    student_user = candidacy.phd_student.student.user
    advisor_user = (
        candidacy.phd_student.advisor.user
        if candidacy.phd_student.advisor
        and candidacy.phd_student.advisor.user
        else None
    )

    student_name = (
        student_user.get_full_name().strip()
        or student_user.username
    )

    advisor_name = (
        advisor_user.get_full_name().strip()
        or advisor_user.username
        if advisor_user
        else "Advisor"
    )

    chair_name = (
        faculty.user.get_full_name().strip()
        or faculty.user.username
    )

    notification_title = "Doctoral Candidacy Rejected"

    notification_message = (
        f"The doctoral candidacy of {student_name} "
        f"has been rejected by Chair {chair_name}. "
        f"Advisor: {advisor_name}. "
        f"The candidacy is no longer pending approval."
    )

    _create_doctoral_candidacy_notification(
        user=student_user,
        title=notification_title,
        message=notification_message,
        notification_type="ERROR",
    )

    if advisor_user:
        _create_doctoral_candidacy_notification(
            user=advisor_user,
            title=notification_title,
            message=notification_message,
            notification_type="ERROR",
        )

    messages.success(
        request,
        "Doctoral candidacy rejected successfully.",
    )

    return redirect(
        "faculty_doctoral_candidacy_detail",
        uuid=faculty.user.uuid,
        candidacy_id=candidacy.candidacy_id,
    )

@login_required
def faculty_doctoral_candidacy_hold(
    request,
    uuid,
    candidacy_id,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
        ),
        user__uuid=uuid,
        user=request.user,
    )

    if request.method != "POST":
        messages.error(
            request,
            "Invalid request method.",
        )

        return redirect(
            "faculty_doctoral_candidacy_list",
            uuid=faculty.user.uuid,
        )

    candidacy = get_object_or_404(
        DoctoralCandidacy.objects.select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "phd_student__doctoral_committee",
            "phd_student__doctoral_committee__chair_faculty",
        ),
        candidacy_id=candidacy_id,
    )

    committee = getattr(
        candidacy.phd_student,
        "doctoral_committee",
        None,
    )

    if not committee:
        messages.error(
            request,
            "This candidacy is not associated with a doctoral committee.",
        )

        return redirect(
            "faculty_doctoral_candidacy_list",
            uuid=faculty.user.uuid,
        )

    if committee.chair_faculty_id != faculty.pk:
        messages.error(
            request,
            "Only the Doctoral Committee Chair can place a candidacy on hold.",
        )

        return redirect(
            "faculty_doctoral_candidacy_list",
            uuid=faculty.user.uuid,
        )

    if candidacy.candidacy_status not in [
        "PENDING",
        "APPROVED",
    ]:
        messages.error(
            request,
            "This candidacy cannot be placed on hold.",
        )

        return redirect(
            "faculty_doctoral_candidacy_list",
            uuid=faculty.user.uuid,
        )

    candidacy.candidacy_status = "ON_HOLD"

    candidacy.save(
        update_fields=[
            "candidacy_status",
        ],
    )

    student_user = candidacy.phd_student.student.user
    advisor_user = (
        candidacy.phd_student.advisor.user
        if candidacy.phd_student.advisor
        and candidacy.phd_student.advisor.user
        else None
    )

    student_name = (
        student_user.get_full_name().strip()
        or student_user.username
    )

    advisor_name = (
        advisor_user.get_full_name().strip()
        or advisor_user.username
        if advisor_user
        else "Advisor"
    )

    chair_name = (
        faculty.user.get_full_name().strip()
        or faculty.user.username
    )

    notification_title = "Doctoral Candidacy Placed on Hold"

    notification_message = (
        f"The doctoral candidacy of {student_name} "
        f"has been placed on hold by Chair {chair_name}. "
        f"Advisor: {advisor_name}. "
        f"The candidacy will remain on hold until it is activated."
    )

    _create_doctoral_candidacy_notification(
        user=student_user,
        title=notification_title,
        message=notification_message,
        notification_type="WARNING",
    )

    if advisor_user:
        _create_doctoral_candidacy_notification(
            user=advisor_user,
            title=notification_title,
            message=notification_message,
            notification_type="WARNING",
        )

    messages.success(
        request,
        "Doctoral candidacy has been placed on hold successfully.",
    )

    return redirect(
        "faculty_doctoral_candidacy_list",
        uuid=faculty.user.uuid,
    )

@login_required
def faculty_doctoral_candidacy_activate(
    request,
    uuid,
    candidacy_id,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
        ),
        user__uuid=uuid,
        user=request.user,
    )

    if request.method != "POST":
        messages.error(
            request,
            "Invalid request method.",
        )

        return redirect(
            "faculty_doctoral_candidacy_list",
            uuid=faculty.user.uuid,
        )

    candidacy = get_object_or_404(
        DoctoralCandidacy.objects.select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "phd_student__doctoral_committee",
            "phd_student__doctoral_committee__chair_faculty",
        ),
        candidacy_id=candidacy_id,
    )

    committee = getattr(
        candidacy.phd_student,
        "doctoral_committee",
        None,
    )

    if not committee:
        messages.error(
            request,
            "This candidacy is not associated with a doctoral committee.",
        )

        return redirect(
            "faculty_doctoral_candidacy_list",
            uuid=faculty.user.uuid,
        )

    if committee.chair_faculty_id != faculty.pk:
        messages.error(
            request,
            "Only the Doctoral Committee Chair can activate a candidacy.",
        )

        return redirect(
            "faculty_doctoral_candidacy_list",
            uuid=faculty.user.uuid,
        )

    if candidacy.candidacy_status != "ON_HOLD":
        messages.error(
            request,
            "Only an on-hold doctoral candidacy can be activated.",
        )

        return redirect(
            "faculty_doctoral_candidacy_list",
            uuid=faculty.user.uuid,
        )

    candidacy.candidacy_status = "APPROVED"

    candidacy.save(
        update_fields=[
            "candidacy_status",
        ],
    )

    student_user = candidacy.phd_student.student.user
    advisor_user = (
        candidacy.phd_student.advisor.user
        if candidacy.phd_student.advisor
        and candidacy.phd_student.advisor.user
        else None
    )

    student_name = (
        student_user.get_full_name().strip()
        or student_user.username
    )

    advisor_name = (
        advisor_user.get_full_name().strip()
        or advisor_user.username
        if advisor_user
        else "Advisor"
    )

    chair_name = (
        faculty.user.get_full_name().strip()
        or faculty.user.username
    )

    notification_title = "Doctoral Candidacy Reactivated"

    notification_message = (
        f"The doctoral candidacy of {student_name} "
        f"has been reactivated by Chair {chair_name}. "
        f"Advisor: {advisor_name}. "
        f"The candidacy is now active and the student may continue "
        f"with the dissertation stage."
    )

    _create_doctoral_candidacy_notification(
        user=student_user,
        title=notification_title,
        message=notification_message,
        notification_type="SUCCESS",
    )

    if advisor_user:
        _create_doctoral_candidacy_notification(
            user=advisor_user,
            title=notification_title,
            message=notification_message,
            notification_type="SUCCESS",
        )

    messages.success(
        request,
        "Doctoral candidacy has been activated successfully.",
    )

    return redirect(
        "faculty_doctoral_candidacy_list",
        uuid=faculty.user.uuid,
    )


###############################################################
# DOCTORAL CANDIDACY MODULE END IN FACULTY DASHBOARD
###############################################################


###############################################################
# ANNUAL PROGRESS MODULE MANAGEMENT IN FACULTY DASHBOARD
###############################################################


@login_required
def faculty_annual_progress_list(request, uuid):

    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
        ),
        user__uuid=uuid,
        user=request.user,
    )

    approved_committees = DoctoralCommittee.objects.filter(
        approval_status="APPROVED",
    )

    chair_student_ids = set(
        approved_committees.filter(
            chair_faculty=faculty,
        ).values_list(
            "phd_student_id",
            flat=True,
        )
    )

    committee_student_ids = set(
        CommitteeMember.objects.filter(
            faculty=faculty,
            committee__approval_status="APPROVED",
            role__in=[
                "CO_CHAIR",
                "INTERNAL_MEMBER",
                "EXTERNAL_MEMBER",
            ],
        ).values_list(
            "committee__phd_student_id",
            flat=True,
        )
    )

    is_chair = bool(chair_student_ids)

    is_committee_member = bool(committee_student_ids)

    eligible_student_ids = chair_student_ids | committee_student_ids

    all_authorized_students = list(
        PhDStudent.objects.filter(
            phd_student_id__in=eligible_student_ids,
            current_status="ACTIVE",
            doctoral_candidacy__candidacy_status="APPROVED",
        )
        .select_related(
            "student",
            "student__user",
            "phd_program",
            "advisor",
            "advisor__user",
            "doctoral_candidacy",
        )
        .order_by(
            "student__user__first_name",
            "student__user__last_name",
        )
    )

    current_year = timezone.now().year

    base_reviews = AnnualProgressReview.objects.filter(
        phd_student_id__in=eligible_student_ids,
        phd_student__doctoral_candidacy__candidacy_status="APPROVED",
    ).select_related(
        "phd_student",
        "phd_student__student",
        "phd_student__student__user",
        "phd_student__phd_program",
        "phd_student__advisor",
        "phd_student__advisor__user",
        "phd_student__doctoral_candidacy",
    )

    review_counts = dict(
        base_reviews.values(
            "phd_student_id",
        )
        .annotate(
            total=Count(
                "review_id",
            ),
        )
        .values_list(
            "phd_student_id",
            "total",
        )
    )

    reviewed_this_year_ids = set(
        base_reviews.filter(
            review_year=current_year,
        ).values_list(
            "phd_student_id",
            flat=True,
        )
    )

    for student in all_authorized_students:

        student.review_count = review_counts.get(
            student.phd_student_id,
            0,
        )

        student.current_year = current_year

        student.current_year_reviewed = student.phd_student_id in reviewed_this_year_ids

        student.is_chair_student = student.phd_student_id in chair_student_ids

        student.is_committee_student = student.phd_student_id in committee_student_ids

        student.can_create_review = is_chair and student.is_chair_student

    student_search = request.GET.get(
        "student_q",
        "",
    ).strip()

    selected_student_status = (
        request.GET.get(
            "student_status",
            "",
        )
        .strip()
        .upper()
    )

    selected_student_program = request.GET.get(
        "student_program",
        "",
    ).strip()

    filtered_students = list(all_authorized_students)

    if student_search:

        search_value = student_search.lower()

        filtered_students = [
            student
            for student in filtered_students
            if (
                search_value in (student.student.user.get_full_name() or "").lower()
                or search_value in (student.student.student_number or "")
            )
        ]

    if selected_student_status == "PENDING":

        filtered_students = [
            student
            for student in filtered_students
            if not student.current_year_reviewed
        ]

    elif selected_student_status == "COMPLETED":

        filtered_students = [
            student for student in filtered_students if student.current_year_reviewed
        ]

    elif selected_student_status:

        selected_student_status = ""

    if selected_student_program:

        filtered_students = [
            student
            for student in filtered_students
            if (
                student.phd_program
                and student.phd_program.program_name == selected_student_program
            )
        ]

    student_paginator = Paginator(
        filtered_students,
        6,
    )

    student_page = student_paginator.get_page(
        request.GET.get(
            "student_page",
            1,
        )
    )

    total_reviews = base_reviews.count()

    satisfactory_reviews = base_reviews.filter(
        status="SATISFACTORY",
    ).count()

    needs_improvement_reviews = base_reviews.filter(
        status="NEEDS_IMPROVEMENT",
    ).count()

    unsatisfactory_reviews = base_reviews.filter(
        status="UNSATISFACTORY",
    ).count()

    search_query = request.GET.get(
        "q",
        "",
    ).strip()

    selected_year = request.GET.get(
        "year",
        "",
    ).strip()

    selected_status = request.GET.get(
        "status",
        "",
    ).strip()

    selected_program = request.GET.get(
        "program",
        "",
    ).strip()

    filtered_reviews = base_reviews

    if search_query:

        filtered_reviews = filtered_reviews.filter(
            Q(phd_student__student__user__first_name__icontains=search_query)
            | Q(phd_student__student__user__last_name__icontains=search_query)
            | Q(phd_student__student__student_number__icontains=search_query)
        )

    if selected_year:

        try:

            filtered_reviews = filtered_reviews.filter(
                review_year=int(
                    selected_year,
                )
            )

        except (
            TypeError,
            ValueError,
        ):

            selected_year = ""

    if selected_status in {
        "SATISFACTORY",
        "NEEDS_IMPROVEMENT",
        "UNSATISFACTORY",
    }:

        filtered_reviews = filtered_reviews.filter(
            status=selected_status,
        )

    elif selected_status:

        selected_status = ""

    if selected_program:

        filtered_reviews = filtered_reviews.filter(
            phd_student__phd_program__program_name=selected_program,
        )

    filtered_reviews = filtered_reviews.order_by(
        "-review_year",
        "phd_student__student__user__first_name",
        "phd_student__student__user__last_name",
        "review_id",
    )

    review_paginator = Paginator(
        filtered_reviews,
        12,
    )

    review_page = review_paginator.get_page(
        request.GET.get(
            "page",
            1,
        )
    )

    review_years = (
        base_reviews.values_list(
            "review_year",
            flat=True,
        )
        .distinct()
        .order_by(
            "-review_year",
        )
    )

    student_programs = (
        PhDStudent.objects.filter(
            phd_student_id__in=eligible_student_ids,
            current_status="ACTIVE",
            doctoral_candidacy__candidacy_status="APPROVED",
        )
        .exclude(
            phd_program__program_name__isnull=True,
        )
        .values_list(
            "phd_program__program_name",
            flat=True,
        )
        .distinct()
        .order_by(
            "phd_program__program_name",
        )
    )

    programs = (
        PhDStudent.objects.filter(
            phd_student_id__in=eligible_student_ids,
            current_status="ACTIVE",
            doctoral_candidacy__candidacy_status="APPROVED",
        )
        .exclude(
            phd_program__program_name__isnull=True,
        )
        .values_list(
            "phd_program__program_name",
            flat=True,
        )
        .distinct()
        .order_by(
            "phd_program__program_name",
        )
    )

    if request.GET.get("ajax") == "1":

        review_data = []

        for review in review_page.object_list:

            student_name = (
                review.phd_student.student.user.get_full_name()
                or review.phd_student.student.student_number
            )

            first_name = review.phd_student.student.user.first_name or student_name

            advisor_name = "Not Assigned"

            if review.phd_student.advisor:

                advisor_name = (
                    review.phd_student.advisor.user.get_full_name() or "Not Assigned"
                )

            comments = Truncator(
                review.committee_comments or "",
            ).chars(
                145,
            )

            phd_student_id = review.phd_student.phd_student_id

            review_data.append(
                {
                    "review_id": review.review_id,
                    "student_name": student_name,
                    "student_number": (review.phd_student.student.student_number),
                    "avatar": first_name[:1].upper(),
                    "review_year": review.review_year,
                    "program": (
                        review.phd_student.phd_program.program_name
                        if review.phd_student.phd_program
                        else "Program Not Assigned"
                    ),
                    "advisor": advisor_name,
                    "progress_score": float(review.progress_score or 0),
                    "status": review.status,
                    "comments": comments,
                    "is_chair_student": (phd_student_id in chair_student_ids),
                    "is_committee_student": (phd_student_id in committee_student_ids),
                    "can_create_review": (
                        is_chair and phd_student_id in chair_student_ids
                    ),
                    "detail_url": reverse(
                        "faculty_annual_progress_detail",
                        kwargs={
                            "uuid": faculty.user.uuid,
                            "phd_student_id": phd_student_id,
                        },
                    ),
                }
            )

        return JsonResponse(
            {
                "reviews": review_data,
                "total": review_paginator.count,
                "page": review_page.number,
                "num_pages": review_page.num_pages,
                "start_index": (
                    review_page.start_index() if review_paginator.count else 0
                ),
                "end_index": (review_page.end_index() if review_paginator.count else 0),
                "has_previous": review_page.has_previous(),
                "has_next": review_page.has_next(),
                "previous_page": (
                    review_page.previous_page_number()
                    if review_page.has_previous()
                    else None
                ),
                "next_page": (
                    review_page.next_page_number() if review_page.has_next() else None
                ),
                "page_range": list(
                    review_page.paginator.get_elided_page_range(
                        review_page.number,
                        on_each_side=2,
                        on_ends=1,
                    )
                ),
                "is_chair": is_chair,
                "is_committee_member": is_committee_member,
                "can_create_review": is_chair,
            }
        )

    if is_chair and is_committee_member:

        workspace_role = "Chair Faculty & Committee Member"

    elif is_chair:

        workspace_role = "Chair Faculty"

    elif is_committee_member:

        workspace_role = "Committee Member"

    else:

        workspace_role = "Faculty"

    context = {
        "faculty": faculty,
        "students": student_page.object_list,
        "all_chair_students": all_authorized_students,
        "all_authorized_students": all_authorized_students,
        "total_assigned_students": len(all_authorized_students),
        "student_page": student_page,
        "student_paginator": student_paginator,
        "student_search": student_search,
        "selected_student_status": selected_student_status,
        "selected_student_program": selected_student_program,
        "student_programs": student_programs,
        "reviews": review_page.object_list,
        "review_page": review_page,
        "review_paginator": review_paginator,
        "total_reviews": total_reviews,
        "satisfactory_reviews": satisfactory_reviews,
        "needs_improvement_reviews": needs_improvement_reviews,
        "unsatisfactory_reviews": unsatisfactory_reviews,
        "review_counts": review_counts,
        "review_years": review_years,
        "programs": programs,
        "current_year": current_year,
        "is_chair": is_chair,
        "is_committee_member": is_committee_member,
        "is_advisor_only": False,
        "can_create_review": is_chair,
        "workspace_role": workspace_role,
        "chair_student_ids": chair_student_ids,
        "committee_student_ids": committee_student_ids,
        "eligible_student_ids": eligible_student_ids,
        "selected_year": selected_year,
        "selected_status": selected_status,
        "selected_program": selected_program,
        "search_query": search_query,
    }

    return render(
        request,
        "leo/AnnualProgress/annual_progress_list.html",
        context,
    )


@login_required
def faculty_annual_progress_detail(
    request,
    uuid,
    phd_student_id,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
        ),
        user__uuid=uuid,
    )

    phd_student = get_object_or_404(
        PhDStudent.objects.select_related(
            "student",
            "student__user",
            "phd_program",
            "phd_program__department",
            "advisor",
            "advisor__user",
        ).prefetch_related(
            Prefetch(
                "doctoral_committee__committee_members",
                queryset=CommitteeMember.objects.select_related(
                    "faculty",
                    "faculty__user",
                    "department",
                ).order_by(
                    "role",
                ),
            ),
        ),
        pk=phd_student_id,
    )

    is_advisor = phd_student.advisor_id == faculty.pk

    is_chair = DoctoralCommittee.objects.filter(
        phd_student=phd_student,
        chair_faculty=faculty,
        approval_status="APPROVED",
    ).exists()

    is_committee_member = CommitteeMember.objects.filter(
        committee__phd_student=phd_student,
        faculty=faculty,
        committee__approval_status="APPROVED",
    ).exists()

    if not (is_advisor or is_chair or is_committee_member):
        raise Http404("You are not authorized to view this student's annual progress.")

    reviews = (
        AnnualProgressReview.objects.filter(
            phd_student=phd_student,
        )
        .select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__phd_program",
            "phd_student__advisor",
            "phd_student__advisor__user",
        )
        .order_by(
            "-review_year",
            "-review_id",
        )
    )

    latest_review = reviews.first()

    previous_reviews = (
        reviews.exclude(
            review_id=latest_review.review_id,
        )
        if latest_review
        else reviews
    )

    committee = getattr(
        phd_student,
        "doctoral_committee",
        None,
    )

    committee_members = (
        committee.committee_members.all()
        if committee
        else CommitteeMember.objects.none()
    )

    candidacy = (
        DoctoralCandidacy.objects.filter(
            phd_student=phd_student,
        )
        .order_by(
            "-pk",
        )
        .first()
    )

    context = {
        "faculty": faculty,
        "phd_student": phd_student,
        "student": phd_student.student,
        "advisor": phd_student.advisor,
        "committee": committee,
        "committee_members": committee_members,
        "candidacy": candidacy,
        "reviews": reviews,
        "latest_review": latest_review,
        "previous_reviews": previous_reviews,
        "is_advisor": is_advisor,
        "is_chair": is_chair,
        "is_committee_member": is_committee_member,
    }

    return render(
        request,
        "leo/AnnualProgress/annual_progress_detail.html",
        context,
    )


@login_required
def faculty_annual_progress_create(
    request,
    uuid,
    phd_student_id,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
        ),
        user__uuid=uuid,
    )

    phd_student = get_object_or_404(
        PhDStudent.objects.select_related(
            "student",
            "student__user",
            "phd_program",
            "advisor",
            "advisor__user",
        ),
        pk=phd_student_id,
        current_status="ACTIVE",
    )

    committee = get_object_or_404(
        DoctoralCommittee.objects.select_related(
            "phd_student",
            "chair_faculty",
            "chair_faculty__user",
        ),
        phd_student=phd_student,
        chair_faculty=faculty,
        approval_status="APPROVED",
    )

    candidacy = (
        DoctoralCandidacy.objects.filter(
            phd_student=phd_student,
            candidacy_status="APPROVED",
        )
        .order_by(
            "-pk",
        )
        .first()
    )

    if not candidacy:
        messages.error(
            request,
            "Cannot create Annual Progress Review. "
            "This student has not yet been granted doctoral candidacy.",
        )

        return redirect(
            "faculty_annual_progress_list",
            uuid=faculty.user.uuid,
        )

    current_year = timezone.now().year

    existing_review = AnnualProgressReview.objects.filter(
        phd_student=phd_student,
        review_year=current_year,
    ).first()

    if existing_review:
        messages.info(
            request,
            f"An annual progress review for {current_year} already exists for this student.",
        )

        return redirect(
            "faculty_annual_progress_list",
            uuid=faculty.user.uuid,
        )

    program_start_year = None

    if phd_student.admission_date:
        program_start_year = phd_student.admission_date.year

    study_year = None

    if program_start_year:
        study_year = current_year - program_start_year + 1

    if request.method == "POST":
        post_data = request.POST.copy()

        post_data["phd_student"] = str(
            phd_student.phd_student_id,
        )

        post_data["review_year"] = str(
            current_year,
        )

        form = AnnualProgressReviewForm(
            post_data,
            faculty=faculty,
        )

        if form.is_valid():
            try:
                review = form.save(
                    commit=False,
                )

                review.phd_student = phd_student
                review.review_year = current_year
                review.save()

                messages.success(
                    request,
                    "Annual progress review created successfully.",
                )

                return redirect(
                    "faculty_annual_progress_list",
                    uuid=faculty.user.uuid,
                )

            except IntegrityError:
                messages.error(
                    request,
                    "This annual progress review already exists.",
                )

                return redirect(
                    "faculty_annual_progress_list",
                    uuid=faculty.user.uuid,
                )

            except Exception:
                messages.error(
                    request,
                    "Unable to save the annual progress review. Please try again.",
                )

                return redirect(
                    "faculty_annual_progress_list",
                    uuid=faculty.user.uuid,
                )

        else:
            messages.error(
                request,
                "Unable to create the annual progress review. Please check the submitted information and try again.",
            )

            return redirect(
                "faculty_annual_progress_list",
                uuid=faculty.user.uuid,
            )

    form = AnnualProgressReviewForm(
        faculty=faculty,
        initial={
            "phd_student": phd_student.phd_student_id,
            "review_year": current_year,
        },
    )

    context = {
        "faculty": faculty,
        "phd_student": phd_student,
        "committee": committee,
        "candidacy": candidacy,
        "form": form,
        "review": None,
        "is_create": True,
        "is_update": False,
        "current_year": current_year,
        "program_start_year": program_start_year,
        "study_year": study_year,
        "form_error_messages": [],
    }

    return render(
        request,
        "leo/AnnualProgress/annual_progress_form.html",
        context,
    )


@login_required
def faculty_annual_progress_update(
    request,
    uuid,
    review_id,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
        ),
        user__uuid=uuid,
    )

    review = get_object_or_404(
        AnnualProgressReview.objects.select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__phd_program",
            "phd_student__advisor",
            "phd_student__advisor__user",
        ),
        pk=review_id,
    )

    phd_student = review.phd_student

    committee = get_object_or_404(
        DoctoralCommittee.objects.select_related(
            "phd_student",
            "chair_faculty",
            "chair_faculty__user",
        ),
        phd_student=phd_student,
        chair_faculty=faculty,
        approval_status="APPROVED",
    )

    candidacy = (
        DoctoralCandidacy.objects.filter(
            phd_student=phd_student,
            candidacy_status="APPROVED",
        )
        .order_by(
            "-pk",
        )
        .first()
    )

    if not candidacy:
        messages.error(
            request,
            "Cannot modify this Annual Progress Review. "
            "This student has not yet been granted doctoral candidacy.",
        )

        return redirect(
            "faculty_annual_progress_list",
            uuid=faculty.user.uuid,
        )

    program_start_year = None

    if phd_student.phd_program:
        program_start_year = getattr(
            phd_student.phd_program,
            "start_year",
            None,
        )

    study_year = None

    if program_start_year:
        study_year = review.review_year - program_start_year + 1

    current_year = timezone.now().year
    form_error_messages = []

    if request.method == "POST":
        post_data = request.POST.copy()

        post_data["phd_student"] = str(
            phd_student.phd_student_id,
        )

        post_data["review_year"] = str(
            review.review_year,
        )

        form = AnnualProgressReviewForm(
            post_data,
            instance=review,
            faculty=faculty,
        )

        if form.is_valid():
            try:
                updated_review = form.save(
                    commit=False,
                )

                updated_review.phd_student = phd_student
                updated_review.review_year = review.review_year
                updated_review.save()

                messages.success(
                    request,
                    "Annual progress review updated successfully.",
                )

                return redirect(
                    "faculty_annual_progress_list",
                    uuid=faculty.user.uuid,
                )

            except Exception:
                messages.error(
                    request,
                    "Unable to update the annual progress review. Please try again.",
                )

        else:
            for field_name, errors in form.errors.items():
                for error in errors:
                    if field_name == "__all__":
                        form_error_messages.append(
                            str(error),
                        )
                    else:
                        field = form.fields.get(
                            field_name,
                        )

                        label = (
                            field.label
                            if field
                            else field_name.replace(
                                "_",
                                " ",
                            ).title()
                        )

                        form_error_messages.append(
                            f"{label}: {error}",
                        )

    else:
        form = AnnualProgressReviewForm(
            instance=review,
            faculty=faculty,
        )

    context = {
        "faculty": faculty,
        "phd_student": phd_student,
        "committee": committee,
        "candidacy": candidacy,
        "form": form,
        "review": review,
        "is_create": False,
        "is_update": True,
        "current_year": current_year,
        "program_start_year": program_start_year,
        "study_year": study_year,
        "form_error_messages": form_error_messages,
    }

    return render(
        request,
        "leo/AnnualProgress/annual_progress_form.html",
        context,
    )


@login_required
def faculty_advisor_annual_progress_all_reviews(request, uuid, phd_student_id):

    faculty = get_object_or_404(
        FacultyProfile.objects.select_related("user"),
        user__uuid=uuid,
    )

    phd_student = get_object_or_404(
        PhDStudent.objects.select_related(
            "student",
            "student__user",
            "phd_program",
            "advisor",
            "advisor__user",
        ),
        phd_student_id=phd_student_id,
    )

    if phd_student.advisor_id != faculty.pk:
        raise Http404("You are not the advisor for this student.")

    reviews = AnnualProgressReview.objects.filter(
        phd_student=phd_student,
    ).order_by("-review_year")

    context = {
        "faculty": faculty,
        "phd_student": phd_student,
        "reviews": reviews,
        "total_reviews": reviews.count(),
    }

    return render(
        request,
        "leo/AnnualProgress/advisor_annual_progress_all_reviews.html",
        context,
    )


###############################################################
# MILESTONE MODULE MANAGEMENT IN FACULTY DASHBOARD
###############################################################


def _timeline_date(value):
    if not value:
        return None

    if hasattr(value, "date"):
        try:
            return value.date()
        except (AttributeError, TypeError):
            pass

    return value


def _student_display_name(student):
    profile = getattr(student, "student", None)

    if profile:
        first_name = getattr(profile, "first_name", "") or ""
        last_name = getattr(profile, "last_name", "") or ""

        full_name = f"{first_name} {last_name}".strip()

        if full_name:
            return full_name

        name = getattr(profile, "name", "") or ""
        if name:
            return name

        user = getattr(profile, "user", None)

        if user:
            full_name = getattr(user, "get_full_name", lambda: "")()

            if full_name:
                return full_name

            username = getattr(user, "username", "") or ""

            if username:
                return username

    first_name = getattr(student, "first_name", "") or ""
    last_name = getattr(student, "last_name", "") or ""

    full_name = f"{first_name} {last_name}".strip()

    if full_name:
        return full_name

    name = getattr(student, "name", "") or ""

    if name:
        return name

    return "Student Name Not Available"


def _student_identifier(student):
    possible_fields = [
        "student_number",
        "student_id",
        "phd_student_id",
    ]

    for field in possible_fields:
        value = getattr(student, field, None)

        if value:
            return str(value)

    profile = getattr(student, "student", None)

    if profile:
        for field in [
            "student_number",
            "student_id",
            "registration_number",
        ]:
            value = getattr(profile, field, None)

            if value:
                return str(value)

    return "N/A"


def _timeline_sort_key(item):
    stage_order = item.get("stage_order", 999)
    date_value = item.get("date")

    if date_value is None:
        return (stage_order, 1, 0)

    try:
        return (stage_order, 0, date_value.toordinal())
    except AttributeError:
        return (stage_order, 0, str(date_value))


def _add_timeline_event(
    timeline,
    event_type,
    title,
    date=None,
    status=None,
    description=None,
    details=None,
    actor=None,
    stage_order=999,
):
    timeline.append(
        {
            "type": event_type,
            "title": title,
            "date": _timeline_date(date),
            "status": status or "Pending",
            "description": description,
            "details": details or [],
            "actor": actor,
            "stage_order": stage_order,
        }
    )


def _build_student_milestone_timeline(student, committee):
    timeline = []

    phd_program = getattr(student, "phd_program", None)

    student_name = _student_display_name(student)
    student_id = _student_identifier(student)

    admission_date = getattr(student, "admission_date", None)

    _add_timeline_event(
        timeline=timeline,
        event_type="admission",
        title="Ph.D. Admission",
        date=admission_date,
        status=student.get_current_status_display(),
        description="Student admission into the Ph.D. program.",
        details=[
            {
                "label": "Student",
                "value": student_name,
            },
            {
                "label": "Student ID",
                "value": student_id,
            },
            {
                "label": "Program",
                "value": str(phd_program) if phd_program else "Not available",
            },
            {
                "label": "Cohort Year",
                "value": getattr(student, "cohort_year", "Not available"),
            },
            {
                "label": "Admission Date",
                "value": admission_date or "Not recorded",
            },
            {
                "label": "Current Status",
                "value": student.get_current_status_display(),
            },
            {
                "label": "Expected Graduation",
                "value": (
                    getattr(student, "expected_graduation_date", None) or "Not recorded"
                ),
            },
        ],
        stage_order=10,
    )

    if student.advisor:
        advisor_assignment_date = getattr(
            student,
            "advisor_assigned_date",
            None,
        )

        if not advisor_assignment_date:
            advisor_assignment_date = getattr(
                student,
                "advisor_assignment_date",
                None,
            )

        if not advisor_assignment_date:
            advisor_assignment_date = admission_date

        advisor_name = str(student.advisor)

        _add_timeline_event(
            timeline=timeline,
            event_type="advisor",
            title="Research Advisor Assigned",
            date=advisor_assignment_date,
            status="Assigned",
            description="Research advisor assigned to the Ph.D. student.",
            actor=student.advisor,
            details=[
                {
                    "label": "Student",
                    "value": student_name,
                },
                {
                    "label": "Advisor",
                    "value": advisor_name,
                },
                {
                    "label": "Assignment Date",
                    "value": (
                        advisor_assignment_date or "Assignment date not recorded"
                    ),
                },
            ],
            stage_order=20,
        )

    if committee:
        committee_members = list(
            committee.committee_members.select_related(
                "faculty",
                "department",
            ).all()
        )

        committee_details = [
            {
                "label": "Student",
                "value": student_name,
            },
            {
                "label": "Chair Faculty",
                "value": str(committee.chair_faculty),
            },
            {
                "label": "Formation Date",
                "value": committee.formation_date or "Not recorded",
            },
            {
                "label": "Approval Status",
                "value": committee.get_approval_status_display(),
            },
        ]

        for member in committee_members:
            committee_details.append(
                {
                    "label": member.get_role_display(),
                    "value": str(member.faculty),
                }
            )

        _add_timeline_event(
            timeline=timeline,
            event_type="committee",
            title="Doctoral Committee Formed",
            date=committee.formation_date,
            status=committee.get_approval_status_display(),
            description="Doctoral committee formation, membership and approval.",
            details=committee_details,
            stage_order=30,
        )

    faculty_courseworks = list(
        FacultyCoursework.objects.filter(
            phd_student=student,
        )
        .select_related(
            "coursework",
            "program",
        )
        .prefetch_related(
            "submission__evaluation__evaluated_by",
        )
    )

    for coursework in faculty_courseworks:
        coursework_name = str(
            getattr(
                getattr(coursework, "coursework", None),
                "coursework_name",
                "Coursework",
            )
        )

        coursework_date = getattr(coursework, "start_date", None) or getattr(
            coursework, "completion_date", None
        )

        coursework_details = [
            {
                "label": "Student",
                "value": student_name,
            },
            {
                "label": "Coursework",
                "value": coursework_name,
            },
            {
                "label": "Academic Year",
                "value": getattr(
                    coursework,
                    "academic_year",
                    "Not available",
                ),
            },
            {
                "label": "Program",
                "value": str(
                    getattr(coursework, "program", None)
                    or phd_program
                    or "Not available"
                ),
            },
            {
                "label": "Start Date",
                "value": getattr(
                    coursework,
                    "start_date",
                    None,
                )
                or "Not recorded",
            },
            {
                "label": "Expected Completion",
                "value": getattr(
                    coursework,
                    "expected_completion_date",
                    None,
                )
                or "Not recorded",
            },
            {
                "label": "Completion Date",
                "value": getattr(
                    coursework,
                    "completion_date",
                    None,
                )
                or "Not completed",
            },
            {
                "label": "Progress",
                "value": (f"{getattr(coursework, 'progress_percentage', 0)}%"),
            },
            {
                "label": "Status",
                "value": coursework.get_status_display(),
            },
            {
                "label": "Faculty Remarks",
                "value": getattr(
                    coursework,
                    "remarks",
                    None,
                )
                or "No remarks",
            },
        ]

        _add_timeline_event(
            timeline=timeline,
            event_type="coursework",
            title=f"Coursework – {coursework_name}",
            date=coursework_date,
            status=coursework.get_status_display(),
            description="Faculty coursework assignment, progress and completion.",
            details=coursework_details,
            stage_order=40,
        )

        try:
            submission = coursework.submission

            submission_details = [
                {
                    "label": "Student",
                    "value": student_name,
                },
                {
                    "label": "Coursework",
                    "value": coursework_name,
                },
                {
                    "label": "Submission Status",
                    "value": submission.get_status_display(),
                },
                {
                    "label": "Submitted At",
                    "value": getattr(
                        submission,
                        "submitted_at",
                        None,
                    )
                    or "Not submitted",
                },
                {
                    "label": "Submission Remarks",
                    "value": getattr(
                        submission,
                        "remarks",
                        None,
                    )
                    or "No remarks",
                },
            ]

            _add_timeline_event(
                timeline=timeline,
                event_type="coursework_submission",
                title=f"Coursework Submission – {coursework_name}",
                date=getattr(submission, "submitted_at", None),
                status=submission.get_status_display(),
                description="Student coursework submission record.",
                details=submission_details,
                stage_order=50,
            )

            try:
                evaluation = submission.evaluation

                evaluation_details = [
                    {
                        "label": "Student",
                        "value": student_name,
                    },
                    {
                        "label": "Coursework",
                        "value": coursework_name,
                    },
                    {
                        "label": "Evaluated By",
                        "value": str(
                            getattr(
                                evaluation,
                                "evaluated_by",
                                None,
                            )
                            or "Not available"
                        ),
                    },
                    {
                        "label": "Marks",
                        "value": getattr(
                            evaluation,
                            "marks",
                            "Not provided",
                        ),
                    },
                    {
                        "label": "Grade",
                        "value": getattr(
                            evaluation,
                            "grade",
                            "Not provided",
                        ),
                    },
                    {
                        "label": "Faculty Feedback",
                        "value": getattr(
                            evaluation,
                            "faculty_feedback",
                            None,
                        )
                        or "No feedback",
                    },
                ]

                _add_timeline_event(
                    timeline=timeline,
                    event_type="coursework_evaluation",
                    title=f"Coursework Evaluation – {coursework_name}",
                    date=getattr(
                        evaluation,
                        "evaluated_at",
                        None,
                    ),
                    status=getattr(
                        evaluation,
                        "grade",
                        None,
                    )
                    or "Evaluated",
                    description="Faculty coursework evaluation and feedback.",
                    actor=getattr(
                        evaluation,
                        "evaluated_by",
                        None,
                    ),
                    details=evaluation_details,
                    stage_order=60,
                )

            except Exception:
                pass

        except Exception:
            pass

    preliminary_examinations = list(
        PreliminaryExamination.objects.filter(
            phd_student=student,
        ).prefetch_related(
            "evaluations__faculty",
        )
    )

    for examination in preliminary_examinations:
        exam_type = examination.get_exam_type_display()

        exam_details = [
            {
                "label": "Student",
                "value": student_name,
            },
            {
                "label": "Exam Type",
                "value": exam_type,
            },
            {
                "label": "Title",
                "value": examination.title or "Not specified",
            },
            {
                "label": "Description",
                "value": examination.description or "No description",
            },
            {
                "label": "Exam Date",
                "value": examination.exam_date or "Not scheduled",
            },
            {
                "label": "Start Time",
                "value": getattr(
                    examination,
                    "start_time",
                    None,
                )
                or "Not recorded",
            },
            {
                "label": "End Time",
                "value": getattr(
                    examination,
                    "end_time",
                    None,
                )
                or "Not recorded",
            },
            {
                "label": "Venue",
                "value": examination.venue or "Not specified",
            },
            {
                "label": "Status",
                "value": examination.get_status_display(),
            },
            {
                "label": "Result",
                "value": examination.get_result_display(),
            },
            {
                "label": "Exam Remarks",
                "value": examination.remarks or "No remarks",
            },
            {
                "label": "Published",
                "value": "Yes" if examination.is_published else "No",
            },
        ]

        _add_timeline_event(
            timeline=timeline,
            event_type="preliminary_exam",
            title=f"{exam_type} Examination",
            date=examination.exam_date,
            status=examination.get_result_display(),
            description="Preliminary / qualifying examination record.",
            details=exam_details,
            stage_order=70,
        )

        for evaluation in examination.evaluations.all():
            evaluation_details = [
                {
                    "label": "Student",
                    "value": student_name,
                },
                {
                    "label": "Faculty",
                    "value": str(evaluation.faculty),
                },
                {
                    "label": "Knowledge Score",
                    "value": evaluation.knowledge_score,
                },
                {
                    "label": "Research Aptitude",
                    "value": evaluation.research_aptitude_score,
                },
                {
                    "label": "Presentation",
                    "value": evaluation.presentation_score,
                },
                {
                    "label": "Technical",
                    "value": evaluation.technical_score,
                },
                {
                    "label": "Recommendation",
                    "value": evaluation.get_recommendation_display(),
                },
                {
                    "label": "Comments",
                    "value": evaluation.comments or "No comments",
                },
                {
                    "label": "Submitted",
                    "value": ("Yes" if evaluation.is_submitted else "No"),
                },
            ]

            _add_timeline_event(
                timeline=timeline,
                event_type="preliminary_evaluation",
                title="Faculty Examination Evaluation",
                date=evaluation.submitted_at,
                status=evaluation.get_recommendation_display(),
                description="Individual faculty examination evaluation.",
                actor=evaluation.faculty,
                details=evaluation_details,
                stage_order=80,
            )

    try:
        proposal = student.dissertation_proposal

        proposal_details = [
            {
                "label": "Student",
                "value": student_name,
            },
            {
                "label": "Proposal Title",
                "value": proposal.proposal_title,
            },
            {
                "label": "Abstract",
                "value": proposal.abstract or "No abstract",
            },
            {
                "label": "Submission Date",
                "value": proposal.submission_date or "Not submitted",
            },
            {
                "label": "Hearing Date",
                "value": proposal.hearing_date or "Not scheduled",
            },
            {
                "label": "Result",
                "value": proposal.get_result_display(),
            },
            {
                "label": "Resubmission Count",
                "value": proposal.resubmission_count,
            },
            {
                "label": "Approved By Committee",
                "value": (
                    str(proposal.approved_by)
                    if proposal.approved_by
                    else "Not approved"
                ),
            },
        ]

        _add_timeline_event(
            timeline=timeline,
            event_type="dissertation_proposal",
            title="Dissertation Proposal",
            date=proposal.submission_date,
            status=proposal.get_result_display(),
            description="Dissertation proposal submission, review and decision.",
            details=proposal_details,
            stage_order=90,
        )

    except Exception:
        pass

    try:
        dissertation = student.dissertation

        dissertation_details = [
            {
                "label": "Student",
                "value": student_name,
            },
            {
                "label": "Dissertation Title",
                "value": dissertation.dissertation_title,
            },
            {
                "label": "Abstract",
                "value": dissertation.abstract or "No abstract",
            },
            {
                "label": "Submission Date",
                "value": dissertation.submission_date or "Not submitted",
            },
            {
                "label": "Current Version",
                "value": dissertation.current_version,
            },
            {
                "label": "Status",
                "value": dissertation.get_status_display(),
            },
        ]

        _add_timeline_event(
            timeline=timeline,
            event_type="dissertation",
            title="Dissertation Submission",
            date=dissertation.submission_date,
            status=dissertation.get_status_display(),
            description="Dissertation submission and review history.",
            details=dissertation_details,
            stage_order=100,
        )

        for evaluation in dissertation.committee_evaluations.select_related(
            "committee_member__faculty",
        ).all():
            evaluation_details = [
                {
                    "label": "Student",
                    "value": student_name,
                },
                {
                    "label": "Committee Member",
                    "value": str(evaluation.committee_member.faculty),
                },
                {
                    "label": "Role",
                    "value": evaluation.committee_member.get_role_display(),
                },
                {
                    "label": "Score",
                    "value": (
                        evaluation.score
                        if evaluation.score is not None
                        else "Not provided"
                    ),
                },
                {
                    "label": "Recommendation",
                    "value": evaluation.get_recommendation_display(),
                },
                {
                    "label": "Remarks",
                    "value": evaluation.remarks or "No remarks",
                },
                {
                    "label": "Submitted",
                    "value": ("Yes" if evaluation.is_submitted else "No"),
                },
            ]

            _add_timeline_event(
                timeline=timeline,
                event_type="dissertation_evaluation",
                title="Committee Dissertation Evaluation",
                date=evaluation.submitted_at,
                status=evaluation.get_recommendation_display(),
                actor=evaluation.committee_member.faculty,
                description="Committee member dissertation evaluation.",
                details=evaluation_details,
                stage_order=110,
            )

        try:
            approval = dissertation.final_approval

            approval_details = [
                {
                    "label": "Student",
                    "value": student_name,
                },
                {
                    "label": "Chair Faculty",
                    "value": str(approval.chair_faculty),
                },
                {
                    "label": "Decision",
                    "value": approval.get_decision_display(),
                },
                {
                    "label": "Final Remarks",
                    "value": approval.final_remarks or "No final remarks",
                },
                {
                    "label": "Approved At",
                    "value": approval.approved_at or "Not approved",
                },
                {
                    "label": "Allow Resubmission",
                    "value": ("Yes" if approval.allow_resubmission else "No"),
                },
                {
                    "label": "Reopened Count",
                    "value": approval.reopened_count,
                },
                {
                    "label": "Resubmission Deadline",
                    "value": (approval.resubmission_deadline or "Not applicable"),
                },
            ]

            _add_timeline_event(
                timeline=timeline,
                event_type="dissertation_approval",
                title="Dissertation Final Approval",
                date=approval.approved_at,
                status=approval.get_decision_display(),
                actor=approval.chair_faculty,
                description="Final dissertation decision by chair faculty.",
                details=approval_details,
                stage_order=120,
            )

        except Exception:
            pass

        try:
            advisor_feedback = dissertation.advisor_feedback

            feedback_details = [
                {
                    "label": "Student",
                    "value": student_name,
                },
                {
                    "label": "Advisor",
                    "value": str(advisor_feedback.advisor),
                },
                {
                    "label": "Advisor Feedback",
                    "value": advisor_feedback.advisor_feedback,
                },
                {
                    "label": "Remarks",
                    "value": advisor_feedback.remarks or "No remarks",
                },
                {
                    "label": "Status",
                    "value": advisor_feedback.get_status_display(),
                },
                {
                    "label": "Submitted",
                    "value": ("Yes" if advisor_feedback.is_submitted else "No"),
                },
            ]

            _add_timeline_event(
                timeline=timeline,
                event_type="advisor_feedback",
                title="Advisor Feedback",
                date=advisor_feedback.submitted_at,
                status=advisor_feedback.get_status_display(),
                actor=advisor_feedback.advisor,
                description="Advisor feedback and dissertation remarks.",
                details=feedback_details,
                stage_order=130,
            )

            try:
                chair_reply = advisor_feedback.chair_reply_feedback

                reply_details = [
                    {
                        "label": "Student",
                        "value": student_name,
                    },
                    {
                        "label": "Chair Faculty",
                        "value": str(chair_reply.chair_faculty),
                    },
                    {
                        "label": "Chair Reply",
                        "value": chair_reply.chair_reply_feedback,
                    },
                    {
                        "label": "Remarks",
                        "value": chair_reply.remarks or "No remarks",
                    },
                    {
                        "label": "Decision",
                        "value": chair_reply.get_decision_display(),
                    },
                    {
                        "label": "Status",
                        "value": chair_reply.get_status_display(),
                    },
                ]

                _add_timeline_event(
                    timeline=timeline,
                    event_type="chair_reply",
                    title="Chair Faculty → Advisor Communication",
                    date=chair_reply.replied_at,
                    status=chair_reply.get_decision_display(),
                    actor=chair_reply.chair_faculty,
                    description="Chair response to advisor feedback.",
                    details=reply_details,
                    stage_order=140,
                )

            except Exception:
                pass

        except Exception:
            pass

        try:
            advisor_advice = dissertation.advisor_advice

            advice_details = [
                {
                    "label": "Student",
                    "value": student_name,
                },
                {
                    "label": "Advisor",
                    "value": str(advisor_advice.advisor),
                },
                {
                    "label": "Guidance / Advice",
                    "value": advisor_advice.advice,
                },
                {
                    "label": "Submitted",
                    "value": ("Yes" if advisor_advice.is_submitted else "No"),
                },
            ]

            _add_timeline_event(
                timeline=timeline,
                event_type="advisor_guidance",
                title="Advisor Guidance",
                date=advisor_advice.submitted_at,
                status=("Submitted" if advisor_advice.is_submitted else "Draft"),
                actor=advisor_advice.advisor,
                description="Advisor guidance and research advice.",
                details=advice_details,
                stage_order=150,
            )

        except Exception:
            pass

    except Exception:
        pass

    try:
        candidacy = student.doctoral_candidacy

        candidacy_details = [
            {
                "label": "Student",
                "value": student_name,
            },
            {
                "label": "Candidacy Date",
                "value": candidacy.candidacy_date,
            },
            {
                "label": "Status",
                "value": candidacy.get_candidacy_status_display(),
            },
            {
                "label": "Approval Date",
                "value": (candidacy.approval_date or "Not approved"),
            },
        ]

        _add_timeline_event(
            timeline=timeline,
            event_type="candidacy",
            title="Doctoral Candidacy",
            date=candidacy.candidacy_date,
            status=candidacy.get_candidacy_status_display(),
            description="Doctoral candidacy status and approval history.",
            details=candidacy_details,
            stage_order=160,
        )

        if candidacy.approval_date:
            _add_timeline_event(
                timeline=timeline,
                event_type="candidacy_approval",
                title="Doctoral Candidacy Decision",
                date=candidacy.approval_date,
                status=candidacy.get_candidacy_status_display(),
                description="Final doctoral candidacy decision.",
                details=[
                    {
                        "label": "Student",
                        "value": student_name,
                    },
                    {
                        "label": "Decision",
                        "value": candidacy.get_candidacy_status_display(),
                    },
                    {
                        "label": "Approval Date",
                        "value": candidacy.approval_date,
                    },
                ],
                stage_order=170,
            )

    except Exception:
        pass

    annual_reviews = list(
        AnnualProgressReview.objects.filter(
            phd_student=student,
        )
    )

    for review in annual_reviews:
        review_date = (
            getattr(review, "review_date", None)
            or getattr(review, "submitted_at", None)
            or getattr(review, "created_at", None)
        )

        _add_timeline_event(
            timeline=timeline,
            event_type="annual_progress",
            title=f"Annual Progress Review – {review.review_year}",
            date=review_date,
            status=review.get_status_display(),
            description="Annual Ph.D. academic progress review.",
            details=[
                {
                    "label": "Student",
                    "value": student_name,
                },
                {
                    "label": "Review Year",
                    "value": review.review_year,
                },
                {
                    "label": "Progress Score",
                    "value": review.progress_score,
                },
                {
                    "label": "Status",
                    "value": review.get_status_display(),
                },
                {
                    "label": "Committee Comments",
                    "value": review.committee_comments or "No comments",
                },
            ],
            stage_order=180,
        )

    publications = list(
        ResearchPublication.objects.filter(
            phd_student=student,
        )
    )

    for publication in publications:
        _add_timeline_event(
            timeline=timeline,
            event_type="publication",
            title=f"Research Publication – {publication.title}",
            date=publication.publication_date,
            status=publication.get_indexed_status_display(),
            description="Research publication record.",
            details=[
                {
                    "label": "Student",
                    "value": student_name,
                },
                {
                    "label": "Title",
                    "value": publication.title,
                },
                {
                    "label": "Journal",
                    "value": publication.journal,
                },
                {
                    "label": "Publication Date",
                    "value": publication.publication_date,
                },
                {
                    "label": "DOI",
                    "value": publication.doi or "Not provided",
                },
                {
                    "label": "Indexing Status",
                    "value": publication.get_indexed_status_display(),
                },
            ],
            stage_order=190,
        )

    try:
        defense = student.dissertation_defense

        _add_timeline_event(
            timeline=timeline,
            event_type="defense",
            title="Dissertation Defense",
            date=defense.defense_date,
            status=defense.get_result_display(),
            description="Final dissertation defense.",
            details=[
                {
                    "label": "Student",
                    "value": student_name,
                },
                {
                    "label": "Defense Date",
                    "value": defense.defense_date,
                },
                {
                    "label": "Location",
                    "value": defense.location,
                },
                {
                    "label": "Result",
                    "value": defense.get_result_display(),
                },
                {
                    "label": "Committee Decision",
                    "value": defense.get_committee_decision_display(),
                },
                {
                    "label": "Final Comments",
                    "value": defense.final_comments or "No final comments",
                },
            ],
            stage_order=200,
        )

    except Exception:
        pass

    try:
        graduation = student.graduation

        _add_timeline_event(
            timeline=timeline,
            event_type="graduation",
            title="Graduation",
            date=graduation.graduation_date,
            status="Completed",
            description="Ph.D. graduation and degree award.",
            details=[
                {
                    "label": "Student",
                    "value": student_name,
                },
                {
                    "label": "Graduation Date",
                    "value": graduation.graduation_date,
                },
                {
                    "label": "Degree Awarded",
                    "value": graduation.degree_awarded,
                },
                {
                    "label": "Final GPA",
                    "value": graduation.final_gpa,
                },
                {
                    "label": "Dissertation Accepted",
                    "value": ("Yes" if graduation.dissertation_accepted else "No"),
                },
            ],
            stage_order=210,
        )

    except Exception:
        pass

    milestones = list(
        PhDMilestone.objects.filter(
            phd_student=student,
        )
    )

    for milestone in milestones:
        _add_timeline_event(
            timeline=timeline,
            event_type="milestone",
            title=milestone.milestone_name,
            date=milestone.completion_date,
            status=milestone.get_status_display(),
            description="Additional Ph.D. milestone tracking record.",
            details=[
                {
                    "label": "Student",
                    "value": student_name,
                },
                {
                    "label": "Milestone",
                    "value": milestone.milestone_name,
                },
                {
                    "label": "Status",
                    "value": milestone.get_status_display(),
                },
                {
                    "label": "Completion Date",
                    "value": (milestone.completion_date or "Not completed"),
                },
            ],
            stage_order=175,
        )

    timeline.sort(key=_timeline_sort_key)

    return timeline


@login_required
def faculty_milestone_list(request, uuid):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related("user"),
        user__uuid=uuid,
    )

    current_faculty = get_object_or_404(
        FacultyProfile.objects.select_related("user"),
        user=request.user,
    )

    chair_committees = (
        DoctoralCommittee.objects.filter(
            chair_faculty=current_faculty,
            approval_status="APPROVED",
        )
        .select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__phd_program",
            "phd_student__advisor",
            "chair_faculty",
        )
        .prefetch_related(
            "committee_members__faculty",
            "committee_members__department",
        )
        .distinct()
    )

    member_committees = (
        DoctoralCommittee.objects.filter(
            committee_members__faculty=current_faculty,
            approval_status="APPROVED",
        )
        .select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__phd_program",
            "phd_student__advisor",
            "chair_faculty",
        )
        .prefetch_related(
            "committee_members__faculty",
            "committee_members__department",
        )
        .distinct()
    )

    is_chair = chair_committees.exists()
    is_committee_member = member_committees.exists()

    if not is_chair and not is_committee_member:
        messages.error(
            request,
            "You are not authorized to access committee milestones.",
        )
        return redirect("faculty_dashboard")

    if is_chair and is_committee_member:
        committees = (
            DoctoralCommittee.objects.filter(
                Q(chair_faculty=current_faculty)
                | Q(committee_members__faculty=current_faculty),
                approval_status="APPROVED",
            )
            .select_related(
                "phd_student",
                "phd_student__student",
                "phd_student__phd_program",
                "phd_student__advisor",
                "chair_faculty",
            )
            .prefetch_related(
                "committee_members__faculty",
                "committee_members__department",
            )
            .distinct()
        )

        page_role = "chair_committee"

    elif is_chair:
        committees = chair_committees
        page_role = "chair"

    else:
        committees = member_committees
        page_role = "committee"

    search_query = request.GET.get(
        "search",
        "",
    ).strip()

    status_filter = request.GET.get(
        "status",
        "",
    ).strip()

    if status_filter:
        committees = committees.filter(
            phd_student__current_status=status_filter,
        )

    if search_query:
        committees = committees.filter(
            Q(
                phd_student__student__student_number__icontains=search_query,
            )
            | Q(
                phd_student__student__first_name__icontains=search_query,
            )
            | Q(
                phd_student__student__last_name__icontains=search_query,
            )
            | Q(
                phd_student__phd_program__program_name__icontains=search_query,
            )
        ).distinct()

    students = []

    for committee in committees:
        student = committee.phd_student

        timeline = _build_student_milestone_timeline(
            student=student,
            committee=committee,
        )

        students.append(
            {
                "student": student,
                "student_name": _student_display_name(student),
                "student_id": _student_identifier(student),
                "committee": committee,
                "timeline": timeline,
                "timeline_count": len(timeline),
            }
        )

    students.sort(
        key=lambda item: (
            str(
                item.get(
                    "student_name",
                    "",
                )
            ).casefold(),
            str(
                item.get(
                    "student_id",
                    "",
                )
            ).casefold(),
        )
    )

    context = {
        "faculty": faculty,
        "current_faculty": current_faculty,
        "students": students,
        "is_chair": is_chair,
        "is_committee_member": is_committee_member,
        "is_advisor": False,
        "page_role": page_role,
        "search_query": search_query,
        "status_filter": status_filter,
        "status_choices": PhDStudent.STATUS_CHOICES,
        "student_count": len(students),
    }

    return render(
        request,
        "leo/milestones/faculty_milestone_list.html",
        context,
    )


@login_required
def faculty_milestone_advisor(request, uuid):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related("user"),
        user__uuid=uuid,
    )

    current_faculty = get_object_or_404(
        FacultyProfile.objects.select_related("user"),
        user=request.user,
    )

    advisor_students = (
        PhDStudent.objects.filter(
            advisor=current_faculty,
        )
        .select_related(
            "student",
            "phd_program",
            "advisor",
        )
        .distinct()
    )

    search_query = request.GET.get(
        "search",
        "",
    ).strip()

    status_filter = request.GET.get(
        "status",
        "",
    ).strip()

    if status_filter:
        advisor_students = advisor_students.filter(
            current_status=status_filter,
        )

    if search_query:
        advisor_students = advisor_students.filter(
            Q(
                student__student_number__icontains=search_query,
            )
            | Q(
                student__first_name__icontains=search_query,
            )
            | Q(
                student__last_name__icontains=search_query,
            )
            | Q(
                phd_program__program_name__icontains=search_query,
            )
        ).distinct()

    students = []

    for student in advisor_students:
        committee = (
            DoctoralCommittee.objects.filter(
                phd_student=student,
                approval_status="APPROVED",
            )
            .select_related(
                "phd_student",
                "phd_student__student",
                "phd_student__phd_program",
                "phd_student__advisor",
                "chair_faculty",
            )
            .prefetch_related(
                "committee_members__faculty",
                "committee_members__department",
            )
            .first()
        )

        timeline = _build_student_milestone_timeline(
            student=student,
            committee=committee,
        )

        students.append(
            {
                "student": student,
                "student_name": _student_display_name(student),
                "student_id": _student_identifier(student),
                "committee": committee,
                "timeline": timeline,
                "timeline_count": len(timeline),
            }
        )

    students.sort(
        key=lambda item: (
            str(
                item.get(
                    "student_name",
                    "",
                )
            ).casefold(),
            str(
                item.get(
                    "student_id",
                    "",
                )
            ).casefold(),
        )
    )

    context = {
        "faculty": faculty,
        "current_faculty": current_faculty,
        "students": students,
        "is_chair": False,
        "is_committee_member": False,
        "is_advisor": True,
        "page_role": "advisor",
        "search_query": search_query,
        "status_filter": status_filter,
        "status_choices": PhDStudent.STATUS_CHOICES,
        "student_count": len(students),
    }

    return render(
        request,
        "leo/milestones/faculty_milestone_list.html",
        context,
    )


@login_required
def faculty_milestone_detail(request, uuid, phd_student_id):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related("user"),
        user__uuid=uuid,
    )

    current_faculty = get_object_or_404(
        FacultyProfile.objects.select_related("user"),
        user=request.user,
    )

    student = get_object_or_404(
        PhDStudent.objects.select_related(
            "student",
            "phd_program",
            "advisor",
        ),
        phd_student_id=phd_student_id,
    )

    is_advisor = student.advisor == current_faculty

    committee = (
        DoctoralCommittee.objects.filter(
            phd_student=student,
            approval_status="APPROVED",
        )
        .select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__phd_program",
            "phd_student__advisor",
            "chair_faculty",
        )
        .prefetch_related(
            "committee_members__faculty",
            "committee_members__department",
        )
        .first()
    )

    is_chair = False
    is_committee_member = False

    if committee:
        is_chair = committee.chair_faculty == current_faculty
        is_committee_member = CommitteeMember.objects.filter(
            committee=committee,
            faculty=current_faculty,
        ).exists()

    if not is_chair and not is_committee_member and not is_advisor:
        messages.error(
            request,
            "You are not authorized to view this student's milestones.",
        )

        return redirect(
            "faculty_milestone_list",
            uuid=faculty.user.uuid,
        )

    student_name = _student_display_name(student)
    student_id = _student_identifier(student)

    timeline = _build_student_milestone_timeline(
        student=student,
        committee=committee,
    )

    completed_statuses = {
        "Completed",
        "Approved",
        "Pass",
        "Passed",
        "Satisfactory",
        "Accepted",
        "Complete",
        "COMPLETED",
        "APPROVED",
        "PASS",
        "PASSED",
        "SATISFACTORY",
        "ACCEPTED",
    }

    pending_statuses = {
        "Pending",
        "In Progress",
        "Under Review",
        "Needs Improvement",
        "ON_HOLD",
        "On Hold",
        "PENDING",
        "IN_PROGRESS",
        "UNDER_REVIEW",
        "NEEDS_IMPROVEMENT",
    }

    completed_count = sum(
        1
        for event in timeline
        if str(event.get("status", "")).strip() in completed_statuses
    )

    pending_count = sum(
        1
        for event in timeline
        if str(event.get("status", "")).strip() in pending_statuses
    )

    total_count = len(timeline)

    completion_percentage = 0

    if total_count:
        completion_percentage = round((completed_count / total_count) * 100)

    student_profile = getattr(
        student,
        "student",
        None,
    )

    advisor = getattr(
        student,
        "advisor",
        None,
    )

    phd_program = getattr(
        student,
        "phd_program",
        None,
    )

    student_information = {
        "name": student_name,
        "student_id": student_id,
        "status": getattr(
            student,
            "current_status",
            None,
        ),
        "program": phd_program,
        "advisor": advisor,
        "profile": student_profile,
        "phd_student": student,
    }

    committee_members = []

    if committee:
        committee_members = list(committee.committee_members.all())

    committee_information = {
        "committee": committee,
        "chair": (committee.chair_faculty if committee else None),
        "members": committee_members,
        "formation_date": (
            getattr(
                committee,
                "formation_date",
                None,
            )
            if committee
            else None
        ),
        "approval_status": (
            getattr(
                committee,
                "approval_status",
                None,
            )
            if committee
            else None
        ),
    }

    academic_records = []

    seen_records = set()

    for field in student._meta.get_fields():

        if not field.auto_created:
            continue

        if not field.is_relation:
            continue

        accessor_name = getattr(
            field,
            "get_accessor_name",
            lambda: None,
        )()

        if not accessor_name:
            continue

        try:
            related_manager = getattr(
                student,
                accessor_name,
            )
        except Exception:
            continue

        try:
            if hasattr(
                related_manager,
                "all",
            ):
                related_objects = list(related_manager.all())
            else:
                related_objects = [related_manager]
        except Exception:
            continue

        for related_object in related_objects:

            if related_object is None:
                continue

            object_key = (
                related_object.__class__,
                getattr(
                    related_object,
                    related_object._meta.pk.name,
                    None,
                ),
            )

            if object_key in seen_records:
                continue

            seen_records.add(object_key)

            record = {
                "object": related_object,
                "model_name": (related_object._meta.verbose_name.title()),
                "model_key": (related_object._meta.model_name),
                "fields": [],
            }

            for related_field in related_object._meta.fields:

                field_name = related_field.name

                if (
                    field_name == related_object._meta.pk.name
                    or field_name == "is_full_crud"
                ):
                    continue

                try:
                    value = getattr(
                        related_object,
                        field_name,
                    )
                except Exception:
                    continue

                if value is None:
                    continue

                if related_field.is_relation:
                    try:
                        value = str(value)
                    except Exception:
                        continue

                if value == "":
                    continue

                label = related_field.verbose_name.replace("_", " ").title()

                record["fields"].append(
                    {
                        "name": field_name,
                        "label": label,
                        "value": value,
                    }
                )

            if record["fields"]:
                academic_records.append(record)

    if committee:
        committee_record_key = (
            committee.__class__,
            getattr(
                committee,
                committee._meta.pk.name,
                None,
            ),
        )

        if committee_record_key not in seen_records:
            committee_record = {
                "object": committee,
                "model_name": (committee._meta.verbose_name.title()),
                "model_key": (committee._meta.model_name),
                "fields": [],
            }

            for committee_field in committee._meta.fields:

                field_name = committee_field.name

                if (
                    field_name == committee._meta.pk.name
                    or field_name == "is_full_crud"
                ):
                    continue

                try:
                    value = getattr(
                        committee,
                        field_name,
                    )
                except Exception:
                    continue

                if value is None:
                    continue

                if committee_field.is_relation:
                    try:
                        value = str(value)
                    except Exception:
                        continue

                if value == "":
                    continue

                label = committee_field.verbose_name.replace("_", " ").title()

                committee_record["fields"].append(
                    {
                        "name": field_name,
                        "label": label,
                        "value": value,
                    }
                )

            if committee_record["fields"]:
                academic_records.append(committee_record)

    academic_records.sort(key=lambda item: item["model_name"].lower())

    history_sections = []

    section_keywords = {
        "admission": [
            "admission",
            "phdstudent",
        ],
        "advisor": [
            "advisor",
            "supervisor",
        ],
        "committee": [
            "committee",
            "committeemember",
        ],
        "coursework": [
            "coursework",
            "course",
            "submission",
        ],
        "examination": [
            "examination",
            "exam",
            "evaluation",
            "preliminary",
            "qualifying",
        ],
        "candidacy": [
            "candidacy",
            "candidate",
        ],
        "proposal": [
            "proposal",
            "dissertationproposal",
        ],
        "dissertation": [
            "dissertation",
            "thesis",
        ],
        "annual_progress": [
            "annualprogress",
            "annual_progress",
            "progressreview",
            "progress_review",
        ],
        "publication": [
            "publication",
            "researchpublication",
            "research_publication",
        ],
        "defense": [
            "defense",
            "viva",
        ],
        "graduation": [
            "graduation",
            "degree",
        ],
        "communication": [
            "communication",
            "message",
            "feedback",
            "guidance",
            "remark",
            "comment",
        ],
    }

    grouped_records = {key: [] for key in section_keywords}

    grouped_records["other"] = []

    for record in academic_records:

        model_key = record["model_key"].lower()

        model_name = record["model_name"].lower()

        matched_section = None

        for section, keywords in section_keywords.items():

            if any(
                keyword in model_key or keyword in model_name for keyword in keywords
            ):
                matched_section = section
                break

        if matched_section:
            grouped_records[matched_section].append(record)
        else:
            grouped_records["other"].append(record)

    section_titles = {
        "admission": "Ph.D. Admission",
        "advisor": "Research Advisor",
        "committee": "Doctoral Committee",
        "coursework": "Coursework",
        "examination": "Examinations & Evaluations",
        "candidacy": "Doctoral Candidacy",
        "proposal": "Dissertation Proposal",
        "dissertation": "Dissertation",
        "annual_progress": "Annual Progress Reviews",
        "publication": "Research Publications",
        "defense": "Dissertation Defense",
        "graduation": "Graduation",
        "communication": "Remarks, Guidance & Communication",
        "other": "Additional Academic Records",
    }

    section_order = [
        "admission",
        "advisor",
        "committee",
        "coursework",
        "examination",
        "candidacy",
        "proposal",
        "dissertation",
        "annual_progress",
        "publication",
        "defense",
        "graduation",
        "communication",
        "other",
    ]

    for section_key in section_order:

        records = grouped_records.get(
            section_key,
            [],
        )

        if records:
            history_sections.append(
                {
                    "key": section_key,
                    "title": section_titles[section_key],
                    "records": records,
                }
            )

    status = getattr(
        student,
        "current_status",
        "",
    )

    admission_date = getattr(
        student,
        "admission_date",
        None,
    )

    formation_date = (
        getattr(
            committee,
            "formation_date",
            None,
        )
        if committee
        else None
    )

    academic_summary = {
        "current_status": status,
        "admission_date": admission_date,
        "committee_formation_date": formation_date,
        "total_milestones": total_count,
        "completed_milestones": completed_count,
        "pending_milestones": pending_count,
        "completion_percentage": completion_percentage,
    }

    if is_advisor:
        access_role = "advisor"
    elif is_chair and is_committee_member:
        access_role = "chair_committee"
    elif is_chair:
        access_role = "chair"
    else:
        access_role = "committee_member"

    context = {
        "faculty": faculty,
        "current_faculty": current_faculty,
        "student": student,
        "student_name": student_name,
        "student_id": student_id,
        "student_information": student_information,
        "committee": committee,
        "committee_information": committee_information,
        "committee_members": committee_members,
        "advisor": advisor,
        "phd_program": phd_program,
        "student_profile": student_profile,
        "timeline": timeline,
        "timeline_count": total_count,
        "completed_count": completed_count,
        "pending_count": pending_count,
        "completion_percentage": completion_percentage,
        "academic_summary": academic_summary,
        "academic_records": academic_records,
        "history_sections": history_sections,
        "is_chair": is_chair,
        "is_committee_member": is_committee_member,
        "is_advisor": is_advisor,
        "access_role": access_role,
    }

    return render(
        request,
        "leo/milestones/faculty_milestone_detail.html",
        context,
    )


#####################################
### RESEARCH MODULE STARTS HERE #####
#####################################

####################################################
### RESEARCH MODULE COMMITTEE SIDE STARTS HERE #####
####################################################

from django.core.exceptions import PermissionDenied


@login_required
def research_milestone_list(
    request,
    uuid,
):

    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
        ),
        user__uuid=uuid,
    )

    chair_student_ids = list(
        DoctoralCommittee.objects.filter(
            chair_faculty=faculty,
            approval_status="APPROVED",
        ).values_list(
            "phd_student_id",
            flat=True,
        )
    )

    committee_student_ids = list(
        CommitteeMember.objects.filter(
            faculty=faculty,
            committee__approval_status="APPROVED",
            role__in=[
                "CO_CHAIR",
                "INTERNAL_MEMBER",
                "EXTERNAL_MEMBER",
            ],
        ).values_list(
            "committee__phd_student_id",
            flat=True,
        )
    )

    advisor_student_ids = list(
        PhDStudent.objects.filter(
            advisor=faculty,
            current_status="ACTIVE",
        ).values_list(
            "phd_student_id",
            flat=True,
        )
    )

    has_committee_access = bool(chair_student_ids or committee_student_ids)

    if not has_committee_access:
        raise PermissionDenied(
            "You do not have access to the Research Milestones workspace."
        )

    allowed_student_ids = set(
        chair_student_ids
        + committee_student_ids
        + advisor_student_ids
    )

    phd_students = (
        PhDStudent.objects.filter(
            phd_student_id__in=allowed_student_ids,
            current_status="ACTIVE",
        )
        .select_related(
            "student",
            "student__user",
            "phd_program",
            "advisor",
            "advisor__user",
        )
        .order_by(
            "student__user__first_name",
            "student__user__last_name",
        )
    )

    milestones = list(
        ResearchMilestone.objects.filter(
            phd_student_id__in=allowed_student_ids,
        )
        .select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__phd_program",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "chair_faculty",
            "chair_faculty__user",
        )
        .prefetch_related(
            "submissions",
            "submissions__evaluations",
            "submissions__evaluations__evaluator",
            "submissions__evaluations__evaluator__user",
            "submissions__advisor_advices",
            "submissions__advisor_advices__advisor",
            "submissions__advisor_advices__advisor__user",
        )
        .order_by(
            "phd_student_id",
            "-sequence_number",
            "-updated_at",
        )
    )

    milestone_map = {}

    for milestone in milestones:
        milestone_map.setdefault(
            milestone.phd_student_id,
            [],
        ).append(
            milestone,
        )

    student_cards = []

    for phd_student in phd_students:

        history = milestone_map.get(
            phd_student.phd_student_id,
            [],
        )

        latest_milestone = history[0] if history else None

        latest_timestamp = latest_milestone.updated_at if latest_milestone else None

        latest_submission = None

        display_status = "NO_MILESTONE"

        latest_evaluation = None

        committee_evaluations = []

        chair_evaluation = None

        advisor_advice = None

        committee_members = []

        required_committee_count = 0

        completed_committee_count = 0

        committee_evaluation_percentage = 0

        committee_evaluation_complete = False

        chair_review_pending = False

        faculty_evaluation = None

        can_evaluate = False

        can_finalize = False

        if latest_milestone:

            committee = (
                DoctoralCommittee.objects.filter(
                    phd_student=phd_student,
                    approval_status="APPROVED",
                )
                .select_related(
                    "chair_faculty",
                    "chair_faculty__user",
                )
                .first()
            )

            if committee:

                committee_members = list(
                    CommitteeMember.objects.filter(
                        committee=committee,
                        role__in=[
                            "CO_CHAIR",
                            "INTERNAL_MEMBER",
                            "EXTERNAL_MEMBER",
                        ],
                    )
                    .select_related(
                        "faculty",
                        "faculty__user",
                    )
                    .order_by(
                        "role",
                        "faculty__user__first_name",
                        "faculty__user__last_name",
                    )
                )

                required_committee_count = len(committee_members)

            submissions = list(latest_milestone.submissions.all())

            submissions.sort(
                key=lambda submission: (
                    submission.submission_number,
                    submission.submitted_at,
                ),
                reverse=True,
            )

            latest_submission = submissions[0] if submissions else None

            display_status = latest_milestone.status

            if latest_submission:

                submission_evaluations = list(
                    latest_submission.evaluations.all()
                    .select_related(
                        "evaluator",
                        "evaluator__user",
                    )
                    .order_by(
                        "-evaluated_at",
                    )
                )

                committee_faculty_ids = {
                    member.faculty_id for member in committee_members
                }

                committee_evaluations = [
                    evaluation
                    for evaluation in submission_evaluations
                    if (
                        evaluation.evaluator_role == "COMMITTEE_MEMBER"
                        and evaluation.evaluator_id in committee_faculty_ids
                    )
                ]

                chair_evaluations = [
                    evaluation
                    for evaluation in submission_evaluations
                    if evaluation.evaluator_role == "CHAIR"
                ]

                chair_evaluation = chair_evaluations[0] if chair_evaluations else None

                latest_evaluation = (
                    submission_evaluations[0] if submission_evaluations else None
                )

                advisor_advice = (
                    latest_submission.advisor_advices.all()
                    .order_by(
                        "-submitted_at",
                        "-created_at",
                    )
                    .first()
                )

                evaluated_faculty_ids = {
                    evaluation.evaluator_id
                    for evaluation in committee_evaluations
                    if evaluation.evaluator_id in committee_faculty_ids
                }

                completed_committee_count = len(evaluated_faculty_ids)

                if required_committee_count > 0:

                    committee_evaluation_percentage = round(
                        (completed_committee_count / required_committee_count) * 100
                    )

                committee_evaluation_complete = (
                    required_committee_count > 0
                    and completed_committee_count >= required_committee_count
                )

                faculty_evaluation = next(
                    (
                        evaluation
                        for evaluation in submission_evaluations
                        if evaluation.evaluator_id == faculty.pk
                    ),
                    None,
                )

                submission_status = latest_submission.status

                if latest_milestone.status == "COMPLETED":

                    display_status = "COMPLETED"

                elif (
                    chair_evaluation
                    and chair_evaluation.decision == "REVISION_REQUIRED"
                ):

                    display_status = "REVISION_REQUIRED"

                elif chair_evaluation:

                    display_status = chair_evaluation.decision

                elif committee_evaluation_complete:

                    display_status = "CHAIR_REVIEW_PENDING"

                    chair_review_pending = True

                elif committee_evaluations:

                    display_status = "UNDER_REVIEW"

                elif submission_status == "REVISION_REQUIRED":

                    display_status = "REVISION_REQUIRED"

                elif submission_status in [
                    "SUBMITTED",
                    "UNDER_REVIEW",
                ]:

                    display_status = submission_status

                elif submission_status == "EVALUATED":

                    display_status = latest_milestone.status

                if (
                    committee
                    and latest_milestone.status != "COMPLETED"
                    and submission_status
                    in [
                        "SUBMITTED",
                        "UNDER_REVIEW",
                    ]
                ):

                    if faculty.pk in committee_faculty_ids and not faculty_evaluation:

                        can_evaluate = True

                    if (
                        committee.chair_faculty_id == faculty.pk
                        and committee_evaluation_complete
                        and not chair_evaluation
                    ):

                        can_finalize = True

        student_cards.append(
            {
                "student": phd_student,
                "latest": latest_milestone,
                "latest_submission": latest_submission,
                "display_status": display_status,
                "latest_evaluation": latest_evaluation,
                "committee_evaluations": committee_evaluations,
                "chair_evaluation": chair_evaluation,
                "advisor_advice": advisor_advice,
                "committee_members": committee_members,
                "required_committee_count": (required_committee_count),
                "completed_committee_count": (completed_committee_count),
                "committee_evaluation_percentage": (committee_evaluation_percentage),
                "committee_evaluation_complete": (committee_evaluation_complete),
                "chair_review_pending": (chair_review_pending),
                "faculty_evaluation": faculty_evaluation,
                "can_evaluate": can_evaluate,
                "can_finalize": can_finalize,
                "history": history,
                "latest_timestamp": latest_timestamp,
                "is_chair": (phd_student.phd_student_id in chair_student_ids),
                "is_advisor": (phd_student.phd_student_id in advisor_student_ids),
                "is_committee_member": (
                    phd_student.phd_student_id in committee_student_ids
                ),
            }
        )

    student_cards.sort(
        key=lambda card: (
            card["latest_timestamp"] is not None,
            card["latest_timestamp"]
            or timezone.make_aware(
                datetime.min,
            ),
        ),
        reverse=True,
    )

    total_milestones = len(milestones)

    progress_count = sum(
        1 for milestone in milestones if milestone.status == "IN_PROGRESS"
    )

    review_count = sum(
        1 for milestone in milestones if milestone.status == "UNDER_REVIEW"
    )

    completed_count = sum(
        1 for milestone in milestones if milestone.status == "COMPLETED"
    )

    hold_count = sum(1 for milestone in milestones if milestone.status == "ON_HOLD")

    submitted_count = sum(
        1 for card in student_cards if card["display_status"] == "SUBMITTED"
    )

    revision_count = sum(
        1 for card in student_cards if card["display_status"] == "REVISION_REQUIRED"
    )

    under_review_submission_count = sum(
        1 for card in student_cards if card["display_status"] == "UNDER_REVIEW"
    )

    chair_review_pending_count = sum(
        1 for card in student_cards if card["display_status"] == "CHAIR_REVIEW_PENDING"
    )

    evaluation_completed_count = sum(
        1 for card in student_cards if card["chair_evaluation"] is not None
    )

    is_chair = bool(chair_student_ids)

    is_advisor = bool(advisor_student_ids)

    is_committee_member = bool(committee_student_ids)

    context = {
        "faculty": faculty,
        "student_cards": student_cards,
        "total_milestones": total_milestones,
        "progress_count": progress_count,
        "review_count": review_count,
        "completed_count": completed_count,
        "hold_count": hold_count,
        "submitted_count": submitted_count,
        "revision_count": revision_count,
        "under_review_submission_count": (under_review_submission_count),
        "chair_review_pending_count": (chair_review_pending_count),
        "evaluation_completed_count": (evaluation_completed_count),
        "student_count": len(student_cards),
        "is_chair": is_chair,
        "is_advisor": is_advisor,
        "is_committee_member": is_committee_member,
    }

    return render(
        request,
        "leo/ResearchMilestone/research_milestone_list.html",
        context,
    )


@login_required
def research_milestone_create(request, uuid):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
        ),
        user__uuid=uuid,
    )

    chair_committees = DoctoralCommittee.objects.filter(
        chair_faculty=faculty,
        approval_status="APPROVED",
        phd_student__current_status="ACTIVE",
    ).select_related(
        "phd_student",
        "phd_student__student",
        "phd_student__student__user",
        "phd_student__phd_program",
        "phd_student__advisor",
        "phd_student__advisor__user",
    )

    if not chair_committees.exists():
        messages.error(
            request,
            (
                "Only the assigned Chair Faculty can create research "
                "milestones. You do not have any approved active PhD "
                "students assigned to you."
            ),
        )

        return redirect(
            "research_milestone_list",
            uuid=faculty.user.uuid,
        )

    chair_student_ids = set(
        chair_committees.values_list(
            "phd_student_id",
            flat=True,
        )
    )

    eligible_student_ids = set()

    for committee in chair_committees:
        phd_student = committee.phd_student

        required_credits = int(
            getattr(
                phd_student.phd_program,
                "total_credits_required",
                0,
            )
            or 0
        )

        completed_credits = (
            FacultyCoursework.objects.filter(
                phd_student=phd_student,
                status="COMPLETED",
            )
            .aggregate(
                total=Sum(
                    "coursework__credits",
                ),
            )
            .get(
                "total",
            )
            or 0
        )

        completed_credits = int(completed_credits or 0)

        coursework_completed = (
            required_credits > 0 and completed_credits >= required_credits
        )

        preliminary_exam = (
            PreliminaryExamination.objects.filter(
                phd_student=phd_student,
            )
            .order_by(
                "-exam_date",
                "-prelim_exam_id",
            )
            .first()
        )

        preliminary_exam_passed = (
            preliminary_exam is not None
            and preliminary_exam.result == "PASS"
            and preliminary_exam.status == "COMPLETED"
            and preliminary_exam.is_published
        )

        proposal_approved = DissertationProposal.objects.filter(
            phd_student=phd_student,
            result="APPROVED",
        ).exists()

        active_milestone_exists = ResearchMilestone.objects.filter(
            phd_student=phd_student,
            status__in=[
                "PENDING",
                "IN_PROGRESS",
            ],
        ).exists()

        research_completed = ResearchMilestone.objects.filter(
            phd_student=phd_student,
            current_progress_percentage__gte=100,
        ).exists()

        if (
            coursework_completed
            and preliminary_exam_passed
            and proposal_approved
            and not active_milestone_exists
            and not research_completed
        ):
            eligible_student_ids.add(phd_student.phd_student_id)

    if request.method == "POST":
        form = ResearchMilestoneForm(
            request.POST,
            faculty=faculty,
        )

        if form.is_valid():
            phd_student = form.cleaned_data.get(
                "phd_student",
            )

            if not phd_student:
                messages.error(
                    request,
                    "Please select a PhD student.",
                )

                return redirect(
                    "research_milestone_create",
                    uuid=faculty.user.uuid,
                )

            if phd_student.phd_student_id not in chair_student_ids:
                messages.error(
                    request,
                    (
                        "You are not authorized to create a research "
                        "milestone for this student."
                    ),
                )

                return redirect(
                    "research_milestone_list",
                    uuid=faculty.user.uuid,
                )

            active_milestone = (
                ResearchMilestone.objects.filter(
                    phd_student=phd_student,
                    status__in=[
                        "PENDING",
                        "IN_PROGRESS",
                    ],
                )
                .order_by(
                    "-sequence_number",
                    "-milestone_id",
                )
                .first()
            )

            if active_milestone:
                messages.error(
                    request,
                    (
                        "This PhD student already has an active or pending "
                        "research milestone. The current milestone must be "
                        "completed before creating another one."
                    ),
                )

                return redirect(
                    "research_milestone_list",
                    uuid=faculty.user.uuid,
                )

            research_completed = ResearchMilestone.objects.filter(
                phd_student=phd_student,
                current_progress_percentage__gte=100,
            ).exists()

            if research_completed:
                messages.error(
                    request,
                    (
                        "Research for this PhD student has already reached "
                        "100% completion. No additional research milestones "
                        "can be created."
                    ),
                )

                return redirect(
                    "research_milestone_list",
                    uuid=faculty.user.uuid,
                )

            if phd_student.phd_student_id not in eligible_student_ids:
                messages.error(
                    request,
                    (
                        "This PhD student is not currently eligible "
                        "for research milestone creation. Please "
                        "ensure coursework, Preliminary / Qualifying "
                        "Examination, and Dissertation Proposal "
                        "requirements are completed and approved."
                    ),
                )

                return redirect(
                    "research_milestone_create",
                    uuid=faculty.user.uuid,
                )

            try:
                committee = get_object_or_404(
                    DoctoralCommittee.objects.select_related(
                        "chair_faculty",
                        "chair_faculty__user",
                    ),
                    phd_student=phd_student,
                    chair_faculty=faculty,
                    approval_status="APPROVED",
                )

                with transaction.atomic():
                    locked_student = PhDStudent.objects.select_for_update().get(
                        pk=phd_student.pk,
                    )

                    active_milestone_exists = ResearchMilestone.objects.filter(
                        phd_student=locked_student,
                        status__in=[
                            "PENDING",
                            "IN_PROGRESS",
                        ],
                    ).exists()

                    if active_milestone_exists:
                        messages.error(
                            request,
                            (
                                "This PhD student already has an active "
                                "or pending research milestone. Complete "
                                "the current milestone before creating "
                                "another one."
                            ),
                        )

                        return redirect(
                            "research_milestone_list",
                            uuid=faculty.user.uuid,
                        )

                    research_completed = ResearchMilestone.objects.filter(
                        phd_student=locked_student,
                        current_progress_percentage__gte=100,
                    ).exists()

                    if research_completed:
                        messages.error(
                            request,
                            (
                                "Research for this PhD student has already "
                                "reached 100% completion. No additional "
                                "milestones can be created."
                            ),
                        )

                        return redirect(
                            "research_milestone_list",
                            uuid=faculty.user.uuid,
                        )

                    milestone = form.save(
                        commit=False,
                    )

                    milestone.chair_faculty = committee.chair_faculty

                    milestone.save()

                messages.success(
                    request,
                    "Research milestone created successfully.",
                )

                return redirect(
                    "research_milestone_detail",
                    uuid=faculty.user.uuid,
                    milestone_id=milestone.milestone_id,
                )

            except IntegrityError:
                messages.error(
                    request,
                    (
                        "Unable to create the research milestone. "
                        "The milestone sequence already exists for "
                        "this student. Please try again."
                    ),
                )

                return redirect(
                    "research_milestone_create",
                    uuid=faculty.user.uuid,
                )

            except Exception:
                messages.error(
                    request,
                    (
                        "Unable to create the research milestone. "
                        "Please verify the submitted information "
                        "and try again."
                    ),
                )

                return redirect(
                    "research_milestone_create",
                    uuid=faculty.user.uuid,
                )

        if not form.is_valid():
            form_error_messages = []

            for field_name, errors in form.errors.items():
                for error in errors:
                    if field_name == "__all__":
                        form_error_messages.append(str(error))
                    else:
                        field = form.fields.get(field_name)

                        if field:
                            label = field.label or field_name.replace("_", " ").title()
                            form_error_messages.append(f"{label}: {error}")
                        else:
                            form_error_messages.append(str(error))

            if form_error_messages:
                messages.error(
                    request,
                    " ".join(form_error_messages),
                )
            else:
                messages.error(
                    request,
                    "Please correct the highlighted fields and try again.",
                )

    else:
        form = ResearchMilestoneForm(
            faculty=faculty,
        )

    context = {
        "faculty": faculty,
        "form": form,
        "is_create": True,
        "is_update": False,
        "form_error_messages": [],
    }

    return render(
        request,
        "leo/ResearchMilestone/research_milestone_form.html",
        context,
    )


@login_required
def research_milestone_detail(
    request,
    uuid,
    milestone_id,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
        ),
        user__uuid=uuid,
    )

    milestone = get_object_or_404(
        ResearchMilestone.objects.select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__phd_program",
            "phd_student__phd_program__department",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "chair_faculty",
            "chair_faculty__user",
        ).prefetch_related(
            "submissions",
            "submissions__evaluations",
            "submissions__evaluations__evaluator",
            "submissions__evaluations__evaluator__user",
            "submissions__advisor_advices",
            "submissions__advisor_advices__advisor",
            "submissions__advisor_advices__advisor__user",
        ),
        pk=milestone_id,
    )

    phd_student = milestone.phd_student

    committee = get_object_or_404(
        DoctoralCommittee.objects.select_related(
            "phd_student",
            "chair_faculty",
            "chair_faculty__user",
        ),
        phd_student=phd_student,
        approval_status="APPROVED",
    )

    committee_members = list(
        CommitteeMember.objects.filter(
            committee=committee,
        )
        .select_related(
            "faculty",
            "faculty__user",
            "department",
        )
        .order_by(
            "role",
            "faculty__user__first_name",
            "faculty__user__last_name",
        )
    )

    is_chair = committee.chair_faculty_id == faculty.pk

    is_committee_member = CommitteeMember.objects.filter(
        committee=committee,
        faculty=faculty,
    ).exists()

    if not (is_chair or is_committee_member):
        messages.error(
            request,
            "You are not authorized to view this research milestone.",
        )

        return redirect(
            "research_milestone_list",
            uuid=faculty.user.uuid,
        )

    submissions = list(
        milestone.submissions.all()
        .prefetch_related(
            "evaluations",
            "evaluations__evaluator",
            "evaluations__evaluator__user",
            "advisor_advices",
            "advisor_advices__advisor",
            "advisor_advices__advisor__user",
        )
        .order_by(
            "-submitted_at",
            "-submission_number",
        )
    )

    latest_submission = submissions[0] if submissions else None

    if latest_submission:
        evaluations = list(
            ResearchMilestoneEvaluation.objects.filter(
                submission=latest_submission,
            )
            .select_related(
                "submission",
                "evaluator",
                "evaluator__user",
            )
            .order_by(
                "-evaluated_at",
                "-updated_at",
            )
        )

        advices = list(
            AdvisorResearchAdvice.objects.filter(
                submission=latest_submission,
            )
            .select_related(
                "submission",
                "advisor",
                "advisor__user",
            )
            .order_by(
                "-submitted_at",
                "-created_at",
            )
        )
    else:
        evaluations = []
        advices = []

    committee_faculty_ids = {member.faculty_id for member in committee_members}

    committee_evaluations = [
        item
        for item in evaluations
        if item.evaluator_role == "COMMITTEE_MEMBER"
        and item.evaluator_id in committee_faculty_ids
    ]

    committee_evaluator_ids = {item.evaluator_id for item in committee_evaluations}

    committee_member_count = len(committee_members)
    committee_evaluation_completed = len(committee_evaluator_ids)

    if committee_member_count:
        committee_evaluation_percent = round(
            committee_evaluation_completed / committee_member_count * 100
        )
    else:
        committee_evaluation_percent = 0

    chair_evaluation = next(
        (
            item
            for item in evaluations
            if item.evaluator_role == "CHAIR"
            and item.evaluator_id == committee.chair_faculty_id
        ),
        None,
    )

    self_evaluation = next(
        (item for item in committee_evaluations if item.evaluator_id == faculty.pk),
        None,
    )
    my_evaluation = next(
        (
            item
            for item in evaluations
            if item.evaluator_id == faculty.pk
            and item.evaluator_role == "COMMITTEE_MEMBER"
        ),
        None,
    )

    chair_evaluation = next(
        (item for item in evaluations if item.evaluator_role == "CHAIR"),
        None,
    )
    if is_chair:
        visible_evaluations = committee_evaluations
        evaluation = chair_evaluation
    else:
        visible_evaluations = [self_evaluation] if self_evaluation else []
        evaluation = self_evaluation

    advisor_advice = [
        advice
        for advice in advices
        if phd_student.advisor_id and advice.advisor_id == phd_student.advisor_id
    ]

    submission_files = []

    if latest_submission:
        file_fields = [
            (
                "main_document",
                "Main Research Document",
                "PRIMARY DOCUMENT",
                "bi-file-earmark-richtext-fill",
            ),
            (
                "additional_file_1",
                "Additional Document 1",
                "ATTACHMENT",
                "bi-paperclip",
            ),
            (
                "additional_file_2",
                "Additional Document 2",
                "ATTACHMENT",
                "bi-paperclip",
            ),
            (
                "additional_file_3",
                "Additional Document 3",
                "ATTACHMENT",
                "bi-paperclip",
            ),
        ]

        for field_name, title, file_type, icon in file_fields:
            file_field = getattr(
                latest_submission,
                field_name,
                None,
            )

            if file_field:
                submission_files.append(
                    {
                        "name": title,
                        "type": file_type,
                        "icon": icon,
                        "url": file_field.url,
                        "filename": file_field.name.split("/")[-1],
                    }
                )

    context = {
        "faculty": faculty,
        "milestone": milestone,
        "phd_student": phd_student,
        "student": phd_student.student,
        "committee": committee,
        "committee_members": committee_members,
        "committee_member_count": committee_member_count,
        "committee_evaluation_completed": committee_evaluation_completed,
        "committee_evaluation_percent": committee_evaluation_percent,
        "committee_evaluations": committee_evaluations,
        "submissions": submissions,
        "submission": latest_submission,
        "latest_submission": latest_submission,
        "submission_files": submission_files,
        "evaluations": evaluations,
        "my_evaluation": my_evaluation,
        "chair_evaluation": chair_evaluation,
        "all_evaluations": evaluations,
        "visible_evaluations": visible_evaluations,
        "evaluation": evaluation,
        "self_evaluation": self_evaluation,
        "chair_evaluation": chair_evaluation,
        "advices": advices,
        "advisor_advice": advisor_advice if is_chair else [],
        "is_chair": is_chair,
        "is_advisor": False,
        "is_committee_member": is_committee_member,
    }

    return render(
        request,
        "leo/ResearchMilestone/research_milestone_detail.html",
        context,
    )


@login_required
def research_milestone_update(
    request,
    uuid,
    milestone_id,
):

    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
        ),
        user__uuid=uuid,
    )

    milestone = get_object_or_404(
        ResearchMilestone.objects.select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__phd_program",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "chair_faculty",
            "chair_faculty__user",
        ),
        pk=milestone_id,
    )

    phd_student = milestone.phd_student

    committee = get_object_or_404(
        DoctoralCommittee.objects.select_related(
            "phd_student",
            "chair_faculty",
            "chair_faculty__user",
        ),
        phd_student=phd_student,
        approval_status="APPROVED",
    )

    if committee.chair_faculty != faculty:
        messages.error(
            request,
            "Only the Chair Faculty can update this research milestone.",
        )

        return redirect(
            "research_milestone_detail",
            uuid=faculty.user.uuid,
            milestone_id=milestone.milestone_id,
        )

    if milestone.status == "COMPLETED":
        messages.warning(
            request,
            "Completed research milestones cannot be modified.",
        )

        return redirect(
            "research_milestone_detail",
            uuid=faculty.user.uuid,
            milestone_id=milestone.milestone_id,
        )

    if request.method == "POST":

        form = ResearchMilestoneForm(
            request.POST,
            instance=milestone,
            faculty=faculty,
        )

        if form.is_valid():

            try:
                updated_milestone = form.save(
                    commit=False,
                )

                updated_milestone.chair_faculty = committee.chair_faculty
                updated_milestone.save()

                messages.success(
                    request,
                    "Research milestone updated successfully.",
                )

                return redirect(
                    "research_milestone_detail",
                    uuid=faculty.user.uuid,
                    milestone_id=updated_milestone.milestone_id,
                )

            except IntegrityError:
                messages.error(
                    request,
                    "Unable to update the research milestone. Please try again.",
                )

            except Exception:
                messages.error(
                    request,
                    "Unable to update the research milestone. Please try again.",
                )

        else:
            messages.error(
                request,
                "Unable to update the research milestone. Please check the submitted information.",
            )

    else:
        form = ResearchMilestoneForm(
            instance=milestone,
            faculty=faculty,
        )

    form_error_messages = []

    for field_name, errors in form.errors.items():

        for error in errors:

            if field_name == "__all__":

                form_error_messages.append(
                    str(error),
                )

            else:

                field = form.fields.get(
                    field_name,
                )

                label = (
                    field.label
                    if field
                    else field_name.replace(
                        "_",
                        " ",
                    ).title()
                )

                form_error_messages.append(
                    f"{label}: {error}",
                )

    context = {
        "faculty": faculty,
        "milestone": milestone,
        "phd_student": phd_student,
        "committee": committee,
        "form": form,
        "is_create": False,
        "is_update": True,
        "form_error_messages": form_error_messages,
    }

    return render(
        request,
        "leo/ResearchMilestone/research_milestone_form.html",
        context,
    )


@login_required
def research_milestone_hold(
    request,
    uuid,
    milestone_id,
):

    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
        ),
        user__uuid=uuid,
    )

    milestone = get_object_or_404(
        ResearchMilestone.objects.select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "chair_faculty",
            "chair_faculty__user",
        ),
        pk=milestone_id,
    )

    phd_student = milestone.phd_student

    committee = get_object_or_404(
        DoctoralCommittee.objects.select_related(
            "chair_faculty",
            "chair_faculty__user",
        ),
        phd_student=phd_student,
        approval_status="APPROVED",
    )

    if committee.chair_faculty != faculty:
        messages.error(
            request,
            "Only the Chair Faculty can place this research milestone on hold.",
        )

        return redirect(
            "research_milestone_detail",
            uuid=faculty.user.uuid,
            milestone_id=milestone.milestone_id,
        )

    if milestone.status == "COMPLETED":
        messages.warning(
            request,
            "Completed research milestones cannot be placed on hold.",
        )

        return redirect(
            "research_milestone_detail",
            uuid=faculty.user.uuid,
            milestone_id=milestone.milestone_id,
        )

    if milestone.status == "ON_HOLD":
        messages.info(
            request,
            "This research milestone is already on hold.",
        )

        return redirect(
            "research_milestone_detail",
            uuid=faculty.user.uuid,
            milestone_id=milestone.milestone_id,
        )

    if request.method != "POST":
        messages.error(
            request,
            "Invalid request method.",
        )

        return redirect(
            "research_milestone_detail",
            uuid=faculty.user.uuid,
            milestone_id=milestone.milestone_id,
        )

    milestone.status = "ON_HOLD"

    milestone.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    messages.success(
        request,
        "Research milestone placed on hold successfully.",
    )

    return redirect(
        "research_milestone_detail",
        uuid=faculty.user.uuid,
        milestone_id=milestone.milestone_id,
    )


@login_required
def research_milestone_activate(
    request,
    uuid,
    milestone_id,
):

    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
        ),
        user__uuid=uuid,
    )

    milestone = get_object_or_404(
        ResearchMilestone.objects.select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "chair_faculty",
            "chair_faculty__user",
        ),
        pk=milestone_id,
    )

    phd_student = milestone.phd_student

    committee = get_object_or_404(
        DoctoralCommittee.objects.select_related(
            "chair_faculty",
            "chair_faculty__user",
        ),
        phd_student=phd_student,
        approval_status="APPROVED",
    )

    if committee.chair_faculty != faculty:
        messages.error(
            request,
            "Only the Chair Faculty can activate this research milestone.",
        )

        return redirect(
            "research_milestone_detail",
            uuid=faculty.user.uuid,
            milestone_id=milestone.milestone_id,
        )

    if milestone.status != "ON_HOLD":
        messages.warning(
            request,
            "Only research milestones currently on hold can be activated.",
        )

        return redirect(
            "research_milestone_detail",
            uuid=faculty.user.uuid,
            milestone_id=milestone.milestone_id,
        )

    if request.method != "POST":
        messages.error(
            request,
            "Invalid request method.",
        )

        return redirect(
            "research_milestone_detail",
            uuid=faculty.user.uuid,
            milestone_id=milestone.milestone_id,
        )

    milestone.status = "IN_PROGRESS"

    milestone.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    messages.success(
        request,
        "Research milestone activated successfully.",
    )

    return redirect(
        "research_milestone_detail",
        uuid=faculty.user.uuid,
        milestone_id=milestone.milestone_id,
    )


@login_required
def research_milestone_evaluate(
    request,
    uuid,
    milestone_id,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
        ),
        user__uuid=uuid,
    )

    milestone = get_object_or_404(
        ResearchMilestone.objects.select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__phd_program",
            "phd_student__phd_program__department",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "chair_faculty",
            "chair_faculty__user",
        ),
        pk=milestone_id,
    )

    phd_student = milestone.phd_student

    committee = get_object_or_404(
        DoctoralCommittee.objects.select_related(
            "phd_student",
            "chair_faculty",
            "chair_faculty__user",
        ),
        phd_student=phd_student,
        approval_status="APPROVED",
    )

    is_chair = committee.chair_faculty_id == faculty.pk

    committee_members = list(
        CommitteeMember.objects.filter(
            committee=committee,
        )
        .exclude(
            faculty=committee.chair_faculty,
        )
        .select_related(
            "faculty",
            "faculty__user",
            "department",
        )
        .order_by(
            "role",
            "faculty__user__first_name",
            "faculty__user__last_name",
        )
    )

    is_committee_member = any(
        member.faculty_id == faculty.pk for member in committee_members
    )

    if not is_chair and not is_committee_member:
        messages.error(
            request,
            "You are not authorized to evaluate this research milestone.",
        )

        return redirect(
            "research_milestone_detail",
            uuid=faculty.user.uuid,
            milestone_id=milestone.milestone_id,
        )

    if milestone.status == "COMPLETED":
        messages.warning(
            request,
            "This research milestone has already been completed and cannot be evaluated again.",
        )

        return redirect(
            "research_milestone_detail",
            uuid=faculty.user.uuid,
            milestone_id=milestone.milestone_id,
        )

    submission = (
        ResearchMilestoneSubmission.objects.filter(
            milestone=milestone,
            status__in=[
                "SUBMITTED",
                "UNDER_REVIEW",
            ],
        )
        .select_related(
            "milestone",
        )
        .order_by(
            "-submitted_at",
            "-submission_number",
        )
        .first()
    )

    if not submission:
        messages.warning(
            request,
            "There is no research submission available for evaluation.",
        )

        return redirect(
            "research_milestone_detail",
            uuid=faculty.user.uuid,
            milestone_id=milestone.milestone_id,
        )

    committee_faculty_ids = [member.faculty_id for member in committee_members]

    required_committee_count = len(committee_faculty_ids)

    committee_evaluations = list(
        ResearchMilestoneEvaluation.objects.filter(
            submission=submission,
            evaluator_role="COMMITTEE_MEMBER",
            evaluator_id__in=committee_faculty_ids,
        )
        .select_related(
            "evaluator",
            "evaluator__user",
        )
        .order_by(
            "evaluated_at",
        )
    )

    submitted_committee_faculty_ids = {
        evaluation.evaluator_id for evaluation in committee_evaluations
    }

    submitted_committee_count = len(submitted_committee_faculty_ids)

    pending_committee_count = max(
        required_committee_count - submitted_committee_count,
        0,
    )

    all_committee_evaluations_submitted = (
        required_committee_count > 0
        and submitted_committee_count == required_committee_count
    )

    committee_evaluation_percent = (
        round((submitted_committee_count / required_committee_count) * 100)
        if required_committee_count
        else 0
    )

    chair_evaluation = (
        ResearchMilestoneEvaluation.objects.filter(
            submission=submission,
            evaluator=committee.chair_faculty,
            evaluator_role="CHAIR",
        )
        .select_related(
            "evaluator",
            "evaluator__user",
        )
        .first()
    )

    latest_committee_evaluation = (
        ResearchMilestoneEvaluation.objects.filter(
            submission__milestone=milestone,
            evaluator_role="COMMITTEE_MEMBER",
        )
        .select_related(
            "evaluator",
            "evaluator__user",
            "submission",
        )
        .order_by(
            "-evaluated_at",
            "-evaluation_id",
        )
        .first()
    )

    existing_evaluation = None

    if is_committee_member:
        existing_evaluation = (
            ResearchMilestoneEvaluation.objects.filter(
                submission=submission,
                evaluator=faculty,
                evaluator_role="COMMITTEE_MEMBER",
            )
            .select_related(
                "evaluator",
                "evaluator__user",
            )
            .first()
        )

        if existing_evaluation:
            messages.info(
                request,
                "You have already evaluated this research submission.",
            )

            return redirect(
                "research_milestone_evaluation_detail",
                uuid=faculty.user.uuid,
                milestone_id=milestone.milestone_id,
                evaluation_id=existing_evaluation.evaluation_id,
            )

        is_finalization = False

    elif is_chair:
        if chair_evaluation:
            messages.info(
                request,
                "The Chair Faculty has already finalized this research submission.",
            )

            return redirect(
                "research_milestone_evaluation_detail",
                uuid=faculty.user.uuid,
                milestone_id=milestone.milestone_id,
                evaluation_id=chair_evaluation.evaluation_id,
            )

        if required_committee_count == 0:
            messages.warning(
                request,
                "No committee members are currently assigned to this doctoral committee.",
            )

            return redirect(
                "research_milestone_detail",
                uuid=faculty.user.uuid,
                milestone_id=milestone.milestone_id,
            )

        if not all_committee_evaluations_submitted:
            pending_label = (
                "evaluation" if pending_committee_count == 1 else "evaluations"
            )

            messages.warning(
                request,
                (
                    "Chair Faculty cannot finalize this research milestone yet. "
                    f"{pending_committee_count} committee {pending_label} "
                    "still pending."
                ),
            )

            return redirect(
                "research_milestone_detail",
                uuid=faculty.user.uuid,
                milestone_id=milestone.milestone_id,
            )

        is_finalization = True

    else:
        messages.error(
            request,
            "You are not authorized to perform this research milestone evaluation.",
        )

        return redirect(
            "research_milestone_detail",
            uuid=faculty.user.uuid,
            milestone_id=milestone.milestone_id,
        )

    previous_milestone_progress = ResearchMilestone.objects.filter(
        phd_student=phd_student,
        sequence_number__lt=milestone.sequence_number,
    ).aggregate(
        total=Max(
            "current_progress_percentage",
        )
    ).get(
        "total"
    ) or Decimal(
        "0"
    )

    try:
        previous_milestone_progress = Decimal(str(previous_milestone_progress))
    except (
        TypeError,
        ValueError,
        InvalidOperation,
    ):
        previous_milestone_progress = Decimal("0")

    previous_milestone_progress = max(
        min(
            previous_milestone_progress,
            Decimal("100"),
        ),
        Decimal("0"),
    )

    current_milestone_progress = milestone.current_progress_percentage or Decimal("0")

    try:
        current_milestone_progress = Decimal(str(current_milestone_progress))
    except (
        TypeError,
        ValueError,
        InvalidOperation,
    ):
        current_milestone_progress = Decimal("0")

    current_milestone_progress = max(
        min(
            current_milestone_progress,
            Decimal("100"),
        ),
        Decimal("0"),
    )

    current_overall_progress = max(
        previous_milestone_progress,
        current_milestone_progress,
    )

    current_overall_progress = min(
        current_overall_progress,
        Decimal("100"),
    )

    remaining_overall_progress = max(
        Decimal("100") - current_overall_progress,
        Decimal("0"),
    )

    default_progress = current_overall_progress

    form_kwargs = {
        "faculty": faculty,
        "submission": submission,
        "is_finalization": is_finalization,
        "previous_progress": previous_milestone_progress,
        "max_progress": remaining_overall_progress,
    }

    if request.method == "POST":
        form = ResearchMilestoneEvaluationForm(
            request.POST,
            **form_kwargs,
        )

        if form.is_valid():
            try:
                with transaction.atomic():
                    evaluation = form.save(
                        commit=False,
                    )

                    progress_percentage = evaluation.progress_percentage

                    if progress_percentage is not None:
                        progress_percentage = Decimal(str(progress_percentage))

                    if (
                        progress_percentage is not None
                        and progress_percentage > Decimal("100")
                    ):
                        form.add_error(
                            "progress_percentage",
                            "Overall research progress cannot exceed 100.00%.",
                        )
                    else:
                        evaluation.save()

                        if is_finalization:
                            if progress_percentage is not None:
                                milestone.current_progress_percentage = (
                                    progress_percentage
                                )

                            if evaluation.decision == "COMPLETED":
                                milestone.status = "COMPLETED"
                                milestone.completion_date = timezone.now().date()
                            else:
                                milestone.status = "REVISION_REQUIRED"
                                milestone.completion_date = None

                            milestone.save(
                                update_fields=[
                                    "current_progress_percentage",
                                    "status",
                                    "completion_date",
                                    "updated_at",
                                ]
                            )

                            submission.status = (
                                "EVALUATED"
                                if evaluation.decision == "COMPLETED"
                                else "REVISION_REQUIRED"
                            )

                            submission.save(
                                update_fields=[
                                    "status",
                                    "updated_at",
                                ]
                            )

                            final_overall_progress = (
                                min(progress_percentage, Decimal("100"))
                                if progress_percentage is not None
                                else current_overall_progress
                            )

                            if evaluation.decision == "COMPLETED":
                                messages.success(
                                    request,
                                    (
                                        "Research milestone finalized successfully. "
                                        "Overall research progress is now "
                                        f"{final_overall_progress:.2f}%."
                                    ),
                                )
                            else:
                                messages.warning(
                                    request,
                                    (
                                        "Research milestone evaluation submitted "
                                        "successfully and revision has been requested."
                                    ),
                                )

                        else:
                            submission.status = "UNDER_REVIEW"

                            submission.save(
                                update_fields=[
                                    "status",
                                    "updated_at",
                                ]
                            )

                            messages.success(
                                request,
                                (
                                    "Research milestone evaluation submitted "
                                    "successfully."
                                ),
                            )

                        return redirect(
                            "research_milestone_evaluation_detail",
                            uuid=faculty.user.uuid,
                            milestone_id=milestone.milestone_id,
                            evaluation_id=evaluation.evaluation_id,
                        )

            except IntegrityError:
                if is_finalization:
                    messages.error(
                        request,
                        (
                            "The Chair Faculty evaluation could not be saved "
                            "because the result has already been finalized."
                        ),
                    )
                else:
                    messages.error(
                        request,
                        (
                            "Your evaluation could not be saved because "
                            "you have already evaluated this research submission."
                        ),
                    )

            except Exception as error:
                messages.error(
                    request,
                    ("Research evaluation failed: " f"{str(error)}"),
                )

        else:
            error_messages = []

            for field_name, errors in form.errors.items():
                for error in errors:
                    error_text = str(error)

                    if field_name == "__all__":
                        error_messages.append(error_text)
                    else:
                        field_label = form.fields[field_name].label

                        error_messages.append(f"{field_label}: {error_text}")

            if error_messages:
                for error_message in error_messages:
                    messages.error(
                        request,
                        error_message,
                    )
            else:
                messages.error(
                    request,
                    "Unable to submit the evaluation. Please check the form.",
                )

    else:
        form = ResearchMilestoneEvaluationForm(
            **form_kwargs,
        )

        form.fields["progress_percentage"].initial = None

    if form.is_bound:
        raw_progress = form.data.get(
            "progress_percentage",
            "",
        )

        try:
            entered_progress = Decimal(str(raw_progress))
        except (
            TypeError,
            ValueError,
            InvalidOperation,
        ):
            entered_progress = Decimal("0.00")
    else:
        entered_progress = form.initial.get(
            "progress_percentage",
            Decimal("0.00"),
        ) or Decimal("0.00")

    if is_finalization:
        entered_progress = max(
            entered_progress,
            Decimal("0.00"),
        )

        entered_progress = min(
            entered_progress,
            remaining_overall_progress,
        )

        projected_overall_progress = min(
            current_overall_progress + entered_progress,
            Decimal("100.00"),
        )
    else:
        entered_progress = max(
            entered_progress,
            Decimal("0.00"),
        )

        entered_progress = min(
            entered_progress,
            remaining_overall_progress,
        )

        projected_overall_progress = min(
            current_overall_progress + entered_progress,
            Decimal("100.00"),
        )

    committee_suggested_overall_progress = current_overall_progress

    if (
        latest_committee_evaluation
        and latest_committee_evaluation.progress_percentage is not None
    ):
        try:
            latest_committee_progress = Decimal(
                str(latest_committee_evaluation.progress_percentage)
            )
        except (TypeError, ValueError, InvalidOperation):
            latest_committee_progress = current_overall_progress

        committee_suggested_overall_progress = max(
            current_overall_progress,
            min(latest_committee_progress, Decimal("100.00")),
        )

    context = {
        "faculty": faculty,
        "milestone": milestone,
        "phd_student": phd_student,
        "committee": committee,
        "committee_members": committee_members,
        "submission": submission,
        "form": form,
        "committee_evaluations": committee_evaluations,
        "chair_evaluation": chair_evaluation,
        "latest_committee_evaluation": latest_committee_evaluation,
        "committee_suggested_overall_progress": committee_suggested_overall_progress,
        "existing_evaluation": existing_evaluation,
        "required_committee_count": required_committee_count,
        "submitted_committee_count": submitted_committee_count,
        "pending_committee_count": pending_committee_count,
        "committee_evaluation_percent": committee_evaluation_percent,
        "all_committee_evaluations_submitted": (all_committee_evaluations_submitted),
        "previous_milestone_progress": previous_milestone_progress,
        "total_other_milestone_progress": previous_milestone_progress,
        "current_milestone_progress": current_milestone_progress,
        "current_overall_progress": current_overall_progress,
        "overall_progress_before_current": current_overall_progress,
        "remaining_overall_progress": remaining_overall_progress,
        "default_progress": None,
        "minimum_progress": Decimal("1.00"),
        "projected_overall_progress": projected_overall_progress,
        "entered_progress": entered_progress,
        "is_chair": is_chair,
        "is_committee_member": is_committee_member,
        "is_finalization": is_finalization,
        "is_create": True,
        "is_update": False,
    }

    return render(
        request,
        "leo/ResearchMilestone/research_milestone_evaluate.html",
        context,
    )


@login_required
@transaction.atomic
def research_milestone_second_chance(
    request,
    uuid,
    milestone_id,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
        ),
        user__uuid=uuid,
    )

    milestone = get_object_or_404(
        ResearchMilestone.objects.select_for_update().select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "chair_faculty",
            "chair_faculty__user",
        ),
        pk=milestone_id,
    )

    phd_student = milestone.phd_student

    committee = get_object_or_404(
        DoctoralCommittee.objects.select_related(
            "chair_faculty",
            "chair_faculty__user",
        ),
        phd_student=phd_student,
        approval_status="APPROVED",
    )

    if committee.chair_faculty != faculty:
        messages.error(
            request,
            "Only the Chair Faculty can grant a second chance for this research milestone.",
        )

        return redirect(
            "research_milestone_detail",
            uuid=faculty.user.uuid,
            milestone_id=milestone.milestone_id,
        )

    if request.method != "POST":
        messages.error(
            request,
            "Invalid request method.",
        )

        return redirect(
            "research_milestone_detail",
            uuid=faculty.user.uuid,
            milestone_id=milestone.milestone_id,
        )

    if milestone.status != "REVISION_REQUIRED":
        messages.warning(
            request,
            "A second chance can only be granted when the research milestone requires revision.",
        )

        return redirect(
            "research_milestone_detail",
            uuid=faculty.user.uuid,
            milestone_id=milestone.milestone_id,
        )

    latest_submission = (
        ResearchMilestoneSubmission.objects.filter(
            milestone=milestone,
            status="REVISION_REQUIRED",
        )
        .order_by(
            "-submission_number",
            "-submitted_at",
        )
        .first()
    )

    if not latest_submission:
        messages.error(
            request,
            "No revision-required submission was found for this research milestone.",
        )

        return redirect(
            "research_milestone_detail",
            uuid=faculty.user.uuid,
            milestone_id=milestone.milestone_id,
        )

    milestone.status = "IN_PROGRESS"
    milestone.completion_date = None

    milestone.save(
        update_fields=[
            "status",
            "completion_date",
            "updated_at",
        ]
    )

    messages.success(
        request,
        (
            "Second chance granted successfully. "
            "The student can now revise and resubmit this research milestone."
        ),
    )

    return redirect(
        "research_milestone_detail",
        uuid=faculty.user.uuid,
        milestone_id=milestone.milestone_id,
    )


@login_required
def research_milestone_evaluation_detail(
    request,
    uuid,
    milestone_id,
    evaluation_id,
):

    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
        ),
        user__uuid=uuid,
    )

    evaluation = get_object_or_404(
        ResearchMilestoneEvaluation.objects.select_related(
            "submission",
            "submission__milestone",
            "submission__milestone__phd_student",
            "submission__milestone__phd_student__student",
            "submission__milestone__phd_student__student__user",
            "submission__milestone__phd_student__advisor",
            "submission__milestone__phd_student__advisor__user",
            "submission__milestone__chair_faculty",
            "submission__milestone__chair_faculty__user",
            "evaluator",
            "evaluator__user",
        ),
        pk=evaluation_id,
        submission__milestone_id=milestone_id,
    )

    milestone = evaluation.submission.milestone

    phd_student = milestone.phd_student

    committee = get_object_or_404(
        DoctoralCommittee.objects.select_related(
            "phd_student",
            "chair_faculty",
            "chair_faculty__user",
        ),
        phd_student=phd_student,
        approval_status="APPROVED",
    )

    is_chair = committee.chair_faculty_id == faculty.pk

    is_committee_member = (
        CommitteeMember.objects.filter(
            committee=committee,
            faculty=faculty,
        )
        .exclude(
            faculty=committee.chair_faculty,
        )
        .exists()
    )

    is_advisor = phd_student.advisor_id == faculty.pk

    if not (is_chair or is_committee_member or is_advisor):
        messages.error(
            request,
            "You are not authorized to view this research evaluation.",
        )

        return redirect(
            "research_milestone_list",
            uuid=faculty.user.uuid,
        )

    submission = evaluation.submission

    all_evaluations = (
        ResearchMilestoneEvaluation.objects.filter(
            submission=submission,
        )
        .select_related(
            "evaluator",
            "evaluator__user",
        )
        .order_by(
            "-evaluated_at",
        )
    )

    chair_evaluation = all_evaluations.filter(
        evaluator_role="CHAIR",
    ).first()

    committee_evaluations = all_evaluations.filter(
        evaluator_role="COMMITTEE_MEMBER",
    )

    committee_members = (
        CommitteeMember.objects.filter(
            committee=committee,
        )
        .exclude(
            faculty=committee.chair_faculty,
        )
        .select_related(
            "faculty",
            "faculty__user",
        )
    )

    required_committee_count = committee_members.count()

    submitted_committee_faculty_ids = set(
        committee_evaluations.values_list(
            "evaluator_id",
            flat=True,
        )
    )

    submitted_committee_count = len(submitted_committee_faculty_ids)

    pending_committee_count = required_committee_count - submitted_committee_count

    all_committee_evaluations_submitted = (
        required_committee_count > 0
        and submitted_committee_count == required_committee_count
    )

    advisor_advice = (
        AdvisorResearchAdvice.objects.filter(
            submission=submission,
        )
        .select_related(
            "advisor",
            "advisor__user",
        )
        .order_by(
            "-submitted_at",
            "-created_at",
        )
    )

    my_evaluation = all_evaluations.filter(
        evaluator=faculty,
    ).first()

    can_finalize = (
        is_chair
        and chair_evaluation is None
        and milestone.status != "COMPLETED"
        and submission.status
        in [
            "SUBMITTED",
            "UNDER_REVIEW",
        ]
        and all_committee_evaluations_submitted
    )

    context = {
        "faculty": faculty,
        "evaluation": evaluation,
        "milestone": milestone,
        "phd_student": phd_student,
        "student": phd_student.student,
        "committee": committee,
        "committee_members": committee_members,
        "submission": submission,
        "all_evaluations": all_evaluations,
        "chair_evaluation": chair_evaluation,
        "committee_evaluations": committee_evaluations,
        "advisor_advice": advisor_advice,
        "my_evaluation": my_evaluation,
        "required_committee_count": required_committee_count,
        "submitted_committee_count": submitted_committee_count,
        "pending_committee_count": pending_committee_count,
        "all_committee_evaluations_submitted": all_committee_evaluations_submitted,
        "can_finalize": can_finalize,
        "is_chair": is_chair,
        "is_committee_member": is_committee_member,
        "is_advisor": is_advisor,
        "is_view_mode": True,
    }

    return render(
        request,
        "leo/ResearchMilestone/research_milestone_evaluation_detail.html",
        context,
    )


####################################################
### RESEARCH MODULE ADVISOR SIDE STARTS HERE #####
####################################################


@login_required
def advisor_research_milestone_list(
    request,
    uuid,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
        ),
        user__uuid=uuid,
    )

    phd_students = (
        PhDStudent.objects.filter(
            advisor=faculty,
            current_status="ACTIVE",
        )
        .select_related(
            "student",
            "student__user",
            "phd_program",
            "phd_program__department",
            "advisor",
            "advisor__user",
        )
        .order_by(
            "student__user__last_name",
            "student__user__first_name",
        )
    )

    milestones = list(
        ResearchMilestone.objects.filter(
            phd_student__advisor=faculty,
            phd_student__current_status="ACTIVE",
        )
        .select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__phd_program",
            "phd_student__phd_program__department",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "chair_faculty",
            "chair_faculty__user",
        )
        .prefetch_related(
            "submissions",
            "submissions__evaluations",
            "submissions__evaluations__evaluator",
            "submissions__evaluations__evaluator__user",
        )
        .order_by(
            "phd_student_id",
            "-sequence_number",
            "-updated_at",
        )
    )

    milestone_map = {}

    for milestone in milestones:
        milestone_map.setdefault(
            milestone.phd_student_id,
            [],
        ).append(
            milestone,
        )

    student_cards = []

    for phd_student in phd_students:
        history = milestone_map.get(
            phd_student.phd_student_id,
            [],
        )

        latest_milestone = history[0] if history else None
        latest_submission = None
        chair_evaluation = None
        committee_evaluations = []
        committee_member_count = 0
        committee_evaluation_completed = 0
        committee_evaluation_percentage = 0

        if latest_milestone:
            submissions = list(
                latest_milestone.submissions.all().order_by(
                    "-submitted_at",
                    "-submission_number",
                )
            )

            latest_submission = submissions[0] if submissions else None

            if latest_submission:
                evaluations = list(
                    latest_submission.evaluations.all()
                    .select_related(
                        "evaluator",
                        "evaluator__user",
                    )
                    .order_by(
                        "-evaluated_at",
                    )
                )

                committee = (
                    DoctoralCommittee.objects.filter(
                        phd_student=phd_student,
                        approval_status="APPROVED",
                    )
                    .prefetch_related(
                        "committee_members",
                    )
                    .first()
                )

                if committee:
                    committee_members = list(committee.committee_members.all())

                    committee_member_count = len(committee_members)

                    committee_faculty_ids = {
                        member.faculty_id for member in committee_members
                    }

                    committee_evaluations = [
                        evaluation
                        for evaluation in evaluations
                        if (
                            evaluation.evaluator_role == "COMMITTEE_MEMBER"
                            and evaluation.evaluator_id in committee_faculty_ids
                        )
                    ]

                    committee_evaluator_ids = {
                        evaluation.evaluator_id for evaluation in committee_evaluations
                    }

                    committee_evaluation_completed = len(committee_evaluator_ids)

                    if committee_member_count:
                        committee_evaluation_percentage = round(
                            (committee_evaluation_completed / committee_member_count)
                            * 100
                        )

                chair_evaluation = next(
                    (
                        evaluation
                        for evaluation in evaluations
                        if evaluation.evaluator_role == "CHAIR"
                    ),
                    None,
                )

        if not latest_milestone:
            display_status = "NO_MILESTONE"
        elif not latest_submission:
            display_status = "WAITING_SUBMISSION"
        elif not chair_evaluation:
            display_status = "CHAIR_REVIEW_PENDING"
        elif latest_milestone.status == "COMPLETED":
            display_status = "COMPLETED"
        else:
            display_status = "IN_PROGRESS"

        student_cards.append(
            {
                "student": phd_student,
                "history": history,
                "latest": latest_milestone,
                "latest_submission": latest_submission,
                "chair_evaluation": chair_evaluation,
                "committee_evaluations": committee_evaluations,
                "committee_member_count": committee_member_count,
                "committee_evaluation_completed": committee_evaluation_completed,
                "committee_evaluation_percentage": committee_evaluation_percentage,
                "display_status": display_status,
            }
        )

    total_students = len(student_cards)

    total_milestones = len(milestones)

    submitted_milestones = sum(
        1 for card in student_cards if card["latest_submission"] is not None
    )

    chair_review_pending_count = sum(
        1
        for card in student_cards
        if (card["latest_submission"] is not None and card["chair_evaluation"] is None)
    )

    completed_count = sum(
        1
        for card in student_cards
        if (card["latest"] is not None and card["latest"].status == "COMPLETED")
    )

    context = {
        "faculty": faculty,
        "student_cards": student_cards,
        "total_students": total_students,
        "total_milestones": total_milestones,
        "submitted_milestones": submitted_milestones,
        "chair_review_pending_count": chair_review_pending_count,
        "completed_count": completed_count,
        "is_advisor": True,
        "is_chair": False,
        "is_committee_member": False,
    }

    return render(
        request,
        "leo/ResearchMilestone/advisor_research_milestone_list.html",
        context,
    )


@login_required
def advisor_research_milestone_detail(
    request,
    uuid,
    milestone_id,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
        ),
        user__uuid=uuid,
    )

    milestone = get_object_or_404(
        ResearchMilestone.objects.select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__phd_program",
            "phd_student__phd_program__department",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "chair_faculty",
            "chair_faculty__user",
        ),
        pk=milestone_id,
    )

    phd_student = milestone.phd_student

    if phd_student.advisor_id != faculty.pk:
        messages.error(
            request,
            "You are not authorized to view this research milestone.",
        )
        return redirect(
            "advisor_research_milestone_list",
            uuid=faculty.user.uuid,
        )

    committee = (
        DoctoralCommittee.objects.filter(
            phd_student=phd_student,
            approval_status="APPROVED",
        )
        .select_related(
            "chair_faculty",
            "chair_faculty__user",
        )
        .first()
    )

    committee_members = []

    if committee:
        committee_members = list(
            CommitteeMember.objects.filter(
                committee=committee,
            )
            .select_related(
                "faculty",
                "faculty__user",
                "department",
            )
            .order_by(
                "role",
                "faculty__user__first_name",
                "faculty__user__last_name",
            )
        )

    milestones = list(
        ResearchMilestone.objects.filter(
            phd_student=phd_student,
        )
        .select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__phd_program",
            "phd_student__phd_program__department",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "chair_faculty",
            "chair_faculty__user",
        )
        .prefetch_related(
            "submissions",
            "submissions__evaluations",
            "submissions__evaluations__evaluator",
            "submissions__evaluations__evaluator__user",
        )
        .order_by(
            "sequence_number",
            "milestone_id",
        )
    )

    overall_progress = max(
        (
            milestone_item.current_progress_percentage or Decimal("0")
            for milestone_item in milestones
        ),
        default=Decimal("0"),
    )

    milestone_records = []
    total_submissions = 0
    total_evaluations = 0
    completed_milestones = 0

    status_classes = {
        "PENDING": "pending",
        "IN_PROGRESS": "progress",
        "SUBMITTED": "submitted",
        "UNDER_REVIEW": "under_review",
        "REVISION_REQUIRED": "revision_required",
        "COMPLETED": "completed",
    }

    for milestone_item in milestones:
        submissions = list(
            milestone_item.submissions.all().order_by(
                "-submission_number",
                "-submitted_at",
            )
        )

        latest_submission = submissions[0] if submissions else None
        evaluation_items = []

        for submission in submissions:
            submission_evaluations = list(
                submission.evaluations.all().order_by(
                    "-evaluated_at",
                    "-updated_at",
                )
            )
            evaluation_items.extend(submission_evaluations)

        total_submissions += len(submissions)
        total_evaluations += len(evaluation_items)

        if milestone_item.status == "COMPLETED":
            completed_milestones += 1

        milestone_records.append(
            {
                "milestone": milestone_item,
                "submissions": submissions,
                "latest_submission": latest_submission,
                "latest_evaluation": evaluation_items[0] if evaluation_items else None,
                "submission_count": len(submissions),
                "evaluation_count": len(evaluation_items),
                "progress": milestone_item.current_progress_percentage or Decimal("0"),
                "status_class": status_classes.get(
                    milestone_item.status,
                    "pending",
                ),
            }
        )

    latest_milestone = milestones[-1] if milestones else None

    if latest_milestone is None:
        latest_milestone = milestone

    context = {
        "faculty": faculty,
        "milestone": milestone,
        "phd_student": phd_student,
        "student": phd_student.student,
        "committee": committee,
        "committee_members": committee_members,
        "milestones": milestones,
        "milestone_records": milestone_records,
        "milestone_count": len(milestones),
        "completed_milestones": completed_milestones,
        "total_submissions": total_submissions,
        "total_evaluations": total_evaluations,
        "overall_progress": overall_progress,
        "latest_milestone": latest_milestone,
        "is_advisor": True,
    }

    return render(
        request,
        "leo/ResearchMilestone/advisor_research_milestone_detail.html",
        context,
    )


@login_required
def advisor_research_advice_create(
    request,
    uuid,
    milestone_id,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
        ),
        user__uuid=uuid,
    )

    milestone = get_object_or_404(
        ResearchMilestone.objects.select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__phd_program",
            "phd_student__phd_program__department",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "chair_faculty",
            "chair_faculty__user",
        ),
        pk=milestone_id,
        phd_student__advisor=faculty,
    )

    phd_student = milestone.phd_student

    submission = (
        ResearchMilestoneSubmission.objects.filter(
            milestone=milestone,
        )
        .order_by(
            "-submitted_at",
            "-submission_number",
        )
        .first()
    )

    if not submission:
        messages.warning(
            request,
            "The student has not submitted the research milestone yet.",
        )

        return redirect(
            "advisor_research_milestone_detail",
            uuid=faculty.user.uuid,
            milestone_id=milestone.milestone_id,
        )

    evaluations = (
        ResearchMilestoneEvaluation.objects.filter(
            submission=submission,
        )
        .select_related(
            "evaluator",
            "evaluator__user",
        )
        .order_by(
            "-evaluated_at",
        )
    )

    chair_evaluation = evaluations.filter(
        evaluator_role="CHAIR",
    ).first()

    if not chair_evaluation:
        messages.warning(
            request,
            "Chair Faculty evaluation must be completed before you can provide research advice.",
        )

        return redirect(
            "advisor_research_milestone_detail",
            uuid=faculty.user.uuid,
            milestone_id=milestone.milestone_id,
        )

    existing_advice = (
        AdvisorResearchAdvice.objects.filter(
            submission=submission,
            advisor=faculty,
        )
        .select_related(
            "advisor",
            "advisor__user",
            "submission",
            "submission__milestone",
        )
        .order_by(
            "-submitted_at",
            "-created_at",
        )
        .first()
    )

    if existing_advice:
        return redirect(
            "advisor_research_advice_detail",
            uuid=faculty.user.uuid,
            milestone_id=milestone.milestone_id,
            advice_id=existing_advice.advice_id,
        )

    if request.method == "POST":
        form = AdvisorResearchAdviceForm(
            request.POST,
            faculty=faculty,
            submission=submission,
        )

        if form.is_valid():
            try:
                advice = form.save(
                    commit=True,
                )

                messages.success(
                    request,
                    "Research advice has been submitted successfully.",
                )

                return redirect(
                    "advisor_research_advice_detail",
                    uuid=faculty.user.uuid,
                    milestone_id=milestone.milestone_id,
                    advice_id=advice.advice_id,
                )

            except IntegrityError:
                messages.error(
                    request,
                    "Research advice has already been submitted for this research submission.",
                )

                return redirect(
                    "advisor_research_milestone_detail",
                    uuid=faculty.user.uuid,
                    milestone_id=milestone.milestone_id,
                )

            except Exception:
                messages.error(
                    request,
                    "Unable to submit research advice. Please try again.",
                )
        else:
            messages.error(
                request,
                "Please correct the errors in the form before submitting.",
            )

    else:
        form = AdvisorResearchAdviceForm(
            faculty=faculty,
            submission=submission,
        )

    context = {
        "faculty": faculty,
        "milestone": milestone,
        "phd_student": phd_student,
        "submission": submission,
        "chair_evaluation": chair_evaluation,
        "evaluations": evaluations,
        "form": form,
        "is_create": True,
        "is_update": False,
        "is_advisor": True,
        "is_chair": False,
        "is_committee_member": False,
    }

    return render(
        request,
        "leo/ResearchMilestone/advisor_research_advice_create.html",
        context,
    )


@login_required
def advisor_research_advice_detail(
    request,
    uuid,
    milestone_id,
    advice_id,
):

    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
        ),
        user__uuid=uuid,
    )

    advice = get_object_or_404(
        AdvisorResearchAdvice.objects.select_related(
            "submission",
            "submission__milestone",
            "submission__milestone__phd_student",
            "submission__milestone__phd_student__student",
            "submission__milestone__phd_student__student__user",
            "submission__milestone__phd_student__advisor",
            "submission__milestone__phd_student__advisor__user",
            "advisor",
            "advisor__user",
        ),
        pk=advice_id,
        submission__milestone_id=milestone_id,
    )

    milestone = advice.submission.milestone
    phd_student = milestone.phd_student

    committee = get_object_or_404(
        DoctoralCommittee.objects.select_related(
            "chair_faculty",
            "chair_faculty__user",
        ),
        phd_student=phd_student,
        approval_status="APPROVED",
    )

    is_chair = committee.chair_faculty == faculty
    is_advisor = phd_student.advisor == faculty

    is_committee_member = CommitteeMember.objects.filter(
        committee=committee,
        faculty=faculty,
    ).exists()

    if not (is_chair or is_advisor or is_committee_member):
        messages.error(
            request,
            "You are not authorized to view this research advice.",
        )

        return redirect(
            "research_milestone_list",
            uuid=faculty.user.uuid,
        )

    chair_evaluation = (
        ResearchMilestoneEvaluation.objects.filter(
            submission=advice.submission,
            evaluator_role="CHAIR",
        )
        .select_related(
            "evaluator",
            "evaluator__user",
        )
        .order_by(
            "-evaluated_at",
        )
        .first()
    )

    committee_evaluations = (
        ResearchMilestoneEvaluation.objects.filter(
            submission=advice.submission,
            evaluator_role="COMMITTEE_MEMBER",
        )
        .select_related(
            "evaluator",
            "evaluator__user",
        )
        .order_by(
            "-evaluated_at",
        )
    )

    context = {
        "faculty": faculty,
        "advice": advice,
        "milestone": milestone,
        "phd_student": phd_student,
        "student": phd_student.student,
        "submission": advice.submission,
        "chair_evaluation": chair_evaluation,
        "committee_evaluations": committee_evaluations,
        "is_chair": is_chair,
        "is_advisor": is_advisor,
        "is_committee_member": is_committee_member,
        "is_view_mode": True,
    }

    return render(
        request,
        "leo/ResearchMilestone/advisor_research_advice_detail.html",
        context,
    )


@login_required
def advisor_research_advice_update(
    request,
    uuid,
    milestone_id,
    advice_id,
):

    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
        ),
        user__uuid=uuid,
    )

    advice = get_object_or_404(
        AdvisorResearchAdvice.objects.select_related(
            "submission",
            "submission__milestone",
            "submission__milestone__phd_student",
            "submission__milestone__phd_student__student",
            "submission__milestone__phd_student__student__user",
            "submission__milestone__phd_student__advisor",
            "submission__milestone__phd_student__advisor__user",
            "advisor",
            "advisor__user",
        ),
        pk=advice_id,
        submission__milestone_id=milestone_id,
    )

    milestone = advice.submission.milestone
    phd_student = milestone.phd_student

    if phd_student.advisor != faculty:
        messages.error(
            request,
            "Only the assigned Advisor can update this research advice.",
        )

        return redirect(
            "advisor_research_advice_detail",
            uuid=faculty.user.uuid,
            milestone_id=milestone.milestone_id,
            advice_id=advice.advice_id,
        )

    if advice.advisor != faculty:
        messages.error(
            request,
            "You are not authorized to update this research advice.",
        )

        return redirect(
            "advisor_research_advice_detail",
            uuid=faculty.user.uuid,
            milestone_id=milestone.milestone_id,
            advice_id=advice.advice_id,
        )

    if advice.is_submitted or advice.status == "SUBMITTED":
        messages.warning(
            request,
            "Submitted research advice cannot be modified.",
        )

        return redirect(
            "advisor_research_advice_detail",
            uuid=faculty.user.uuid,
            milestone_id=milestone.milestone_id,
            advice_id=advice.advice_id,
        )

    chair_evaluation = (
        ResearchMilestoneEvaluation.objects.filter(
            submission=advice.submission,
            evaluator_role="CHAIR",
        )
        .select_related(
            "evaluator",
            "evaluator__user",
        )
        .order_by(
            "-evaluated_at",
        )
        .first()
    )

    if not chair_evaluation:
        messages.warning(
            request,
            "Advisor advice requires a Chair Faculty evaluation.",
        )

        return redirect(
            "research_milestone_detail",
            uuid=faculty.user.uuid,
            milestone_id=milestone.milestone_id,
        )

    if request.method == "POST":

        form = AdvisorResearchAdviceForm(
            request.POST,
            instance=advice,
            faculty=faculty,
            submission=advice.submission,
        )

        if form.is_valid():

            try:
                updated_advice = form.save(
                    commit=True,
                )

                messages.success(
                    request,
                    "Research advice updated successfully.",
                )

                return redirect(
                    "advisor_research_advice_detail",
                    uuid=faculty.user.uuid,
                    milestone_id=milestone.milestone_id,
                    advice_id=updated_advice.advice_id,
                )

            except Exception:
                messages.error(
                    request,
                    "Unable to update research advice. Please try again.",
                )

        else:
            messages.error(
                request,
                "Unable to update research advice. Please check the submitted information.",
            )

    else:
        form = AdvisorResearchAdviceForm(
            instance=advice,
            faculty=faculty,
            submission=advice.submission,
        )

    context = {
        "faculty": faculty,
        "advice": advice,
        "milestone": milestone,
        "phd_student": phd_student,
        "submission": advice.submission,
        "chair_evaluation": chair_evaluation,
        "form": form,
        "is_create": False,
        "is_update": True,
    }

    return render(
        request,
        "leo/ResearchMilestone/advisor_research_advice_form.html",
        context,
    )


###################################################
### RESEARCH PUBLICATION MODULE STARTS HERE #####
###################################################
@login_required
def faculty_advisor_publication_list(request, uuid):

    faculty = get_faculty_or_404(
        uuid,
        request.user,
    )

    search = request.GET.get(
        "search",
        "",
    ).strip()

    status_filter = request.GET.get(
        "status",
        "",
    ).strip()

    indexed_filter = request.GET.get(
        "indexed",
        "",
    ).strip()

    publication_date = request.GET.get(
        "publication_date",
        "",
    ).strip()

    publications = (
        ResearchPublication.objects.filter(
            phd_student__advisor=faculty,
        )
        .select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__phd_program",
            "milestone",
        )
        .order_by(
            "-publication_date",
            "-publication_id",
        )
    )

    if search:
        publications = publications.filter(
            Q(title__icontains=search)
            | Q(authors__icontains=search)
            | Q(journal__icontains=search)
            | Q(doi__icontains=search)
            | Q(phd_student__student__user__first_name__icontains=search)
            | Q(phd_student__student__user__last_name__icontains=search)
            | Q(phd_student__student__student_number__icontains=search)
        )

    if status_filter:
        publications = publications.filter(
            publication_status=status_filter,
        )

    if indexed_filter:
        publications = publications.filter(
            indexed_status=indexed_filter,
        )

    if publication_date:
        try:
            selected_date = datetime.strptime(
                publication_date,
                "%Y-%m-%d",
            ).date()

            publications = publications.filter(
                publication_date=selected_date,
            )

        except ValueError:
            publication_date = ""

    total_publications = publications.count()

    published_count = publications.filter(
        publication_status="PUBLISHED",
    ).count()

    accepted_count = publications.filter(
        publication_status="ACCEPTED",
    ).count()

    submitted_count = publications.filter(
        publication_status="SUBMITTED",
    ).count()

    indexed_count = publications.filter(
        indexed_status="INDEXED",
    ).count()

    paginator = Paginator(
        publications,
        10,
    )

    publication_list = paginator.get_page(
        request.GET.get("page"),
    )

    context = {
        "faculty": faculty,
        "publication_list": publication_list,
        "search": search,
        "status_filter": status_filter,
        "indexed_filter": indexed_filter,
        "publication_date": publication_date,
        "total_publications": total_publications,
        "published_count": published_count,
        "accepted_count": accepted_count,
        "submitted_count": submitted_count,
        "indexed_count": indexed_count,
        "publication_status_choices": (ResearchPublication.PUBLICATION_STATUS_CHOICES),
        "indexed_status_choices": (ResearchPublication.INDEXED_STATUS_CHOICES),
    }

    return render(
        request,
        "leo/ResearchPublication/advisor_publication_list.html",
        context,
    )


@login_required
def faculty_advisor_publication_detail(
    request,
    uuid,
    publication_id,
):

    faculty = get_faculty_or_404(
        uuid,
        request.user,
    )

    publication = get_object_or_404(
        ResearchPublication.objects.select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__phd_program",
            "phd_student__phd_program__department",
            "milestone",
        ),
        publication_id=publication_id,
        phd_student__advisor=faculty,
    )

    context = {
        "faculty": faculty,
        "publication": publication,
        "phd_student": publication.phd_student,
    }

    return render(
        request,
        "leo/ResearchPublication/advisor_publication_detail.html",
        context,
    )


####################################################################
### RESEARCH PUBLICATION COMMITTEE MEMBER MODULE STARTS HERE #######
####################################################################


@login_required
def faculty_committee_member_publication_list(
    request,
    uuid,
):
    faculty = get_faculty_or_404(
        uuid,
        request.user,
    )

    chair_committees = DoctoralCommittee.objects.filter(
        chair_faculty=faculty,
        approval_status="APPROVED",
    )

    member_committees = DoctoralCommittee.objects.filter(
        committee_members__faculty=faculty,
        approval_status="APPROVED",
    )

    is_chair = chair_committees.exists()

    is_committee_member = member_committees.exists()
    publications = (
        ResearchPublication.objects.filter(
            Q(
                phd_student__doctoral_committee__chair_faculty=faculty,
                phd_student__doctoral_committee__approval_status="APPROVED",
            )
            | Q(
                phd_student__doctoral_committee__committee_members__faculty=faculty,
                phd_student__doctoral_committee__approval_status="APPROVED",
            )
        )
        .select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__phd_program",
            "phd_student__phd_program__department",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "milestone",
        )
        .distinct()
        .order_by(
            "-publication_date",
            "-publication_id",
        )
    )
    search = request.GET.get(
        "search",
        "",
    ).strip()

    if search:
        publications = publications.filter(
            Q(
                title__icontains=search,
            )
            | Q(
                authors__icontains=search,
            )
            | Q(
                journal__icontains=search,
            )
            | Q(
                doi__icontains=search,
            )
            | Q(
                phd_student__student__user__first_name__icontains=search,
            )
            | Q(
                phd_student__student__user__last_name__icontains=search,
            )
            | Q(
                phd_student__student__student_number__icontains=search,
            )
            | Q(
                phd_student__phd_program__program_name__icontains=search,
            )
        )

    status_filter = request.GET.get(
        "status",
        "",
    ).strip()

    if status_filter:
        publications = publications.filter(
            publication_status=status_filter,
        )

    indexed_filter = request.GET.get(
        "indexed",
        "",
    ).strip()

    if indexed_filter:
        publications = publications.filter(
            indexed_status=indexed_filter,
        )
    total_publications = publications.count()

    published_count = publications.filter(
        publication_status="PUBLISHED",
    ).count()

    accepted_count = publications.filter(
        publication_status="ACCEPTED",
    ).count()

    submitted_count = publications.filter(
        publication_status="SUBMITTED",
    ).count()

    indexed_count = publications.filter(
        indexed_status="INDEXED",
    ).count()
    paginator = Paginator(
        publications,
        10,
    )

    publication_list = paginator.get_page(
        request.GET.get("page"),
    )
    context = {
        "faculty": faculty,
        "publication_list": publication_list,
        "search": search,
        "status_filter": status_filter,
        "indexed_filter": indexed_filter,
        "total_publications": total_publications,
        "published_count": published_count,
        "accepted_count": accepted_count,
        "submitted_count": submitted_count,
        "indexed_count": indexed_count,
        "publication_status_choices": (ResearchPublication.PUBLICATION_STATUS_CHOICES),
        "indexed_status_choices": (ResearchPublication.INDEXED_STATUS_CHOICES),
        # Role information
        "is_chair": is_chair,
        "is_committee_member": is_committee_member,
        # Explicitly view-only
        "is_view_mode": True,
    }

    return render(
        request,
        "leo/ResearchPublication/committee_member_publication_list.html",
        context,
    )


@login_required
def faculty_committee_member_publication_detail(
    request,
    uuid,
    publication_id,
):
    faculty = get_faculty_or_404(
        uuid,
        request.user,
    )
    publication = get_object_or_404(
        ResearchPublication.objects.select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__phd_program",
            "phd_student__phd_program__department",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "milestone",
        ),
        Q(
            publication_id=publication_id,
        )
        & (
            Q(
                phd_student__doctoral_committee__chair_faculty=faculty,
                phd_student__doctoral_committee__approval_status="APPROVED",
            )
            | Q(
                phd_student__doctoral_committee__committee_members__faculty=faculty,
                phd_student__doctoral_committee__approval_status="APPROVED",
            )
        ),
    )
    committee = getattr(
        publication.phd_student,
        "doctoral_committee",
        None,
    )

    is_chair = bool(
        committee
        and committee.approval_status == "APPROVED"
        and committee.chair_faculty_id == faculty.pk
    )

    is_committee_member = False

    if committee:
        is_committee_member = CommitteeMember.objects.filter(
            committee=committee,
            faculty=faculty,
        ).exists()
    committee_members = (
        CommitteeMember.objects.filter(
            committee=committee,
        )
        .select_related(
            "faculty",
            "faculty__user",
            "department",
        )
        .order_by(
            "role",
            "faculty__user__first_name",
            "faculty__user__last_name",
        )
        if committee
        else CommitteeMember.objects.none()
    )

    context = {
        "faculty": faculty,
        "publication": publication,
        "phd_student": publication.phd_student,
        "committee": committee,
        "committee_members": committee_members,
        # Role information
        "is_chair": is_chair,
        "is_committee_member": is_committee_member,
        # Explicitly view-only
        "is_view_mode": True,
    }

    return render(
        request,
        "leo/ResearchPublication/committee_member_publication_detail.html",
        context,
    )


####################################################################
######## FINAL DISSERTATION EVALUATION - ADVISOR SIDE ##############
####################################################################


@login_required
def faculty_advisor_final_dissertation_list(request, uuid):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
            "faculty_rank",
            "department",
        ),
        user__uuid=uuid,
        user=request.user,
        employment_status="ACTIVE",
    )

    submissions = (
        FinalDissertationSubmission.objects.filter(
            phd_student__advisor=faculty,
        )
        .select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__phd_program",
            "phd_student__phd_program__department",
            "phd_student__advisor",
            "phd_student__advisor__user",
        )
        .order_by(
            "phd_student_id",
            "-submission_number",
            "-created_at",
        )
    )

    all_submissions = list(submissions)
    latest_by_student = {}

    for submission in all_submissions:
        student_key = submission.phd_student_id

        if student_key not in latest_by_student:
            latest_by_student[student_key] = submission

    submission_list = list(latest_by_student.values())

    submission_list.sort(
        key=lambda item: (
            item.created_at or datetime.min,
            item.submission_number or 0,
        ),
        reverse=True,
    )

    for submission in submission_list:
        evaluation = (
            FinalDissertationAdvisorEvaluation.objects.filter(
                submission=submission,
                advisor=faculty,
                submission_number=submission.submission_number,
            )
            .order_by(
                "-submitted_at",
                "-evaluation_id",
            )
            .first()
        )

        submission.advisor_evaluation = evaluation
        submission.evaluation_submitted = bool(evaluation and evaluation.is_submitted)
        submission.can_evaluate = (
            submission.status == "ADVISOR_REVIEW"
            and not submission.evaluation_submitted
        )

    search = request.GET.get("search", "").strip()
    status = request.GET.get("status", "").strip()
    selected_date = request.GET.get("date", "").strip()

    if search:
        search_lower = search.lower()

        submission_list = [
            submission
            for submission in submission_list
            if (
                search_lower
                in (submission.phd_student.student.user.get_full_name() or "").lower()
                or search_lower
                in (submission.phd_student.student.student_number or "").lower()
                or search_lower
                in (
                    str(submission.phd_student.phd_program)
                    if submission.phd_student.phd_program
                    else ""
                ).lower()
            )
        ]

    if status:
        submission_list = [
            submission for submission in submission_list if submission.status == status
        ]

    if selected_date:
        try:
            parsed_date = datetime.strptime(
                selected_date,
                "%Y-%m-%d",
            ).date()

            filtered_by_date = []

            for submission in submission_list:
                submission_date = None

                if submission.submitted_at:
                    submission_date = submission.submitted_at.date()
                elif submission.submission_date:
                    submission_date = submission.submission_date

                if submission_date == parsed_date:
                    filtered_by_date.append(submission)

            submission_list = filtered_by_date

        except ValueError:
            selected_date = ""

    total_submissions = len(submission_list)

    pending_count = sum(1 for submission in submission_list if submission.can_evaluate)

    evaluated_count = sum(
        1 for submission in submission_list if submission.evaluation_submitted
    )

    approved_count = sum(
        1
        for submission in submission_list
        if (
            submission.advisor_evaluation
            and submission.advisor_evaluation.recommendation == "APPROVE"
        )
    )

    revision_count = sum(
        1
        for submission in submission_list
        if (
            submission.advisor_evaluation
            and submission.advisor_evaluation.recommendation == "REVISION_REQUIRED"
        )
    )

    rejected_count = sum(
        1
        for submission in submission_list
        if (
            submission.advisor_evaluation
            and submission.advisor_evaluation.recommendation == "REJECT"
        )
    )

    context = {
        "faculty": faculty,
        "submissions": submission_list,
        "search": search,
        "selected_date": selected_date,
        "total_submissions": total_submissions,
        "pending_count": pending_count,
        "evaluated_count": evaluated_count,
        "approved_count": approved_count,
        "revision_count": revision_count,
        "rejected_count": rejected_count,
    }

    return render(
        request,
        "leo/FinalDissertation/advisor_final_dissertation_list.html",
        context,
    )


@login_required
def faculty_advisor_final_dissertation_detail(
    request,
    uuid,
    submission_id,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
            "faculty_rank",
            "department",
        ),
        user__uuid=uuid,
        user=request.user,
        employment_status="ACTIVE",
    )

    submission = get_object_or_404(
        FinalDissertationSubmission.objects.select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__phd_program",
            "phd_student__phd_program__department",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "phd_student__doctoral_committee",
            "phd_student__doctoral_committee__chair_faculty",
            "phd_student__doctoral_committee__chair_faculty__user",
        ),
        submission_id=submission_id,
        phd_student__advisor=faculty,
    )

    phd_student = submission.phd_student

    submission_content_type = ContentType.objects.get_for_model(
        submission,
    )

    video_evidence = (
        PhDVideoEvidence.objects.filter(
            phd_student=phd_student,
            evidence_type="FINAL_DISSERTATION_SUBMISSION",
            target_content_type=submission_content_type,
            target_object_id=submission.pk,
        )
        .select_related(
            "uploaded_by",
        )
        .first()
    )

    evaluation = (
        FinalDissertationAdvisorEvaluation.objects.filter(
            submission=submission,
            advisor=faculty,
            submission_number=submission.submission_number,
        )
        .select_related(
            "advisor",
            "advisor__user",
        )
        .order_by(
            "-submitted_at",
            "-evaluation_id",
        )
        .first()
    )

    evaluation_submitted = bool(evaluation and evaluation.is_submitted)

    can_evaluate = submission.status == "ADVISOR_REVIEW" and not evaluation_submitted

    previous_submissions = (
        FinalDissertationSubmission.objects.filter(
            phd_student=phd_student,
        )
        .exclude(
            submission_id=submission.submission_id,
        )
        .order_by(
            "-submission_number",
            "-submitted_at",
        )
    )

    previous_evaluations = (
        FinalDissertationAdvisorEvaluation.objects.filter(
            submission__phd_student=phd_student,
            advisor=faculty,
            is_submitted=True,
        )
        .exclude(
            submission=submission,
        )
        .select_related(
            "submission",
            "advisor",
            "advisor__user",
        )
        .order_by(
            "-submitted_at",
            "-evaluation_id",
        )
    )

    context = {
        "faculty": faculty,
        "phd_student": phd_student,
        "submission": submission,
        "evaluation": evaluation,
        "advisor_evaluation": evaluation,
        "evaluation_submitted": evaluation_submitted,
        "can_evaluate": can_evaluate,
        "previous_submissions": previous_submissions,
        "previous_evaluations": previous_evaluations,
        "video_evidence": video_evidence,
    }

    return render(
        request,
        "leo/FinalDissertation/advisor_final_dissertation_detail.html",
        context,
    )


@login_required
def faculty_advisor_final_dissertation_evaluate(
    request,
    uuid,
    submission_id,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
        ),
        user__uuid=uuid,
        user=request.user,
        employment_status="ACTIVE",
    )

    submission = get_object_or_404(
        FinalDissertationSubmission.objects.select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__phd_program",
            "phd_student__advisor",
            "phd_student__advisor__user",
        ),
        submission_id=submission_id,
        phd_student__advisor=faculty,
    )

    if submission.status != "ADVISOR_REVIEW":
        messages.warning(
            request,
            "This dissertation is not currently awaiting advisor review.",
        )

        return redirect(
            "faculty_advisor_final_dissertation_detail",
            uuid=uuid,
            submission_id=submission_id,
        )

    existing_evaluation = (
        FinalDissertationAdvisorEvaluation.objects.filter(
            submission=submission,
            advisor=faculty,
            submission_number=submission.submission_number,
        )
        .order_by(
            "-submitted_at",
            "-evaluation_id",
        )
        .first()
    )

    if existing_evaluation and existing_evaluation.is_submitted:
        messages.warning(
            request,
            "This dissertation has already been evaluated.",
        )

        return redirect(
            "faculty_advisor_final_dissertation_evaluation_detail",
            uuid=uuid,
            submission_id=submission_id,
            evaluation_id=existing_evaluation.evaluation_id,
        )

    if request.method == "POST":
        form = FinalDissertationAdvisorEvaluationForm(
            request.POST,
            instance=existing_evaluation,
            faculty=faculty,
            submission=submission,
        )

        if form.is_valid():
            with transaction.atomic():
                evaluation = form.save(
                    commit=True,
                )

                if evaluation.recommendation == "APPROVE":
                    submission.status = "COMMITTEE_EVALUATION"

                elif evaluation.recommendation == "REVISION_REQUIRED":
                    submission.status = "REVISION_REQUIRED"

                elif evaluation.recommendation == "REJECT":
                    submission.status = "REJECTED"

                submission.save(
                    update_fields=[
                        "status",
                        "updated_at",
                    ],
                )

            if evaluation.recommendation == "APPROVE":
                messages.success(
                    request,
                    "Final dissertation approved by advisor and moved to committee evaluation.",
                )

            elif evaluation.recommendation == "REVISION_REQUIRED":
                messages.warning(
                    request,
                    "Revision has been requested for the final dissertation.",
                )

            elif evaluation.recommendation == "REJECT":
                messages.error(
                    request,
                    "Final dissertation has been rejected by the advisor.",
                )

            return redirect(
                "faculty_advisor_final_dissertation_evaluation_detail",
                uuid=uuid,
                submission_id=submission_id,
                evaluation_id=evaluation.evaluation_id,
            )

    else:
        form = FinalDissertationAdvisorEvaluationForm(
            instance=existing_evaluation,
            faculty=faculty,
            submission=submission,
        )

    context = {
        "faculty": faculty,
        "submission": submission,
        "form": form,
        "evaluation": existing_evaluation,
    }

    return render(
        request,
        "leo/FinalDissertation/advisor_final_dissertation_evaluate.html",
        context,
    )


@login_required
def faculty_advisor_final_dissertation_evaluation_detail(
    request,
    uuid,
    submission_id,
    evaluation_id,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
            "faculty_rank",
            "department",
        ),
        user__uuid=uuid,
        user=request.user,
        employment_status="ACTIVE",
    )

    evaluation = get_object_or_404(
        FinalDissertationAdvisorEvaluation.objects.select_related(
            "submission",
            "submission__phd_student",
            "submission__phd_student__student",
            "submission__phd_student__student__user",
            "submission__phd_student__phd_program",
            "submission__phd_student__advisor",
            "advisor",
            "advisor__user",
        ),
        evaluation_id=evaluation_id,
        submission_id=submission_id,
        advisor=faculty,
    )

    if not evaluation.is_submitted:
        messages.warning(
            request,
            "This advisor evaluation has not been submitted yet.",
        )

        return redirect(
            "faculty_advisor_final_dissertation_evaluate",
            uuid=uuid,
            submission_id=submission_id,
        )

    context = {
        "faculty": faculty,
        "submission": evaluation.submission,
        "evaluation": evaluation,
    }

    return render(
        request,
        "leo/FinalDissertation/advisor_final_dissertation_evaluation_detail.html",
        context,
    )


# ========================================================
# Final Dissertation evaluation - Committee and Chair Side
# ========================================================


@login_required
def faculty_committee_final_dissertation_list(
    request,
    uuid,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
            "faculty_rank",
            "department",
        ),
        user__uuid=uuid,
        user=request.user,
        employment_status="ACTIVE",
    )

    submissions = (
        FinalDissertationSubmission.objects.filter(
            Q(phd_student__doctoral_committee__chair_faculty=faculty)
            | Q(phd_student__doctoral_committee__committee_members__faculty=faculty)
        )
        .filter(
            status__in=[
                "SUBMITTED",
                "ADVISOR_REVIEW",
                "COMMITTEE_EVALUATION",
                "CHAIR_REVIEW",
                "REVISION_REQUIRED",
                "APPROVED",
                "REJECTED",
            ]
        )
        .select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__phd_program",
            "phd_student__phd_program__department",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "phd_student__doctoral_committee",
            "phd_student__doctoral_committee__chair_faculty",
            "phd_student__doctoral_committee__chair_faculty__user",
        )
        .prefetch_related(
            Prefetch(
                "phd_student__doctoral_committee__committee_members",
                queryset=CommitteeMember.objects.select_related(
                    "faculty",
                    "faculty__user",
                    "department",
                ).order_by(
                    "role",
                    "member_id",
                ),
            )
        )
        .order_by(
            "phd_student_id",
            "-submission_number",
            "-created_at",
        )
    )

    all_submissions = list(submissions)

    latest_by_student = {}

    for submission in all_submissions:
        student_key = submission.phd_student_id

        if student_key not in latest_by_student:
            latest_by_student[student_key] = submission

    submission_list = list(latest_by_student.values())

    submission_list.sort(
        key=lambda item: (
            item.created_at or datetime.min,
            item.submission_number or 0,
        ),
        reverse=True,
    )

    submission_ids = [submission.submission_id for submission in submission_list]

    submission_numbers = {
        submission.submission_id: submission.submission_number
        for submission in submission_list
    }

    advisor_evaluations = (
        FinalDissertationAdvisorEvaluation.objects.filter(
            submission_id__in=submission_ids,
            submission_number__in=list(submission_numbers.values()),
            is_submitted=True,
        )
        .select_related(
            "advisor",
            "advisor__user",
        )
        .order_by(
            "-submitted_at",
            "-evaluation_id",
        )
    )

    advisor_evaluation_map = {}

    for evaluation in advisor_evaluations:
        key = (
            evaluation.submission_id,
            evaluation.submission_number,
        )

        if key not in advisor_evaluation_map:
            advisor_evaluation_map[key] = evaluation

    committee_evaluations = (
        FinalDissertationCommitteeEvaluation.objects.filter(
            submission_id__in=submission_ids,
            reviewer_role__in=[
                "COMMITTEE_MEMBER",
                "CHAIR",
            ],
        )
        .select_related(
            "committee_member",
            "committee_member__faculty",
            "committee_member__faculty__user",
        )
        .order_by(
            "-submitted_at",
            "-evaluation_id",
        )
    )

    committee_evaluation_map = {}

    for evaluation in committee_evaluations:
        key = (
            evaluation.submission_id,
            evaluation.submission_number,
            evaluation.committee_member_id,
        )

        if key not in committee_evaluation_map:
            committee_evaluation_map[key] = evaluation

    for submission in submission_list:
        committee = getattr(
            submission.phd_student,
            "doctoral_committee",
            None,
        )

        submission.committee = committee

        if not committee:
            submission.current_role = None
            submission.current_role_display = "Not Assigned"
            submission.workflow_status = "Committee Not Assigned"
            submission.workflow_status_code = "NO_COMMITTEE"
            submission.workflow_message = "Doctoral committee has not been assigned."
            submission.action_label = "View Details"
            submission.action_type = "DETAIL"
            submission.can_evaluate = False
            submission.can_finalize = False
            submission.committee_required_count = 0
            submission.committee_completed_count = 0
            submission.committee_pending_count = 0
            submission.committee_progress = 0
            submission.current_evaluation = None
            submission.final_decision = None
            continue

        current_member = None

        if committee.chair_faculty_id == faculty.pk:
            current_role = "CHAIR"
            current_role_display = "Chair"
        else:
            current_member = next(
                (
                    member
                    for member in committee.committee_members.all()
                    if member.faculty_id == faculty.pk
                ),
                None,
            )

            if current_member:
                current_role = current_member.role
                current_role_display = current_member.get_role_display()
            else:
                current_role = None
                current_role_display = "Committee Member"

        submission.current_role = current_role
        submission.current_role_display = current_role_display

        required_members = [
            member
            for member in committee.committee_members.all()
            if member.role
            in [
                "CO_CHAIR",
                "INTERNAL_MEMBER",
                "EXTERNAL_MEMBER",
            ]
        ]

        completed_member_ids = set()

        for member in required_members:
            evaluation = committee_evaluation_map.get(
                (
                    submission.submission_id,
                    submission.submission_number,
                    member.member_id,
                )
            )

            if evaluation and evaluation.is_submitted:
                completed_member_ids.add(member.member_id)

        required_count = len(required_members)
        completed_count = len(completed_member_ids)
        pending_count = required_count - completed_count

        if required_count:
            committee_progress = round((completed_count / required_count) * 100)
        else:
            committee_progress = 0

        submission.committee_required_count = required_count
        submission.committee_completed_count = completed_count
        submission.committee_pending_count = pending_count
        submission.committee_progress = committee_progress

        current_evaluation = None

        if current_member:
            current_evaluation = committee_evaluation_map.get(
                (
                    submission.submission_id,
                    submission.submission_number,
                    current_member.member_id,
                )
            )

        submission.current_evaluation = current_evaluation

        chair_final_decision = None

        if committee.chair_faculty_id:
            chair_member = next(
                (
                    member
                    for member in committee.committee_members.all()
                    if member.faculty_id == committee.chair_faculty_id
                    and member.role == "CHAIR"
                ),
                None,
            )

            if chair_member:
                chair_final_decision = committee_evaluation_map.get(
                    (
                        submission.submission_id,
                        submission.submission_number,
                        chair_member.member_id,
                    )
                )

        submission.final_decision = chair_final_decision

        advisor_evaluation = advisor_evaluation_map.get(
            (
                submission.submission_id,
                submission.submission_number,
            )
        )

        submission.advisor_evaluation = advisor_evaluation
        submission.advisor_approved = bool(
            advisor_evaluation
            and advisor_evaluation.recommendation == "APPROVE"
            and advisor_evaluation.is_submitted
        )

        submission.can_evaluate = False
        submission.can_finalize = False
        submission.action_label = "View Details"
        submission.action_type = "DETAIL"

        if submission.status in [
            "SUBMITTED",
            "ADVISOR_REVIEW",
        ]:
            submission.workflow_status = "Waiting for Advisor Evaluation"
            submission.workflow_status_code = "WAITING_ADVISOR"
            submission.workflow_message = "The dissertation is waiting for the Advisor to complete the evaluation."

        elif submission.status == "COMMITTEE_EVALUATION":
            if current_role == "CHAIR":
                if completed_count == required_count and required_count > 0:
                    submission.workflow_status = "Ready for Chair Final Review"
                    submission.workflow_status_code = "READY_FOR_CHAIR"
                    submission.workflow_message = (
                        "All required committee evaluations have been completed."
                    )
                    submission.action_label = "Review & Finalize"
                    submission.action_type = "CHAIR_REVIEW"
                    submission.can_finalize = True
                else:
                    submission.workflow_status = "Waiting for Committee Evaluations"
                    submission.workflow_status_code = "WAITING_COMMITTEE"
                    submission.workflow_message = (
                        f"{completed_count} of {required_count} "
                        "required committee evaluations are complete."
                    )
            elif current_role in [
                "CO_CHAIR",
                "INTERNAL_MEMBER",
                "EXTERNAL_MEMBER",
            ]:
                if current_evaluation and current_evaluation.is_submitted:
                    if completed_count == required_count and required_count > 0:
                        submission.workflow_status = "Waiting for Chair to Finalize"
                        submission.workflow_status_code = "WAITING_CHAIR"
                        submission.workflow_message = "Your evaluation is complete and all required committee evaluations have been submitted."
                    else:
                        submission.workflow_status = "Evaluation Submitted"
                        submission.workflow_status_code = "EVALUATION_SUBMITTED"
                        submission.workflow_message = (
                            f"Your evaluation is complete. "
                            f"{pending_count} committee evaluation"
                            f"{'s' if pending_count != 1 else ''} still pending."
                        )
                    submission.action_label = "View Evaluation"
                    submission.action_type = "EVALUATION_DETAIL"
                else:
                    submission.workflow_status = "Committee Evaluation Required"
                    submission.workflow_status_code = "EVALUATION_REQUIRED"
                    submission.workflow_message = (
                        "Your committee evaluation is required."
                    )
                    submission.action_label = "Evaluate"
                    submission.action_type = "EVALUATE"
                    submission.can_evaluate = True
            else:
                submission.workflow_status = "Committee Evaluation in Progress"
                submission.workflow_status_code = "COMMITTEE_IN_PROGRESS"
                submission.workflow_message = (
                    f"{completed_count} of {required_count} "
                    "required committee evaluations are complete."
                )

        elif submission.status == "CHAIR_REVIEW":
            if current_role == "CHAIR":
                submission.workflow_status = "Ready for Chair Final Review"
                submission.workflow_status_code = "READY_FOR_CHAIR"
                submission.workflow_message = "All committee evaluations are complete and the dissertation is ready for final review."
                submission.action_label = "Review & Finalize"
                submission.action_type = "CHAIR_REVIEW"
                submission.can_finalize = True
            elif current_role in [
                "CO_CHAIR",
                "INTERNAL_MEMBER",
                "EXTERNAL_MEMBER",
            ]:
                submission.workflow_status = "Waiting for Chair to Finalize"
                submission.workflow_status_code = "WAITING_CHAIR"
                submission.workflow_message = "Committee evaluation is complete. The dissertation is waiting for the Chair's final decision."
                submission.action_label = "View Details"
                submission.action_type = "DETAIL"
            else:
                submission.workflow_status = "Chair Final Review"
                submission.workflow_status_code = "CHAIR_REVIEW"
                submission.workflow_message = (
                    "The dissertation is currently under Chair final review."
                )

        elif submission.status == "REVISION_REQUIRED":
            submission.workflow_status = "Revision Required"
            submission.workflow_status_code = "REVISION_REQUIRED"
            submission.workflow_message = (
                "The Chair has requested revisions to the final dissertation."
            )

        elif submission.status == "APPROVED":
            submission.workflow_status = "Dissertation Approved"
            submission.workflow_status_code = "APPROVED"
            submission.workflow_message = (
                "The final dissertation has been approved by the Chair."
            )

        elif submission.status == "REJECTED":
            submission.workflow_status = "Dissertation Rejected"
            submission.workflow_status_code = "REJECTED"
            submission.workflow_message = (
                "The final dissertation has been rejected by the Chair."
            )

        submission.submission_status_display = submission.get_status_display()

        submission.submission_date_display = (
            submission.submitted_at.date()
            if submission.submitted_at
            else submission.submission_date
        )

    search = request.GET.get(
        "search",
        "",
    ).strip()

    status_filter = request.GET.get(
        "status",
        "",
    ).strip()

    selected_date = request.GET.get(
        "date",
        "",
    ).strip()

    if search:
        search_lower = search.lower()

        submission_list = [
            submission
            for submission in submission_list
            if (
                search_lower
                in (submission.phd_student.student.user.get_full_name() or "").lower()
                or search_lower
                in (submission.phd_student.student.student_number or "").lower()
                or search_lower
                in (
                    str(submission.phd_student.phd_program)
                    if submission.phd_student.phd_program
                    else ""
                ).lower()
                or search_lower in (submission.dissertation_title or "").lower()
            )
        ]

    if status_filter:
        submission_list = [
            submission
            for submission in submission_list
            if submission.workflow_status_code == status_filter
        ]

    if selected_date:
        try:
            parsed_date = datetime.strptime(
                selected_date,
                "%Y-%m-%d",
            ).date()

            submission_list = [
                submission
                for submission in submission_list
                if submission.submission_date_display == parsed_date
            ]
        except ValueError:
            selected_date = ""

    total_submissions = len(submission_list)

    evaluation_required_count = sum(
        1
        for submission in submission_list
        if submission.workflow_status_code == "EVALUATION_REQUIRED"
    )

    waiting_advisor_count = sum(
        1
        for submission in submission_list
        if submission.workflow_status_code == "WAITING_ADVISOR"
    )

    waiting_committee_count = sum(
        1
        for submission in submission_list
        if submission.workflow_status_code == "WAITING_COMMITTEE"
    )

    waiting_chair_count = sum(
        1
        for submission in submission_list
        if submission.workflow_status_code == "WAITING_CHAIR"
    )

    ready_for_chair_count = sum(
        1
        for submission in submission_list
        if submission.workflow_status_code == "READY_FOR_CHAIR"
    )

    approved_count = sum(
        1
        for submission in submission_list
        if submission.workflow_status_code == "APPROVED"
    )

    revision_count = sum(
        1
        for submission in submission_list
        if submission.workflow_status_code == "REVISION_REQUIRED"
    )

    rejected_count = sum(
        1
        for submission in submission_list
        if submission.workflow_status_code == "REJECTED"
    )

    status_choices = [
        ("WAITING_ADVISOR", "Waiting for Advisor"),
        ("EVALUATION_REQUIRED", "Evaluation Required"),
        ("EVALUATION_SUBMITTED", "Evaluation Submitted"),
        ("WAITING_COMMITTEE", "Waiting for Committee"),
        ("WAITING_CHAIR", "Waiting for Chair"),
        ("READY_FOR_CHAIR", "Ready for Chair Review"),
        ("REVISION_REQUIRED", "Revision Required"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]

    context = {
        "faculty": faculty,
        "submissions": submission_list,
        "search": search,
        "status_filter": status_filter,
        "selected_date": selected_date,
        "total_submissions": total_submissions,
        "evaluation_required_count": evaluation_required_count,
        "waiting_advisor_count": waiting_advisor_count,
        "waiting_committee_count": waiting_committee_count,
        "waiting_chair_count": waiting_chair_count,
        "ready_for_chair_count": ready_for_chair_count,
        "approved_count": approved_count,
        "revision_count": revision_count,
        "rejected_count": rejected_count,
        "status_choices": status_choices,
    }

    return render(
        request,
        "leo/FinalDissertation/committee_final_dissertation_list.html",
        context,
    )


@login_required
def faculty_committee_final_dissertation_detail(
    request,
    uuid,
    submission_id,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
            "faculty_rank",
            "department",
        ),
        user__uuid=uuid,
        user=request.user,
        employment_status="ACTIVE",
    )

    submission = get_object_or_404(
        FinalDissertationSubmission.objects.select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__phd_program",
            "phd_student__phd_program__department",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "phd_student__doctoral_committee",
            "phd_student__doctoral_committee__chair_faculty",
            "phd_student__doctoral_committee__chair_faculty__user",
        ),
        submission_id=submission_id,
    )

    phd_student = submission.phd_student

    committee = getattr(
        phd_student,
        "doctoral_committee",
        None,
    )

    # ---------------------------------------------------------
    # Committee validation
    # ---------------------------------------------------------

    if not committee:
        messages.error(
            request,
            "No doctoral committee is associated with this dissertation submission.",
        )

        return redirect(
            "faculty_committee_final_dissertation_list",
            uuid=uuid,
        )

    if committee.approval_status != "APPROVED":
        messages.error(
            request,
            "The doctoral committee has not been approved.",
        )

        return redirect(
            "faculty_committee_final_dissertation_list",
            uuid=uuid,
        )

    # ---------------------------------------------------------
    # Faculty authorization
    # ---------------------------------------------------------

    is_chair = committee.chair_faculty_id == faculty.pk

    committee_member = (
        CommitteeMember.objects.select_related(
            "faculty",
            "faculty__user",
            "faculty__faculty_rank",
            "faculty__department",
            "department",
        )
        .filter(
            committee=committee,
            faculty=faculty,
        )
        .first()
    )

    is_committee_member = committee_member is not None

    if not is_chair and not is_committee_member:
        messages.error(
            request,
            "You are not authorized to access this dissertation submission.",
        )

        return redirect(
            "faculty_committee_final_dissertation_list",
            uuid=uuid,
        )

    # ---------------------------------------------------------
    # Current faculty role
    # ---------------------------------------------------------

    if is_chair:
        current_role = "CHAIR"
        current_role_display = "Chair"
    elif committee_member:
        current_role = committee_member.role
        current_role_display = committee_member.get_role_display()
    else:
        current_role = None
        current_role_display = "Committee Member"

    # ---------------------------------------------------------
    # Current submission number
    # ---------------------------------------------------------

    current_submission_number = (
        getattr(
            submission,
            "submission_number",
            1,
        )
        or 1
    )

    submission_content_type = ContentType.objects.get_for_model(
        submission,
    )

    video_evidence = (
        PhDVideoEvidence.objects.filter(
            phd_student=submission.phd_student,
            evidence_type="FINAL_DISSERTATION_SUBMISSION",
            target_content_type=submission_content_type,
            target_object_id=submission.pk,
        )
        .select_related(
            "uploaded_by",
        )
        .first()
    )

    # ---------------------------------------------------------
    # Advisor evaluation
    # ---------------------------------------------------------

    advisor_evaluation = (
        FinalDissertationAdvisorEvaluation.objects.filter(
            submission=submission,
            submission_number=current_submission_number,
            is_submitted=True,
        )
        .select_related(
            "advisor",
            "advisor__user",
        )
        .order_by(
            "-submitted_at",
            "-evaluation_id",
        )
        .first()
    )

    advisor_evaluation_submitted = bool(
        advisor_evaluation and advisor_evaluation.is_submitted
    )

    advisor_approved = bool(
        advisor_evaluation
        and advisor_evaluation.recommendation == "APPROVE"
        and advisor_evaluation.is_submitted
    )

    # ---------------------------------------------------------
    # Committee members
    # ---------------------------------------------------------

    committee_members = list(
        CommitteeMember.objects.select_related(
            "faculty",
            "faculty__user",
            "faculty__faculty_rank",
            "faculty__department",
            "department",
        )
        .filter(
            committee=committee,
        )
        .order_by(
            "role",
            "member_id",
        )
    )

    # ---------------------------------------------------------
    # Required evaluators
    #
    # Chair is NOT counted here.
    # Required:
    #   CO_CHAIR
    #   INTERNAL_MEMBER
    #   EXTERNAL_MEMBER
    # ---------------------------------------------------------

    required_members = [
        member
        for member in committee_members
        if member.role
        in [
            "CO_CHAIR",
            "INTERNAL_MEMBER",
            "EXTERNAL_MEMBER",
        ]
    ]

    required_member_ids = [member.member_id for member in required_members]

    # ---------------------------------------------------------
    # All committee evaluations for current submission
    # ---------------------------------------------------------

    committee_evaluations = (
        FinalDissertationCommitteeEvaluation.objects.filter(
            submission=submission,
            submission_number=current_submission_number,
            committee_member__committee=committee,
        )
        .select_related(
            "committee_member",
            "committee_member__faculty",
            "committee_member__faculty__user",
            "committee_member__faculty__faculty_rank",
            "committee_member__faculty__department",
            "committee_member__department",
        )
        .order_by(
            "-submitted_at",
            "-evaluation_id",
        )
    )

    # ---------------------------------------------------------
    # Latest evaluation per committee member
    # ---------------------------------------------------------

    evaluation_map = {}

    for evaluation in committee_evaluations:
        member_id = evaluation.committee_member_id

        if member_id not in evaluation_map:
            evaluation_map[member_id] = evaluation

    # ---------------------------------------------------------
    # Attach evaluation status to each committee member
    # ---------------------------------------------------------

    completed_members = []
    pending_members = []

    for member in required_members:
        evaluation = evaluation_map.get(member.member_id)

        member.evaluation = evaluation

        member.evaluation_submitted = bool(evaluation and evaluation.is_submitted)

        if member.evaluation_submitted:
            completed_members.append(member)
        else:
            pending_members.append(member)

    # ---------------------------------------------------------
    # Evaluation statistics
    # ---------------------------------------------------------

    evaluations_required = len(required_members)

    evaluations_completed = len(completed_members)

    evaluations_pending = len(pending_members)

    evaluation_percentage = (
        int((evaluations_completed / evaluations_required) * 100)
        if evaluations_required
        else 0
    )

    evaluation_ready_for_chair = (
        evaluations_required > 0 and evaluations_completed == evaluations_required
    )

    # ---------------------------------------------------------
    # Current faculty evaluation
    # ---------------------------------------------------------

    my_evaluation = None

    if committee_member:
        my_evaluation = evaluation_map.get(committee_member.member_id)

    my_evaluation_submitted = bool(my_evaluation and my_evaluation.is_submitted)

    # ---------------------------------------------------------
    # Committee evaluation permission
    # ---------------------------------------------------------

    committee_evaluation_allowed = (
        is_committee_member
        and current_role
        in [
            "CO_CHAIR",
            "INTERNAL_MEMBER",
            "EXTERNAL_MEMBER",
        ]
        and submission.status == "COMMITTEE_EVALUATION"
        and advisor_approved
        and not my_evaluation_submitted
    )

    # ---------------------------------------------------------
    # Chair final decision
    # ---------------------------------------------------------

    chair_member = (
        CommitteeMember.objects.select_related(
            "faculty",
            "faculty__user",
        )
        .filter(
            committee=committee,
            faculty=committee.chair_faculty,
            role="CHAIR",
        )
        .first()
    )

    chair_final_decision = None

    if chair_member:
        chair_final_decision = evaluation_map.get(chair_member.member_id)

    chair_final_decision_submitted = bool(
        chair_final_decision
        and chair_final_decision.is_submitted
        and getattr(
            chair_final_decision,
            "is_final_decision",
            False,
        )
    )

    # ---------------------------------------------------------
    # Chair finalization permission
    # ---------------------------------------------------------

    chair_finalize_allowed = (
        is_chair
        and submission.status
        in [
            "COMMITTEE_EVALUATION",
            "CHAIR_REVIEW",
        ]
        and advisor_approved
        and evaluation_ready_for_chair
        and not chair_final_decision_submitted
    )

    # ---------------------------------------------------------
    # Workflow state
    # ---------------------------------------------------------

    workflow_status = "UNKNOWN"
    workflow_status_code = "UNKNOWN"
    workflow_message = ""

    if submission.status in [
        "SUBMITTED",
        "ADVISOR_REVIEW",
    ]:
        workflow_status = "Waiting for Advisor Evaluation"
        workflow_status_code = "WAITING_ADVISOR"
        workflow_message = (
            "The final dissertation is waiting for the Advisor evaluation."
        )

    elif submission.status == "COMMITTEE_EVALUATION":

        if is_chair:

            if evaluation_ready_for_chair:
                workflow_status = "Ready for Chair Final Review"
                workflow_status_code = "READY_FOR_CHAIR"
                workflow_message = (
                    "All required committee evaluations have been completed."
                )
            else:
                workflow_status = "Committee Evaluation in Progress"
                workflow_status_code = "WAITING_COMMITTEE"
                workflow_message = (
                    f"{evaluations_completed} of "
                    f"{evaluations_required} "
                    "required committee evaluations are complete."
                )

        elif current_role in [
            "CO_CHAIR",
            "INTERNAL_MEMBER",
            "EXTERNAL_MEMBER",
        ]:

            if my_evaluation_submitted:

                if evaluation_ready_for_chair:
                    workflow_status = "Waiting for Chair to Finalize"
                    workflow_status_code = "WAITING_CHAIR"
                    workflow_message = (
                        "All committee evaluations have been submitted. "
                        "The dissertation is waiting for the Chair's final decision."
                    )
                else:
                    workflow_status = "Evaluation Submitted"
                    workflow_status_code = "EVALUATION_SUBMITTED"
                    workflow_message = (
                        f"Your evaluation has been submitted. "
                        f"{evaluations_pending} committee evaluation"
                        f"{'s' if evaluations_pending != 1 else ''} "
                        "still pending."
                    )

            else:
                workflow_status = "Committee Evaluation Required"
                workflow_status_code = "EVALUATION_REQUIRED"
                workflow_message = "Your committee evaluation is required."

    elif submission.status == "CHAIR_REVIEW":

        if is_chair:
            workflow_status = "Ready for Chair Final Review"
            workflow_status_code = "READY_FOR_CHAIR"
            workflow_message = (
                "All committee evaluations are complete. "
                "The dissertation is ready for your final decision."
            )
        else:
            workflow_status = "Waiting for Chair to Finalize"
            workflow_status_code = "WAITING_CHAIR"
            workflow_message = (
                "Committee evaluation is complete and the dissertation "
                "is waiting for the Chair's final decision."
            )

    elif submission.status == "REVISION_REQUIRED":
        workflow_status = "Revision Required"
        workflow_status_code = "REVISION_REQUIRED"
        workflow_message = (
            "The Chair has requested revisions to the final dissertation."
        )

    elif submission.status == "APPROVED":
        workflow_status = "Dissertation Approved"
        workflow_status_code = "APPROVED"
        workflow_message = "The final dissertation has been approved by the Chair."

    elif submission.status == "REJECTED":
        workflow_status = "Dissertation Rejected"
        workflow_status_code = "REJECTED"
        workflow_message = "The final dissertation has been rejected by the Chair."

    # ---------------------------------------------------------
    # Previous submissions
    # ---------------------------------------------------------

    previous_submissions = (
        FinalDissertationSubmission.objects.filter(
            phd_student=phd_student,
        )
        .exclude(
            submission_id=submission.submission_id,
        )
        .order_by(
            "-submission_number",
            "-submitted_at",
            "-submission_id",
        )
    )

    # ---------------------------------------------------------
    # Previous committee evaluations
    # ---------------------------------------------------------

    previous_committee_evaluations = (
        FinalDissertationCommitteeEvaluation.objects.filter(
            submission__phd_student=phd_student,
            committee_member__committee=committee,
            is_submitted=True,
        )
        .exclude(
            submission=submission,
        )
        .select_related(
            "submission",
            "committee_member",
            "committee_member__faculty",
            "committee_member__faculty__user",
        )
        .order_by(
            "-submitted_at",
            "-evaluation_id",
        )
    )

    # ---------------------------------------------------------
    # Student information
    # ---------------------------------------------------------

    student_name = str(phd_student.student)

    student_id = getattr(
        phd_student.student,
        "student_number",
        None,
    )

    program_name = str(phd_student.phd_program) if phd_student.phd_program else "—"

    department_name = "—"

    if phd_student.phd_program:
        department = getattr(
            phd_student.phd_program,
            "department",
            None,
        )

        if department:
            department_name = str(department)

    advisor = phd_student.advisor

    advisor_name = str(advisor) if advisor else "—"

    chair_name = str(committee.chair_faculty) if committee.chair_faculty else "—"

    # ---------------------------------------------------------
    # Submission display values
    # ---------------------------------------------------------

    submission_status_display = submission.get_status_display()

    submission_date = getattr(
        submission,
        "submitted_at",
        None,
    )

    if submission_date:
        submission_date_display = submission_date.strftime("%b %d, %Y %I:%M %p")
    else:
        raw_submission_date = getattr(
            submission,
            "submission_date",
            None,
        )

        submission_date_display = (
            raw_submission_date.strftime("%b %d, %Y") if raw_submission_date else "—"
        )

    # ---------------------------------------------------------
    # Context
    # ---------------------------------------------------------

    context = {
        "uuid": uuid,
        "faculty": faculty,
        "submission": submission,
        "phd_student": phd_student,
        "student": phd_student.student,
        "student_name": student_name,
        "student_id": student_id,
        "program_name": program_name,
        "department_name": department_name,
        "advisor": advisor,
        "advisor_name": advisor_name,
        "committee": committee,
        "committee_members": committee_members,
        "chair_name": chair_name,
        "current_role": current_role,
        "current_role_display": current_role_display,
        "is_chair": is_chair,
        "is_committee_member": is_committee_member,
        "committee_member": committee_member,
        "advisor_evaluation": advisor_evaluation,
        "advisor_evaluation_submitted": advisor_evaluation_submitted,
        "advisor_approved": advisor_approved,
        "current_submission_number": current_submission_number,
        "required_members": required_members,
        "completed_members": completed_members,
        "pending_members": pending_members,
        "committee_evaluations": committee_evaluations,
        "evaluation_map": evaluation_map,
        "evaluations_required": evaluations_required,
        "evaluations_completed": evaluations_completed,
        "evaluations_pending": evaluations_pending,
        "evaluation_percentage": evaluation_percentage,
        "my_evaluation": my_evaluation,
        "my_evaluation_submitted": my_evaluation_submitted,
        "committee_evaluation_allowed": (committee_evaluation_allowed),
        "chair_member": chair_member,
        "chair_final_decision": chair_final_decision,
        "chair_final_decision_submitted": (chair_final_decision_submitted),
        "chair_finalize_allowed": (chair_finalize_allowed),
        "evaluation_ready_for_chair": (evaluation_ready_for_chair),
        "workflow_status": workflow_status,
        "workflow_status_code": workflow_status_code,
        "workflow_message": workflow_message,
        "submission_status_display": (submission_status_display),
        "submission_date_display": (submission_date_display),
        "previous_submissions": (previous_submissions),
        "previous_committee_evaluations": (previous_committee_evaluations),
        "video_evidence": video_evidence,
    }

    return render(
        request,
        "leo/FinalDissertation/committee_final_dissertation_detail.html",
        context,
    )


@login_required
@transaction.atomic
def faculty_committee_final_dissertation_evaluate(
    request,
    uuid,
    submission_id,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
            "faculty_rank",
            "department",
        ),
        user__uuid=uuid,
        user=request.user,
        employment_status="ACTIVE",
    )

    # =========================================================
    # GET SUBMISSION
    # =========================================================

    submission = get_object_or_404(
        FinalDissertationSubmission.objects.select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__phd_program",
            "phd_student__phd_program__department",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "phd_student__doctoral_committee",
            "phd_student__doctoral_committee__chair_faculty",
            "phd_student__doctoral_committee__chair_faculty__user",
        ).select_for_update(),
        submission_id=submission_id,
    )

    phd_student = submission.phd_student

    # =========================================================
    # GET COMMITTEE
    # =========================================================

    committee = getattr(
        phd_student,
        "doctoral_committee",
        None,
    )

    if not committee:
        messages.error(
            request,
            "No doctoral committee is associated with this dissertation.",
        )

        return redirect(
            "faculty_committee_final_dissertation_list",
            uuid=uuid,
        )

    # =========================================================
    # COMMITTEE MUST BE APPROVED
    # =========================================================

    if committee.approval_status != "APPROVED":
        messages.error(
            request,
            "The doctoral committee has not been approved.",
        )

        return redirect(
            "faculty_committee_final_dissertation_detail",
            uuid=uuid,
            submission_id=submission_id,
        )

    # =========================================================
    # IDENTIFY CURRENT FACULTY ROLE
    # =========================================================

    is_chair = committee.chair_faculty_id == faculty.pk

    committee_member = (
        CommitteeMember.objects.select_related(
            "faculty",
            "faculty__user",
            "faculty__faculty_rank",
            "faculty__department",
            "department",
        )
        .filter(
            committee=committee,
            faculty=faculty,
        )
        .first()
    )

    is_committee_member = committee_member is not None

    # =========================================================
    # ONLY COMMITTEE MEMBERS CAN EVALUATE
    # CHAIR DOES NOT USE THIS VIEW
    # =========================================================

    if not is_committee_member:
        messages.error(
            request,
            "Only assigned committee members can submit a committee evaluation.",
        )

        return redirect(
            "faculty_committee_final_dissertation_detail",
            uuid=uuid,
            submission_id=submission_id,
        )

    # =========================================================
    # CHAIR CANNOT SUBMIT THROUGH MEMBER EVALUATION
    # =========================================================

    if is_chair:
        messages.error(
            request,
            "The Chair must use the final review process.",
        )

        return redirect(
            "faculty_committee_final_dissertation_detail",
            uuid=uuid,
            submission_id=submission_id,
        )

    # =========================================================
    # ONLY THESE ROLES CAN EVALUATE
    #
    # CO_CHAIR
    # INTERNAL_MEMBER
    # EXTERNAL_MEMBER
    # =========================================================

    allowed_roles = [
        "CO_CHAIR",
        "INTERNAL_MEMBER",
        "EXTERNAL_MEMBER",
    ]

    if committee_member.role not in allowed_roles:
        messages.error(
            request,
            "You are not assigned as an eligible committee evaluator.",
        )

        return redirect(
            "faculty_committee_final_dissertation_detail",
            uuid=uuid,
            submission_id=submission_id,
        )

    # =========================================================
    # CURRENT SUBMISSION
    # =========================================================

    current_submission_number = submission.submission_number or 1

    # =========================================================
    # WORKFLOW VALIDATION
    #
    # Committee evaluation is allowed only after
    # Advisor APPROVE.
    # =========================================================

    if submission.status != "COMMITTEE_EVALUATION":
        messages.warning(
            request,
            "This dissertation is not currently awaiting committee evaluation.",
        )

        return redirect(
            "faculty_committee_final_dissertation_detail",
            uuid=uuid,
            submission_id=submission_id,
        )

    advisor_evaluation = (
        FinalDissertationAdvisorEvaluation.objects.filter(
            submission=submission,
            advisor=phd_student.advisor,
            submission_number=current_submission_number,
            is_submitted=True,
        )
        .order_by(
            "-submitted_at",
            "-evaluation_id",
        )
        .first()
    )

    if not advisor_evaluation:
        messages.error(
            request,
            "The Advisor evaluation has not been completed.",
        )

        return redirect(
            "faculty_committee_final_dissertation_detail",
            uuid=uuid,
            submission_id=submission_id,
        )

    if advisor_evaluation.recommendation != "APPROVE":
        messages.error(
            request,
            "Committee evaluation cannot begin until the Advisor approves the dissertation.",
        )

        return redirect(
            "faculty_committee_final_dissertation_detail",
            uuid=uuid,
            submission_id=submission_id,
        )

    # =========================================================
    # GET EXISTING EVALUATION
    # =========================================================

    evaluation = (
        FinalDissertationCommitteeEvaluation.objects.filter(
            submission=submission,
            submission_number=current_submission_number,
            committee_member=committee_member,
        )
        .order_by(
            "-submitted_at",
            "-evaluation_id",
        )
        .first()
    )

    # =========================================================
    # PREVENT DUPLICATE SUBMISSION
    # =========================================================

    if evaluation and evaluation.is_submitted:
        messages.warning(
            request,
            "You have already submitted your committee evaluation for this dissertation.",
        )

        return redirect(
            "faculty_committee_final_dissertation_detail",
            uuid=uuid,
            submission_id=submission_id,
        )

    # =========================================================
    # CREATE DRAFT EVALUATION IF REQUIRED
    # =========================================================

    if evaluation is None:
        evaluation = FinalDissertationCommitteeEvaluation(
            submission=submission,
            submission_number=current_submission_number,
            committee_member=committee_member,
            reviewer_role="COMMITTEE_MEMBER",
        )

    # =========================================================
    # POST
    # =========================================================

    if request.method == "POST":

        score = request.POST.get(
            "score",
            "",
        ).strip()

        recommendation = request.POST.get(
            "recommendation",
            "",
        ).strip()

        comments = request.POST.get(
            "comments",
            "",
        ).strip()

        # -----------------------------------------------------
        # VALIDATE RECOMMENDATION
        # -----------------------------------------------------

        allowed_recommendations = [
            "APPROVE",
            "REVISION_REQUIRED",
            "REJECT",
        ]

        if recommendation not in allowed_recommendations:
            messages.error(
                request,
                "Please select a valid recommendation.",
            )

            context = {
                "faculty": faculty,
                "submission": submission,
                "phd_student": phd_student,
                "committee": committee,
                "committee_member": committee_member,
                "evaluation": evaluation,
                "advisor_evaluation": advisor_evaluation,
                "current_submission_number": (current_submission_number),
            }

            return render(
                request,
                "leo/FinalDissertation/committee_final_dissertation_evaluate.html",
                context,
            )

        # -----------------------------------------------------
        # VALIDATE SCORE
        # -----------------------------------------------------

        if score == "":
            messages.error(
                request,
                "Please provide a score.",
            )

            context = {
                "faculty": faculty,
                "submission": submission,
                "phd_student": phd_student,
                "committee": committee,
                "committee_member": committee_member,
                "evaluation": evaluation,
                "advisor_evaluation": advisor_evaluation,
                "current_submission_number": (current_submission_number),
            }

            return render(
                request,
                "leo/FinalDissertation/committee_final_dissertation_evaluate.html",
                context,
            )

        # =====================================================
        # SAVE COMMITTEE EVALUATION
        # =====================================================

        evaluation.score = score
        evaluation.recommendation = recommendation
        evaluation.comments = comments
        evaluation.reviewer_role = "COMMITTEE_MEMBER"
        evaluation.is_submitted = True
        evaluation.submitted_at = timezone.now()

        evaluation.save()

        # =====================================================
        # IMPORTANT WORKFLOW RULE
        #
        # COMMITTEE REJECTION DOES NOT REJECT SUBMISSION.
        #
        # Even if:
        #
        #   Co-Chair      -> APPROVE
        #   Internal      -> REJECT
        #   External      -> APPROVE
        #
        # the dissertation goes to CHAIR_REVIEW after
        # all required committee evaluations are complete.
        # =====================================================

        required_members = CommitteeMember.objects.filter(
            committee=committee,
            role__in=[
                "CO_CHAIR",
                "INTERNAL_MEMBER",
                "EXTERNAL_MEMBER",
            ],
        )

        required_member_ids = list(
            required_members.values_list(
                "member_id",
                flat=True,
            )
        )

        required_count = len(required_member_ids)

        # =====================================================
        # COUNT COMPLETED CURRENT-SUBMISSION EVALUATIONS
        # =====================================================

        submitted_member_ids = set(
            FinalDissertationCommitteeEvaluation.objects.filter(
                submission=submission,
                submission_number=current_submission_number,
                committee_member_id__in=required_member_ids,
                is_submitted=True,
            ).values_list(
                "committee_member_id",
                flat=True,
            )
        )

        completed_count = len(submitted_member_ids)

        pending_count = max(
            required_count - completed_count,
            0,
        )

        # =====================================================
        # ALL COMMITTEE EVALUATIONS COMPLETE
        # =====================================================

        if required_count > 0 and completed_count >= required_count:

            # -------------------------------------------------
            # DO NOT CHECK WHETHER ANY MEMBER REJECTED.
            #
            # Chair is the final decision maker.
            # -------------------------------------------------

            submission.status = "CHAIR_REVIEW"

            submission.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            messages.success(
                request,
                "Committee evaluation submitted successfully. All committee evaluations are complete and the dissertation has been moved to Chair final review.",
            )

        else:

            # -------------------------------------------------
            # STILL WAITING FOR OTHER MEMBERS
            # -------------------------------------------------

            submission.status = "COMMITTEE_EVALUATION"

            submission.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            messages.success(
                request,
                f"Committee evaluation submitted successfully. {pending_count} committee evaluation"
                f"{'s' if pending_count != 1 else ''} still pending.",
            )

        # =====================================================
        # ALWAYS RETURN TO DETAIL
        # =====================================================

        return redirect(
            "faculty_committee_final_dissertation_detail",
            uuid=uuid,
            submission_id=submission_id,
        )

    # =========================================================
    # GET REQUEST
    # =========================================================

    context = {
        "faculty": faculty,
        "submission": submission,
        "phd_student": phd_student,
        "committee": committee,
        "committee_member": committee_member,
        "advisor_evaluation": advisor_evaluation,
        "evaluation": evaluation,
        "current_submission_number": (current_submission_number),
        "is_chair": is_chair,
        "is_committee_member": is_committee_member,
        "allowed_roles": allowed_roles,
    }

    return render(
        request,
        "leo/FinalDissertation/committee_final_dissertation_evaluate.html",
        context,
    )


@login_required
def faculty_committee_final_dissertation_evaluation_detail(
    request,
    uuid,
    submission_id,
    evaluation_id,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
            "faculty_rank",
            "department",
        ),
        user__uuid=uuid,
        user=request.user,
        employment_status="ACTIVE",
    )

    evaluation = get_object_or_404(
        FinalDissertationCommitteeEvaluation.objects.select_related(
            "submission",
            "submission__phd_student",
            "submission__phd_student__student",
            "submission__phd_student__student__user",
            "submission__phd_student__phd_program",
            "submission__phd_student__phd_program__department",
            "submission__phd_student__advisor",
            "submission__phd_student__advisor__user",
            "committee_member",
            "committee_member__faculty",
            "committee_member__faculty__user",
            "committee_member__faculty__faculty_rank",
            "committee_member__faculty__department",
            "committee_member__department",
        ),
        evaluation_id=evaluation_id,
        submission_id=submission_id,
        is_submitted=True,
    )

    submission = evaluation.submission
    phd_student = submission.phd_student

    committee = get_object_or_404(
        DoctoralCommittee.objects.select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__phd_program",
            "phd_student__phd_program__department",
            "chair_faculty",
            "chair_faculty__user",
        ),
        phd_student=phd_student,
        approval_status="APPROVED",
    )

    is_chair = committee.chair_faculty_id == faculty.pk

    committee_member = (
        CommitteeMember.objects.select_related(
            "faculty",
            "faculty__user",
            "faculty__faculty_rank",
            "faculty__department",
            "department",
        )
        .filter(
            committee=committee,
            faculty=faculty,
        )
        .first()
    )

    is_committee_member = committee_member is not None

    if not is_chair and not is_committee_member:
        messages.error(
            request,
            "You are not authorized to view this committee evaluation.",
        )

        return redirect(
            "faculty_committee_final_dissertation_list",
            uuid=uuid,
        )

    current_submission_number = submission.submission_number or 1

    advisor_evaluation = (
        FinalDissertationAdvisorEvaluation.objects.filter(
            submission=submission,
            advisor=phd_student.advisor,
            submission_number=current_submission_number,
            is_submitted=True,
        )
        .order_by(
            "-submitted_at",
            "-evaluation_id",
        )
        .first()
    )

    committee_evaluations = (
        FinalDissertationCommitteeEvaluation.objects.filter(
            submission=submission,
            submission_number=current_submission_number,
            committee_member__committee=committee,
            is_submitted=True,
        )
        .select_related(
            "committee_member",
            "committee_member__faculty",
            "committee_member__faculty__user",
            "committee_member__faculty__faculty_rank",
            "committee_member__faculty__department",
            "committee_member__department",
        )
        .order_by(
            "committee_member__role",
            "committee_member__faculty__user__first_name",
            "committee_member__faculty__user__last_name",
        )
    )

    required_committee_members = (
        CommitteeMember.objects.filter(
            committee=committee,
            role__in=[
                "CO_CHAIR",
                "INTERNAL_MEMBER",
                "EXTERNAL_MEMBER",
            ],
        )
        .select_related(
            "faculty",
            "faculty__user",
            "faculty__faculty_rank",
            "faculty__department",
            "department",
        )
        .order_by(
            "role",
            "faculty__user__first_name",
            "faculty__user__last_name",
        )
    )

    evaluations_required = required_committee_members.count()

    evaluations_completed = committee_evaluations.count()

    evaluations_pending = max(
        evaluations_required - evaluations_completed,
        0,
    )

    evaluation_percentage = (
        round((evaluations_completed / evaluations_required) * 100)
        if evaluations_required
        else 0
    )

    evaluation_ready_for_chair = (
        evaluations_required > 0 and evaluations_completed >= evaluations_required
    )

    current_evaluation = (
        FinalDissertationCommitteeEvaluation.objects.filter(
            evaluation_id=evaluation.evaluation_id,
        )
        .select_related(
            "committee_member",
            "committee_member__faculty",
            "committee_member__faculty__user",
            "committee_member__department",
        )
        .first()
    )

    evaluator_name = str(current_evaluation.committee_member.faculty)

    evaluator_role = current_evaluation.committee_member.role

    evaluator_role_display = (
        current_evaluation.committee_member.get_role_display()
        if hasattr(
            current_evaluation.committee_member,
            "get_role_display",
        )
        else evaluator_role.replace(
            "_",
            " ",
        ).title()
    )

    recommendation = (
        current_evaluation.recommendation if current_evaluation.recommendation else None
    )

    recommendation_display = (
        current_evaluation.get_recommendation_display()
        if hasattr(
            current_evaluation,
            "get_recommendation_display",
        )
        else (
            recommendation.replace(
                "_",
                " ",
            ).title()
            if recommendation
            else "—"
        )
    )

    score = current_evaluation.score if current_evaluation.score is not None else None

    submitted_at = current_evaluation.submitted_at

    if submission.status == "SUBMITTED":
        workflow_status = "Waiting for Advisor"
        workflow_status_code = "WAITING_ADVISOR"
        workflow_message = (
            "The final dissertation is waiting for the Advisor evaluation."
        )

    elif submission.status == "ADVISOR_REVIEW":
        workflow_status = "Waiting for Advisor"
        workflow_status_code = "WAITING_ADVISOR"
        workflow_message = (
            "The final dissertation is waiting for the Advisor evaluation."
        )

    elif submission.status == "COMMITTEE_EVALUATION":
        if evaluation_ready_for_chair:
            workflow_status = "Waiting for Chair to Finalize"
            workflow_status_code = "WAITING_CHAIR"
            workflow_message = "All required committee evaluations have been submitted."
        else:
            workflow_status = "Committee Evaluation in Progress"
            workflow_status_code = "COMMITTEE_IN_PROGRESS"
            workflow_message = (
                f"{evaluations_completed} of "
                f"{evaluations_required} "
                "required committee evaluations are complete."
            )

    elif submission.status == "CHAIR_REVIEW":
        workflow_status = "Waiting for Chair to Finalize"
        workflow_status_code = "WAITING_CHAIR"
        workflow_message = "All committee evaluations are complete and the dissertation is waiting for the Chair's final decision."

    elif submission.status == "APPROVED":
        workflow_status = "Dissertation Approved"
        workflow_status_code = "APPROVED"
        workflow_message = "The final dissertation has been approved by the Chair."

    elif submission.status == "REVISION_REQUIRED":
        workflow_status = "Revision Required"
        workflow_status_code = "REVISION_REQUIRED"
        workflow_message = "The Chair has requested a new dissertation submission."

    elif submission.status == "REJECTED":
        workflow_status = "Dissertation Rejected"
        workflow_status_code = "REJECTED"
        workflow_message = "The final dissertation has been rejected by the Chair."

    else:
        workflow_status = submission.get_status_display()
        workflow_status_code = submission.status
        workflow_message = ""

    student_name = str(phd_student.student)

    student_number = getattr(
        phd_student.student,
        "student_number",
        None,
    )

    program_name = str(phd_student.phd_program) if phd_student.phd_program else "—"

    department_name = "—"

    if phd_student.phd_program:
        department = getattr(
            phd_student.phd_program,
            "department",
            None,
        )

        if department:
            department_name = str(department)

    advisor_name = str(phd_student.advisor) if phd_student.advisor else "—"

    chair_name = str(committee.chair_faculty) if committee.chair_faculty else "—"

    context = {
        "uuid": uuid,
        "faculty": faculty,
        "submission": submission,
        "phd_student": phd_student,
        "student_name": student_name,
        "student_number": student_number,
        "program_name": program_name,
        "department_name": department_name,
        "advisor_name": advisor_name,
        "committee": committee,
        "committee_member": committee_member,
        "chair_name": chair_name,
        "evaluation": current_evaluation,
        "evaluator_name": evaluator_name,
        "evaluator_role": evaluator_role,
        "evaluator_role_display": evaluator_role_display,
        "recommendation": recommendation,
        "recommendation_display": recommendation_display,
        "score": score,
        "submitted_at": submitted_at,
        "advisor_evaluation": advisor_evaluation,
        "committee_evaluations": committee_evaluations,
        "required_committee_members": required_committee_members,
        "evaluations_required": evaluations_required,
        "evaluations_completed": evaluations_completed,
        "evaluations_pending": evaluations_pending,
        "evaluation_percentage": evaluation_percentage,
        "evaluation_ready_for_chair": (evaluation_ready_for_chair),
        "current_submission_number": (current_submission_number),
        "workflow_status": workflow_status,
        "workflow_status_code": workflow_status_code,
        "workflow_message": workflow_message,
        "is_chair": is_chair,
        "is_committee_member": is_committee_member,
        "is_view_mode": True,
    }

    return render(
        request,
        "leo/FinalDissertation/committee_final_dissertation_evaluation_detail.html",
        context,
    )


@login_required
@transaction.atomic
def faculty_chair_final_dissertation_review(
    request,
    uuid,
    submission_id,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
            "faculty_rank",
            "department",
        ),
        user__uuid=uuid,
        user=request.user,
        employment_status="ACTIVE",
    )

    submission = get_object_or_404(
        FinalDissertationSubmission.objects.select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__phd_program",
            "phd_student__phd_program__department",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "phd_student__doctoral_committee",
            "phd_student__doctoral_committee__chair_faculty",
            "phd_student__doctoral_committee__chair_faculty__user",
        ).select_for_update(),
        submission_id=submission_id,
    )

    phd_student = submission.phd_student

    committee = getattr(
        phd_student,
        "doctoral_committee",
        None,
    )

    if not committee:
        messages.error(
            request,
            "No doctoral committee is associated with this dissertation.",
        )

        return redirect(
            "faculty_committee_final_dissertation_list",
            uuid=uuid,
        )

    if committee.approval_status != "APPROVED":
        messages.error(
            request,
            "The doctoral committee has not been approved.",
        )

        return redirect(
            "faculty_committee_final_dissertation_list",
            uuid=uuid,
        )

    if committee.chair_faculty_id != faculty.pk:
        messages.error(
            request,
            "Only the Chair Faculty can access the final review.",
        )

        return redirect(
            "faculty_committee_final_dissertation_detail",
            uuid=uuid,
            submission_id=submission_id,
        )

    current_submission_number = submission.submission_number or 1

    advisor_evaluation = (
        FinalDissertationAdvisorEvaluation.objects.filter(
            submission=submission,
            advisor=phd_student.advisor,
            submission_number=current_submission_number,
            is_submitted=True,
        )
        .select_related(
            "advisor",
            "advisor__user",
        )
        .order_by(
            "-submitted_at",
            "-evaluation_id",
        )
        .first()
    )

    if not advisor_evaluation:
        messages.warning(
            request,
            "Chair finalization is not available because the Advisor evaluation has not been completed.",
        )

        return redirect(
            "faculty_committee_final_dissertation_detail",
            uuid=uuid,
            submission_id=submission_id,
        )

    advisor_approved = advisor_evaluation.recommendation == "APPROVE"

    if not advisor_approved:
        messages.warning(
            request,
            "Chair finalization is not available because the Advisor has not approved the dissertation.",
        )

        return redirect(
            "faculty_committee_final_dissertation_detail",
            uuid=uuid,
            submission_id=submission_id,
        )

    chair_member = (
        CommitteeMember.objects.filter(
            committee=committee,
            faculty=faculty,
            role="CHAIR",
        )
        .select_related(
            "faculty",
            "faculty__user",
            "faculty__faculty_rank",
            "faculty__department",
            "department",
        )
        .first()
    )

    if not chair_member:
        chair_department = faculty.department or getattr(
            phd_student.phd_program,
            "department",
            None,
        )

        if not chair_department:
            messages.error(
                request,
                "The Chair Faculty does not have a department assigned.",
            )

            return redirect(
                "faculty_committee_final_dissertation_detail",
                uuid=uuid,
                submission_id=submission_id,
            )

        chair_member = CommitteeMember.objects.create(
            committee=committee,
            faculty=faculty,
            role="CHAIR",
            department=chair_department,
            is_full_crud=False,
        )

    committee_members = list(
        CommitteeMember.objects.filter(
            committee=committee,
        )
        .exclude(
            role="CHAIR",
        )
        .select_related(
            "faculty",
            "faculty__user",
            "faculty__faculty_rank",
            "faculty__department",
            "department",
        )
        .order_by(
            "role",
            "faculty__user__first_name",
            "faculty__user__last_name",
        )
    )

    required_roles = [
        "CO_CHAIR",
        "INTERNAL_MEMBER",
        "EXTERNAL_MEMBER",
    ]

    required_members = [
        member for member in committee_members if member.role in required_roles
    ]

    required_member_ids = [member.member_id for member in required_members]

    committee_evaluations = list(
        FinalDissertationCommitteeEvaluation.objects.filter(
            submission=submission,
            submission_number=current_submission_number,
            committee_member__committee=committee,
            reviewer_role="COMMITTEE_MEMBER",
            is_submitted=True,
        )
        .select_related(
            "committee_member",
            "committee_member__faculty",
            "committee_member__faculty__user",
            "committee_member__faculty__faculty_rank",
            "committee_member__faculty__department",
            "committee_member__department",
        )
        .order_by(
            "-submitted_at",
            "-evaluation_id",
        )
    )

    evaluation_map = {}

    for evaluation in committee_evaluations:
        member_id = evaluation.committee_member_id

        if member_id not in evaluation_map:
            evaluation_map[member_id] = evaluation

    completed_members = []
    pending_members = []

    for member in required_members:
        evaluation = evaluation_map.get(member.member_id)

        member.evaluation = evaluation

        member.evaluation_submitted = bool(evaluation and evaluation.is_submitted)

        if member.evaluation_submitted:
            completed_members.append(member)
        else:
            pending_members.append(member)

    evaluations_required = len(required_members)

    evaluations_completed = len(completed_members)

    evaluations_pending = len(pending_members)

    evaluation_percentage = (
        round((evaluations_completed / evaluations_required) * 100)
        if evaluations_required
        else 0
    )

    evaluation_ready_for_chair = (
        evaluations_required > 0 and evaluations_completed == evaluations_required
    )

    existing_chair_evaluation = (
        FinalDissertationCommitteeEvaluation.objects.filter(
            submission=submission,
            submission_number=current_submission_number,
            committee_member=chair_member,
            reviewer_role="CHAIR",
            is_final_decision=True,
        )
        .select_related(
            "committee_member",
            "committee_member__faculty",
            "committee_member__faculty__user",
        )
        .order_by(
            "-submitted_at",
            "-evaluation_id",
        )
        .first()
    )

    if existing_chair_evaluation and existing_chair_evaluation.is_submitted:
        messages.info(
            request,
            "This dissertation has already been finalized by the Chair.",
        )

        return redirect(
            "faculty_chair_final_dissertation_final_detail",
            uuid=uuid,
            submission_id=submission_id,
        )

    if submission.status not in [
        "COMMITTEE_EVALUATION",
        "CHAIR_REVIEW",
    ]:
        messages.warning(
            request,
            "This dissertation is not currently available for Chair final review.",
        )

        return redirect(
            "faculty_committee_final_dissertation_detail",
            uuid=uuid,
            submission_id=submission_id,
        )

    if not evaluation_ready_for_chair:
        messages.warning(
            request,
            (
                "Chair finalization is not available yet. "
                f"{evaluations_completed} of "
                f"{evaluations_required} "
                "required committee evaluations are complete."
            ),
        )

        return redirect(
            "faculty_committee_final_dissertation_detail",
            uuid=uuid,
            submission_id=submission_id,
        )

    if submission.status == "COMMITTEE_EVALUATION":
        submission.status = "CHAIR_REVIEW"
        submission.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

    if existing_chair_evaluation:
        chair_evaluation = existing_chair_evaluation
    else:
        chair_evaluation = FinalDissertationCommitteeEvaluation(
            submission=submission,
            committee_member=chair_member,
            reviewer_role="CHAIR",
            submission_number=current_submission_number,
            resubmission_count=(submission.resubmission_count or 0),
            is_final_decision=True,
            is_submitted=False,
        )

    form = FinalDissertationChairFinalizationForm(
        request.POST or None,
        instance=chair_evaluation,
        faculty=faculty,
        submission=submission,
    )

    if request.method == "POST":
        if form.is_valid():
            final_evaluation = form.save(
                commit=True,
            )

            if final_evaluation.recommendation == "APPROVE":
                messages.success(
                    request,
                    "Final dissertation has been approved successfully by the Chair.",
                )

            elif final_evaluation.recommendation == "REVISION_REQUIRED":
                messages.warning(
                    request,
                    "Revision has been requested for the final dissertation.",
                )

            elif final_evaluation.recommendation == "REJECT":
                messages.error(
                    request,
                    "Final dissertation has been rejected by the Chair.",
                )

            return redirect(
                "faculty_chair_final_dissertation_final_detail",
                uuid=uuid,
                submission_id=submission_id,
            )

    context = {
        "faculty": faculty,
        "submission": submission,
        "phd_student": phd_student,
        "committee": committee,
        "chair_member": chair_member,
        "committee_members": committee_members,
        "required_members": required_members,
        "advisor_evaluation": advisor_evaluation,
        "committee_evaluations": committee_evaluations,
        "evaluation_map": evaluation_map,
        "evaluations_required": evaluations_required,
        "evaluations_completed": evaluations_completed,
        "evaluations_pending": evaluations_pending,
        "evaluation_percentage": evaluation_percentage,
        "evaluation_ready_for_chair": evaluation_ready_for_chair,
        "chair_evaluation": chair_evaluation,
        "existing_chair_evaluation": existing_chair_evaluation,
        "current_submission_number": current_submission_number,
        "form": form,
        "is_chair": True,
        "can_finalize": True,
        "workflow_status": "Ready for Chair Final Review",
        "workflow_status_code": "READY_FOR_CHAIR",
        "workflow_message": (
            "All required committee evaluations have been completed. "
            "You can now make the final decision."
        ),
    }

    return render(
        request,
        "leo/FinalDissertation/chair_final_dissertation_review.html",
        context,
    )


@login_required
def faculty_chair_final_dissertation_final_detail(
    request,
    uuid,
    submission_id,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
            "faculty_rank",
            "department",
        ),
        user__uuid=uuid,
        user=request.user,
        employment_status="ACTIVE",
    )

    submission = get_object_or_404(
        FinalDissertationSubmission.objects.select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__phd_program",
            "phd_student__phd_program__department",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "phd_student__doctoral_committee",
            "phd_student__doctoral_committee__chair_faculty",
            "phd_student__doctoral_committee__chair_faculty__user",
        ),
        submission_id=submission_id,
    )

    phd_student = submission.phd_student

    committee = getattr(
        phd_student,
        "doctoral_committee",
        None,
    )

    if not committee:
        messages.error(
            request,
            "No doctoral committee is associated with this dissertation.",
        )

        return redirect(
            "faculty_committee_final_dissertation_list",
            uuid=uuid,
        )

    if committee.approval_status != "APPROVED":
        messages.error(
            request,
            "The doctoral committee has not been approved.",
        )

        return redirect(
            "faculty_committee_final_dissertation_detail",
            uuid=uuid,
            submission_id=submission_id,
        )

    if committee.chair_faculty_id != faculty.pk:
        messages.error(
            request,
            "Only the Chair Faculty can access the final decision.",
        )

        return redirect(
            "faculty_committee_final_dissertation_detail",
            uuid=uuid,
            submission_id=submission_id,
        )

    current_submission_number = submission.submission_number or 1

    chair_member = (
        CommitteeMember.objects.filter(
            committee=committee,
            faculty=faculty,
            role="CHAIR",
        )
        .select_related(
            "faculty",
            "faculty__user",
            "faculty__faculty_rank",
            "faculty__department",
            "department",
        )
        .first()
    )

    if not chair_member:
        messages.error(
            request,
            "You are not configured as the Chair of this doctoral committee.",
        )

        return redirect(
            "faculty_committee_final_dissertation_list",
            uuid=uuid,
        )

    chair_final_evaluation = (
        FinalDissertationCommitteeEvaluation.objects.filter(
            submission=submission,
            submission_number=current_submission_number,
            reviewer_role="CHAIR",
            is_final_decision=True,
            is_submitted=True,
        )
        .select_related(
            "committee_member",
            "committee_member__faculty",
            "committee_member__faculty__user",
        )
        .order_by(
            "-submitted_at",
            "-evaluation_id",
        )
        .first()
    )

    if not chair_final_evaluation:
        messages.warning(
            request,
            "The Chair has not finalized this dissertation yet.",
        )

        return redirect(
            "faculty_chair_final_dissertation_review",
            uuid=uuid,
            submission_id=submission_id,
        )

    advisor_evaluation = (
        FinalDissertationAdvisorEvaluation.objects.filter(
            submission=submission,
            advisor=phd_student.advisor,
            submission_number=current_submission_number,
            is_submitted=True,
        )
        .select_related(
            "advisor",
            "advisor__user",
        )
        .order_by(
            "-submitted_at",
            "-evaluation_id",
        )
        .first()
    )

    committee_members = list(
        CommitteeMember.objects.filter(
            committee=committee,
        )
        .select_related(
            "faculty",
            "faculty__user",
            "faculty__faculty_rank",
            "faculty__department",
            "department",
        )
        .order_by(
            "role",
            "faculty__user__first_name",
            "faculty__user__last_name",
        )
    )

    committee_evaluations = list(
        FinalDissertationCommitteeEvaluation.objects.filter(
            submission=submission,
            submission_number=current_submission_number,
            committee_member__committee=committee,
            reviewer_role="COMMITTEE_MEMBER",
            is_submitted=True,
        )
        .select_related(
            "committee_member",
            "committee_member__faculty",
            "committee_member__faculty__user",
            "committee_member__faculty__faculty_rank",
            "committee_member__faculty__department",
            "committee_member__department",
        )
        .order_by(
            "committee_member__role",
            "committee_member__faculty__user__first_name",
            "committee_member__faculty__user__last_name",
        )
    )

    evaluation_map = {}

    for evaluation in committee_evaluations:
        member_id = evaluation.committee_member_id

        if member_id not in evaluation_map:
            evaluation_map[member_id] = evaluation

    required_committee_members = [
        member
        for member in committee_members
        if member.role
        in [
            "CO_CHAIR",
            "INTERNAL_MEMBER",
            "EXTERNAL_MEMBER",
        ]
    ]

    completed_members = []
    pending_members = []

    for member in required_committee_members:
        member.evaluation = evaluation_map.get(member.member_id)

        member.evaluation_submitted = bool(
            member.evaluation and member.evaluation.is_submitted
        )

        if member.evaluation_submitted:
            completed_members.append(member)
        else:
            pending_members.append(member)

    evaluations_required = len(required_committee_members)

    evaluations_completed = len(completed_members)

    evaluations_pending = len(pending_members)

    evaluation_percentage = (
        round((evaluations_completed / evaluations_required) * 100)
        if evaluations_required
        else 0
    )

    all_committee_evaluations_completed = (
        evaluations_required > 0 and evaluations_completed >= evaluations_required
    )

    final_recommendation = chair_final_evaluation.recommendation

    if final_recommendation == "APPROVE":
        final_decision = "APPROVED"
        final_decision_display = "Approved"
        final_decision_code = "APPROVED"

    elif final_recommendation == "REVISION_REQUIRED":
        final_decision = "REVISION_REQUIRED"
        final_decision_display = "Revision Required"
        final_decision_code = "REVISION_REQUIRED"

    elif final_recommendation in [
        "REJECT",
        "REJECTED",
    ]:
        final_decision = "REJECTED"
        final_decision_display = "Rejected"
        final_decision_code = "REJECTED"

    else:
        final_decision = submission.status
        final_decision_display = submission.get_status_display()
        final_decision_code = submission.status

    if submission.status == "APPROVED":
        workflow_status = "Dissertation Approved"
        workflow_status_code = "APPROVED"
        workflow_message = "The final dissertation has been approved by the Chair."

    elif submission.status == "REVISION_REQUIRED":
        workflow_status = "Revision Required"
        workflow_status_code = "REVISION_REQUIRED"
        workflow_message = "The Chair has requested a new dissertation submission."

    elif submission.status == "REJECTED":
        workflow_status = "Dissertation Rejected"
        workflow_status_code = "REJECTED"
        workflow_message = "The final dissertation has been rejected by the Chair."

    else:
        workflow_status = submission.get_status_display()
        workflow_status_code = submission.status
        workflow_message = "The Chair final decision has been recorded."

    student_name = str(phd_student.student)

    student_number = getattr(
        phd_student.student,
        "student_number",
        None,
    )

    program_name = str(phd_student.phd_program) if phd_student.phd_program else "—"

    department_name = "—"

    if phd_student.phd_program:
        department = getattr(
            phd_student.phd_program,
            "department",
            None,
        )

        if department:
            department_name = str(department)

    advisor_name = str(phd_student.advisor) if phd_student.advisor else "—"

    chair_name = str(committee.chair_faculty) if committee.chair_faculty else "—"

    submission_date = getattr(
        submission,
        "submitted_at",
        None,
    )

    if submission_date:
        submission_date_display = submission_date.strftime("%b %d, %Y %I:%M %p")
    else:
        raw_submission_date = getattr(
            submission,
            "submission_date",
            None,
        )

        submission_date_display = (
            raw_submission_date.strftime("%b %d, %Y") if raw_submission_date else "—"
        )

    finalization_date = chair_final_evaluation.submitted_at

    if finalization_date:
        finalization_date_display = finalization_date.strftime("%b %d, %Y %I:%M %p")
    else:
        finalization_date_display = "—"

    final_score = (
        chair_final_evaluation.score
        if chair_final_evaluation.score is not None
        else None
    )

    previous_submissions = (
        FinalDissertationSubmission.objects.filter(
            phd_student=phd_student,
        )
        .exclude(
            submission_id=submission.submission_id,
        )
        .order_by(
            "-submission_number",
            "-submitted_at",
            "-submission_id",
        )
    )

    previous_committee_evaluations = (
        FinalDissertationCommitteeEvaluation.objects.filter(
            submission__phd_student=phd_student,
            committee_member__committee=committee,
            is_submitted=True,
        )
        .exclude(
            submission=submission,
        )
        .select_related(
            "submission",
            "committee_member",
            "committee_member__faculty",
            "committee_member__faculty__user",
        )
        .order_by(
            "-submitted_at",
            "-evaluation_id",
        )
    )

    context = {
        "uuid": uuid,
        "faculty": faculty,
        "submission": submission,
        "phd_student": phd_student,
        "student_name": student_name,
        "student_number": student_number,
        "program_name": program_name,
        "department_name": department_name,
        "advisor_name": advisor_name,
        "advisor_evaluation": advisor_evaluation,
        "committee": committee,
        "committee_members": committee_members,
        "required_committee_members": (required_committee_members),
        "chair_member": chair_member,
        "chair_name": chair_name,
        "committee_evaluations": committee_evaluations,
        "evaluation_map": evaluation_map,
        "completed_members": completed_members,
        "pending_members": pending_members,
        "evaluations_required": evaluations_required,
        "evaluations_completed": evaluations_completed,
        "evaluations_pending": evaluations_pending,
        "evaluation_percentage": evaluation_percentage,
        "all_committee_evaluations_completed": (all_committee_evaluations_completed),
        "chair_final_evaluation": (chair_final_evaluation),
        "chair_evaluation": chair_final_evaluation,
        "final_recommendation": final_recommendation,
        "final_decision": final_decision,
        "final_decision_display": (final_decision_display),
        "final_decision_code": final_decision_code,
        "final_score": final_score,
        "finalization_date": finalization_date,
        "finalization_date_display": (finalization_date_display),
        "current_submission_number": (current_submission_number),
        "submission_date_display": (submission_date_display),
        "workflow_status": workflow_status,
        "workflow_status_code": workflow_status_code,
        "workflow_message": workflow_message,
        "previous_submissions": (previous_submissions),
        "previous_committee_evaluations": (previous_committee_evaluations),
        "is_chair": True,
        "is_finalized": True,
        "can_finalize": False,
    }

    return render(
        request,
        "leo/FinalDissertation/chair_final_dissertation_final_detail.html",
        context,
    )


# ========================================================
# Final Dissertation Defense MODULE
# ========================================================


@login_required
def faculty_dissertation_defense_list(
    request,
    uuid,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
            "faculty_rank",
            "department",
        ),
        user__uuid=uuid,
        user=request.user,
        employment_status="ACTIVE",
    )

    phd_students = (
        PhDStudent.objects.select_related(
            "student",
            "student__user",
            "phd_program",
            "phd_program__department",
            "advisor",
            "advisor__user",
            "doctoral_committee",
            "doctoral_committee__chair_faculty",
            "doctoral_committee__chair_faculty__user",
        )
        .filter(
            final_dissertation_submissions__status="APPROVED",
            doctoral_committee__approval_status="APPROVED",
            current_status="ACTIVE",
        )
        .distinct()
        .order_by(
            "student__user__first_name",
            "student__user__last_name",
        )
    )

    defense_records = []
    today = timezone.localdate()

    for phd_student in phd_students:
        defense = (
            DissertationDefense.objects.select_related(
                "phd_student",
            )
            .filter(phd_student=phd_student)
            .first()
        )

        committee = getattr(
            phd_student,
            "doctoral_committee",
            None,
        )

        committee_member = None

        if committee:
            committee_member = (
                CommitteeMember.objects.filter(
                    committee=committee,
                    faculty=faculty,
                )
                .select_related(
                    "committee",
                    "faculty",
                    "faculty__user",
                    "department",
                )
                .first()
            )

        is_chair = bool(committee and committee.chair_faculty_id == faculty.pk)

        is_committee_member = committee_member is not None

        if is_chair:
            defense_role = "CHAIR"
        elif is_committee_member:
            defense_role = "COMMITTEE_MEMBER"
        else:
            defense_role = None

        total_evaluations = 0
        submitted_evaluations = 0
        pending_evaluations = 0
        own_evaluation = None
        all_evaluations_submitted = False
        evaluation_available = False
        finalization_available = False

        if defense:
            required_members = CommitteeMember.objects.filter(
                committee=committee,
                role__in=[
                    "CO_CHAIR",
                    "INTERNAL_MEMBER",
                    "EXTERNAL_MEMBER",
                ],
            )

            required_member_ids = list(
                required_members.values_list(
                    "pk",
                    flat=True,
                )
            )

            total_evaluations = len(
                required_member_ids,
            )

            submitted_evaluations = (
                DissertationDefenseEvaluation.objects.filter(
                    defense=defense,
                    committee_member_id__in=required_member_ids,
                    is_submitted=True,
                )
                .values(
                    "committee_member_id",
                )
                .distinct()
                .count()
            )

            pending_evaluations = max(
                total_evaluations - submitted_evaluations,
                0,
            )

            if committee_member:
                own_evaluation = (
                    DissertationDefenseEvaluation.objects.filter(
                        defense=defense,
                        committee_member=committee_member,
                    )
                    .order_by(
                        "-submitted_at",
                        "-evaluation_id",
                    )
                    .first()
                )

            all_evaluations_submitted = (
                total_evaluations > 0 and submitted_evaluations == total_evaluations
            )

            if defense.result in {
                "PASS",
                "FAIL",
            }:
                defense_status = "COMPLETED"
                status_label = "Completed"
            elif defense.defense_date and defense.defense_date <= today:
                defense_status = "EVALUATION_PENDING"
                status_label = "Evaluation Pending"
            else:
                defense_status = "SCHEDULED"
                status_label = "Scheduled"

            if (
                is_committee_member
                and defense.result == "PENDING"
                and defense.defense_date
                and defense.defense_date <= today
                and own_evaluation is None
            ):
                evaluation_available = True

            if (
                is_chair
                and defense.result == "PENDING"
                and defense.defense_date
                and defense.defense_date <= today
                and all_evaluations_submitted
            ):
                finalization_available = True

            if is_chair:
                if finalization_available:
                    action_type = "FINALIZE"
                    action_label = "Finalize Defense"
                else:
                    action_type = "VIEW"
                    action_label = "View Defense"
            elif is_committee_member:
                if evaluation_available:
                    action_type = "EVALUATE"
                    action_label = "Evaluate Defense"
                elif own_evaluation and own_evaluation.is_submitted:
                    action_type = "VIEW_EVALUATION"
                    action_label = "View Evaluation"
                else:
                    action_type = "VIEW"
                    action_label = "View Defense"
            else:
                action_type = None
                action_label = None

            if defense.result in {
                "PASS",
                "FAIL",
            }:
                if is_chair:
                    action_type = "FINAL_DETAIL"
                    action_label = "View Final Decision"
                elif is_committee_member:
                    if own_evaluation and own_evaluation.is_submitted:
                        action_type = "VIEW_EVALUATION"
                        action_label = "View Evaluation"
                    else:
                        action_type = "VIEW"
                        action_label = "View Defense"

        else:
            defense_status = "NOT_SCHEDULED"
            status_label = "Not Scheduled"

            if is_chair:
                action_type = "SCHEDULE"
                action_label = "Schedule Defense"
            else:
                action_type = None
                action_label = None

        defense_records.append(
            {
                "phd_student": phd_student,
                "defense": defense,
                "committee": committee,
                "committee_member": committee_member,
                "defense_role": defense_role,
                "defense_status": defense_status,
                "status_label": status_label,
                "submitted_evaluations": submitted_evaluations,
                "total_evaluations": total_evaluations,
                "pending_evaluations": pending_evaluations,
                "own_evaluation": own_evaluation,
                "all_evaluations_submitted": all_evaluations_submitted,
                "evaluation_available": evaluation_available,
                "finalization_available": finalization_available,
                "action_type": action_type,
                "action_label": action_label,
            }
        )

    total_count = len(
        defense_records,
    )

    scheduled_count = sum(
        1 for record in defense_records if record["defense_status"] == "SCHEDULED"
    )

    evaluation_pending_count = sum(
        1
        for record in defense_records
        if record["defense_status"] == "EVALUATION_PENDING"
    )

    pending_count = sum(
        1 for record in defense_records if record["defense_status"] == "NOT_SCHEDULED"
    )

    completed_count = sum(
        1 for record in defense_records if record["defense_status"] == "COMPLETED"
    )

    chair_count = sum(
        1 for record in defense_records if record["defense_role"] == "CHAIR"
    )

    committee_count = sum(
        1 for record in defense_records if record["defense_role"] == "COMMITTEE_MEMBER"
    )

    pending_evaluation_actions = sum(
        1 for record in defense_records if record["evaluation_available"]
    )

    pending_finalization_actions = sum(
        1 for record in defense_records if record["finalization_available"]
    )

    context = {
        "faculty": faculty,
        "defense_records": defense_records,
        "total_count": total_count,
        "scheduled_count": scheduled_count,
        "evaluation_pending_count": evaluation_pending_count,
        "pending_count": pending_count,
        "completed_count": completed_count,
        "chair_count": chair_count,
        "committee_count": committee_count,
        "pending_evaluation_actions": pending_evaluation_actions,
        "pending_finalization_actions": pending_finalization_actions,
    }

    return render(
        request,
        "leo/FinalDissertation/Defense/dissertation_defense_list.html",
        context,
    )


@login_required
@transaction.atomic
def faculty_chair_dissertation_defense_schedule(
    request,
    uuid,
    phd_student_id,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
            "faculty_rank",
            "department",
        ),
        user__uuid=uuid,
        user=request.user,
        employment_status="ACTIVE",
    )

    phd_student = get_object_or_404(
        PhDStudent.objects.select_related(
            "student",
            "student__user",
            "phd_program",
            "phd_program__department",
            "advisor",
            "advisor__user",
            "doctoral_committee",
            "doctoral_committee__chair_faculty",
            "doctoral_committee__chair_faculty__user",
        ),
        pk=phd_student_id,
        current_status="ACTIVE",
    )

    committee = getattr(
        phd_student,
        "doctoral_committee",
        None,
    )

    if not committee:
        messages.error(
            request,
            "No doctoral committee is associated with this student.",
        )
        return redirect(
            "faculty_dissertation_defense_list",
            uuid=uuid,
        )

    if committee.chair_faculty_id != faculty.pk:
        messages.error(
            request,
            "Only the Chair Faculty can schedule this dissertation defense.",
        )
        return redirect(
            "faculty_dissertation_defense_list",
            uuid=uuid,
        )

    if committee.approval_status != "APPROVED":
        messages.error(
            request,
            "The doctoral committee has not been approved.",
        )
        return redirect(
            "faculty_dissertation_defense_list",
            uuid=uuid,
        )

    approved_submission = (
        FinalDissertationSubmission.objects.filter(
            phd_student=phd_student,
            status="APPROVED",
        )
        .order_by(
            "-submission_number",
            "-created_at",
        )
        .first()
    )

    if not approved_submission:
        messages.error(
            request,
            "The Final Dissertation has not been approved yet.",
        )
        return redirect(
            "faculty_dissertation_defense_list",
            uuid=uuid,
        )

    defense = (
        DissertationDefense.objects.filter(
            phd_student=phd_student,
        )
        .order_by("-defense_id")
        .first()
    )

    defense_locations = DefenseLocation.objects.filter(
        is_active=True,
    ).order_by(
        "name",
    )

    is_update = defense is not None

    if defense and defense.result != "PENDING":
        messages.warning(
            request,
            "This dissertation defense has already been finalized and cannot be rescheduled.",
        )
        return redirect(
            "faculty_chair_dissertation_defense_detail",
            uuid=uuid,
            defense_id=defense.defense_id,
        )

    if request.method == "POST":
        form = DissertationDefenseScheduleForm(
            request.POST,
            instance=defense,
            faculty=faculty,
        )

        if form.is_valid():
            try:
                defense = form.save(commit=False)
                defense.phd_student = phd_student
                defense.result = "PENDING"

                if not defense.committee_decision:
                    defense.committee_decision = "MINOR_REVISIONS"

                defense.save()

                messages.success(
                    request,
                    (
                        "Dissertation defense updated successfully."
                        if is_update
                        else "Dissertation defense scheduled successfully."
                    ),
                )

                return redirect(
                    "faculty_chair_dissertation_defense_detail",
                    uuid=uuid,
                    defense_id=defense.defense_id,
                )

            except IntegrityError:
                messages.error(
                    request,
                    "Unable to save the dissertation defense. Please verify the schedule and try again.",
                )
    else:
        form = DissertationDefenseScheduleForm(
            instance=defense,
            faculty=faculty,
        )

        if defense is None:
            form.initial["phd_student"] = phd_student.pk

    context = {
        "faculty": faculty,
        "phd_student": phd_student,
        "committee": committee,
        "approved_submission": approved_submission,
        "defense": defense,
        "form": form,
        "is_update": is_update,
        "defense_locations": defense_locations,
    }

    return render(
        request,
        "leo/FinalDissertation/Defense/chair_defense_schedule.html",
        context,
    )


@login_required
@require_POST
def chair_add_defense_location(request, uuid):

    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
            "faculty_rank",
            "department",
        ),
        user__uuid=uuid,
        user=request.user,
        employment_status="ACTIVE",
    )

    name = request.POST.get(
        "name",
        "",
    ).strip()

    if not name:

        return JsonResponse(
            {
                "success": False,
                "message": "Please enter a defense location.",
            },
            status=400,
        )

    if len(name) > 255:

        return JsonResponse(
            {
                "success": False,
                "message": "Defense location cannot exceed 255 characters.",
            },
            status=400,
        )

    location, created = DefenseLocation.objects.get_or_create(
        name=name,
        defaults={
            "is_active": True,
        },
    )

    if not location.is_active:

        location.is_active = True
        location.save(
            update_fields=[
                "is_active",
                "updated_at",
            ],
        )

    return JsonResponse(
        {
            "success": True,
            "created": created,
            "location": {
                "id": location.pk,
                "name": location.name,
            },
            "message": (
                "Defense location added successfully."
                if created
                else "This defense location already exists."
            ),
        }
    )


@login_required
def faculty_chair_dissertation_defense_detail(
    request,
    uuid,
    defense_id,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
            "faculty_rank",
            "department",
        ),
        user__uuid=uuid,
        user=request.user,
        employment_status="ACTIVE",
    )

    defense = get_object_or_404(
        DissertationDefense.objects.select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__phd_program",
            "phd_student__phd_program__department",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "phd_student__doctoral_committee",
            "phd_student__doctoral_committee__chair_faculty",
            "phd_student__doctoral_committee__chair_faculty__user",
        ),
        defense_id=defense_id,
    )

    phd_student = defense.phd_student
    committee = getattr(
        phd_student,
        "doctoral_committee",
        None,
    )

    if not committee:
        messages.error(
            request,
            "No doctoral committee is associated with this dissertation.",
        )
        return redirect(
            "faculty_dissertation_defense_list",
            uuid=uuid,
        )

    if committee.approval_status != "APPROVED":
        messages.error(
            request,
            "The doctoral committee has not been approved.",
        )
        return redirect(
            "faculty_dissertation_defense_list",
            uuid=uuid,
        )

    if committee.chair_faculty_id != faculty.pk:
        messages.error(
            request,
            "You are not authorized to view this dissertation defense.",
        )
        return redirect(
            "faculty_dissertation_defense_list",
            uuid=uuid,
        )

    required_members = list(
        CommitteeMember.objects.filter(
            committee=committee,
            role__in=[
                "CO_CHAIR",
                "INTERNAL_MEMBER",
                "EXTERNAL_MEMBER",
            ],
        )
        .select_related(
            "faculty",
            "faculty__user",
            "faculty__faculty_rank",
            "faculty__department",
            "department",
        )
        .order_by(
            "role",
            "faculty__user__first_name",
            "faculty__user__last_name",
        )
    )

    evaluations = list(
        DissertationDefenseEvaluation.objects.filter(
            defense=defense,
            committee_member__in=required_members,
        )
        .select_related(
            "committee_member",
            "committee_member__faculty",
            "committee_member__faculty__user",
            "committee_member__faculty__faculty_rank",
            "committee_member__faculty__department",
        )
        .order_by(
            "committee_member__role",
            "committee_member__faculty__user__first_name",
            "committee_member__faculty__user__last_name",
        )
    )

    evaluation_map = {
        evaluation.committee_member_id: evaluation for evaluation in evaluations
    }

    for member in required_members:
        member.defense_evaluation = evaluation_map.get(member.member_id)

    required_count = len(required_members)

    submitted_evaluations = [
        evaluation for evaluation in evaluations if evaluation.is_submitted
    ]

    submitted_count = len(
        {evaluation.committee_member_id for evaluation in submitted_evaluations}
    )

    pending_count = max(
        required_count - submitted_count,
        0,
    )

    all_evaluations_submitted = required_count > 0 and submitted_count == required_count

    defense_date = getattr(
        defense,
        "defense_date",
        None,
    )

    defense_time = getattr(
        defense,
        "defense_time",
        None,
    )

    defense_conducted = (
        defense_date is not None and defense_date <= timezone.localdate()
    )

    defense_content_type = ContentType.objects.get_for_model(
        defense,
    )

    video_evidence = (
        PhDVideoEvidence.objects.filter(
            phd_student=defense.phd_student,
            evidence_type="DISSERTATION_DEFENSE",
            target_content_type=defense_content_type,
            target_object_id=defense.pk,
        )
        .select_related(
            "uploaded_by",
        )
        .first()
    )

    is_pending = defense.result == "PENDING"
    is_passed = defense.result == "PASS"
    is_failed = defense.result == "FAIL"
    is_finalized = is_passed or is_failed

    can_update_schedule = is_pending and not defense_conducted

    can_finalize = is_pending and defense_conducted and all_evaluations_submitted

    if is_passed:
        defense_status_label = "Passed"
        defense_status_class = "passed"
    elif is_failed:
        defense_status_label = "Failed"
        defense_status_class = "failed"
    elif defense_conducted:
        defense_status_label = "Conducted"
        defense_status_class = "conducted"
    elif defense_date:
        defense_status_label = "Scheduled"
        defense_status_class = "scheduled"
    else:
        defense_status_label = "Not Scheduled"
        defense_status_class = "pending"

    if is_finalized:
        workflow_stage = "Final Decision Recorded"
        workflow_stage_description = (
            "The Chair Faculty has recorded the final defense decision."
        )
    elif all_evaluations_submitted and defense_conducted:
        workflow_stage = "Ready for Final Decision"
        workflow_stage_description = "All required evaluations are complete and the defense is ready for final decision."
    elif defense_conducted:
        workflow_stage = "Committee Evaluation"
        workflow_stage_description = (
            "The defense has been conducted and committee evaluations are in progress."
        )
    elif defense_date:
        workflow_stage = "Defense Scheduled"
        workflow_stage_description = (
            "The defense has been scheduled and is awaiting completion."
        )
    else:
        workflow_stage = "Scheduling Required"
        workflow_stage_description = "A defense schedule has not yet been finalized."

    submitted_percentage = (
        round((submitted_count / required_count) * 100) if required_count else 0
    )

    approved_submission = (
        FinalDissertationSubmission.objects.filter(
            phd_student=phd_student,
            status="APPROVED",
        )
        .order_by(
            "-submission_number",
            "-created_at",
        )
        .first()
    )

    average_score = None

    submitted_scores = [
        evaluation.score
        for evaluation in submitted_evaluations
        if evaluation.score is not None
    ]

    if submitted_scores:
        average_score = round(
            sum(submitted_scores) / len(submitted_scores),
            1,
        )

    pass_recommendation_count = sum(
        1 for evaluation in submitted_evaluations if evaluation.recommendation == "PASS"
    )

    fail_recommendation_count = sum(
        1 for evaluation in submitted_evaluations if evaluation.recommendation == "FAIL"
    )

    committee_member_count = len(required_members)

    if not defense_date:
        schedule_state = "not_scheduled"
    elif defense_conducted:
        schedule_state = "conducted"
    else:
        schedule_state = "scheduled"

    context = {
        "faculty": faculty,
        "defense": defense,
        "phd_student": phd_student,
        "committee": committee,
        "committee_members": required_members,
        "evaluations": evaluations,
        "approved_submission": approved_submission,
        "required_count": required_count,
        "submitted_count": submitted_count,
        "pending_count": pending_count,
        "submitted_percentage": submitted_percentage,
        "all_evaluations_submitted": all_evaluations_submitted,
        "defense_conducted": defense_conducted,
        "is_pending": is_pending,
        "is_passed": is_passed,
        "is_failed": is_failed,
        "is_finalized": is_finalized,
        "can_update_schedule": can_update_schedule,
        "can_finalize": can_finalize,
        "defense_status_label": defense_status_label,
        "defense_status_class": defense_status_class,
        "workflow_stage": workflow_stage,
        "workflow_stage_description": workflow_stage_description,
        "schedule_state": schedule_state,
        "average_score": average_score,
        "pass_recommendation_count": pass_recommendation_count,
        "fail_recommendation_count": fail_recommendation_count,
        "committee_member_count": committee_member_count,
        "chair_name": faculty.user.get_full_name(),
        "defense_date": defense_date,
        "defense_time": defense_time,
        "approved_submission": approved_submission,
        "video_evidence": video_evidence,
    }

    return render(
        request,
        "leo/FinalDissertation/Defense/chair_defense_detail.html",
        context,
    )


@login_required
def faculty_committee_dissertation_defense_detail(
    request,
    uuid,
    defense_id,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
            "faculty_rank",
            "department",
        ),
        user__uuid=uuid,
        user=request.user,
        employment_status="ACTIVE",
    )

    defense = get_object_or_404(
        DissertationDefense.objects.select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__phd_program",
            "phd_student__phd_program__department",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "phd_student__doctoral_committee",
            "phd_student__doctoral_committee__chair_faculty",
            "phd_student__doctoral_committee__chair_faculty__user",
        ),
        defense_id=defense_id,
    )

    phd_student = defense.phd_student

    committee = getattr(
        phd_student,
        "doctoral_committee",
        None,
    )

    if not committee:
        messages.error(
            request,
            "No doctoral committee is associated with this dissertation defense.",
        )
        return redirect(
            "faculty_dissertation_defense_list",
            uuid=uuid,
        )

    if committee.approval_status != "APPROVED":
        messages.error(
            request,
            "The doctoral committee has not been approved.",
        )
        return redirect(
            "faculty_dissertation_defense_list",
            uuid=uuid,
        )

    committee_member = (
        CommitteeMember.objects.filter(
            committee=committee,
            faculty=faculty,
        )
        .select_related(
            "faculty",
            "faculty__user",
            "faculty__faculty_rank",
            "faculty__department",
            "department",
        )
        .first()
    )

    if not committee_member:
        messages.error(
            request,
            "You are not a member of this doctoral committee.",
        )
        return redirect(
            "faculty_dissertation_defense_list",
            uuid=uuid,
        )

    committee_members = (
        CommitteeMember.objects.filter(
            committee=committee,
            role__in=[
                "CO_CHAIR",
                "INTERNAL_MEMBER",
                "EXTERNAL_MEMBER",
            ],
        )
        .select_related(
            "faculty",
            "faculty__user",
            "faculty__faculty_rank",
            "faculty__department",
            "department",
        )
        .order_by(
            "role",
            "faculty__user__first_name",
            "faculty__user__last_name",
        )
    )

    required_count = committee_members.count()

    evaluations = (
        DissertationDefenseEvaluation.objects.filter(
            defense=defense,
            committee_member__in=committee_members,
            is_submitted=True,
        )
        .select_related(
            "committee_member",
            "committee_member__faculty",
            "committee_member__faculty__user",
            "committee_member__faculty__faculty_rank",
            "committee_member__faculty__department",
        )
        .order_by(
            "committee_member__role",
            "committee_member__faculty__user__first_name",
            "committee_member__faculty__user__last_name",
        )
    )

    evaluation_map = {
        evaluation.committee_member_id: evaluation for evaluation in evaluations
    }

    for member in committee_members:
        member.defense_evaluation = evaluation_map.get(
            member.member_id,
        )

    own_evaluation = (
        evaluations.filter(
            committee_member=committee_member,
        )
        .order_by(
            "-submitted_at",
            "-evaluation_id",
        )
        .first()
    )

    defense_date = getattr(
        defense,
        "defense_date",
        None,
    )

    defense_conducted = (
        defense_date is not None and defense_date <= timezone.localdate()
    )

    defense_content_type = ContentType.objects.get_for_model(
        defense,
    )

    video_evidence = (
        PhDVideoEvidence.objects.filter(
            phd_student=defense.phd_student,
            evidence_type="DISSERTATION_DEFENSE",
            target_content_type=defense_content_type,
            target_object_id=defense.pk,
        )
        .select_related(
            "uploaded_by",
        )
        .first()
    )

    evaluation_submitted = own_evaluation is not None

    can_evaluate = (
        defense.result == "PENDING" and defense_conducted and not evaluation_submitted
    )

    is_finalized = defense.result in {
        "PASS",
        "FAIL",
    }

    submitted_count = (
        evaluations.values(
            "committee_member_id",
        )
        .distinct()
        .count()
    )

    pending_count = max(
        required_count - submitted_count,
        0,
    )

    all_evaluations_submitted = required_count > 0 and submitted_count == required_count

    approved_submission = (
        FinalDissertationSubmission.objects.filter(
            phd_student=phd_student,
            status="APPROVED",
        )
        .order_by(
            "-submission_number",
            "-created_at",
        )
        .first()
    )

    context = {
        "faculty": faculty,
        "defense": defense,
        "phd_student": phd_student,
        "video_evidence": video_evidence,
        "committee": committee,
        "committee_member": committee_member,
        "committee_members": committee_members,
        "evaluations": evaluations,
        "own_evaluation": own_evaluation,
        "approved_submission": approved_submission,
        "can_evaluate": can_evaluate,
        "evaluation_submitted": evaluation_submitted,
        "defense_conducted": defense_conducted,
        "is_finalized": is_finalized,
        "required_count": required_count,
        "submitted_count": submitted_count,
        "pending_count": pending_count,
        "all_evaluations_submitted": all_evaluations_submitted,
    }

    return render(
        request,
        "leo/FinalDissertation/Defense/committee_defense_detail.html",
        context,
    )


# ========================================================
# Final Dissertation & Defense - Advisor
# ========================================================


@login_required
def faculty_advisor_dissertation_defense_list(
    request,
    uuid,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
            "faculty_rank",
            "department",
        ),
        user__uuid=uuid,
        user=request.user,
        employment_status="ACTIVE",
    )

    latest_submission = FinalDissertationSubmission.objects.filter(
        phd_student=OuterRef("pk"),
    ).order_by(
        "-submission_number",
        "-created_at",
    )

    phd_students = (
        PhDStudent.objects.select_related(
            "student",
            "student__user",
            "phd_program",
            "phd_program__department",
            "advisor",
            "advisor__user",
            "doctoral_committee",
            "doctoral_committee__chair_faculty",
            "doctoral_committee__chair_faculty__user",
        )
        .prefetch_related(
            Prefetch(
                "doctoral_committee__committee_members",
                queryset=CommitteeMember.objects.select_related(
                    "faculty",
                    "faculty__user",
                    "faculty__faculty_rank",
                    "faculty__department",
                    "department",
                ).order_by(
                    "role",
                    "faculty__user__first_name",
                    "faculty__user__last_name",
                ),
            ),
        )
        .annotate(
            latest_dissertation_status=Subquery(
                latest_submission.values(
                    "status",
                )[:1]
            ),
            latest_dissertation_submission_id=Subquery(
                latest_submission.values(
                    "submission_id",
                )[:1]
            ),
        )
        .filter(
            advisor=faculty,
            latest_dissertation_status="APPROVED",
            doctoral_committee__approval_status="APPROVED",
            current_status="ACTIVE",
        )
        .distinct()
        .order_by(
            "student__user__first_name",
            "student__user__last_name",
        )
    )

    defense_records = []

    for phd_student in phd_students:

        defense = (
            DissertationDefense.objects.filter(
                phd_student=phd_student,
            )
            .order_by(
                "-defense_id",
            )
            .first()
        )

        committee = getattr(
            phd_student,
            "doctoral_committee",
            None,
        )

        committee_members = []

        if committee:
            committee_members = list(committee.committee_members.all())

        committee_count = len(committee_members)

        required_members = [
            member
            for member in committee_members
            if member.role
            in {
                "CO_CHAIR",
                "INTERNAL_MEMBER",
                "EXTERNAL_MEMBER",
            }
        ]

        required_evaluation_count = len(required_members)

        if defense:

            submitted_evaluations = defense.evaluations.filter(
                committee_member__in=required_members,
                is_submitted=True,
            ).count()

            if defense.result in {
                "PASS",
                "FAIL",
            }:
                defense_status = "COMPLETED"
            else:
                defense_status = "SCHEDULED"

        else:

            submitted_evaluations = 0
            defense_status = "NOT_SCHEDULED"

        if required_evaluation_count:
            evaluation_percentage = round(
                (submitted_evaluations / required_evaluation_count) * 100
            )
        else:
            evaluation_percentage = 0

        defense_records.append(
            {
                "phd_student": phd_student,
                "defense": defense,
                "committee": committee,
                "committee_members": committee_members,
                "committee_count": committee_count,
                "required_evaluation_count": required_evaluation_count,
                "submitted_evaluations": submitted_evaluations,
                "total_evaluations": required_evaluation_count,
                "evaluation_percentage": evaluation_percentage,
                "defense_status": defense_status,
            }
        )

    total_count = len(defense_records)

    scheduled_count = sum(
        1 for record in defense_records if record["defense_status"] == "SCHEDULED"
    )

    pending_count = sum(
        1 for record in defense_records if record["defense_status"] == "NOT_SCHEDULED"
    )

    completed_count = sum(
        1 for record in defense_records if record["defense_status"] == "COMPLETED"
    )

    context = {
        "faculty": faculty,
        "defense_records": defense_records,
        "total_count": total_count,
        "scheduled_count": scheduled_count,
        "pending_count": pending_count,
        "completed_count": completed_count,
    }

    return render(
        request,
        "leo/FinalDissertation/Defense/advisor_defense_list.html",
        context,
    )


@login_required
def faculty_advisor_dissertation_defense_detail(
    request,
    uuid,
    defense_id,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
            "faculty_rank",
            "department",
        ),
        user__uuid=uuid,
        user=request.user,
        employment_status="ACTIVE",
    )

    defense = get_object_or_404(
        DissertationDefense.objects.select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__phd_program",
            "phd_student__phd_program__department",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "phd_student__doctoral_committee",
            "phd_student__doctoral_committee__chair_faculty",
            "phd_student__doctoral_committee__chair_faculty__user",
        ),
        defense_id=defense_id,
        phd_student__advisor=faculty,
        phd_student__current_status="ACTIVE",
        phd_student__doctoral_committee__approval_status="APPROVED",
    )

    phd_student = defense.phd_student

    committee = getattr(
        phd_student,
        "doctoral_committee",
        None,
    )

    if not committee:
        messages.error(
            request,
            "No doctoral committee is associated with this dissertation defense.",
        )
        return redirect(
            "faculty_advisor_dissertation_defense_list",
            uuid=uuid,
        )

    approved_submission = (
        FinalDissertationSubmission.objects.filter(
            phd_student=phd_student,
            status="APPROVED",
        )
        .order_by(
            "-submission_number",
            "-created_at",
        )
        .first()
    )

    if not approved_submission:
        messages.error(
            request,
            "The approved final dissertation submission could not be found.",
        )
        return redirect(
            "faculty_advisor_dissertation_defense_list",
            uuid=uuid,
        )

    defense_content_type = ContentType.objects.get_for_model(
        defense,
    )

    video_evidence = (
        PhDVideoEvidence.objects.filter(
            phd_student=phd_student,
            evidence_type="DISSERTATION_DEFENSE",
            target_content_type=defense_content_type,
            target_object_id=defense.pk,
        )
        .select_related(
            "uploaded_by",
        )
        .first()
    )

    committee_members = (
        CommitteeMember.objects.filter(
            committee=committee,
        )
        .select_related(
            "faculty",
            "faculty__user",
            "faculty__faculty_rank",
            "faculty__department",
            "department",
        )
        .order_by(
            "role",
            "faculty__user__first_name",
            "faculty__user__last_name",
        )
    )

    required_members = committee_members.filter(
        role__in=[
            "CO_CHAIR",
            "INTERNAL_MEMBER",
            "EXTERNAL_MEMBER",
        ],
    )

    evaluations = (
        DissertationDefenseEvaluation.objects.filter(
            defense=defense,
        )
        .select_related(
            "committee_member",
            "committee_member__faculty",
            "committee_member__faculty__user",
            "committee_member__faculty__faculty_rank",
            "committee_member__faculty__department",
        )
        .order_by(
            "committee_member__role",
            "committee_member__faculty__user__first_name",
            "committee_member__faculty__user__last_name",
        )
    )

    evaluation_map = {
        evaluation.committee_member_id: evaluation for evaluation in evaluations
    }

    for member in committee_members:
        member.defense_evaluation = evaluation_map.get(
            member.member_id,
        )

    required_count = required_members.count()

    submitted_count = evaluations.filter(
        committee_member__in=required_members,
        is_submitted=True,
    ).count()

    pending_count = max(
        required_count - submitted_count,
        0,
    )

    all_evaluations_submitted = required_count > 0 and submitted_count == required_count

    if defense.result in {
        "PASS",
        "FAIL",
    }:
        defense_status = "COMPLETED"
    else:
        defense_status = "SCHEDULED"

    evaluation_percentage = 0

    if required_count:
        evaluation_percentage = round((submitted_count / required_count) * 100)

    context = {
        "faculty": faculty,
        "defense": defense,
        "phd_student": phd_student,
        "committee": committee,
        "committee_members": committee_members,
        "evaluations": evaluations,
        "approved_submission": approved_submission,
        "video_evidence": video_evidence,
        "required_count": required_count,
        "submitted_count": submitted_count,
        "pending_count": pending_count,
        "all_evaluations_submitted": all_evaluations_submitted,
        "evaluation_percentage": evaluation_percentage,
        "defense_status": defense_status,
    }

    return render(
        request,
        "leo/FinalDissertation/Defense/advisor_defense_detail.html",
        context,
    )


@login_required
@transaction.atomic
def faculty_committee_dissertation_defense_evaluate(
    request,
    uuid,
    defense_id,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
            "faculty_rank",
            "department",
        ),
        user__uuid=uuid,
        user=request.user,
        employment_status="ACTIVE",
    )

    defense = get_object_or_404(
        DissertationDefense.objects.select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__phd_program",
            "phd_student__phd_program__department",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "phd_student__doctoral_committee",
            "phd_student__doctoral_committee__chair_faculty",
            "phd_student__doctoral_committee__chair_faculty__user",
        ),
        defense_id=defense_id,
    )

    phd_student = defense.phd_student
    committee = getattr(
        phd_student,
        "doctoral_committee",
        None,
    )

    if not committee:
        messages.error(
            request,
            "No doctoral committee is associated with this dissertation defense.",
        )
        return redirect(
            "faculty_dissertation_defense_list",
            uuid=uuid,
        )

    if committee.approval_status != "APPROVED":
        messages.error(
            request,
            "The doctoral committee has not been approved.",
        )
        return redirect(
            "faculty_committee_dissertation_defense_detail",
            uuid=uuid,
            defense_id=defense.defense_id,
        )

    committee_member = (
        CommitteeMember.objects.filter(
            committee=committee,
            faculty=faculty,
        )
        .select_related(
            "faculty",
            "faculty__user",
            "faculty__faculty_rank",
            "faculty__department",
            "department",
        )
        .first()
    )

    if not committee_member:
        messages.error(
            request,
            "You are not a member of this doctoral committee.",
        )
        return redirect(
            "faculty_dissertation_defense_detail",
            uuid=uuid,
            defense_id=defense.defense_id,
        )

    if defense.result != "PENDING":
        messages.warning(
            request,
            "This dissertation defense has already been finalized. Evaluation is closed.",
        )
        return redirect(
            "faculty_committee_dissertation_defense_detail",
            uuid=uuid,
            defense_id=defense.defense_id,
        )

    if not defense.defense_date:
        messages.error(
            request,
            "The dissertation defense date has not been scheduled.",
        )
        return redirect(
            "faculty_committee_dissertation_defense_detail",
            uuid=uuid,
            defense_id=defense.defense_id,
        )

    if defense.defense_date > timezone.localdate():
        messages.warning(
            request,
            "Defense evaluation can only be submitted after the defense date.",
        )
        return redirect(
            "faculty_committee_dissertation_defense_detail",
            uuid=uuid,
            defense_id=defense.defense_id,
        )

    existing_evaluation = (
        DissertationDefenseEvaluation.objects.filter(
            defense=defense,
            committee_member=committee_member,
        )
        .order_by(
            "-submitted_at",
            "-evaluation_id",
        )
        .first()
    )

    if existing_evaluation:
        messages.info(
            request,
            "You have already submitted your evaluation for this dissertation defense.",
        )
        return redirect(
            "faculty_committee_dissertation_defense_evaluation_detail",
            uuid=uuid,
            defense_id=defense.defense_id,
            evaluation_id=existing_evaluation.evaluation_id,
        )

    if request.method == "POST":
        form = DissertationDefenseEvaluationForm(
            request.POST,
            faculty=faculty,
            defense=defense,
        )

        if form.is_valid():
            try:
                evaluation = form.save()
                messages.success(
                    request,
                    "Defense evaluation submitted successfully.",
                )
                return redirect(
                    "faculty_committee_dissertation_defense_evaluation_detail",
                    uuid=uuid,
                    defense_id=defense.defense_id,
                    evaluation_id=evaluation.evaluation_id,
                )
            except IntegrityError:
                messages.error(
                    request,
                    "Unable to submit the defense evaluation. You may have already submitted an evaluation.",
                )
    else:
        form = DissertationDefenseEvaluationForm(
            faculty=faculty,
            defense=defense,
        )

    approved_submission = (
        FinalDissertationSubmission.objects.filter(
            phd_student=phd_student,
            status="APPROVED",
        )
        .order_by(
            "-submission_number",
            "-created_at",
        )
        .first()
    )

    context = {
        "faculty": faculty,
        "defense": defense,
        "phd_student": phd_student,
        "committee": committee,
        "committee_member": committee_member,
        "approved_submission": approved_submission,
        "form": form,
    }

    return render(
        request,
        "leo/FinalDissertation/Defense/committee_defense_evaluate.html",
        context,
    )


@login_required
def faculty_committee_dissertation_defense_evaluation_detail(
    request,
    uuid,
    defense_id,
    evaluation_id,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
            "faculty_rank",
            "department",
        ),
        user__uuid=uuid,
        user=request.user,
        employment_status="ACTIVE",
    )

    defense = get_object_or_404(
        DissertationDefense.objects.select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__phd_program",
            "phd_student__phd_program__department",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "phd_student__doctoral_committee",
            "phd_student__doctoral_committee__chair_faculty",
            "phd_student__doctoral_committee__chair_faculty__user",
        ),
        defense_id=defense_id,
    )

    phd_student = defense.phd_student
    committee = getattr(
        phd_student,
        "doctoral_committee",
        None,
    )

    if not committee:
        messages.error(
            request,
            "No doctoral committee is associated with this dissertation defense.",
        )
        return redirect(
            "faculty_dissertation_defense_list",
            uuid=uuid,
        )

    if committee.approval_status != "APPROVED":
        messages.error(
            request,
            "The doctoral committee has not been approved.",
        )
        return redirect(
            "faculty_dissertation_defense_list",
            uuid=uuid,
        )

    committee_member = (
        CommitteeMember.objects.filter(
            committee=committee,
            faculty=faculty,
        )
        .select_related(
            "faculty",
            "faculty__user",
            "faculty__faculty_rank",
            "faculty__department",
            "department",
        )
        .first()
    )
    committee_members = CommitteeMember.objects.filter(
        committee=committee,
    ).select_related(
        "faculty",
        "faculty__user",
        "faculty__faculty_rank",
        "faculty__department",
        "department",
    )

    if not committee_member:
        messages.error(
            request,
            "You are not a member of this doctoral committee.",
        )
        return redirect(
            "faculty_dissertation_defense_detail",
            uuid=uuid,
            defense_id=defense.defense_id,
        )

    evaluation = get_object_or_404(
        DissertationDefenseEvaluation.objects.select_related(
            "defense",
            "committee_member",
            "committee_member__faculty",
            "committee_member__faculty__user",
            "committee_member__faculty__faculty_rank",
            "committee_member__faculty__department",
        ),
        evaluation_id=evaluation_id,
        defense=defense,
        committee_member=committee_member,
    )

    if not evaluation.is_submitted:
        messages.warning(
            request,
            "This defense evaluation has not been submitted.",
        )
        return redirect(
            "faculty_committee_dissertation_defense_evaluate",
            uuid=uuid,
            defense_id=defense.defense_id,
        )

    approved_submission = (
        FinalDissertationSubmission.objects.filter(
            phd_student=phd_student,
            status="APPROVED",
        )
        .order_by(
            "-submission_number",
            "-created_at",
        )
        .first()
    )

    context = {
        "faculty": faculty,
        "defense": defense,
        "phd_student": phd_student,
        "committee": committee,
        "committee_member": committee_member,
        "evaluation": evaluation,
        "approved_submission": approved_submission,
        "committee_members": committee_members,
    }

    return render(
        request,
        "leo/FinalDissertation/Defense/committee_defense_evaluation_detail.html",
        context,
    )


@login_required
@transaction.atomic
def faculty_chair_dissertation_defense_finalize(
    request,
    uuid,
    defense_id,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
            "faculty_rank",
            "department",
        ),
        user__uuid=uuid,
        user=request.user,
        employment_status="ACTIVE",
    )

    defense = get_object_or_404(
        DissertationDefense.objects.select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__phd_program",
            "phd_student__phd_program__department",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "phd_student__doctoral_committee",
            "phd_student__doctoral_committee__chair_faculty",
            "phd_student__doctoral_committee__chair_faculty__user",
        ),
        defense_id=defense_id,
    )

    phd_student = defense.phd_student
    committee = getattr(
        phd_student,
        "doctoral_committee",
        None,
    )

    if not committee:
        messages.error(
            request,
            "No doctoral committee is associated with this dissertation defense.",
        )
        return redirect(
            "faculty_dissertation_defense_list",
            uuid=uuid,
        )

    if committee.approval_status != "APPROVED":
        messages.error(
            request,
            "The doctoral committee has not been approved.",
        )
        return redirect(
            "faculty_chair_dissertation_defense_detail",
            uuid=uuid,
            defense_id=defense.defense_id,
        )

    if committee.chair_faculty_id != faculty.pk:
        messages.error(
            request,
            "Only the Chair Faculty can finalize this dissertation defense.",
        )
        return redirect(
            "faculty_chair_dissertation_defense_detail",
            uuid=uuid,
            defense_id=defense.defense_id,
        )

    if defense.result != "PENDING":
        messages.warning(
            request,
            "This dissertation defense has already been finalized.",
        )
        return redirect(
            "faculty_chair_dissertation_defense_final_detail",
            uuid=uuid,
            defense_id=defense.defense_id,
        )

    if not defense.defense_date:
        messages.error(
            request,
            "The dissertation defense date has not been scheduled.",
        )
        return redirect(
            "faculty_chair_dissertation_defense_detail",
            uuid=uuid,
            defense_id=defense.defense_id,
        )

    if defense.defense_date > timezone.localdate():
        messages.warning(
            request,
            "The dissertation defense must be conducted before it can be finalized.",
        )
        return redirect(
            "faculty_chair_dissertation_defense_detail",
            uuid=uuid,
            defense_id=defense.defense_id,
        )

    required_members = CommitteeMember.objects.filter(
        committee=committee,
        role__in=[
            "CO_CHAIR",
            "INTERNAL_MEMBER",
            "EXTERNAL_MEMBER",
        ],
    )

    required_count = required_members.count()

    if required_count == 0:
        messages.error(
            request,
            "At least one committee member evaluation is required before finalization.",
        )
        return redirect(
            "faculty_chair_dissertation_defense_detail",
            uuid=uuid,
            defense_id=defense.defense_id,
        )

    submitted_count = (
        DissertationDefenseEvaluation.objects.filter(
            defense=defense,
            committee_member__in=required_members,
            is_submitted=True,
        )
        .values(
            "committee_member_id",
        )
        .distinct()
        .count()
    )

    if submitted_count != required_count:
        messages.error(
            request,
            "All required committee members must submit their defense evaluations before Chair finalization.",
        )
        return redirect(
            "faculty_chair_dissertation_defense_detail",
            uuid=uuid,
            defense_id=defense.defense_id,
        )

    evaluations = (
        DissertationDefenseEvaluation.objects.filter(
            defense=defense,
            committee_member__in=required_members,
        )
        .select_related(
            "committee_member",
            "committee_member__faculty",
            "committee_member__faculty__user",
            "committee_member__faculty__faculty_rank",
            "committee_member__faculty__department",
        )
        .order_by(
            "committee_member__role",
            "committee_member__faculty__user__first_name",
            "committee_member__faculty__user__last_name",
        )
    )

    if request.method == "POST":
        form = DissertationDefenseChairFinalizationForm(
            request.POST,
            instance=defense,
            faculty=faculty,
        )

        if form.is_valid():
            try:
                finalized_defense = form.save()
                messages.success(
                    request,
                    "Dissertation defense finalized successfully.",
                )
                return redirect(
                    "faculty_chair_dissertation_defense_final_detail",
                    uuid=uuid,
                    defense_id=finalized_defense.defense_id,
                )
            except IntegrityError:
                messages.error(
                    request,
                    "Unable to finalize the dissertation defense. Please try again.",
                )
    else:
        form = DissertationDefenseChairFinalizationForm(
            instance=defense,
            faculty=faculty,
        )

    approved_submission = (
        FinalDissertationSubmission.objects.filter(
            phd_student=phd_student,
            status="APPROVED",
        )
        .order_by(
            "-submission_number",
            "-created_at",
        )
        .first()
    )

    context = {
        "faculty": faculty,
        "defense": defense,
        "phd_student": phd_student,
        "committee": committee,
        "committee_members": required_members,
        "evaluations": evaluations,
        "approved_submission": approved_submission,
        "required_count": required_count,
        "submitted_count": submitted_count,
        "pending_count": max(
            required_count - submitted_count,
            0,
        ),
        "form": form,
    }

    return render(
        request,
        "leo/FinalDissertation/Defense/chair_defense_finalize.html",
        context,
    )


@login_required
def faculty_chair_dissertation_defense_final_detail(
    request,
    uuid,
    defense_id,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
            "faculty_rank",
            "department",
        ),
        user__uuid=uuid,
        user=request.user,
        employment_status="ACTIVE",
    )

    defense = get_object_or_404(
        DissertationDefense.objects.select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__phd_program",
            "phd_student__phd_program__department",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "phd_student__doctoral_committee",
            "phd_student__doctoral_committee__chair_faculty",
            "phd_student__doctoral_committee__chair_faculty__user",
        ),
        defense_id=defense_id,
    )

    phd_student = defense.phd_student
    committee = getattr(
        phd_student,
        "doctoral_committee",
        None,
    )

    if not committee:
        messages.error(
            request,
            "No doctoral committee is associated with this dissertation defense.",
        )
        return redirect(
            "faculty_dissertation_defense_list",
            uuid=uuid,
        )

    if committee.approval_status != "APPROVED":
        messages.error(
            request,
            "The doctoral committee has not been approved.",
        )
        return redirect(
            "faculty_dissertation_defense_list",
            uuid=uuid,
        )

    if committee.chair_faculty_id != faculty.pk:
        messages.error(
            request,
            "Only the Chair Faculty can view the final defense decision.",
        )
        return redirect(
            "faculty_chair_dissertation_defense_detail",
            uuid=uuid,
            defense_id=defense.defense_id,
        )

    if defense.result == "PENDING":
        messages.warning(
            request,
            "This dissertation defense has not been finalized yet.",
        )
        return redirect(
            "faculty_chair_dissertation_defense_detail",
            uuid=uuid,
            defense_id=defense.defense_id,
        )

    required_members = (
        CommitteeMember.objects.filter(
            committee=committee,
            role__in=[
                "CO_CHAIR",
                "INTERNAL_MEMBER",
                "EXTERNAL_MEMBER",
            ],
        )
        .select_related(
            "faculty",
            "faculty__user",
            "faculty__faculty_rank",
            "faculty__department",
            "department",
        )
        .order_by(
            "role",
            "faculty__user__first_name",
            "faculty__user__last_name",
        )
    )

    evaluations = (
        DissertationDefenseEvaluation.objects.filter(
            defense=defense,
            committee_member__in=required_members,
            is_submitted=True,
        )
        .select_related(
            "committee_member",
            "committee_member__faculty",
            "committee_member__faculty__user",
            "committee_member__faculty__faculty_rank",
            "committee_member__faculty__department",
        )
        .order_by(
            "committee_member__role",
            "committee_member__faculty__user__first_name",
            "committee_member__faculty__user__last_name",
        )
    )

    required_count = required_members.count()
    submitted_count = evaluations.count()

    approved_submission = (
        FinalDissertationSubmission.objects.filter(
            phd_student=phd_student,
            status="APPROVED",
        )
        .order_by(
            "-submission_number",
            "-created_at",
        )
        .first()
    )

    context = {
        "faculty": faculty,
        "defense": defense,
        "phd_student": phd_student,
        "committee": committee,
        "committee_members": required_members,
        "evaluations": evaluations,
        "approved_submission": approved_submission,
        "required_count": required_count,
        "submitted_count": submitted_count,
        "pending_count": max(
            required_count - submitted_count,
            0,
        ),
        "is_finalized": defense.result != "PENDING",
    }

    return render(
        request,
        "leo/FinalDissertation/Defense/chair_defense_final_detail.html",
        context,
    )


# ========================================================
# graduation module - committee
# ========================================================


@login_required
def committee_graduation_student_list(request, uuid):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
            "faculty_rank",
            "department",
        ),
        user__uuid=uuid,
        user=request.user,
        employment_status="ACTIVE",
    )

    graduations = (
        Graduation.objects.filter(
            Q(phd_student__doctoral_committee__chair_faculty=faculty)
            | Q(phd_student__doctoral_committee__committee_members__faculty=faculty)
        )
        .select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__phd_program",
            "phd_student__phd_program__department",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "phd_student__doctoral_committee",
            "phd_student__doctoral_committee__chair_faculty",
            "phd_student__doctoral_committee__chair_faculty__user",
        )
        .prefetch_related(
            "phd_student__doctoral_committee__committee_members",
        )
        .distinct()
        .order_by(
            "-created_at",
        )
    )

    search = request.GET.get(
        "search",
        "",
    ).strip()

    status = request.GET.get(
        "status",
        "",
    ).strip()

    if search:
        graduations = graduations.filter(
            Q(phd_student__student__user__first_name__icontains=search)
            | Q(phd_student__student__user__last_name__icontains=search)
            | Q(phd_student__student__user__email__icontains=search)
            | Q(phd_student__student__student_number__icontains=search)
        )

    if status:
        graduations = graduations.filter(
            status=status,
        )

    for graduation in graduations:
        committee = getattr(
            graduation.phd_student,
            "doctoral_committee",
            None,
        )

        graduation.committee = committee

        if committee and committee.chair_faculty_id == faculty.pk:
            graduation.current_role = "CHAIR"
            graduation.action_label = "Finalize"
            graduation.action_type = "FINALIZE"
        else:
            graduation.current_role = "COMMITTEE_MEMBER"
            graduation.action_label = "View Details"
            graduation.action_type = "DETAIL"

    context = {
        "faculty": faculty,
        "graduations": graduations,
        "search": search,
        "status": status,
        "status_choices": Graduation.STATUS_CHOICES,
    }

    return render(
        request,
        "leo/graduation/committee_graduation_student_list.html",
        context,
    )


@login_required
def committee_graduation_student_detail(
    request,
    uuid,
    graduation_id,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
            "faculty_rank",
            "department",
        ),
        user__uuid=uuid,
        user=request.user,
        employment_status="ACTIVE",
    )

    graduation = get_object_or_404(
        Graduation.objects.select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__phd_program",
            "phd_student__phd_program__department",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "phd_student__doctoral_committee",
            "phd_student__doctoral_committee__chair_faculty",
            "phd_student__doctoral_committee__chair_faculty__user",
            "created_by",
            "created_by__user",
            "chair_approved_by",
            "chair_approved_by__user",
        ).prefetch_related(
            "phd_student__doctoral_committee__committee_members",
        ),
        graduation_id=graduation_id,
    )

    phd_student = graduation.phd_student
    student = phd_student.student
    committee = getattr(phd_student, "doctoral_committee", None)

    if not committee:
        messages.error(
            request,
            "No doctoral committee is associated with this graduation record.",
        )
        return redirect(
            "committee_graduation_student_list",
            uuid=uuid,
        )

    is_chair = committee.chair_faculty_id == faculty.pk

    is_committee_member = committee.committee_members.filter(
        faculty=faculty,
    ).exists()

    if not is_chair and not is_committee_member:
        messages.error(
            request,
            "You are not authorized to view this graduation record.",
        )
        return redirect(
            "committee_graduation_student_list",
            uuid=uuid,
        )

    final_dissertation = (
        FinalDissertationSubmission.objects.filter(
            phd_student=phd_student,
        )
        .order_by(
            "-submission_number",
            "-created_at",
        )
        .first()
    )

    defense = (
        DissertationDefense.objects.filter(
            phd_student=phd_student,
        )
        .order_by(
            "-defense_date",
            "-defense_time",
        )
        .first()
    )

    dissertation_accepted = bool(
        final_dissertation and final_dissertation.status == "APPROVED"
    )

    defense_passed = bool(defense and defense.result == "PASS")

    graduation_fields_changed = False

    if graduation.dissertation_accepted != dissertation_accepted:
        graduation.dissertation_accepted = dissertation_accepted
        graduation_fields_changed = True

    if graduation.defense_passed != defense_passed:
        graduation.defense_passed = defense_passed
        graduation_fields_changed = True

    if graduation_fields_changed:
        graduation.save(
            update_fields=[
                "dissertation_accepted",
                "defense_passed",
                "updated_at",
            ]
        )

    doctoral_candidacy = (
        DoctoralCandidacy.objects.filter(
            phd_student=phd_student,
        )
        .order_by(
            "-candidacy_date",
        )
        .first()
    )

    proposals = DissertationProposal.objects.filter(
        phd_student=phd_student,
    ).order_by(
        "-submission_date",
    )

    milestones = ResearchMilestone.objects.filter(
        phd_student=phd_student,
    ).order_by(
        "sequence_number",
    )
    dissertation_history = FinalDissertationSubmission.objects.filter(
        phd_student=phd_student,
    ).order_by(
        "-submission_number",
        "-created_at",
    )
    annual_reviews = AnnualProgressReview.objects.filter(
        phd_student=phd_student,
    ).order_by(
        "-review_year",
    )

    publications = ResearchPublication.objects.filter(
        phd_student=phd_student,
    ).order_by(
        "-publication_date",
    )

    dissertations = Dissertation.objects.filter(
        phd_student=phd_student,
    ).order_by(
        "-submission_date",
    )

    preliminary_examinations = PreliminaryExamination.objects.filter(
        phd_student=phd_student,
    ).order_by(
        "-exam_date",
    )

    coursework = (
        FacultyCoursework.objects.filter(
            phd_student=phd_student,
        )
        .select_related(
            "coursework",
            "program",
        )
        .order_by(
            "coursework",
        )
    )

    committee_members = list(
        committee.committee_members.select_related(
            "faculty",
            "faculty__user",
        ).all()
    )

    advisor = getattr(
        phd_student,
        "advisor",
        None,
    )

    advisor_name = None

    if advisor:
        advisor_name = advisor.user.get_full_name()

    chair_faculty = committee.chair_faculty

    chair_name = None

    if chair_faculty:
        chair_name = chair_faculty.user.get_full_name()

    student_name = student.user.get_full_name()

    graduation_ready = dissertation_accepted and defense_passed

    chair_approval_completed = bool(
        graduation.chair_approved_by_id and graduation.chair_approved_at
    )

    chair_note_available = bool(
        graduation.chair_congratulations_note
        and graduation.chair_congratulations_note.strip()
    )

    graduation_achievements = [
        {
            "number": "01",
            "title": "Admission Completed",
            "icon": "fa-solid fa-door-open",
            "status": "Completed",
            "description": "Doctoral admission record is available.",
        },
        {
            "number": "02",
            "title": "Advisor Assigned",
            "icon": "fa-solid fa-user-tie",
            "status": "Completed" if advisor else "Not Available",
            "description": (
                f"Advisor assigned: {advisor_name}"
                if advisor_name
                else "Advisor information is not available."
            ),
        },
        {
            "number": "03",
            "title": "Chair Faculty Assigned",
            "icon": "fa-solid fa-user-shield",
            "status": "Completed" if chair_faculty else "Not Available",
            "description": (
                f"Chair Faculty: {chair_name}"
                if chair_name
                else "Chair Faculty information is not available."
            ),
        },
        {
            "number": "04",
            "title": "Doctoral Committee Formed",
            "icon": "fa-solid fa-users",
            "status": "Completed" if committee else "Not Available",
            "description": (
                f"{len(committee_members)} committee member(s) assigned."
                if committee
                else "Doctoral committee is not available."
            ),
        },
        {
            "number": "05",
            "title": "Coursework",
            "icon": "fa-solid fa-book-open",
            "status": f"{coursework.count()} Record(s)",
            "description": "Doctoral coursework records.",
        },
        {
            "number": "06",
            "title": "Qualifying Examination",
            "icon": "fa-solid fa-file-circle-check",
            "status": f"{preliminary_examinations.count()} Examination(s)",
            "description": "Qualifying examination history.",
        },
        {
            "number": "07",
            "title": "Dissertation Proposal",
            "icon": "fa-solid fa-file-signature",
            "status": f"{proposals.count()} Proposal(s)",
            "description": "Dissertation proposal submissions.",
        },
        {
            "number": "08",
            "title": "Doctoral Candidacy",
            "icon": "fa-solid fa-user-graduate",
            "status": (
                doctoral_candidacy.get_candidacy_status_display()
                if doctoral_candidacy
                else "Not Available"
            ),
            "description": "Doctoral candidacy record.",
        },
        {
            "number": "09",
            "title": "Research Milestones",
            "icon": "fa-solid fa-chart-line",
            "status": f"{milestones.count()} Milestone(s)",
            "description": "Research milestone progress.",
        },
        {
            "number": "10",
            "title": "Annual Progress",
            "icon": "fa-solid fa-calendar-check",
            "status": f"{annual_reviews.count()} Review(s)",
            "description": "Annual research progress reviews.",
        },
        {
            "number": "11",
            "title": "Research Publications",
            "icon": "fa-solid fa-book-open-reader",
            "status": f"{publications.count()} Publication(s)",
            "description": "Research publication achievements.",
        },
        {
            "number": "12",
            "title": "Final Dissertation Submission",
            "icon": "fa-solid fa-file-lines",
            "status": (
                final_dissertation.get_status_display()
                if final_dissertation
                else "Not Available"
            ),
            "description": (
                "Final dissertation submission record."
                if final_dissertation
                else "Final dissertation record is not available."
            ),
        },
        {
            "number": "13",
            "title": "Dissertation Defense",
            "icon": "fa-solid fa-chalkboard-user",
            "status": (defense.get_result_display() if defense else "Not Available"),
            "description": (
                "Dissertation defense result."
                if defense
                else "Dissertation defense record is not available."
            ),
        },
        {
            "number": "14",
            "title": "Final Dissertation Approved",
            "icon": "fa-solid fa-file-circle-check",
            "status": ("Approved" if dissertation_accepted else "Not Approved"),
            "description": (
                "Final dissertation has been accepted for graduation."
                if dissertation_accepted
                else "Final dissertation acceptance is pending."
            ),
        },
        {
            "number": "15",
            "title": "Dissertation Defense Passed",
            "icon": "fa-solid fa-medal",
            "status": ("Passed" if defense_passed else "Not Passed"),
            "description": (
                "Dissertation defense requirement has been satisfied."
                if defense_passed
                else "Dissertation defense requirement is not satisfied."
            ),
        },
        {
            "number": "16",
            "title": "Graduation",
            "icon": "fa-solid fa-graduation-cap",
            "status": graduation.get_status_display(),
            "description": (
                "Graduation requirements are complete and awaiting chair approval."
                if graduation_ready and graduation.status == "PENDING_CHAIR_APPROVAL"
                else (
                    "Graduation record has been approved by the chair."
                    if graduation.status == "APPROVED"
                    else (
                        "Graduation has been completed."
                        if graduation.status == "COMPLETED"
                        else "Graduation record status."
                    )
                )
            ),
        },
    ]
    graduation_content_type = ContentType.objects.get_for_model(
        graduation,
    )

    video_evidence = (
        PhDVideoEvidence.objects.filter(
            phd_student=phd_student,
            evidence_type="GRADUATION",
            target_content_type=graduation_content_type,
            target_object_id=graduation.pk,
        )
        .select_related(
            "uploaded_by",
        )
        .first()
    )

    if request.method == "POST" and is_chair:
        chair_note = request.POST.get(
            "chair_congratulations_note",
            "",
        ).strip()

        if not graduation_ready:
            messages.error(
                request,
                "Graduation requirements are not yet complete.",
            )
        elif not chair_note:
            messages.error(
                request,
                "Congratulations note is required for graduation approval.",
            )
        elif graduation.status in {"APPROVED", "COMPLETED"}:
            messages.info(
                request,
                "Graduation has already been approved.",
            )
        else:
            graduation.chair_congratulations_note = chair_note
            graduation.chair_approved_by = faculty
            graduation.chair_approved_at = timezone.now()
            graduation.status = "APPROVED"

            graduation.save(
                update_fields=[
                    "chair_congratulations_note",
                    "chair_approved_by",
                    "chair_approved_at",
                    "status",
                    "updated_at",
                ]
            )

            messages.success(
                request,
                "Graduation approved successfully.",
            )

            return redirect(
                "committee_graduation_student_detail",
                uuid=uuid,
                graduation_id=graduation_id,
            )

    context = {
        "faculty": faculty,
        "graduation": graduation,
        "phd_student": phd_student,
        "student": student,
        "student_name": student_name,
        "committee": committee,
        "committee_members": committee_members,
        "advisor": advisor,
        "advisor_name": advisor_name,
        "chair_faculty": chair_faculty,
        "chair_name": chair_name,
        "is_chair": is_chair,
        "is_committee_member": is_committee_member,
        "graduation_ready": graduation_ready,
        "dissertation_accepted": dissertation_accepted,
        "defense_passed": defense_passed,
        "chair_approval_completed": chair_approval_completed,
        "chair_note_available": chair_note_available,
        "final_dissertation": final_dissertation,
        "defense": defense,
        "doctoral_candidacy": doctoral_candidacy,
        "proposals": proposals,
        "milestones": milestones,
        "annual_reviews": annual_reviews,
        "publications": publications,
        "dissertations": dissertations,
        "preliminary_examinations": preliminary_examinations,
        "coursework": coursework,
        "graduation_achievements": graduation_achievements,
        "dissertation_history": dissertation_history,
        "video_evidence": video_evidence,
    }

    return render(
        request,
        "leo/graduation/committee_graduation_student_detail.html",
        context,
    )


# ========================================================
# Graduation module - advisor
# ========================================================


@login_required
def faculty_advisor_graduation_list(request, uuid):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
            "faculty_rank",
            "department",
        ),
        user__uuid=uuid,
        user=request.user,
        employment_status="ACTIVE",
    )

    graduations = (
        Graduation.objects.filter(
            phd_student__advisor=faculty,
        )
        .select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__phd_program",
            "phd_student__phd_program__department",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "phd_student__doctoral_committee",
            "phd_student__doctoral_committee__chair_faculty",
            "phd_student__doctoral_committee__chair_faculty__user",
        )
        .prefetch_related(
            "phd_student__doctoral_committee__committee_members",
        )
        .distinct()
        .order_by(
            "-created_at",
        )
    )

    search = request.GET.get(
        "search",
        "",
    ).strip()

    status = request.GET.get(
        "status",
        "",
    ).strip()

    if search:
        graduations = graduations.filter(
            Q(phd_student__student__user__first_name__icontains=search)
            | Q(phd_student__student__user__last_name__icontains=search)
            | Q(phd_student__student__user__email__icontains=search)
            | Q(phd_student__student__student_number__icontains=search)
        )

    if status:
        graduations = graduations.filter(
            status=status,
        )

    for graduation in graduations:
        graduation.current_role = "ADVISOR"
        graduation.action_label = "View Details"
        graduation.action_type = "DETAIL"

    context = {
        "faculty": faculty,
        "graduations": graduations,
        "search": search,
        "status": status,
        "status_choices": Graduation.STATUS_CHOICES,
    }

    return render(
        request,
        "leo/graduation/advisor_graduation_student_list.html",
        context,
    )


@login_required
def faculty_advisor_graduation_detail(
    request,
    uuid,
    graduation_id,
):
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related(
            "user",
            "faculty_rank",
            "department",
        ),
        user__uuid=uuid,
        user=request.user,
        employment_status="ACTIVE",
    )

    graduation = get_object_or_404(
        Graduation.objects.select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "phd_student__phd_program",
            "phd_student__phd_program__department",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "phd_student__doctoral_committee",
            "phd_student__doctoral_committee__chair_faculty",
            "phd_student__doctoral_committee__chair_faculty__user",
            "created_by",
            "created_by__user",
            "chair_approved_by",
            "chair_approved_by__user",
        ).prefetch_related(
            "phd_student__doctoral_committee__committee_members",
        ),
        graduation_id=graduation_id,
        phd_student__advisor=faculty,
    )

    phd_student = graduation.phd_student
    student = phd_student.student

    committee = getattr(
        phd_student,
        "doctoral_committee",
        None,
    )

    if not committee:
        messages.error(
            request,
            "No doctoral committee is associated with this graduation record.",
        )

        return redirect(
            "faculty_advisor_graduation_list",
            uuid=uuid,
        )

    final_dissertation = (
        FinalDissertationSubmission.objects.filter(
            phd_student=phd_student,
        )
        .order_by(
            "-submission_number",
            "-created_at",
        )
        .first()
    )

    defense = (
        DissertationDefense.objects.filter(
            phd_student=phd_student,
        )
        .order_by(
            "-defense_date",
            "-defense_time",
        )
        .first()
    )

    doctoral_candidacy = (
        DoctoralCandidacy.objects.filter(
            phd_student=phd_student,
        )
        .order_by(
            "-candidacy_date",
        )
        .first()
    )

    proposals = DissertationProposal.objects.filter(
        phd_student=phd_student,
    ).order_by(
        "-submission_date",
    )

    milestones = PhDMilestone.objects.filter(
        phd_student=phd_student,
    ).order_by(
        "-completion_date",
    )

    annual_reviews = AnnualProgressReview.objects.filter(
        phd_student=phd_student,
    ).order_by(
        "-review_year",
    )

    publications = ResearchPublication.objects.filter(
        phd_student=phd_student,
    ).order_by(
        "-publication_date",
    )

    dissertations = Dissertation.objects.filter(
        phd_student=phd_student,
    ).order_by(
        "-submission_date",
    )

    preliminary_examinations = PreliminaryExamination.objects.filter(
        phd_student=phd_student,
    ).order_by(
        "-exam_date",
    )

    coursework = (
        FacultyCoursework.objects.filter(
            phd_student=phd_student,
        )
        .select_related(
            "coursework",
            "program",
        )
        .order_by(
            "coursework",
        )
    )

    committee_members = list(
        committee.committee_members.select_related(
            "faculty",
            "faculty__user",
        ).all()
    )

    advisor = getattr(
        phd_student,
        "advisor",
        None,
    )

    advisor_name = None

    if advisor:
        advisor_name = advisor.user.get_full_name()

    chair_faculty = committee.chair_faculty

    chair_name = None

    if chair_faculty:
        chair_name = chair_faculty.user.get_full_name()

    student_name = student.user.get_full_name()

    graduation_ready = graduation.dissertation_accepted and graduation.defense_passed

    graduation_content_type = ContentType.objects.get_for_model(
        graduation,
    )

    video_evidence = (
        PhDVideoEvidence.objects.filter(
            phd_student=phd_student,
            evidence_type="GRADUATION",
            target_content_type=graduation_content_type,
            target_object_id=graduation.pk,
        )
        .select_related(
            "uploaded_by",
        )
        .first()
    )

    chair_approval_completed = bool(
        graduation.chair_approved_by_id and graduation.chair_approved_at
    )

    chair_note_available = bool(
        graduation.chair_congratulations_note
        and graduation.chair_congratulations_note.strip()
    )

    graduation_achievements = [
        {
            "number": "01",
            "title": "Admission Completed",
            "icon": "fa-solid fa-door-open",
            "status": "Completed",
            "description": "Doctoral admission record is available.",
        },
        {
            "number": "02",
            "title": "Advisor Assigned",
            "icon": "fa-solid fa-user-tie",
            "status": "Completed" if advisor else "Not Available",
            "description": (
                f"Advisor assigned: {advisor_name}"
                if advisor_name
                else "Advisor information is not available."
            ),
        },
        {
            "number": "03",
            "title": "Chair Faculty Assigned",
            "icon": "fa-solid fa-user-shield",
            "status": "Completed" if chair_faculty else "Not Available",
            "description": (
                f"Chair Faculty: {chair_name}"
                if chair_name
                else "Chair Faculty information is not available."
            ),
        },
        {
            "number": "04",
            "title": "Doctoral Committee Formed",
            "icon": "fa-solid fa-users",
            "status": "Completed" if committee else "Not Available",
            "description": (
                f"{len(committee_members)} committee member(s) assigned."
                if committee
                else "Doctoral committee is not available."
            ),
        },
        {
            "number": "05",
            "title": "Coursework",
            "icon": "fa-solid fa-book-open",
            "status": f"{coursework.count()} Record(s)",
            "description": "Doctoral coursework records.",
        },
        {
            "number": "06",
            "title": "Qualifying Examination",
            "icon": "fa-solid fa-file-circle-check",
            "status": f"{preliminary_examinations.count()} Examination(s)",
            "description": "Qualifying examination history.",
        },
        {
            "number": "07",
            "title": "Dissertation Proposal",
            "icon": "fa-solid fa-file-signature",
            "status": f"{proposals.count()} Proposal(s)",
            "description": "Dissertation proposal submissions.",
        },
        {
            "number": "08",
            "title": "Doctoral Candidacy",
            "icon": "fa-solid fa-user-graduate",
            "status": (
                doctoral_candidacy.get_candidacy_status_display()
                if doctoral_candidacy
                else "Not Available"
            ),
            "description": "Doctoral candidacy record.",
        },
        {
            "number": "09",
            "title": "Research Milestones",
            "icon": "fa-solid fa-chart-line",
            "status": f"{milestones.count()} Milestone(s)",
            "description": "Research milestone progress.",
        },
        {
            "number": "10",
            "title": "Annual Progress",
            "icon": "fa-solid fa-calendar-check",
            "status": f"{annual_reviews.count()} Review(s)",
            "description": "Annual research progress reviews.",
        },
        {
            "number": "11",
            "title": "Research Publications",
            "icon": "fa-solid fa-book-open-reader",
            "status": f"{publications.count()} Publication(s)",
            "description": "Research publication achievements.",
        },
        {
            "number": "12",
            "title": "Dissertation",
            "icon": "fa-solid fa-file-lines",
            "status": (
                final_dissertation.get_status_display()
                if final_dissertation
                else "Not Available"
            ),
            "description": (
                "Final dissertation submission record."
                if final_dissertation
                else "Final dissertation record is not available."
            ),
        },
        {
            "number": "13",
            "title": "Dissertation Defense",
            "icon": "fa-solid fa-chalkboard-user",
            "status": (defense.get_result_display() if defense else "Not Available"),
            "description": (
                "Dissertation defense result."
                if defense
                else "Dissertation defense record is not available."
            ),
        },
        {
            "number": "14",
            "title": "Final Dissertation Approved",
            "icon": "fa-solid fa-file-circle-check",
            "status": (
                "Approved" if graduation.dissertation_accepted else "Not Approved"
            ),
            "description": (
                "Final dissertation has been accepted for graduation."
                if graduation.dissertation_accepted
                else "Final dissertation acceptance is pending."
            ),
        },
        {
            "number": "15",
            "title": "Dissertation Defense Passed",
            "icon": "fa-solid fa-medal",
            "status": ("Passed" if graduation.defense_passed else "Not Passed"),
            "description": (
                "Dissertation defense requirement has been satisfied."
                if graduation.defense_passed
                else "Dissertation defense requirement is not satisfied."
            ),
        },
        {
            "number": "16",
            "title": "Graduation",
            "icon": "fa-solid fa-graduation-cap",
            "status": graduation.get_status_display(),
            "description": (
                "Graduation record created and awaiting finalization."
                if graduation.status == "PENDING_CHAIR_APPROVAL"
                else "Graduation record status."
            ),
        },
    ]

    context = {
        "faculty": faculty,
        "graduation": graduation,
        "phd_student": phd_student,
        "student": student,
        "student_name": student_name,
        "committee": committee,
        "committee_members": committee_members,
        "advisor": advisor,
        "advisor_name": advisor_name,
        "chair_faculty": chair_faculty,
        "chair_name": chair_name,
        "is_chair": False,
        "is_committee_member": False,
        "is_advisor": True,
        "graduation_ready": graduation_ready,
        "chair_approval_completed": chair_approval_completed,
        "chair_note_available": chair_note_available,
        "final_dissertation": final_dissertation,
        "defense": defense,
        "doctoral_candidacy": doctoral_candidacy,
        "proposals": proposals,
        "milestones": milestones,
        "annual_reviews": annual_reviews,
        "publications": publications,
        "dissertations": dissertations,
        "preliminary_examinations": preliminary_examinations,
        "coursework": coursework,
        "graduation_achievements": graduation_achievements,
        "video_evidence": video_evidence,
    }

    return render(
        request,
        "leo/graduation/advisor_graduation_student_detail.html",
        context,
    )


############################################################
# Faculty Advisor Module
############################################################


@login_required
def faculty_advisor_list(request, uuid):
    """
    Display list of advisees for a faculty member.

    Purpose:
        Show all PhD students advised by the faculty with statistics.

    Parameters:
        request: HTTP request object
        uuid: UUID of the faculty member

    Returns:
        Rendered template with advisee list and statistics

    Workflow:
        1. Get faculty profile
        2. Get PhD students with advisor
        3. Apply search filter
        4. Calculate statistics
        5. Render template
    """
    faculty = get_faculty_or_404(
        uuid,
        request.user,
    )

    search = request.GET.get(
        "search",
        "",
    )

    # Get advisees with all related data
    phd_students = (
        PhDStudent.objects.filter(
            advisor=faculty,
        )
        .select_related(
            "student",
            "student__user",
            "phd_program",
            "phd_program__department",
            "advisor",
            "advisor__user",
            "doctoral_committee",
            "doctoral_committee__chair_faculty",
            "doctoral_committee__chair_faculty__user",
            "graduation",
        )
        .prefetch_related(
            "doctoral_committee__committee_members",
        )
        .order_by(
            "student__user__last_name",
            "student__user__first_name",
        )
    )

    # Apply search filter
    if search:
        phd_students = phd_students.filter(
            Q(student__user__first_name__icontains=search)
            | Q(student__user__last_name__icontains=search)
            | Q(student__student_number__icontains=search)
            | Q(phd_program__program_name__icontains=search)
            | Q(phd_program__department__department_name__icontains=search)
        )

    # Calculate statistics
    total_advisees = phd_students.count()
    active_advisees = phd_students.filter(
        current_status="ACTIVE",
    ).count()
    in_progress = phd_students.exclude(
        current_status="GRADUATED",
    ).count()
    completed = phd_students.filter(
        graduation__isnull=False,
    ).count()

    doctoral_committees = DoctoralCommittee.objects.filter(
        phd_student__advisor=faculty,
    ).count()

    total_courseworks = FacultyCoursework.objects.filter(
        phd_student__advisor=faculty,
    ).count()
    completed_courseworks = FacultyCoursework.objects.filter(
        phd_student__advisor=faculty,
        status="COMPLETED",
    ).count()
    pending_courseworks = (
        FacultyCoursework.objects.filter(
            phd_student__advisor=faculty,
        )
        .exclude(
            status="COMPLETED",
        )
        .count()
    )

    context = {
        "faculty": faculty,
        "phd_students": phd_students,
        "search": search,
        "total_advisees": total_advisees,
        "active_advisees": active_advisees,
        "in_progress": in_progress,
        "completed": completed,
        "doctoral_committees": doctoral_committees,
        "total_courseworks": total_courseworks,
        "completed_courseworks": completed_courseworks,
        "pending_courseworks": pending_courseworks,
    }

    return render(
        request,
        "leo/PhD/faculty_advisees.html",
        context,
    )


@login_required
def faculty_advisor_workspace(request, uuid, phd_student_id):
    faculty = get_faculty_or_404(
        uuid,
        request.user,
    )

    phd_student = get_object_or_404(
        PhDStudent.objects.select_related(
            "student",
            "student__user",
            "advisor",
            "advisor__user",
            "phd_program",
            "phd_program__department",
            "doctoral_committee",
            "doctoral_committee__chair_faculty",
            "doctoral_committee__chair_faculty__user",
            "doctoral_candidacy",
            "dissertation_proposal",
            "dissertation",
            "graduation",
        ).prefetch_related(
            Prefetch(
                "doctoral_committee__committee_members",
                queryset=CommitteeMember.objects.select_related(
                    "faculty",
                    "faculty__user",
                    "department",
                ).order_by(
                    "role",
                ),
            ),
            Prefetch(
                "phd_milestones",
                queryset=PhDMilestone.objects.order_by(
                    "-completion_date",
                    "-milestone_id",
                ),
            ),
            Prefetch(
                "research_publications",
                queryset=ResearchPublication.objects.order_by(
                    "-publication_date",
                ),
            ),
            Prefetch(
                "annual_progress_reviews",
                queryset=AnnualProgressReview.objects.order_by(
                    "-review_year",
                ),
            ),
            Prefetch(
                "faculty_courseworks",
                queryset=FacultyCoursework.objects.select_related(
                    "coursework",
                    "program",
                    "submission__evaluation",
                ).order_by(
                    "-academic_year",
                    "coursework__coursework_name",
                ),
            ),
            Prefetch(
                "preliminary_examinations",
                queryset=PreliminaryExamination.objects.order_by(
                    "-exam_date",
                    "-start_time",
                ),
            ),
        ),
        phd_student_id=phd_student_id,
        advisor=faculty,
    )

    advisor = phd_student.advisor

    committee = getattr(
        phd_student,
        "doctoral_committee",
        None,
    )

    committee_members = list(committee.committee_members.all()) if committee else []

    chair_faculty = committee.chair_faculty if committee else None

    phd_program = phd_student.phd_program

    department = phd_program.department if phd_program else None

    candidacy = getattr(
        phd_student,
        "doctoral_candidacy",
        None,
    )

    proposal = getattr(
        phd_student,
        "dissertation_proposal",
        None,
    )

    dissertation = getattr(
        phd_student,
        "dissertation",
        None,
    )

    graduation = getattr(
        phd_student,
        "graduation",
        None,
    )

    defense = getattr(
        phd_student,
        "dissertation_defense",
        None,
    )

    milestones = list(phd_student.phd_milestones.all())

    publications = list(phd_student.research_publications.all())

    reviews = list(phd_student.annual_progress_reviews.all())

    courseworks = list(phd_student.faculty_courseworks.all())

    examinations = list(phd_student.preliminary_examinations.all())

    total_courseworks = len(courseworks)

    completed_courseworks = sum(1 for item in courseworks if item.status == "COMPLETED")

    in_progress_courseworks = sum(
        1 for item in courseworks if item.status == "IN_PROGRESS"
    )

    pending_courseworks = sum(1 for item in courseworks if item.status == "NOT_STARTED")

    failed_courseworks = sum(1 for item in courseworks if item.status == "FAILED")

    average_progress = round(
        FacultyCoursework.objects.filter(
            phd_student=phd_student,
        ).aggregate(
            average=Avg("progress_percentage")
        )["average"]
        or 0
    )

    coursework_completion_percentage = (
        round(completed_courseworks / total_courseworks * 100)
        if total_courseworks
        else 0
    )

    total_credits_required = (
        getattr(
            phd_program,
            "total_credits_required",
            0,
        )
        or 0
    )

    completed_credits = sum(
        getattr(
            item.coursework,
            "credits",
            0,
        )
        or 0
        for item in courseworks
        if (item.coursework and item.status == "COMPLETED")
    )

    assigned_credits = sum(
        getattr(
            item.coursework,
            "credits",
            0,
        )
        or 0
        for item in courseworks
        if item.coursework
    )

    remaining_credits = max(
        0,
        total_credits_required - completed_credits,
    )

    credit_completion_percentage = (
        min(
            100,
            round(completed_credits / total_credits_required * 100),
        )
        if total_credits_required
        else 0
    )

    total_examinations = len(examinations)

    scheduled_examinations = sum(
        1 for item in examinations if item.status == "SCHEDULED"
    )

    completed_examinations = sum(
        1 for item in examinations if item.status == "COMPLETED"
    )

    cancelled_examinations = sum(
        1 for item in examinations if item.status == "CANCELLED"
    )

    draft_examinations = sum(1 for item in examinations if item.status == "DRAFT")

    passed_examinations = sum(1 for item in examinations if item.result == "PASS")

    failed_examinations = sum(1 for item in examinations if item.result == "FAIL")

    pending_examinations = sum(1 for item in examinations if item.result == "PENDING")

    examination_success_percentage = (
        round(passed_examinations / (passed_examinations + failed_examinations) * 100)
        if (passed_examinations + failed_examinations)
        else 0
    )

    total_milestones = len(milestones)

    completed_milestones = sum(1 for item in milestones if item.status == "COMPLETED")

    pending_milestones = sum(1 for item in milestones if item.status == "PENDING")

    in_progress_milestones = sum(
        1 for item in milestones if item.status == "IN_PROGRESS"
    )

    milestone_completion_percentage = (
        round(completed_milestones / total_milestones * 100) if total_milestones else 0
    )

    total_publications = len(publications)

    indexed_publications = sum(
        1 for item in publications if item.indexed_status == "INDEXED"
    )

    under_review_publications = sum(
        1 for item in publications if item.indexed_status == "UNDER_REVIEW"
    )

    not_indexed_publications = sum(
        1 for item in publications if item.indexed_status == "NOT_INDEXED"
    )

    publication_indexing_percentage = (
        round(indexed_publications / total_publications * 100)
        if total_publications
        else 0
    )

    total_reviews = len(reviews)

    satisfactory_reviews = sum(1 for item in reviews if item.status == "SATISFACTORY")

    needs_improvement_reviews = sum(
        1 for item in reviews if item.status == "NEEDS_IMPROVEMENT"
    )

    unsatisfactory_reviews = sum(
        1 for item in reviews if item.status == "UNSATISFACTORY"
    )

    review_success_percentage = (
        round(satisfactory_reviews / total_reviews * 100) if total_reviews else 0
    )

    candidacy_status = candidacy.candidacy_status if candidacy else "PENDING"

    candidacy_approved = candidacy_status == "APPROVED"

    candidacy_date = (
        getattr(
            candidacy,
            "candidacy_date",
            None,
        )
        if candidacy
        else None
    )

    proposal_status = (
        getattr(
            proposal,
            "result",
            "PENDING",
        )
        if proposal
        else "PENDING"
    )

    proposal_title = (
        getattr(
            proposal,
            "proposal_title",
            None,
        )
        if proposal
        else None
    )

    dissertation_status = (
        getattr(
            dissertation,
            "status",
            "DRAFT",
        )
        if dissertation
        else "DRAFT"
    )

    dissertation_title = (
        getattr(
            dissertation,
            "dissertation_title",
            None,
        )
        if dissertation
        else None
    )

    dissertation_version = (
        getattr(
            dissertation,
            "current_version",
            None,
        )
        if dissertation
        else None
    )

    dissertation_submission_date = (
        getattr(
            dissertation,
            "submission_date",
            None,
        )
        if dissertation
        else None
    )

    graduation_date = (
        getattr(
            graduation,
            "graduation_date",
            None,
        )
        if graduation
        else None
    )

    dissertation_accepted = (
        getattr(
            graduation,
            "dissertation_accepted",
            False,
        )
        if graduation
        else False
    )

    final_gpa = (
        getattr(
            graduation,
            "final_gpa",
            None,
        )
        if graduation
        else None
    )

    admission_date = getattr(
        phd_student,
        "admission_date",
        None,
    )

    admission_year = (
        admission_date.year
        if admission_date
        else getattr(
            phd_student,
            "admission_year",
            None,
        )
    )

    current_year = date.today().year

    years_in_program = (
        max(
            0,
            current_year - admission_year,
        )
        if admission_year
        else 0
    )

    candidacy_requirements = {
        "advisor_assigned": bool(advisor),
        "committee_approved": bool(
            committee and committee.approval_status == "APPROVED"
        ),
        "coursework_completed": bool(
            total_credits_required and completed_credits >= total_credits_required
        ),
        "examination_passed": any(item.result == "PASS" for item in examinations),
        "proposal_approved": bool(proposal and proposal.result == "APPROVED"),
    }

    candidacy_requirements_total = len(candidacy_requirements)

    candidacy_requirements_completed = sum(
        1 for item in candidacy_requirements.values() if item
    )

    candidacy_readiness = (
        round(candidacy_requirements_completed / candidacy_requirements_total * 100)
        if candidacy_requirements_total
        else 0
    )

    candidacy_eligible = all(candidacy_requirements.values())

    stage_items = [
        {
            "name": "Admission",
            "icon": "bi bi-mortarboard",
            "completed": bool(admission_date),
        },
        {
            "name": "Advisor",
            "icon": "bi bi-person-check",
            "completed": bool(advisor),
        },
        {
            "name": "Committee",
            "icon": "bi bi-people",
            "completed": bool(committee and committee.approval_status == "APPROVED"),
        },
        {
            "name": "Coursework",
            "icon": "bi bi-journal-text",
            "completed": bool(
                total_credits_required and completed_credits >= total_credits_required
            ),
        },
        {
            "name": "Candidacy",
            "icon": "bi bi-award",
            "completed": candidacy_approved,
        },
        {
            "name": "Proposal",
            "icon": "bi bi-file-earmark-text",
            "completed": bool(proposal and proposal.result == "APPROVED"),
        },
        {
            "name": "Research",
            "icon": "bi bi-microscope",
            "completed": bool(total_publications or in_progress_milestones),
        },
        {
            "name": "Dissertation",
            "icon": "bi bi-file-earmark-richtext",
            "completed": bool(
                dissertation
                and dissertation_status
                in [
                    "SUBMITTED",
                    "UNDER_REVIEW",
                    "APPROVED",
                ]
            ),
        },
        {
            "name": "Defense",
            "icon": "bi bi-gavel",
            "completed": bool(
                defense
                and getattr(
                    defense,
                    "result",
                    None,
                )
                == "PASS"
            ),
        },
        {
            "name": "Completion",
            "icon": "bi bi-check-circle",
            "completed": bool(graduation),
        },
    ]

    completed_stage_count = sum(1 for item in stage_items if item["completed"])

    total_stage_count = len(stage_items)

    overall_progress = (
        round(completed_stage_count / total_stage_count * 100)
        if total_stage_count
        else 0
    )

    latest_coursework = courseworks[0] if courseworks else None

    latest_exam = examinations[0] if examinations else None

    latest_publication = publications[0] if publications else None

    latest_review = reviews[0] if reviews else None

    latest_milestone = milestones[0] if milestones else None

    next_milestone = next(
        (item for item in milestones if item.status != "COMPLETED"),
        None,
    )

    today = date.today()

    future_exams = [
        item
        for item in examinations
        if (
            getattr(
                item,
                "exam_date",
                None,
            )
            and item.exam_date >= today
            and item.status
            not in [
                "CANCELLED",
                "COMPLETED",
            ]
        )
    ]

    upcoming_exam = (
        sorted(
            future_exams,
            key=lambda item: (
                item.exam_date,
                getattr(
                    item,
                    "start_time",
                    time.min,
                )
                or time.min,
            ),
        )[0]
        if future_exams
        else None
    )

    actions = []

    if not committee:
        actions.append(
            {
                "priority": "critical",
                "title": "Doctoral Committee Required",
                "description": ("A doctoral committee " "has not been formed."),
                "icon": "bi bi-people",
                "action": "Review Committee",
            }
        )
    elif committee.approval_status != "APPROVED":
        actions.append(
            {
                "priority": "high",
                "title": "Committee Approval Pending",
                "description": ("The doctoral committee " "is awaiting approval."),
                "icon": "bi bi-hourglass-split",
                "action": "Review Committee",
            }
        )

    if total_credits_required and completed_credits < total_credits_required:
        actions.append(
            {
                "priority": "high",
                "title": "Coursework Incomplete",
                "description": (
                    f"{remaining_credits} credits "
                    "remain to complete the "
                    "program requirement."
                ),
                "icon": "bi bi-journal-text",
                "action": "Review Coursework",
            }
        )

    if not any(item.result == "PASS" for item in examinations):
        actions.append(
            {
                "priority": "high",
                "title": "Examination Pending",
                "description": (
                    "A passed doctoral " "examination is not yet recorded."
                ),
                "icon": "bi bi-clipboard-check",
                "action": "Review Examination",
            }
        )

    if not proposal:
        actions.append(
            {
                "priority": "medium",
                "title": "Proposal Not Submitted",
                "description": ("The dissertation proposal " "has not been submitted."),
                "icon": "bi bi-file-earmark-text",
                "action": "Review Proposal",
            }
        )
    elif proposal_status != "APPROVED":
        actions.append(
            {
                "priority": "medium",
                "title": "Proposal Approval Pending",
                "description": ("The dissertation proposal " "is awaiting approval."),
                "icon": "bi bi-file-earmark-check",
                "action": "Review Proposal",
            }
        )

    if not candidacy_approved and not candidacy_eligible:
        actions.append(
            {
                "priority": "medium",
                "title": "Candidacy Requirements",
                "description": (
                    f"{candidacy_requirements_completed} "
                    f"of {candidacy_requirements_total} "
                    "tracked requirements completed."
                ),
                "icon": "bi bi-award",
                "action": "Review Candidacy",
            }
        )

    if dissertation and dissertation_status == "DRAFT":
        actions.append(
            {
                "priority": "low",
                "title": "Dissertation In Progress",
                "description": ("The dissertation is currently " "in draft stage."),
                "icon": "bi bi-file-earmark-richtext",
                "action": "Review Dissertation",
            }
        )

    insights = []

    if candidacy_approved:
        insights.append("Doctoral candidacy has been approved.")

    if committee and committee.approval_status == "APPROVED":
        insights.append("The doctoral committee is " "fully established and approved.")

    if credit_completion_percentage >= 75:
        insights.append(
            "Coursework completion is above " "75% of the required credits."
        )

    if proposal and proposal_status == "APPROVED":
        insights.append("The dissertation proposal has " "received approval.")

    if total_publications:
        insights.append(
            f"{total_publications} research " "publication record(s) are available."
        )

    if not insights:
        insights.append(
            "Continue monitoring the advisee's " "academic and research progress."
        )

    recent_activities = []

    if candidacy:
        recent_activities.append(
            {
                "title": "Candidacy Status",
                "description": (
                    "Doctoral candidacy is "
                    f"{candidacy_status.replace('_', ' ').title()}."
                ),
                "date": candidacy_date,
                "icon": "bi bi-award",
            }
        )

    if proposal:
        recent_activities.append(
            {
                "title": "Research Proposal",
                "description": (
                    f"{proposal_title or 'Proposal'} "
                    f"is {proposal_status.replace('_', ' ').title()}."
                ),
                "date": getattr(
                    proposal,
                    "created_at",
                    None,
                ),
                "icon": "bi bi-file-earmark-text",
            }
        )

    if dissertation:
        recent_activities.append(
            {
                "title": "Dissertation",
                "description": (
                    f"{dissertation_title or 'Dissertation'} "
                    f"is {dissertation_status.replace('_', ' ').title()}."
                ),
                "date": dissertation_submission_date,
                "icon": "bi bi-file-earmark-richtext",
            }
        )

    if committee:
        recent_activities.append(
            {
                "title": "Doctoral Committee",
                "description": (
                    "Doctoral committee " f"is {committee.approval_status.title()}."
                ),
                "date": getattr(
                    committee,
                    "formation_date",
                    None,
                ),
                "icon": "bi bi-people",
            }
        )

    if upcoming_exam:
        recent_activities.append(
            {
                "title": "Upcoming Examination",
                "description": (
                    f"{getattr(upcoming_exam, 'title', 'Doctoral Examination')} "
                    f"is scheduled for "
                    f"{upcoming_exam.exam_date.strftime('%b %d, %Y')}."
                ),
                "date": upcoming_exam.exam_date,
                "icon": "bi bi-calendar-event",
            }
        )

    for item in milestones[:4]:
        recent_activities.append(
            {
                "title": "Research Milestone",
                "description": (
                    f"{getattr(item, 'milestone_name', 'Milestone')} "
                    f"is {item.status.replace('_', ' ').title()}."
                ),
                "date": getattr(
                    item,
                    "completion_date",
                    None,
                ),
                "icon": "bi bi-flag",
            }
        )

    for item in publications[:3]:
        recent_activities.append(
            {
                "title": "Research Publication",
                "description": (
                    getattr(
                        item,
                        "title",
                        "Publication",
                    )
                ),
                "date": getattr(
                    item,
                    "publication_date",
                    None,
                ),
                "icon": "bi bi-journal-richtext",
            }
        )

    def normalize_activity_date(value):
        if value is None:
            return None

        if isinstance(value, datetime):
            if timezone.is_naive(value):
                return timezone.make_aware(
                    value,
                    timezone.get_current_timezone(),
                )
            return value

        if isinstance(value, date):
            return timezone.make_aware(
                datetime.combine(
                    value,
                    time.min,
                ),
                timezone.get_current_timezone(),
            )

        return None

    for item in recent_activities:
        item["date"] = normalize_activity_date(item.get("date"))

    recent_activities = sorted(
        recent_activities,
        key=lambda item: (
            item["date"] is not None,
            item["date"]
            or timezone.make_aware(
                datetime.min,
                timezone.get_current_timezone(),
            ),
        ),
        reverse=True,
    )[:10]

    context = {
        "faculty": faculty,
        "phd_student": phd_student,
        "advisor": advisor,
        "phd_program": phd_program,
        "department": department,
        "committee": committee,
        "chair_faculty": chair_faculty,
        "committee_members": committee_members,
        "committee_member_count": len(committee_members),
        "candidacy": candidacy,
        "candidacy_status": candidacy_status,
        "candidacy_date": candidacy_date,
        "candidacy_approved": candidacy_approved,
        "candidacy_eligible": candidacy_eligible,
        "candidacy_readiness": candidacy_readiness,
        "candidacy_requirements": candidacy_requirements,
        "candidacy_requirements_completed": (candidacy_requirements_completed),
        "candidacy_requirements_total": (candidacy_requirements_total),
        "proposal": proposal,
        "proposal_status": proposal_status,
        "proposal_title": proposal_title,
        "dissertation": dissertation,
        "dissertation_status": dissertation_status,
        "dissertation_title": dissertation_title,
        "dissertation_version": dissertation_version,
        "dissertation_submission_date": (dissertation_submission_date),
        "graduation": graduation,
        "graduation_date": graduation_date,
        "dissertation_accepted": dissertation_accepted,
        "final_gpa": final_gpa,
        "defense": defense,
        "admission_date": admission_date,
        "admission_year": admission_year,
        "years_in_program": years_in_program,
        "milestones": milestones,
        "total_milestones": total_milestones,
        "completed_milestones": completed_milestones,
        "pending_milestones": pending_milestones,
        "in_progress_milestones": in_progress_milestones,
        "milestone_completion_percentage": (milestone_completion_percentage),
        "latest_milestone": latest_milestone,
        "next_milestone": next_milestone,
        "publications": publications,
        "total_publications": total_publications,
        "indexed_publications": indexed_publications,
        "under_review_publications": (under_review_publications),
        "not_indexed_publications": (not_indexed_publications),
        "publication_indexing_percentage": (publication_indexing_percentage),
        "latest_publication": latest_publication,
        "reviews": reviews,
        "total_reviews": total_reviews,
        "satisfactory_reviews": satisfactory_reviews,
        "needs_improvement_reviews": (needs_improvement_reviews),
        "unsatisfactory_reviews": (unsatisfactory_reviews),
        "review_success_percentage": (review_success_percentage),
        "latest_review": latest_review,
        "courseworks": courseworks,
        "coursework_list": courseworks,
        "total_courseworks": total_courseworks,
        "completed_courseworks": completed_courseworks,
        "in_progress_courseworks": in_progress_courseworks,
        "pending_courseworks": pending_courseworks,
        "not_started_courseworks": pending_courseworks,
        "failed_courseworks": failed_courseworks,
        "average_progress": average_progress,
        "average_coursework_progress": (average_progress),
        "coursework_completion_percentage": (coursework_completion_percentage),
        "total_credits_required": (total_credits_required),
        "completed_credits": completed_credits,
        "assigned_credits": assigned_credits,
        "remaining_credits": remaining_credits,
        "credit_completion_percentage": (credit_completion_percentage),
        "latest_coursework": latest_coursework,
        "examinations": examinations,
        "examination_list": examinations,
        "total_examinations": total_examinations,
        "scheduled_examinations": scheduled_examinations,
        "completed_examinations": completed_examinations,
        "cancelled_examinations": cancelled_examinations,
        "draft_examinations": draft_examinations,
        "passed_examinations": passed_examinations,
        "failed_examinations": failed_examinations,
        "pending_examinations": pending_examinations,
        "examination_success_percentage": (examination_success_percentage),
        "latest_exam": latest_exam,
        "upcoming_exam": upcoming_exam,
        "stage_items": stage_items,
        "completed_stage_count": completed_stage_count,
        "total_stage_count": total_stage_count,
        "overall_progress": overall_progress,
        "recent_activities": recent_activities,
        "actions": actions,
        "insights": insights,
    }

    return render(
        request,
        "leo/PhD/advisee_workspace.html",
        context,
    )


@login_required
def faculty_advisor_message_list(request, uuid):
    faculty = get_faculty_or_404(
        uuid,
        request.user,
    )

    if request.method == "POST":
        phd_student_id = request.POST.get("phd_student_id")
        message_text = request.POST.get("message", "").strip()
        attachments = request.FILES.getlist("attachments")

        if not phd_student_id:
            return JsonResponse(
                {
                    "success": False,
                    "error": "PhD student is required.",
                },
                status=400,
            )

        phd_student = get_object_or_404(
            PhDStudent,
            phd_student_id=phd_student_id,
            advisor=faculty,
        )

        if not message_text and not attachments:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Message or attachment is required.",
                },
                status=400,
            )

        chat_message = AdvisorStudentMessage.objects.create(
            phd_student=phd_student,
            advisor=faculty,
            sender_role="ADVISOR",
            message=message_text or None,
            is_read=False,
            is_full_crud=False,
        )

        attachment_data = []

        for uploaded_file in attachments:
            file_record = AdvisorStudentMessageAttachment.objects.create(
                message=chat_message,
                attachment=uploaded_file,
                original_name=uploaded_file.name,
                file_size=uploaded_file.size,
                content_type=getattr(
                    uploaded_file,
                    "content_type",
                    None,
                ),
                is_full_crud=False,
            )

            attachment_data.append(
                {
                    "attachment_id": file_record.attachment_id,
                    "attachment_url": file_record.attachment.url,
                    "attachment_name": file_record.original_name,
                    "file_size": file_record.file_size,
                    "content_type": file_record.content_type or "",
                }
            )

        created_at = timezone.localtime(chat_message.created_at)

        return JsonResponse(
            {
                "success": True,
                "message_id": chat_message.message_id,
                "sender_role": chat_message.sender_role,
                "phd_student_id": chat_message.phd_student_id,
                "message": chat_message.message or "",
                "attachments": attachment_data,
                "created_at": created_at.strftime("%I:%M %p"),
                "created_date": created_at.strftime("%Y-%m-%d"),
            }
        )

    if request.GET.get("chat_poll") == "1":
        phd_student_id = request.GET.get("phd_student_id")
        after_id = request.GET.get("after_id", "0")
        mark_read = request.GET.get("mark_read") == "1"

        try:
            after_id = int(after_id)
        except (TypeError, ValueError):
            after_id = 0

        if not phd_student_id:
            return JsonResponse(
                {
                    "success": False,
                    "error": "PhD student is required.",
                },
                status=400,
            )

        phd_student = get_object_or_404(
            PhDStudent,
            phd_student_id=phd_student_id,
            advisor=faculty,
        )

        if mark_read:
            AdvisorStudentMessage.objects.filter(
                phd_student=phd_student,
                advisor=faculty,
                sender_role="STUDENT",
                is_read=False,
            ).update(
                is_read=True,
                read_at=timezone.now(),
            )

        messages = (
            AdvisorStudentMessage.objects.filter(
                phd_student=phd_student,
                advisor=faculty,
                message_id__gt=after_id,
            )
            .prefetch_related("attachments")
            .order_by("message_id")
        )

        unread_count = AdvisorStudentMessage.objects.filter(
            phd_student=phd_student,
            advisor=faculty,
            sender_role="STUDENT",
            is_read=False,
        ).count()

        message_data = []

        for message in messages:
            attachments = []

            for attachment in message.attachments.all():
                attachments.append(
                    {
                        "attachment_id": attachment.attachment_id,
                        "attachment_url": attachment.attachment.url,
                        "attachment_name": attachment.original_name,
                        "file_size": attachment.file_size,
                        "content_type": attachment.content_type or "",
                    }
                )

            created_at = timezone.localtime(message.created_at)

            message_data.append(
                {
                    "message_id": message.message_id,
                    "sender_role": message.sender_role,
                    "phd_student_id": message.phd_student_id,
                    "message": message.message or "",
                    "attachments": attachments,
                    "created_at": created_at.strftime("%I:%M %p"),
                    "created_date": created_at.strftime("%Y-%m-%d"),
                }
            )

        return JsonResponse(
            {
                "success": True,
                "messages": message_data,
                "unread_count": unread_count,
            }
        )

    phd_students = (
        PhDStudent.objects.filter(
            advisor=faculty,
        )
        .select_related(
            "student",
            "student__user",
            "phd_program",
            "phd_program__department",
            "advisor",
            "advisor__user",
        )
        .order_by(
            "student__user__last_name",
            "student__user__first_name",
        )
    )

    messages_queryset = (
        AdvisorStudentMessage.objects.filter(
            phd_student__advisor=faculty,
            advisor=faculty,
        )
        .select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
            "advisor",
            "advisor__user",
        )
        .prefetch_related(
            "attachments",
        )
        .order_by("created_at")
    )

    message_map = {}

    for message in messages_queryset:
        message_map.setdefault(
            message.phd_student_id,
            [],
        ).append(message)

    advisee_data = []

    for phd_student in phd_students:
        student_messages = message_map.get(
            phd_student.phd_student_id,
            [],
        )

        unread_count = sum(
            1
            for message in student_messages
            if message.sender_role == "STUDENT" and not message.is_read
        )

        last_message = student_messages[-1] if student_messages else None

        advisee_data.append(
            {
                "phd_student": phd_student,
                "messages": student_messages,
                "unread_count": unread_count,
                "last_message": last_message,
            }
        )

    context = {
        "faculty": faculty,
        "phd_students": phd_students,
        "advisee_data": advisee_data,
        "total_advisees": phd_students.count(),
    }

    return render(
        request,
        "leo/Messages/faculty_advisor_message_list.html",
        context,
    )


## Leo's Code End ##
