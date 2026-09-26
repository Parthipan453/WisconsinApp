##### Leo's Code Start #####

############################################################
# Standard Library Imports
############################################################
from datetime import date, datetime, time

############################################################
# Django Core Imports
############################################################
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import Avg, Count, Prefetch, Q, Sum
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from Students.Leo_Student.models import ResearchPublication
from .forms import ResearchPublicationForm

############################################################
# Admin App Imports
############################################################
from Admin.bela_admin.models import Department

############################################################
# Faculty App Imports
############################################################
from Faculty.leo.forms import CourseworkSubmissionForm

from Faculty.leo.models import (
    AdvisorResearchAdvice,
    CourseworkSubmission,
    DissertationAdvisorAdvice,
    DissertationApproval,
    FacultyCoursework,
    ResearchMilestone,
    ResearchMilestoneEvaluation,
    ResearchMilestoneSubmission,
    ResearchMilestone,
    FinalDissertationAdvisorEvaluation,
    FinalDissertationCommitteeEvaluation,
    AdvisorStudentMessage,
    AdvisorStudentMessageAttachment,
)

############################################################
# Students App Imports
############################################################
from Students.models import (
    AnnualProgressReview,
    CommitteeMember,
    Dissertation,
    DissertationDefense,
    DissertationProposal,
    DissertationProposalResubmissionRequest,
    DoctoralCandidacy,
    DoctoralCommittee,
    Graduation,
    PhD,
    PhDStudent,
    PhDMilestone,
    PreliminaryExamination,
    ResearchPublication,
    StudentProfile,
    FinalDissertationSubmission,
    DefenseLocation,
)

############################################################
# Student Forms
############################################################
from Students.Leo_Student.forms import (
    ResearchMilestoneSubmissionForm,
    FinalDissertationSubmissionForm,
)
from Staff.models import Notification
from notifications.utils import send_notification

############################################################
# Local Forms
############################################################
from .forms import (
    DissertationProposalForm,
)

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render

from Faculty.leo.models import (
    ResearchMilestone,
    ResearchMilestoneSubmission,
)

from .forms import ResearchMilestoneSubmissionForm
from .models import PhDStudent


@login_required
def phd_dashboard(request, uuid):
    from datetime import datetime, time, date
    from collections import defaultdict

    from django.shortcuts import get_object_or_404, render
    from django.utils import timezone
    from django.db.models import Prefetch

    student = get_object_or_404(
        StudentProfile,
        user__uuid=uuid,
        user=request.user,
    )

    phd_student = (
        PhDStudent.objects.select_related(
            "student",
            "student__user",
            "advisor",
            "advisor__user",
            "advisor__faculty_rank",
            "advisor__department",
            "phd_program",
            "phd_program__department",
            "doctoral_committee",
            "doctoral_committee__chair_faculty",
            "doctoral_committee__chair_faculty__user",
            "doctoral_committee__chair_faculty__faculty_rank",
            "doctoral_committee__chair_faculty__department",
            "doctoral_candidacy",
            "graduation",
        )
        .prefetch_related(
            Prefetch(
                "doctoral_committee__committee_members",
                queryset=CommitteeMember.objects.select_related(
                    "faculty",
                    "faculty__user",
                    "faculty__faculty_rank",
                    "faculty__department",
                ).order_by("role"),
            ),
            Prefetch(
                "research_milestones",
                queryset=ResearchMilestone.objects.order_by(
                    "sequence_number",
                    "milestone_id",
                ),
            ),
            Prefetch(
                "research_publications",
                queryset=ResearchPublication.objects.order_by("-publication_date"),
            ),
            Prefetch(
                "annual_progress_reviews",
                queryset=AnnualProgressReview.objects.order_by("-review_year"),
            ),
            Prefetch(
                "faculty_courseworks",
                queryset=FacultyCoursework.objects.select_related(
                    "coursework",
                    "program",
                    "submission__evaluation",
                ).order_by("-faculty_coursework_id"),
            ),
            Prefetch(
                "preliminary_examinations",
                queryset=PreliminaryExamination.objects.order_by(
                    "-exam_date",
                    "-start_time",
                ),
            ),
        )
        .filter(student=student)
        .first()
    )

    if phd_student is None:
        empty_context = {
            "student": student,
            "phd_student": None,
            "advisor": None,
            "advisor_name": None,
            "advisor_department": None,
            "committee": None,
            "chair_faculty": None,
            "committee_members": [],
            "committee_member_count": 0,
            "phd_program": None,
            "department": None,
            "candidacy": None,
            "candidacy_status": "PENDING",
            "candidacy_date": None,
            "candidacy_approved": False,
            "candidacy_eligible": False,
            "candidacy_readiness": 0,
            "candidacy_requirements": {},
            "candidacy_requirements_completed": 0,
            "candidacy_requirements_total": 5,
            "proposal": None,
            "proposal_status": "PENDING",
            "proposal_title": None,
            "dissertation": None,
            "dissertation_status": "DRAFT",
            "dissertation_title": None,
            "dissertation_version": None,
            "dissertation_submission_date": None,
            "graduation": None,
            "graduation_date": None,
            "dissertation_accepted": False,
            "final_gpa": None,
            "admission_year": None,
            "years_in_program": 0,
            "research_milestones": [],
            "research_publications": [],
            "total_milestones": 0,
            "completed_milestones": 0,
            "pending_milestones": 0,
            "in_progress_milestones": 0,
            "milestone_completion_percentage": 0,
            "total_courseworks": 0,
            "completed_courseworks": 0,
            "in_progress_courseworks": 0,
            "failed_courseworks": 0,
            "not_started_courseworks": 0,
            "coursework_completion_percentage": 0,
            "total_credits_required": 0,
            "completed_credits": 0,
            "assigned_credits": 0,
            "remaining_credits": 0,
            "credit_completion_percentage": 0,
            "total_exams": 0,
            "scheduled_exams": 0,
            "completed_exams": 0,
            "cancelled_exams": 0,
            "draft_exams": 0,
            "passed_exams": 0,
            "failed_exams": 0,
            "pending_exams": 0,
            "exam_success_percentage": 0,
            "total_publications": 0,
            "indexed_publications": 0,
            "under_review_publications": 0,
            "not_indexed_publications": 0,
            "publication_indexing_percentage": 0,
            "total_reviews": 0,
            "satisfactory_reviews": 0,
            "needs_improvement_reviews": 0,
            "unsatisfactory_reviews": 0,
            "review_success_percentage": 0,
            "overall_progress": 0,
            "completed_stage_count": 0,
            "total_stage_count": 10,
            "stages": [],
            "stage_items": [],
            "stage_completed": {},
            "stage_icons": {},
            "latest_coursework": None,
            "latest_exam": None,
            "latest_publication": None,
            "latest_publication_indexed_status": None,
            "latest_publication_date": None,
            "latest_publication_journal": "",
            "latest_review": None,
            "latest_milestone": None,
            "latest_milestone_progress": 0,
            "latest_milestone_status": "PENDING",
            "latest_milestone_expected_date": None,
            "latest_milestone_updated_date": None,
            "next_milestone": None,
            "upcoming_exam": None,
            "recent_activities": [],
            "actions": [],
            "insights": ["Your PhD profile has not been created yet."],
            "chart_labels_progress": [],
            "chart_data_progress": [],
            "chart_data_progress_values": [],
            "chart_labels_coursework": [],
            "chart_data_coursework": [],
            "chart_labels_exams": [],
            "chart_data_exams": [],
            "chart_labels_publications": [],
            "chart_data_publications": [],
            "chart_labels_milestones": [],
            "chart_data_milestones": [],
            "chart_labels_reviews": [],
            "chart_data_reviews": [],
            "chart_labels_credits": [],
            "chart_data_credits": [],
            "chart_labels_yearly": [],
            "chart_data_yearly": [],
        }

        return render(
            request,
            "Leo_Student/phd_dashboard.html",
            empty_context,
        )

    advisor = phd_student.advisor

    committee = getattr(
        phd_student,
        "doctoral_committee",
        None,
    )

    chair_faculty = None
    committee_members = []

    if committee:
        chair_faculty = committee.chair_faculty
        committee_members = list(committee.committee_members.all())

    phd_program = phd_student.phd_program
    department = phd_program.department if phd_program else None

    candidacy = getattr(
        phd_student,
        "doctoral_candidacy",
        None,
    )

    graduation = getattr(
        phd_student,
        "graduation",
        None,
    )

    graduation_status = graduation.status if graduation else None

    proposal = getattr(
        phd_student,
        "dissertation_proposal",
        None,
    )

    latest_final_dissertation_submission = (
        FinalDissertationSubmission.objects.filter(
            phd_student=phd_student,
        )
        .order_by(
            "-submission_number",
            "-created_at",
        )
        .first()
    )

    dissertation_history = FinalDissertationSubmission.objects.filter(
        phd_student=phd_student,
    ).order_by(
        "-submission_number",
        "-created_at",
    )

    try:
        defense = phd_student.dissertation_defense
    except Exception:
        defense = None

    milestones = list(phd_student.research_milestones.all())

    publications = list(phd_student.research_publications.all())

    reviews = list(phd_student.annual_progress_reviews.all())

    courseworks = list(phd_student.faculty_courseworks.all())

    examinations = list(phd_student.preliminary_examinations.all())

    research_milestones = milestones
    research_publications = publications

    total_milestones = len(milestones)

    completed_milestones = sum(
        1 for milestone in milestones if milestone.status == "COMPLETED"
    )

    pending_milestones = sum(
        1 for milestone in milestones if milestone.status == "PENDING"
    )

    in_progress_milestones = sum(
        1 for milestone in milestones if milestone.status == "IN_PROGRESS"
    )

    milestone_completion_percentage = (
        round(completed_milestones / total_milestones * 100) if total_milestones else 0
    )

    total_courseworks = len(courseworks)

    completed_courseworks = sum(
        1 for coursework in courseworks if coursework.status == "COMPLETED"
    )

    in_progress_courseworks = sum(
        1 for coursework in courseworks if coursework.status == "IN_PROGRESS"
    )

    failed_courseworks = sum(
        1 for coursework in courseworks if coursework.status == "FAILED"
    )

    not_started_courseworks = sum(
        1 for coursework in courseworks if coursework.status == "NOT_STARTED"
    )

    coursework_completion_percentage = (
        round(completed_courseworks / total_courseworks * 100)
        if total_courseworks
        else 0
    )

    total_credits_required = phd_program.total_credits_required if phd_program else 0

    completed_credits = sum(
        coursework.coursework.credits
        for coursework in courseworks
        if coursework.coursework and coursework.status == "COMPLETED"
    )

    assigned_credits = sum(
        coursework.coursework.credits
        for coursework in courseworks
        if coursework.coursework
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

    total_exams = len(examinations)

    scheduled_exams = sum(1 for exam in examinations if exam.status == "SCHEDULED")

    completed_exams = sum(1 for exam in examinations if exam.status == "COMPLETED")

    cancelled_exams = sum(1 for exam in examinations if exam.status == "CANCELLED")

    draft_exams = sum(1 for exam in examinations if exam.status == "DRAFT")

    passed_exams = sum(1 for exam in examinations if exam.result == "PASS")

    failed_exams = sum(1 for exam in examinations if exam.result == "FAIL")

    pending_exams = sum(1 for exam in examinations if exam.result == "PENDING")

    exam_success_percentage = (
        round(passed_exams / (passed_exams + failed_exams) * 100)
        if passed_exams + failed_exams
        else 0
    )

    total_publications = len(publications)

    indexed_publications = sum(
        1 for publication in publications if publication.indexed_status == "INDEXED"
    )

    under_review_publications = sum(
        1
        for publication in publications
        if publication.indexed_status == "UNDER_REVIEW"
    )

    not_indexed_publications = sum(
        1 for publication in publications if publication.indexed_status == "NOT_INDEXED"
    )

    publication_indexing_percentage = (
        round(indexed_publications / total_publications * 100)
        if total_publications
        else 0
    )

    total_reviews = len(reviews)

    satisfactory_reviews = sum(
        1 for review in reviews if review.status == "SATISFACTORY"
    )

    needs_improvement_reviews = sum(
        1 for review in reviews if review.status == "NEEDS_IMPROVEMENT"
    )

    unsatisfactory_reviews = sum(
        1 for review in reviews if review.status == "UNSATISFACTORY"
    )

    review_success_percentage = (
        round(satisfactory_reviews / total_reviews * 100) if total_reviews else 0
    )

    candidacy_status = candidacy.candidacy_status if candidacy else "PENDING"

    candidacy_date = candidacy.candidacy_date if candidacy else None

    candidacy_approved = candidacy_status == "APPROVED"

    admission_year = (
        phd_student.admission_date.year if phd_student.admission_date else None
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

    proposal_status = proposal.result if proposal else "PENDING"

    proposal_title = proposal.proposal_title if proposal else None

    dissertation_status = (
        latest_final_dissertation_submission.status
        if latest_final_dissertation_submission
        else "DRAFT"
    )

    dissertation_title = (
        latest_final_dissertation_submission.dissertation_title
        if latest_final_dissertation_submission
        else None
    )

    dissertation_version = (
        latest_final_dissertation_submission.version
        if latest_final_dissertation_submission
        else None
    )

    dissertation_submission_date = (
        getattr(
            latest_final_dissertation_submission,
            "submitted_at",
            None,
        )
        or getattr(
            latest_final_dissertation_submission,
            "submission_date",
            None,
        )
        or getattr(
            latest_final_dissertation_submission,
            "created_at",
            None,
        )
        if latest_final_dissertation_submission
        else None
    )

    graduation_date = graduation.graduation_date if graduation else None

    dissertation_accepted = graduation.dissertation_accepted if graduation else False

    final_gpa = graduation.final_gpa if graduation else None

    graduation_status = graduation.status if graduation else None

    graduation_time = graduation.graduation_time if graduation else None

    graduation_location = graduation.graduation_location if graduation else None

    degree_awarded = graduation.degree_awarded if graduation else None

    defense_passed = graduation.defense_passed if graduation else False

    graduation_created_at = graduation.created_at if graduation else None

    graduation_created_by = graduation.created_by if graduation else None

    chair_approved_by = graduation.chair_approved_by if graduation else None

    chair_approved_at = graduation.chair_approved_at if graduation else None

    chair_congratulations_note = (
        graduation.chair_congratulations_note if graduation else None
    )

    graduation_completed_at = graduation.completed_at if graduation else None

    candidacy_requirements = {
        "advisor_assigned": bool(advisor),
        "committee_approved": bool(
            committee and committee.approval_status == "APPROVED"
        ),
        "coursework_completed": bool(
            total_credits_required > 0 and completed_credits >= total_credits_required
        ),
        "exam_passed": any(exam.result == "PASS" for exam in examinations),
        "proposal_approved": bool(proposal and proposal.result == "APPROVED"),
    }

    doctoral_milestone_status = {
        "admission": bool(phd_student.admission_date),
        "advisor": bool(advisor),
        "committee": bool(committee and committee.approval_status == "APPROVED"),
        "coursework_assigned": total_courseworks > 0,
        "coursework_completed": bool(
            total_credits_required > 0 and completed_credits >= total_credits_required
        ),
        "exam_assigned": total_exams > 0,
        "exam_passed": any(exam.result == "PASS" for exam in examinations),
        "proposal_approved": bool(proposal and proposal.result == "APPROVED"),
        "candidacy_approved": candidacy_approved,
        "annual_progress": bool(reviews),
    }

    doctoral_milestone_completed_count = sum(
        1 for status in doctoral_milestone_status.values() if status
    )

    doctoral_milestone_total_count = len(doctoral_milestone_status)

    doctoral_milestone_completion_percentage = (
        round(doctoral_milestone_completed_count / doctoral_milestone_total_count * 100)
        if doctoral_milestone_total_count
        else 0
    )

    candidacy_requirements_total = len(candidacy_requirements)

    candidacy_requirements_completed = sum(
        1 for requirement in candidacy_requirements.values() if requirement
    )

    candidacy_readiness = (
        round(candidacy_requirements_completed / candidacy_requirements_total * 100)
        if candidacy_requirements_total
        else 0
    )

    candidacy_eligible = all(candidacy_requirements.values())

    stages = [
        "Admission",
        "Advisor",
        "Committee",
        "Coursework",
        "Candidacy",
        "Proposal",
        "Research",
        "Dissertation",
        "Defense",
        "Completion",
    ]

    stage_icons = {
        "Admission": "ti ti-school",
        "Advisor": "ti ti-user-star",
        "Committee": "ti ti-users",
        "Coursework": "ti ti-book-2",
        "Candidacy": "ti ti-award",
        "Proposal": "ti ti-file-description",
        "Research": "ti ti-microscope",
        "Dissertation": "ti ti-file-text",
        "Defense": "ti ti-gavel",
        "Completion": "ti ti-check-circle",
    }

    stage_completed = {
        "Admission": bool(phd_student.admission_date),
        "Advisor": bool(advisor),
        "Committee": bool(committee and committee.approval_status == "APPROVED"),
        "Coursework": bool(
            total_credits_required > 0 and completed_credits >= total_credits_required
        ),
        "Candidacy": candidacy_approved,
        "Proposal": bool(proposal and proposal.result == "APPROVED"),
        "Research": bool(
            milestones
            and all(milestone.status == "COMPLETED" for milestone in milestones)
        ),
        "Dissertation": bool(
            latest_final_dissertation_submission
            and latest_final_dissertation_submission.status == "APPROVED"
        ),
        "Defense": bool(
            defense
            and getattr(
                defense,
                "result",
                None,
            )
            == "PASS"
        ),
        "Completion": bool(graduation),
    }

    stage_items = []

    for stage in stages:
        stage_items.append(
            {
                "name": stage,
                "icon": stage_icons.get(
                    stage,
                    "ti ti-circle",
                ),
                "completed": stage_completed.get(
                    stage,
                    False,
                ),
                "status": (
                    "COMPLETED"
                    if stage_completed.get(
                        stage,
                        False,
                    )
                    else "PENDING"
                ),
            }
        )

    completed_stage_count = sum(1 for value in stage_completed.values() if value)

    total_stage_count = len(stages)

    overall_progress = (
        round(completed_stage_count / total_stage_count * 100)
        if total_stage_count
        else 0
    )

    research_overall_progress = (
        round(
            sum(
                float(milestone.current_progress_percentage or 0)
                for milestone in research_milestones
            )
            / len(research_milestones)
        )
        if research_milestones
        else 0
    )

    research_overall_progress = min(
        max(research_overall_progress, 0),
        100,
    )

    research_completed_for_final_dissertation = bool(
        research_milestones
        and all(milestone.status == "COMPLETED" for milestone in research_milestones)
    )

    coursework_credits_completed = (
        total_credits_required > 0 and completed_credits >= total_credits_required
    )

    qualifying_exam_passed = any(
        exam.exam_type in ["QUALIFYING", "PRELIMINARY"]
        and exam.status == "COMPLETED"
        and exam.result == "PASS"
        and getattr(exam, "is_published", False)
        for exam in examinations
    )

    dissertation_proposal_approved = (
        proposal is not None and proposal.result == "APPROVED"
    )

    candidacy_approved_for_final_dissertation = (
        candidacy is not None and candidacy_status == "APPROVED"
    )

    final_dissertation_eligible = all(
        [
            coursework_credits_completed,
            qualifying_exam_passed,
            dissertation_proposal_approved,
            candidacy_approved_for_final_dissertation,
            research_completed_for_final_dissertation,
        ]
    )

    latest_coursework = courseworks[0] if courseworks else None

    latest_exam = examinations[0] if examinations else None

    latest_review = reviews[0] if reviews else None

    latest_annual_review = latest_review

    annual_review_reviewer = None

    if latest_annual_review:
        reviewer = getattr(
            latest_annual_review,
            "reviewed_by",
            None,
        )

        if reviewer:
            if hasattr(
                reviewer,
                "user",
            ):
                annual_review_reviewer = reviewer.user.get_full_name()
            else:
                annual_review_reviewer = str(reviewer)

    latest_milestone = (
        max(
            milestones,
            key=lambda milestone: (milestone.updated_at or milestone.created_at),
        )
        if milestones
        else None
    )

    latest_publication = (
        max(
            publications,
            key=lambda publication: (
                publication.publication_date
                or getattr(
                    publication,
                    "created_at",
                    None,
                )
                or date.min
            ),
        )
        if publications
        else None
    )

    latest_milestone_progress = (
        float(latest_milestone.current_progress_percentage or 0)
        if latest_milestone
        else 0
    )

    latest_milestone_status = latest_milestone.status if latest_milestone else "PENDING"

    latest_milestone_expected_date = (
        latest_milestone.expected_completion_date if latest_milestone else None
    )

    latest_milestone_updated_date = (
        latest_milestone.updated_at if latest_milestone else None
    )

    latest_publication_indexed_status = (
        latest_publication.indexed_status if latest_publication else None
    )

    latest_publication_date = (
        latest_publication.publication_date if latest_publication else None
    )

    latest_publication_journal = ""

    if latest_publication:
        latest_publication_journal = (
            getattr(
                latest_publication,
                "journal_name",
                None,
            )
            or getattr(
                latest_publication,
                "journal",
                None,
            )
            or getattr(
                latest_publication,
                "publication_venue",
                None,
            )
            or getattr(
                latest_publication,
                "conference_name",
                None,
            )
            or getattr(
                latest_publication,
                "publisher_name",
                None,
            )
            or "Research Publication"
        )

    next_milestone = next(
        (milestone for milestone in milestones if milestone.status != "COMPLETED"),
        None,
    )

    upcoming_exam = None

    today = date.today()

    future_exams = [
        exam
        for exam in examinations
        if getattr(
            exam,
            "exam_date",
            None,
        )
        and exam.exam_date >= today
        and exam.status
        not in [
            "CANCELLED",
            "COMPLETED",
        ]
    ]

    if future_exams:
        upcoming_exam = sorted(
            future_exams,
            key=lambda exam: (
                exam.exam_date,
                getattr(
                    exam,
                    "start_time",
                    time.min,
                )
                or time.min,
            ),
        )[0]

    recent_activities = []

    if advisor:
        advisor_date = getattr(
            phd_student,
            "updated_at",
            getattr(
                phd_student,
                "created_at",
                None,
            ),
        )

        advisor_name = advisor.user.get_full_name()

        recent_activities.append(
            {
                "title": "Advisor Assigned",
                "description": (
                    f"{advisor_name} has been assigned " f"as your research advisor."
                ),
                "date": advisor_date,
                "icon": "ti ti-user-star",
                "color": "primary",
            }
        )

    if committee:
        formation_date = getattr(
            committee,
            "formation_date",
            None,
        )

        chair_name = (
            committee.chair_faculty.user.get_full_name()
            if committee.chair_faculty
            else "Not Assigned"
        )

        recent_activities.append(
            {
                "title": "Doctoral Committee",
                "description": (
                    f"Doctoral committee formed with " f"Dr. {chair_name} as chair."
                ),
                "date": formation_date,
                "icon": "ti ti-users",
                "color": "success",
            }
        )

    if candidacy:
        recent_activities.append(
            {
                "title": "Candidacy Status",
                "description": (
                    f"Doctoral candidacy status is "
                    f"{candidacy_status.replace('_', ' ').title()}."
                ),
                "date": candidacy_date,
                "icon": "ti ti-award",
                "color": "warning",
            }
        )

    if proposal:
        proposal_date = getattr(
            proposal,
            "created_at",
            None,
        )

        recent_activities.append(
            {
                "title": "Research Proposal",
                "description": (
                    f'"{proposal.proposal_title}" '
                    f"is currently "
                    f"{proposal_status.replace('_', ' ').title()}."
                ),
                "date": proposal_date,
                "icon": "ti ti-file-description",
                "color": "warning",
            }
        )

    if latest_final_dissertation_submission:
        dissertation_date = getattr(
            latest_final_dissertation_submission,
            "updated_at",
            None,
        ) or getattr(
            latest_final_dissertation_submission,
            "created_at",
            None,
        )

        recent_activities.append(
            {
                "title": "Final Dissertation Submission",
                "description": (
                    f'"{dissertation_title}" '
                    f"is currently "
                    f"{dissertation_status.replace('_', ' ').title()}."
                ),
                "date": dissertation_date,
                "icon": "ti ti-file-text",
                "color": "danger",
            }
        )

    for coursework in courseworks[:5]:
        coursework_date = getattr(
            coursework,
            "updated_at",
            None,
        )

        coursework_name = (
            getattr(
                coursework.coursework,
                "coursework_name",
                str(coursework.coursework),
            )
            if coursework.coursework
            else "Coursework"
        )

        recent_activities.append(
            {
                "title": "Coursework Activity",
                "description": (
                    f"{coursework_name} is "
                    f"{coursework.status.replace('_', ' ').title()}."
                ),
                "date": coursework_date,
                "icon": "ti ti-book-2",
                "color": "info",
            }
        )

    for exam in examinations[:5]:
        exam_date = getattr(
            exam,
            "exam_date",
            None,
        )

        exam_name = (
            exam.get_exam_type_display()
            if hasattr(
                exam,
                "get_exam_type_display",
            )
            else "Doctoral Examination"
        )

        recent_activities.append(
            {
                "title": "Examination",
                "description": (
                    f"{exam_name} is " f"{exam.status.replace('_', ' ').title()}."
                ),
                "date": exam_date,
                "icon": "ti ti-award",
                "color": "primary",
            }
        )

    for milestone in milestones[:5]:
        milestone_date = getattr(
            milestone,
            "completion_date",
            None,
        )

        recent_activities.append(
            {
                "title": "Milestone",
                "description": (
                    f"{milestone.milestone_title} is "
                    f"{milestone.status.replace('_', ' ').title()}."
                ),
                "date": milestone_date,
                "icon": "ti ti-flag",
                "color": "success",
            }
        )

    for publication in publications[:5]:
        publication_date = getattr(
            publication,
            "publication_date",
            None,
        )

        recent_activities.append(
            {
                "title": "Research Publication",
                "description": (
                    f'"{publication.title}" ' f"was added to your research portfolio."
                ),
                "date": publication_date,
                "icon": "ti ti-file-text",
                "color": "secondary",
            }
        )

    for review in reviews[:5]:
        review_date = getattr(
            review,
            "review_date",
            None,
        )

        recent_activities.append(
            {
                "title": "Annual Progress Review",
                "description": (
                    f"Annual progress review is "
                    f"{review.status.replace('_', ' ').title()}."
                ),
                "date": review_date,
                "icon": "ti ti-clipboard-check",
                "color": "warning",
            }
        )

    if defense:
        defense_date = getattr(
            defense,
            "defense_date",
            None,
        )

        recent_activities.append(
            {
                "title": "Dissertation Defense",
                "description": ("Dissertation defense activity " "has been recorded."),
                "date": defense_date,
                "icon": "ti ti-gavel",
                "color": "danger",
            }
        )

    normalized_activities = []

    for activity in recent_activities:
        activity_date = activity.get("date")

        if activity_date is None:
            normalized_date = None

        elif isinstance(
            activity_date,
            datetime,
        ):
            if timezone.is_naive(activity_date):
                normalized_date = timezone.make_aware(
                    activity_date,
                    timezone.get_current_timezone(),
                )
            else:
                normalized_date = activity_date

        elif isinstance(
            activity_date,
            date,
        ):
            normalized_date = timezone.make_aware(
                datetime.combine(
                    activity_date,
                    time.min,
                ),
                timezone.get_current_timezone(),
            )

        else:
            normalized_date = None

        activity["date"] = normalized_date
        normalized_activities.append(activity)

    recent_activities = sorted(
        normalized_activities,
        key=lambda activity: (
            activity["date"] is not None,
            activity["date"]
            or timezone.make_aware(
                datetime.min,
                timezone.get_current_timezone(),
            ),
        ),
        reverse=True,
    )

    actions = []

    if not advisor:
        actions.append(
            {
                "priority": "critical",
                "title": "Advisor Required",
                "description": ("No research advisor has been assigned."),
                "action": "Contact Department",
            }
        )

    if not committee:
        actions.append(
            {
                "priority": "high",
                "title": "Committee Formation",
                "description": ("Your doctoral committee has not " "been created yet."),
                "action": "Contact Department",
            }
        )

    elif committee.approval_status != "APPROVED":
        actions.append(
            {
                "priority": "high",
                "title": "Committee Approval",
                "description": ("Your doctoral committee is " "waiting for approval."),
                "action": "Contact Chair",
            }
        )

    if total_credits_required and completed_credits < total_credits_required:
        actions.append(
            {
                "priority": "high",
                "title": "Coursework Completion",
                "description": (
                    f"{remaining_credits} credits "
                    f"remaining to complete your program."
                ),
                "action": "Review Coursework",
            }
        )

    if not any(exam.result == "PASS" for exam in examinations):
        actions.append(
            {
                "priority": "medium",
                "title": "Examination Required",
                "description": (
                    "Preliminary or qualifying " "examination is not yet passed."
                ),
                "action": "Review Examination",
            }
        )

    if not proposal:
        actions.append(
            {
                "priority": "medium",
                "title": "Proposal Required",
                "description": (
                    "Your dissertation proposal " "has not been submitted."
                ),
                "action": "Submit Proposal",
            }
        )

    elif proposal.result != "APPROVED":
        actions.append(
            {
                "priority": "medium",
                "title": "Proposal Approval",
                "description": ("Your dissertation proposal " "is awaiting approval."),
                "action": "Review Proposal",
            }
        )

    if not candidacy_eligible and not candidacy_approved:
        actions.append(
            {
                "priority": "medium",
                "title": "Candidacy Requirements",
                "description": (
                    f"{candidacy_requirements_completed} of "
                    f"{candidacy_requirements_total} "
                    f"requirements completed."
                ),
                "action": "Review Requirements",
            }
        )

    if final_dissertation_eligible and not latest_final_dissertation_submission:
        actions.append(
            {
                "priority": "high",
                "title": "Final Dissertation Required",
                "description": ("You are eligible to submit your final dissertation."),
                "action": "Submit Final Dissertation",
            }
        )

    elif latest_final_dissertation_submission:
        if dissertation_status == "DRAFT":
            actions.append(
                {
                    "priority": "medium",
                    "title": "Final Dissertation",
                    "description": (
                        "Your final dissertation submission " "is in draft stage."
                    ),
                    "action": "Continue Dissertation",
                }
            )

        elif dissertation_status == "REVISION_REQUIRED":
            actions.append(
                {
                    "priority": "high",
                    "title": "Dissertation Revision Required",
                    "description": ("Your final dissertation requires revision."),
                    "action": "Review Dissertation",
                }
            )

    insights = []

    if advisor:
        insights.append(
            f"Your research advisor is " f"Dr. {advisor.user.get_full_name()}."
        )

    if committee and committee.approval_status == "APPROVED":
        insights.append("Your doctoral committee is fully " "established and approved.")

    if candidacy_approved:
        insights.append("Your doctoral candidacy has been approved.")

    elif candidacy_eligible:
        insights.append("You are eligible for doctoral candidacy.")

    if total_credits_required:
        insights.append(
            f"You have completed {completed_credits} "
            f"of {total_credits_required} required credits."
        )

    if total_courseworks:
        insights.append(
            f"{completed_courseworks} of "
            f"{total_courseworks} coursework items "
            f"are completed."
        )

    if total_publications:
        insights.append(
            f"Your research portfolio contains " f"{total_publications} publication(s)."
        )

    if indexed_publications:
        insights.append(
            f"{indexed_publications} publication(s) " f"are currently indexed."
        )

    if proposal and proposal.result == "APPROVED":
        insights.append("Your dissertation proposal has been approved.")

    if latest_final_dissertation_submission:
        if dissertation_status == "SUBMITTED":
            insights.append(
                "Your final dissertation has been submitted " "and is awaiting review."
            )

        elif dissertation_status in [
            "ADVISOR_REVIEW",
            "COMMITTEE_REVIEW",
            "CHAIR_REVIEW",
            "UNDER_REVIEW",
        ]:
            insights.append("Your final dissertation is currently under review.")

        elif dissertation_status == "REVISION_REQUIRED":
            insights.append("Your final dissertation requires revision.")

        elif dissertation_status == "APPROVED":
            insights.append("Your final dissertation has been approved.")

    if total_milestones:
        insights.append(
            f"You have completed "
            f"{completed_milestones} of "
            f"{total_milestones} milestones."
        )

    if next_milestone:
        insights.append(f"Your next milestone is " f"{next_milestone.milestone_title}.")

    if total_reviews:
        insights.append(f"{total_reviews} annual progress " f"review(s) are recorded.")

    if not insights:
        insights.append(
            "Welcome to your PhD journey. "
            "Continue completing your academic milestones."
        )

    chart_labels_progress = stages

    chart_data_progress = [
        100 if stage_completed.get(stage, False) else 0 for stage in stages
    ]

    chart_data_progress_values = [
        1 if stage_completed.get(stage, False) else 0 for stage in stages
    ]

    chart_labels_coursework = [
        "Completed",
        "In Progress",
        "Not Started",
        "Failed",
    ]

    chart_data_coursework = [
        completed_courseworks,
        in_progress_courseworks,
        not_started_courseworks,
        failed_courseworks,
    ]

    chart_labels_exams = [
        "Scheduled",
        "Completed",
        "Cancelled",
        "Draft",
    ]

    chart_data_exams = [
        scheduled_exams,
        completed_exams,
        cancelled_exams,
        draft_exams,
    ]

    chart_labels_publications = [
        "Indexed",
        "Under Review",
        "Not Indexed",
    ]

    chart_data_publications = [
        indexed_publications,
        under_review_publications,
        not_indexed_publications,
    ]

    chart_labels_milestones = [
        "Completed",
        "In Progress",
        "Pending",
    ]

    chart_data_milestones = [
        completed_milestones,
        in_progress_milestones,
        pending_milestones,
    ]

    chart_labels_reviews = [
        "Satisfactory",
        "Needs Improvement",
        "Unsatisfactory",
    ]

    chart_data_reviews = [
        satisfactory_reviews,
        needs_improvement_reviews,
        unsatisfactory_reviews,
    ]

    chart_labels_credits = [
        "Completed",
        "Remaining",
    ]

    chart_data_credits = [
        completed_credits,
        remaining_credits,
    ]

    yearly_publications = defaultdict(int)

    for publication in publications:
        if publication.publication_date:
            yearly_publications[publication.publication_date.year] += 1

    chart_labels_yearly = sorted(yearly_publications.keys())

    chart_data_yearly = [yearly_publications[year] for year in chart_labels_yearly]

    chair_faculty = None
    committee_members = []

    chair_approved_by_name = (
        chair_approved_by.user.get_full_name()
        if chair_approved_by and chair_approved_by.user
        else None
    )

    if committee:
        chair_faculty = committee.chair_faculty
        committee_members = list(committee.committee_members.all())

    chair_faculty_name = (
        chair_faculty.user.get_full_name()
        if chair_faculty and chair_faculty.user
        else None
    )

    chair_faculty_email = (
        chair_faculty.user.email if chair_faculty and chair_faculty.user else None
    )

    context = {
        "student": student,
        "phd_student": phd_student,
        "advisor": advisor,
        "advisor_name": (advisor.user.get_full_name() if advisor else None),
        "advisor_department": (advisor.department if advisor else None),
        "committee": committee,
        "chair_faculty": chair_faculty,
        "chair_faculty_name": chair_faculty_name,
        "chair_faculty_email": chair_faculty_email,
        "committee_members": committee_members,
        "committee_member_count": len(committee_members),
        "phd_program": phd_program,
        "department": department,
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
        "dissertation": latest_final_dissertation_submission,
        "dissertation_status": dissertation_status,
        "dissertation_title": dissertation_title,
        "dissertation_version": dissertation_version,
        "dissertation_submission_date": dissertation_submission_date,
        "graduation": graduation,
        "graduation_date": graduation_date,
        "dissertation_accepted": dissertation_accepted,
        "graduation_status": graduation_status,
        "graduation_time": graduation_time,
        "graduation_location": graduation_location,
        "degree_awarded": degree_awarded,
        "final_gpa": final_gpa,
        "defense_passed": defense_passed,
        "graduation_created_at": graduation_created_at,
        "graduation_created_by": graduation_created_by,
        "chair_approved_by": chair_approved_by,
        "chair_approved_at": chair_approved_at,
        "chair_congratulations_note": chair_congratulations_note,
        "graduation_completed_at": graduation_completed_at,
        "defense": defense,
        "admission_year": admission_year,
        "years_in_program": years_in_program,
        "research_milestones": research_milestones,
        "research_publications": research_publications,
        "total_milestones": total_milestones,
        "completed_milestones": completed_milestones,
        "pending_milestones": pending_milestones,
        "in_progress_milestones": in_progress_milestones,
        "chair_approved_by_name": chair_approved_by_name,
        "milestone_completion_percentage": (milestone_completion_percentage),
        "doctoral_milestone_completion_percentage": (
            doctoral_milestone_completion_percentage
        ),
        "doctoral_milestone_completed_count": (doctoral_milestone_completed_count),
        "doctoral_milestone_total_count": (doctoral_milestone_total_count),
        "total_courseworks": total_courseworks,
        "completed_courseworks": completed_courseworks,
        "in_progress_courseworks": in_progress_courseworks,
        "failed_courseworks": failed_courseworks,
        "not_started_courseworks": not_started_courseworks,
        "coursework_completion_percentage": (coursework_completion_percentage),
        "total_credits_required": total_credits_required,
        "completed_credits": completed_credits,
        "assigned_credits": assigned_credits,
        "remaining_credits": remaining_credits,
        "credit_completion_percentage": (credit_completion_percentage),
        "total_exams": total_exams,
        "scheduled_exams": scheduled_exams,
        "completed_exams": completed_exams,
        "cancelled_exams": cancelled_exams,
        "draft_exams": draft_exams,
        "passed_exams": passed_exams,
        "failed_exams": failed_exams,
        "pending_exams": pending_exams,
        "exam_success_percentage": (exam_success_percentage),
        "total_publications": total_publications,
        "indexed_publications": indexed_publications,
        "under_review_publications": under_review_publications,
        "not_indexed_publications": not_indexed_publications,
        "publication_indexing_percentage": (publication_indexing_percentage),
        "total_reviews": total_reviews,
        "satisfactory_reviews": satisfactory_reviews,
        "needs_improvement_reviews": needs_improvement_reviews,
        "unsatisfactory_reviews": unsatisfactory_reviews,
        "review_success_percentage": review_success_percentage,
        "overall_progress": overall_progress,
        "completed_stage_count": completed_stage_count,
        "total_stage_count": total_stage_count,
        "stages": stages,
        "stage_items": stage_items,
        "stage_completed": stage_completed,
        "stage_icons": stage_icons,
        "latest_coursework": latest_coursework,
        "latest_exam": latest_exam,
        "dissertation_history": dissertation_history,
        "latest_publication": latest_publication,
        "latest_publication_indexed_status": (latest_publication_indexed_status),
        "latest_publication_date": latest_publication_date,
        "latest_publication_journal": latest_publication_journal,
        "latest_review": latest_review,
        "latest_annual_review": latest_annual_review,
        "annual_review_reviewer": annual_review_reviewer,
        "latest_milestone": latest_milestone,
        "latest_milestone_progress": latest_milestone_progress,
        "latest_milestone_status": latest_milestone_status,
        "latest_milestone_expected_date": (latest_milestone_expected_date),
        "latest_milestone_updated_date": (latest_milestone_updated_date),
        "next_milestone": next_milestone,
        "upcoming_exam": upcoming_exam,
        "recent_activities": recent_activities,
        "actions": actions,
        "insights": insights,
        "chart_labels_progress": chart_labels_progress,
        "chart_data_progress": chart_data_progress,
        "chart_data_progress_values": (chart_data_progress_values),
        "chart_labels_coursework": (chart_labels_coursework),
        "chart_data_coursework": chart_data_coursework,
        "chart_labels_exams": chart_labels_exams,
        "chart_data_exams": chart_data_exams,
        "chart_labels_publications": (chart_labels_publications),
        "chart_data_publications": chart_data_publications,
        "chart_labels_milestones": chart_labels_milestones,
        "chart_data_milestones": chart_data_milestones,
        "chart_labels_reviews": chart_labels_reviews,
        "chart_data_reviews": chart_data_reviews,
        "chart_labels_credits": chart_labels_credits,
        "chart_data_credits": chart_data_credits,
        "chart_labels_yearly": chart_labels_yearly,
        "chart_data_yearly": chart_data_yearly,
        "coursework_credits_completed": (coursework_credits_completed),
        "qualifying_exam_passed": qualifying_exam_passed,
        "dissertation_proposal_approved": (dissertation_proposal_approved),
        "candidacy_approved_for_final_dissertation": (
            candidacy_approved_for_final_dissertation
        ),
        "research_overall_progress": (research_overall_progress),
        "research_completed_for_final_dissertation": (
            research_completed_for_final_dissertation
        ),
        "final_dissertation_eligible": (final_dissertation_eligible),
        "latest_final_dissertation_submission": (latest_final_dissertation_submission),
        "graduation_status": graduation_status,
    }

    return render(
        request,
        "Leo_Student/phd_dashboard.html",
        context,
    )


@login_required
def student_coursework_list(request, uuid):

    student = get_object_or_404(
        StudentProfile,
        user__uuid=uuid,
        user=request.user,
    )

    phd_student = get_object_or_404(
        PhDStudent.objects.select_related(
            "student",
            "advisor",
            "advisor__user",
            "phd_program",
            "phd_program__department",
        ),
        student=student,
    )

    coursework_list = list(
        FacultyCoursework.objects.filter(
            phd_student=phd_student,
        )
        .select_related(
            "program",
            "coursework",
            "coursework__program",
            "submission",
            "submission__evaluation",
            "submission__evaluation__evaluated_by",
            "submission__evaluation__evaluated_by__user",
        )
        .order_by(
            "-created_at",
            "-pk",
        )
    )

    total_count = len(coursework_list)

    pending_count = 0
    submitted_count = 0
    approved_count = 0
    rejected_count = 0
    completed_count = 0
    evaluated_count = 0

    latest_assignment = coursework_list[0] if coursework_list else None

    latest_submission = None
    latest_submission_date = None

    for coursework in coursework_list:

        submission = getattr(
            coursework,
            "submission",
            None,
        )

        evaluation = None

        if submission:
            evaluation = getattr(
                submission,
                "evaluation",
                None,
            )

        if evaluation:

            evaluated_count += 1

            if evaluation.marks >= 40:

                if submission.status != "APPROVED":
                    submission.status = "APPROVED"
                    submission.save(
                        update_fields=[
                            "status",
                            "updated_at",
                        ]
                    )

                if coursework.status != "COMPLETED":
                    coursework.status = "COMPLETED"
                    coursework.progress_percentage = 100
                    coursework.completion_date = evaluation.evaluated_at.date()

                    coursework.save(
                        update_fields=[
                            "status",
                            "progress_percentage",
                            "completion_date",
                            "updated_at",
                        ]
                    )

                approved_count += 1
                completed_count += 1

            else:

                if submission.status != "REJECTED":
                    submission.status = "REJECTED"
                    submission.save(
                        update_fields=[
                            "status",
                            "updated_at",
                        ]
                    )

                if coursework.status != "FAILED":
                    coursework.status = "FAILED"
                    coursework.progress_percentage = 100
                    coursework.completion_date = evaluation.evaluated_at.date()

                    coursework.save(
                        update_fields=[
                            "status",
                            "progress_percentage",
                            "completion_date",
                            "updated_at",
                        ]
                    )

                rejected_count += 1

        elif submission:

            if submission.status == "SUBMITTED":
                pending_count += 1

            elif submission.status == "UNDER_REVIEW":
                pending_count += 1

            elif submission.status == "APPROVED":
                approved_count += 1
                completed_count += 1

            elif submission.status == "REJECTED":
                rejected_count += 1

        else:

            if coursework.status in [
                "NOT_STARTED",
                "IN_PROGRESS",
            ]:
                pending_count += 1

            elif coursework.status == "COMPLETED":
                completed_count += 1

        submission_date = None

        if submission:
            submission_date = getattr(
                submission,
                "updated_at",
                None,
            ) or getattr(
                submission,
                "submitted_at",
                None,
            )

        if (
            submission
            and submission_date
            and (
                latest_submission_date is None
                or submission_date > latest_submission_date
            )
        ):
            latest_submission = coursework
            latest_submission_date = submission_date

    if latest_assignment:

        latest_assignment_submission = getattr(
            latest_assignment,
            "submission",
            None,
        )

        latest_assignment_evaluation = None

        if latest_assignment_submission:
            latest_assignment_evaluation = getattr(
                latest_assignment_submission,
                "evaluation",
                None,
            )

        latest_assignment.evaluation = latest_assignment_evaluation

        if latest_assignment_evaluation:

            latest_assignment.evaluation_marks = latest_assignment_evaluation.marks

            latest_assignment.evaluation_grade = latest_assignment_evaluation.grade

            latest_assignment.evaluation_feedback = (
                latest_assignment_evaluation.faculty_feedback
            )

            latest_assignment.evaluated_at = latest_assignment_evaluation.evaluated_at

            if latest_assignment_evaluation.marks >= 40:
                latest_assignment.result_status = "APPROVED"
                latest_assignment.result_label = "Approved"
            else:
                latest_assignment.result_status = "REJECTED"
                latest_assignment.result_label = "Rejected"

        elif latest_assignment_submission:

            latest_assignment.result_status = latest_assignment_submission.status

            latest_assignment.result_label = (
                latest_assignment_submission.get_status_display()
            )

            latest_assignment.evaluation_marks = None
            latest_assignment.evaluation_grade = None
            latest_assignment.evaluation_feedback = None
            latest_assignment.evaluated_at = None

        else:

            latest_assignment.result_status = None
            latest_assignment.result_label = None
            latest_assignment.evaluation_marks = None
            latest_assignment.evaluation_grade = None
            latest_assignment.evaluation_feedback = None
            latest_assignment.evaluated_at = None

    context = {
        "student": student,
        "phd_student": phd_student,
        "coursework_list": coursework_list,
        "total_count": total_count,
        "pending_count": pending_count,
        "submitted_count": submitted_count,
        "approved_count": approved_count,
        "rejected_count": rejected_count,
        "completed_count": completed_count,
        "evaluated_count": evaluated_count,
        "latest_assignment": latest_assignment,
        "latest_submission": latest_submission,
    }

    return render(
        request,
        "Leo_Student/student_coursework_list.html",
        context,
    )


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


@login_required
def student_coursework_submit(
    request,
    uuid,
    coursework_id,
):
    student = get_object_or_404(
        StudentProfile,
        user__uuid=uuid,
        user=request.user,
    )

    phd_student = get_object_or_404(
        PhDStudent.objects.select_related(
            "student",
            "advisor",
            "advisor__user",
            "phd_program",
        ),
        student=student,
    )

    coursework = get_object_or_404(
        FacultyCoursework.objects.select_related(
            "program",
            "phd_student",
            "coursework",
        ),
        coursework_id=coursework_id,
        phd_student=phd_student,
    )

    submission = CourseworkSubmission.objects.filter(
        coursework=coursework,
    ).first()

    if submission:
        messages.warning(
            request,
            "You have already submitted this coursework.",
        )

        return redirect(
            "Student:student_coursework_submissions",
            uuid=uuid,
        )

    if request.method == "POST":
        form = CourseworkSubmissionForm(
            request.POST,
            request.FILES,
            coursework=coursework,
        )

        if form.is_valid():
            with transaction.atomic():
                submission = form.save()

                coursework.status = "IN_PROGRESS"
                coursework.progress_percentage = 100

                coursework.save(
                    update_fields=[
                        "status",
                        "progress_percentage",
                        "updated_at",
                    ]
                )

                faculty_user = None

                if phd_student.advisor_id and phd_student.advisor.user_id:
                    faculty_user = phd_student.advisor.user

                coursework_name = (
                    coursework.coursework.coursework_name
                    if coursework.coursework
                    else "Coursework"
                )

                _create_coursework_notification(
                    user=faculty_user,
                    title="Coursework Submitted",
                    message=(
                        f"{student.user.get_full_name() or student.user.username} "
                        f"has submitted the coursework "
                        f"'{coursework_name}'."
                    ),
                    notification_type="INFO",
                )

            messages.success(
                request,
                "Coursework submitted successfully.",
            )

            return redirect(
                "Student:student_coursework_submissions",
                uuid=uuid,
            )

    else:
        form = CourseworkSubmissionForm(
            coursework=coursework,
        )

    context = {
        "student": student,
        "phd_student": phd_student,
        "coursework": coursework,
        "form": form,
    }

    return render(
        request,
        "Leo_Student/student_coursework_submit.html",
        context,
    )


@login_required
def student_coursework_submissions(request, uuid):

    student = get_object_or_404(
        StudentProfile,
        user__uuid=uuid,
        user=request.user,
    )

    phd_student = get_object_or_404(
        PhDStudent.objects.select_related(
            "student",
            "advisor",
            "advisor__user",
            "phd_program",
            "phd_program__department",
        ),
        student=student,
    )

    submissions = list(
        CourseworkSubmission.objects.filter(
            coursework__phd_student=phd_student,
        )
        .select_related(
            "coursework",
            "coursework__program",
            "coursework__coursework",
            "coursework__phd_student",
            "evaluation",
            "evaluation__evaluated_by",
            "evaluation__evaluated_by__user",
        )
        .order_by(
            "-submitted_at",
        )
    )

    pending_count = 0
    approved_count = 0
    rejected_count = 0

    for submission in submissions:

        evaluation = getattr(
            submission,
            "evaluation",
            None,
        )

        if evaluation:

            if evaluation.marks >= 40:

                if submission.status != "APPROVED":

                    submission.status = "APPROVED"

                    submission.save(
                        update_fields=[
                            "status",
                            "updated_at",
                        ]
                    )

            else:

                if submission.status != "REJECTED":

                    submission.status = "REJECTED"

                    submission.save(
                        update_fields=[
                            "status",
                            "updated_at",
                        ]
                    )

        if submission.status in [
            "SUBMITTED",
            "UNDER_REVIEW",
        ]:

            pending_count += 1

        elif submission.status == "APPROVED":

            approved_count += 1

        elif submission.status == "REJECTED":

            rejected_count += 1

    context = {
        "student": student,
        "phd_student": phd_student,
        "submissions": submissions,
        "pending_count": pending_count,
        "approved_count": approved_count,
        "rejected_count": rejected_count,
    }

    return render(
        request,
        "Leo_Student/student_coursework_submissions.html",
        context,
    )


@login_required
def student_qualifying_exam_list(request, uuid):

    student = get_object_or_404(
        StudentProfile,
        user=request.user,
        user__uuid=uuid,
    )

    phd_student = get_object_or_404(
        PhDStudent.objects.select_related(
            "student",
            "advisor",
            "advisor__user",
            "phd_program",
        ),
        student=student,
    )
    examination_list = (
        phd_student.preliminary_examinations.all()
        .select_related(
            "phd_student",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "phd_student__phd_program",
        )
        .order_by(
            "-exam_date",
            "-start_time",
        )
    )
    total_exams = examination_list.count()

    scheduled_exams = examination_list.filter(status="SCHEDULED").count()

    completed_exams = examination_list.filter(status="COMPLETED").count()

    pending_results = examination_list.filter(result="PENDING").count()

    pass_count = examination_list.filter(result="PASS").count()

    fail_count = examination_list.filter(result="FAIL").count()
    context = {
        "student": student,
        "phd_student": phd_student,
        "examination_list": examination_list,
        "total_exams": total_exams,
        "scheduled_exams": scheduled_exams,
        "completed_exams": completed_exams,
        "pending_results": pending_results,
        "pass_count": pass_count,
        "fail_count": fail_count,
    }

    return render(
        request,
        "Leo_Student/student_qualifying_exam_list.html",
        context,
    )


@login_required
def student_qualifying_exam_detail(
    request,
    uuid,
    exam_id,
):

    student = get_object_or_404(
        StudentProfile,
        user=request.user,
        user__uuid=uuid,
    )

    phd_student = get_object_or_404(
        PhDStudent.objects.select_related(
            "student",
            "advisor",
            "advisor__user",
            "phd_program",
            "phd_program__department",
            "doctoral_committee",
            "doctoral_committee__chair_faculty",
            "doctoral_committee__chair_faculty__user",
        ),
        student=student,
    )

    examination = get_object_or_404(
        PreliminaryExamination.objects.select_related(
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
        ).prefetch_related(
            Prefetch(
                "phd_student__doctoral_committee__committee_members",
                queryset=CommitteeMember.objects.select_related(
                    "faculty",
                    "faculty__user",
                    "department",
                ).order_by(
                    "role",
                ),
            ),
            "evaluations",
        ),
        prelim_exam_id=exam_id,
        phd_student=phd_student,
    )

    committee = phd_student.doctoral_committee

    committee_members = []

    if committee:
        committee_members = committee.committee_members.all()

    context = {
        "student": student,
        "phd_student": phd_student,
        "examination": examination,
        "committee": committee,
        "committee_members": committee_members,
    }

    return render(
        request,
        "Leo_Student/student_qualifying_exam_detail.html",
        context,
    )


@login_required
def student_dissertation_list(request, uuid):

    student = get_object_or_404(
        StudentProfile,
        user__uuid=uuid,
        user=request.user,
    )

    phd_student = get_object_or_404(
        PhDStudent.objects.select_related(
            "student",
            "student__user",
            "advisor",
            "advisor__user",
            "advisor__faculty_rank",
            "phd_program",
            "phd_program__department",
        ).prefetch_related(
            Prefetch(
                "doctoral_committee__committee_members",
                queryset=CommitteeMember.objects.select_related(
                    "faculty",
                    "faculty__user",
                    "department",
                ).order_by("role"),
            )
        ),
        student=student,
    )

    advisor = phd_student.advisor

    advisor_department = None
    if advisor and advisor.department_id:
        advisor_department = Department.objects.filter(
            department_id=advisor.department_id
        ).first()

    committee = getattr(phd_student, "doctoral_committee", None)

    committee_members = (
        committee.committee_members.all()
        if committee
        else CommitteeMember.objects.none()
    )

    proposal = (
        DissertationProposal.objects.filter(
            phd_student=phd_student,
        )
        .order_by("-proposal_id")
        .first()
    )

    dissertation = (
        Dissertation.objects.filter(
            phd_student=phd_student,
        )
        .order_by("-dissertation_id")
        .first()
    )
    approval = None

    if dissertation:
        approval = (
            DissertationApproval.objects.select_related(
                "chair_faculty",
            )
            .filter(
                dissertation=dissertation,
            )
            .first()
        )
        if approval:
            print("Decision:", approval.decision)
            print("Allow:", approval.allow_resubmission)
            print("Count:", approval.reopened_count)
    milestones = PhDMilestone.objects.filter(phd_student=phd_student).order_by(
        "completion_date"
    )
    advisor_advice = None

    if dissertation:
        advisor_advice = (
            DissertationAdvisorAdvice.objects.select_related(
                "advisor",
                "advisor__user",
                "advisor__faculty_rank",
                "advisor__department",
            )
            .filter(
                dissertation=dissertation,
                is_submitted=True,
            )
            .first()
        )
    publications = ResearchPublication.objects.filter(
        phd_student=phd_student,
    ).order_by("-publication_date")

    annual_reviews = AnnualProgressReview.objects.filter(
        phd_student=phd_student
    ).order_by("-review_year")

    defense = (
        DissertationDefense.objects.filter(
            phd_student=phd_student,
        )
        .order_by("-defense_date")
        .first()
    )

    graduation = (
        Graduation.objects.filter(
            phd_student=phd_student,
        )
        .order_by("-graduation_date")
        .first()
    )

    context = {
        "student": student,
        "phd_student": phd_student,
        "advisor": advisor,
        "advisor_department": advisor_department,
        "committee": committee,
        "committee_members": committee_members,
        "proposal": proposal,
        "dissertation": dissertation,
        "approval": approval,
        "milestones": milestones,
        "publications": publications,
        "annual_reviews": annual_reviews,
        "defense": defense,
        "graduation": graduation,
        "approval": approval,
        "advisor_advice": advisor_advice,
    }

    return render(
        request,
        "Leo_Student/student_dissertation_list.html",
        context,
    )


@login_required
def student_dissertation_submit(request, uuid):

    student = get_object_or_404(
        StudentProfile,
        user__uuid=uuid,
        user=request.user,
    )

    phd_student = get_object_or_404(
        PhDStudent.objects.select_related(
            "student",
        ),
        student=student,
    )

    dissertation = Dissertation.objects.filter(
        phd_student=phd_student,
    ).first()

    if not dissertation:

        messages.error(
            request,
            "Dissertation has not been created by the Chair Faculty yet.",
        )

        return redirect(
            "Student:student_dissertation_list",
            uuid=uuid,
        )

    approval = DissertationApproval.objects.filter(
        dissertation=dissertation,
    ).first()

    allow_resubmission = approval and approval.allow_resubmission

    if (
        dissertation.status
        in [
            "SUBMITTED",
            "UNDER_REVIEW",
            "APPROVED",
        ]
        and not allow_resubmission
    ):

        messages.warning(
            request,
            "Your dissertation has already been submitted and cannot be submitted again.",
        )

        return redirect(
            "Student:student_dissertation_list",
            uuid=uuid,
        )

    if request.method == "POST":

        form = DissertationSubmissionForm(
            request.POST,
            request.FILES,
            instance=dissertation,
            phd_student=phd_student,
        )

        if form.is_valid():

            dissertation = form.save()

            dissertation.status = "SUBMITTED"

            dissertation.save(
                update_fields=[
                    "status",
                ],
            )

            if approval:

                approval.allow_resubmission = False

                approval.save()

                dissertation.save(update_fields=["status"])

                proposal.save(update_fields=["result"])

            messages.success(
                request,
                "Dissertation submitted successfully.",
            )

            return redirect(
                "Student:student_dissertation_list",
                uuid=uuid,
            )

    else:

        form = DissertationSubmissionForm(
            instance=dissertation,
            phd_student=phd_student,
        )

    context = {
        "student": student,
        "phd_student": phd_student,
        "dissertation": dissertation,
        "approval": approval,
        "form": form,
    }

    return render(
        request,
        "Leo_Student/student_dissertation_submit.html",
        context,
    )


from Students.models import (
    StudentProfile,
    PhDStudent,
    DoctoralCommittee,
    CommitteeMember,
)


@login_required
def student_advisory_committee(request, uuid):

    student = get_object_or_404(
        StudentProfile,
        user=request.user,
        user__uuid=uuid,
    )

    phd_student = get_object_or_404(
        PhDStudent.objects.select_related(
            "student",
            "student__user",
            "advisor",
            "advisor__user",
            "advisor__faculty_rank",
            "advisor__department",
            "doctoral_committee",
            "doctoral_committee__chair_faculty",
            "doctoral_committee__chair_faculty__user",
            "doctoral_committee__chair_faculty__faculty_rank",
            "doctoral_committee__chair_faculty__department",
        ).prefetch_related(
            Prefetch(
                "doctoral_committee__committee_members",
                queryset=CommitteeMember.objects.select_related(
                    "faculty",
                    "faculty__user",
                    "faculty__faculty_rank",
                    "faculty__department",
                ).order_by("role"),
            )
        ),
        student=student,
    )

    advisor = phd_student.advisor

    committee = getattr(
        phd_student,
        "doctoral_committee",
        None,
    )

    chair_faculty = committee.chair_faculty if committee else None

    committee_members = (
        committee.committee_members.all()
        if committee
        else CommitteeMember.objects.none()
    )

    context = {
        "student": student,
        "phd_student": phd_student,
        "advisor": advisor,
        "committee": committee,
        "chair_faculty": chair_faculty,
        "committee_members": committee_members,
    }

    return render(
        request,
        "Leo_Student/student_advisory_committee.html",
        context,
    )


@login_required
def student_dissertation_detail(request, uuid):

    student = get_object_or_404(
        StudentProfile,
        user__uuid=uuid,
        user=request.user,
    )

    phd_student = get_object_or_404(
        PhDStudent.objects.select_related(
            "student",
            "advisor",
            "advisor__user",
            "advisor__faculty_rank",
            "advisor__department",
            "phd_program",
            "phd_program__department",
            "doctoral_committee",
            "doctoral_committee__chair_faculty",
            "doctoral_committee__chair_faculty__user",
        ).prefetch_related("doctoral_committee__committee_members__faculty__user"),
        student=student,
    )

    dissertation = (
        Dissertation.objects.filter(
            phd_student=phd_student,
        )
        .select_related(
            "phd_student",
        )
        .first()
    )

    proposal = DissertationProposal.objects.filter(
        phd_student=phd_student,
    ).first()

    approval = None

    if dissertation:

        approval = (
            DissertationApproval.objects.select_related(
                "chair_faculty",
            )
            .filter(
                dissertation=dissertation,
            )
            .first()
        )

        if approval:
            print("Decision :", approval.decision)
            print("Allow :", approval.allow_resubmission)
            print("Count :", approval.reopened_count)
            print("Deadline :", approval.resubmission_deadline)

    committee = getattr(
        phd_student,
        "doctoral_committee",
        None,
    )
    advisor_advice = None

    if dissertation:
        advisor_advice = (
            DissertationAdvisorAdvice.objects.select_related(
                "advisor",
                "advisor__user",
            )
            .filter(
                dissertation=dissertation,
                is_submitted=True,
            )
            .first()
        )
    committee_members = (
        committee.committee_members.select_related(
            "faculty",
            "faculty__user",
            "faculty__department",
            "faculty__faculty_rank",
        ).all()
        if committee
        else CommitteeMember.objects.none()
    )

    context = {
        "student": student,
        "phd_student": phd_student,
        "advisor": phd_student.advisor,
        "committee": committee,
        "committee_members": committee_members,
        "proposal": proposal,
        "dissertation": dissertation,
        "approval": approval,
        "advisor_advice": advisor_advice,
    }

    return render(
        request,
        "Leo_Student/student_dissertation_detail.html",
        context,
    )


@login_required
def student_dissertation_proposal_create(
    request,
    uuid,
):

    student = get_object_or_404(
        StudentProfile,
        user__uuid=uuid,
        user=request.user,
    )

    phd_student = get_object_or_404(
        PhDStudent.objects.select_related(
            "student",
            "student__user",
            "advisor",
            "advisor__user",
            "phd_program",
            "phd_program__department",
        ),
        student=student,
    )

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
            )
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

    preliminary_exam_passed = PreliminaryExamination.objects.filter(
        phd_student=phd_student,
        result="PASS",
    ).exists()

    proposal_eligible = coursework_completed and preliminary_exam_passed

    existing_proposal = DissertationProposal.objects.filter(
        phd_student=phd_student,
    ).first()

    if existing_proposal:

        messages.warning(
            request,
            "You already have a dissertation proposal.",
        )

        return redirect(
            "Student:student_dissertation_proposal_detail",
            uuid=uuid,
        )

    if not coursework_completed:

        messages.warning(
            request,
            (
                "You must complete all required coursework credits "
                "before creating a dissertation proposal."
            ),
        )

        form = DissertationProposalForm(
            phd_student=phd_student,
            coursework_completed=coursework_completed,
            preliminary_exam_passed=preliminary_exam_passed,
        )

        context = {
            "student": student,
            "phd_student": phd_student,
            "advisor": phd_student.advisor,
            "proposal": None,
            "form": form,
            "is_edit": False,
            "coursework_completed": coursework_completed,
            "preliminary_exam_passed": preliminary_exam_passed,
            "proposal_eligible": proposal_eligible,
            "required_credits": required_credits,
            "completed_credits": completed_credits,
            "remaining_credits": max(
                required_credits - completed_credits,
                0,
            ),
            "current_submission_number": 1,
        }

        return render(
            request,
            "Leo_Student/student_dissertation_proposal_form.html",
            context,
        )

    if not preliminary_exam_passed:

        messages.warning(
            request,
            (
                "You must pass the Preliminary / Qualifying Examination "
                "before creating a dissertation proposal."
            ),
        )

        form = DissertationProposalForm(
            phd_student=phd_student,
            coursework_completed=coursework_completed,
            preliminary_exam_passed=preliminary_exam_passed,
        )

        context = {
            "student": student,
            "phd_student": phd_student,
            "advisor": phd_student.advisor,
            "proposal": None,
            "form": form,
            "is_edit": False,
            "coursework_completed": coursework_completed,
            "preliminary_exam_passed": preliminary_exam_passed,
            "proposal_eligible": proposal_eligible,
            "required_credits": required_credits,
            "completed_credits": completed_credits,
            "remaining_credits": max(
                required_credits - completed_credits,
                0,
            ),
            "current_submission_number": 1,
        }

        return render(
            request,
            "Leo_Student/student_dissertation_proposal_form.html",
            context,
        )

    if request.method == "POST":

        form = DissertationProposalForm(
            request.POST,
            request.FILES,
            phd_student=phd_student,
            coursework_completed=coursework_completed,
            preliminary_exam_passed=preliminary_exam_passed,
        )

        if form.is_valid():

            proposal = form.save()

            messages.success(
                request,
                "Dissertation proposal created successfully.",
            )

            return redirect(
                "Student:student_dissertation_proposal_detail",
                uuid=uuid,
            )

    else:

        form = DissertationProposalForm(
            phd_student=phd_student,
            coursework_completed=coursework_completed,
            preliminary_exam_passed=preliminary_exam_passed,
        )

    context = {
        "student": student,
        "phd_student": phd_student,
        "advisor": phd_student.advisor,
        "proposal": None,
        "form": form,
        "is_edit": False,
        "coursework_completed": coursework_completed,
        "preliminary_exam_passed": preliminary_exam_passed,
        "proposal_eligible": proposal_eligible,
        "required_credits": required_credits,
        "completed_credits": completed_credits,
        "remaining_credits": max(
            required_credits - completed_credits,
            0,
        ),
        "current_submission_number": 1,
    }

    return render(
        request,
        "Leo_Student/student_dissertation_proposal_form.html",
        context,
    )


@login_required
def student_dissertation_proposal_edit(
    request,
    uuid,
):

    student = get_object_or_404(
        StudentProfile,
        user__uuid=uuid,
        user=request.user,
    )

    phd_student = get_object_or_404(
        PhDStudent.objects.select_related(
            "student",
            "student__user",
            "advisor",
            "advisor__user",
            "phd_program",
            "phd_program__department",
        ),
        student=student,
    )

    proposal = get_object_or_404(
        DissertationProposal,
        phd_student=phd_student,
    )

    if proposal.status not in [
        "DRAFT",
        "REVISION_REQUIRED",
    ]:

        messages.warning(
            request,
            "This proposal cannot be edited at its current stage.",
        )

        return redirect(
            "Student:student_dissertation_proposal_detail",
            uuid=uuid,
        )

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
            )
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

    preliminary_exam_passed = PreliminaryExamination.objects.filter(
        phd_student=phd_student,
        result="PASS",
    ).exists()

    proposal_eligible = coursework_completed and preliminary_exam_passed

    current_submission_number = (
        getattr(
            proposal,
            "resubmission_count",
            0,
        )
        + 1
    )

    if not coursework_completed:

        messages.warning(
            request,
            (
                "You must complete all required coursework credits "
                "before editing the dissertation proposal."
            ),
        )

        return redirect(
            "Student:student_dissertation_proposal_detail",
            uuid=uuid,
        )

    if not preliminary_exam_passed:

        messages.warning(
            request,
            (
                "You must pass the Preliminary / Qualifying Examination "
                "before editing the dissertation proposal."
            ),
        )

        return redirect(
            "Student:student_dissertation_proposal_detail",
            uuid=uuid,
        )

    if request.method == "POST":

        form = DissertationProposalForm(
            request.POST,
            request.FILES,
            instance=proposal,
            phd_student=phd_student,
            coursework_completed=coursework_completed,
            preliminary_exam_passed=preliminary_exam_passed,
        )

        if form.is_valid():

            proposal = form.save()

            messages.success(
                request,
                "Dissertation proposal updated successfully.",
            )

            return redirect(
                "Student:student_dissertation_proposal_detail",
                uuid=uuid,
            )

    else:

        form = DissertationProposalForm(
            instance=proposal,
            phd_student=phd_student,
            coursework_completed=coursework_completed,
            preliminary_exam_passed=preliminary_exam_passed,
        )

    context = {
        "student": student,
        "phd_student": phd_student,
        "advisor": phd_student.advisor,
        "proposal": proposal,
        "form": form,
        "is_edit": True,
        "coursework_completed": coursework_completed,
        "preliminary_exam_passed": preliminary_exam_passed,
        "proposal_eligible": proposal_eligible,
        "required_credits": required_credits,
        "completed_credits": completed_credits,
        "remaining_credits": max(
            required_credits - completed_credits,
            0,
        ),
        "current_submission_number": current_submission_number,
    }

    return render(
        request,
        "Leo_Student/student_dissertation_proposal_form.html",
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
def student_dissertation_proposal_submit(
    request,
    uuid,
):

    student = get_object_or_404(
        StudentProfile,
        user__uuid=uuid,
        user=request.user,
    )

    phd_student = get_object_or_404(
        PhDStudent.objects.select_related(
            "student",
            "student__user",
            "advisor",
            "advisor__user",
            "phd_program",
            "phd_program__department",
        ),
        student=student,
    )

    proposal = get_object_or_404(
        DissertationProposal,
        phd_student=phd_student,
    )

    if request.method != "POST":

        messages.warning(
            request,
            "Invalid request.",
        )

        return redirect(
            "Student:student_dissertation_proposal_detail",
            uuid=uuid,
        )

    if proposal.status not in [
        "DRAFT",
        "REVISION_REQUIRED",
    ]:

        messages.warning(
            request,
            "This proposal cannot be submitted at its current stage.",
        )

        return redirect(
            "Student:student_dissertation_proposal_detail",
            uuid=uuid,
        )

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
            )
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

    preliminary_exam_passed = PreliminaryExamination.objects.filter(
        phd_student=phd_student,
        result="PASS",
    ).exists()

    if not coursework_completed:

        messages.error(
            request,
            (
                "You cannot submit the dissertation proposal because "
                "the required coursework credits are not completed."
            ),
        )

        return redirect(
            "Student:student_dissertation_proposal_detail",
            uuid=uuid,
        )

    if not preliminary_exam_passed:

        messages.error(
            request,
            (
                "You cannot submit the dissertation proposal because "
                "the Preliminary / Qualifying Examination has not been passed."
            ),
        )

        return redirect(
            "Student:student_dissertation_proposal_detail",
            uuid=uuid,
        )

    if not proposal.proposal_title or not proposal.proposal_title.strip():

        messages.error(
            request,
            "Proposal title is required before submission.",
        )

        return redirect(
            "Student:student_dissertation_proposal_edit",
            uuid=uuid,
        )

    if len(proposal.proposal_title.strip()) < 5:

        messages.error(
            request,
            "Proposal title must contain at least 5 characters.",
        )

        return redirect(
            "Student:student_dissertation_proposal_edit",
            uuid=uuid,
        )

    if not proposal.abstract or not proposal.abstract.strip():

        messages.error(
            request,
            "Proposal abstract is required before submission.",
        )

        return redirect(
            "Student:student_dissertation_proposal_edit",
            uuid=uuid,
        )

    if len(proposal.abstract.strip()) < 50:

        messages.error(
            request,
            "Proposal abstract must contain at least 50 characters.",
        )

        return redirect(
            "Student:student_dissertation_proposal_edit",
            uuid=uuid,
        )

    if not proposal.proposal_file:

        messages.error(
            request,
            "Proposal file is required before submission.",
        )

        return redirect(
            "Student:student_dissertation_proposal_edit",
            uuid=uuid,
        )

    if not phd_student.advisor:

        messages.error(
            request,
            "A research advisor must be assigned before submitting the proposal.",
        )

        return redirect(
            "Student:student_dissertation_proposal_detail",
            uuid=uuid,
        )

    previous_status = proposal.status

    proposal.status = "ADVISOR_REVIEW"
    proposal.advisor_review_status = "PENDING"
    proposal.advisor_review_remarks = None
    proposal.advisor_reviewed_at = None
    proposal.result = "PENDING"
    proposal.submission_date = timezone.now().date()

    if previous_status == "REVISION_REQUIRED":
        proposal.resubmission_count += 1

    with transaction.atomic():

        proposal.save(
            update_fields=[
                "status",
                "advisor_review_status",
                "advisor_review_remarks",
                "advisor_reviewed_at",
                "result",
                "submission_date",
                "resubmission_count",
            ]
        )

        _create_dissertation_proposal_notification(
            user=phd_student.advisor.user,
            title="Dissertation Proposal Submitted for Review",
            message="A new dissertation proposal has been submitted and is waiting for your review.",
            notification_type="INFO",
        )

    current_submission_number = proposal.resubmission_count + 1

    messages.success(
        request,
        (
            "Dissertation proposal submitted successfully for advisor review. "
            f"Submission #{current_submission_number} is now under review."
        ),
    )

    return redirect(
        "Student:student_dissertation_proposal_detail",
        uuid=uuid,
    )


@login_required
def student_dissertation_proposal_detail(
    request,
    uuid,
):

    student = get_object_or_404(
        StudentProfile,
        user__uuid=uuid,
        user=request.user,
    )

    phd_student = get_object_or_404(
        PhDStudent.objects.select_related(
            "student",
            "student__user",
            "advisor",
            "advisor__user",
            "advisor__faculty_rank",
            "advisor__department",
            "phd_program",
            "phd_program__department",
            "doctoral_committee",
            "doctoral_committee__chair_faculty",
            "doctoral_committee__chair_faculty__user",
            "doctoral_committee__chair_faculty__faculty_rank",
            "doctoral_committee__chair_faculty__department",
        ).prefetch_related(
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
                ),
            )
        ),
        student=student,
    )

    proposal = get_object_or_404(
        DissertationProposal.objects.select_related(
            "phd_student",
            "phd_student__advisor",
            "phd_student__advisor__user",
            "approved_by",
            "approved_by__chair_faculty",
            "approved_by__chair_faculty__user",
            "finalized_by",
            "finalized_by__user",
        ),
        phd_student=phd_student,
    )

    advisor = phd_student.advisor

    committee = getattr(
        phd_student,
        "doctoral_committee",
        None,
    )

    chair_faculty = committee.chair_faculty if committee else None

    committee_members = (
        committee.committee_members.all()
        if committee
        else CommitteeMember.objects.none()
    )

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
            )
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

    preliminary_exam_passed = PreliminaryExamination.objects.filter(
        phd_student=phd_student,
        result="PASS",
    ).exists()

    proposal_eligible = coursework_completed and preliminary_exam_passed

    current_submission_number = (
        getattr(
            proposal,
            "resubmission_count",
            0,
        )
        + 1
    )

    can_edit = (
        proposal.status
        in [
            "DRAFT",
            "REVISION_REQUIRED",
        ]
        and proposal_eligible
    )

    can_submit = (
        proposal.status
        in [
            "DRAFT",
            "REVISION_REQUIRED",
        ]
        and proposal_eligible
        and bool(
            proposal.proposal_title and proposal.abstract and proposal.proposal_file
        )
        and bool(advisor)
    )

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
        latest_resubmission_request is not None
        and latest_resubmission_request.status == "PENDING"
    )

    resubmission_request_exists = latest_resubmission_request is not None

    can_request_resubmission = (
        proposal.status == "REJECTED" and not pending_resubmission_request
    )

    can_view_resubmission_request = latest_resubmission_request is not None

    context = {
        "uuid": uuid,
        "student": student,
        "phd_student": phd_student,
        "advisor": advisor,
        "committee": committee,
        "chair_faculty": chair_faculty,
        "committee_members": committee_members,
        "proposal": proposal,
        "can_edit": can_edit,
        "can_submit": can_submit,
        "coursework_completed": coursework_completed,
        "preliminary_exam_passed": preliminary_exam_passed,
        "proposal_eligible": proposal_eligible,
        "required_credits": required_credits,
        "completed_credits": completed_credits,
        "remaining_credits": max(
            required_credits - completed_credits,
            0,
        ),
        "current_submission_number": current_submission_number,
        "latest_resubmission_request": latest_resubmission_request,
        "pending_resubmission_request": pending_resubmission_request,
        "resubmission_request_exists": resubmission_request_exists,
        "can_request_resubmission": can_request_resubmission,
        "can_view_resubmission_request": can_view_resubmission_request,
    }

    return render(
        request,
        "Leo_Student/student_dissertation_proposal_detail.html",
        context,
    )


@login_required
def student_dissertation_proposal(
    request,
    uuid,
):

    student = get_object_or_404(
        StudentProfile,
        user__uuid=uuid,
        user=request.user,
    )

    phd_student = get_object_or_404(
        PhDStudent.objects.select_related(
            "phd_program",
            "student",
            "student__user",
            "advisor",
            "advisor__user",
        ),
        student=student,
    )

    proposal = DissertationProposal.objects.filter(
        phd_student=phd_student,
    ).first()

    if proposal:

        return redirect(
            "Student:student_dissertation_proposal_detail",
            uuid=uuid,
        )

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
            )
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

    preliminary_exam_passed = PreliminaryExamination.objects.filter(
        phd_student=phd_student,
        result="PASS",
    ).exists()

    proposal_eligible = coursework_completed and preliminary_exam_passed

    if not coursework_completed:

        messages.warning(
            request,
            (
                "You must complete all required coursework credits "
                "before creating a dissertation proposal."
            ),
        )

        form = DissertationProposalForm(
            phd_student=phd_student,
            coursework_completed=coursework_completed,
            preliminary_exam_passed=preliminary_exam_passed,
        )

        context = {
            "student": student,
            "phd_student": phd_student,
            "advisor": phd_student.advisor,
            "proposal": None,
            "form": form,
            "is_edit": False,
            "coursework_completed": coursework_completed,
            "preliminary_exam_passed": preliminary_exam_passed,
            "proposal_eligible": proposal_eligible,
            "required_credits": required_credits,
            "completed_credits": completed_credits,
            "remaining_credits": max(
                required_credits - completed_credits,
                0,
            ),
            "current_submission_number": 1,
        }

        return render(
            request,
            "Leo_Student/student_dissertation_proposal_form.html",
            context,
        )

    if not preliminary_exam_passed:

        messages.warning(
            request,
            (
                "You must pass the Preliminary / Qualifying Examination "
                "before creating a dissertation proposal."
            ),
        )

        form = DissertationProposalForm(
            phd_student=phd_student,
            coursework_completed=coursework_completed,
            preliminary_exam_passed=preliminary_exam_passed,
        )

        context = {
            "student": student,
            "phd_student": phd_student,
            "advisor": phd_student.advisor,
            "proposal": None,
            "form": form,
            "is_edit": False,
            "coursework_completed": coursework_completed,
            "preliminary_exam_passed": preliminary_exam_passed,
            "proposal_eligible": proposal_eligible,
            "required_credits": required_credits,
            "completed_credits": completed_credits,
            "remaining_credits": max(
                required_credits - completed_credits,
                0,
            ),
            "current_submission_number": 1,
        }

        return render(
            request,
            "Leo_Student/student_dissertation_proposal_form.html",
            context,
        )

    return redirect(
        "Student:student_dissertation_proposal_create",
        uuid=uuid,
    )


@login_required
def student_dissertation_proposal_resubmission_request(
    request,
    uuid,
):

    if request.method != "POST":

        return redirect(
            "Student:student_dissertation_proposal_detail",
            uuid=uuid,
        )

    student = get_object_or_404(
        StudentProfile.objects.select_related(
            "user",
        ),
        user=request.user,
        user__uuid=uuid,
    )

    phd_student = get_object_or_404(
        PhDStudent.objects.select_related(
            "student",
        ),
        student=student,
    )

    reason = request.POST.get(
        "reason",
        "",
    ).strip()

    assurance = request.POST.get(
        "assurance",
        "",
    ).strip()

    student_declaration = (
        request.POST.get(
            "student_declaration",
            "",
        )
        == "on"
    )

    if len(reason) < 20:

        messages.error(
            request,
            "The resubmission reason must contain at least 20 characters.",
        )

        return redirect(
            "Student:student_dissertation_proposal_detail",
            uuid=uuid,
        )

    if len(reason) > 1000:

        messages.error(
            request,
            "The resubmission reason cannot exceed 1000 characters.",
        )

        return redirect(
            "Student:student_dissertation_proposal_detail",
            uuid=uuid,
        )

    if len(assurance) < 20:

        messages.error(
            request,
            "The assurance must contain at least 20 characters.",
        )

        return redirect(
            "Student:student_dissertation_proposal_detail",
            uuid=uuid,
        )

    if len(assurance) > 1000:

        messages.error(
            request,
            "The assurance cannot exceed 1000 characters.",
        )

        return redirect(
            "Student:student_dissertation_proposal_detail",
            uuid=uuid,
        )

    if not student_declaration:

        messages.error(
            request,
            "Please accept the student declaration before submitting the request.",
        )

        return redirect(
            "Student:student_dissertation_proposal_detail",
            uuid=uuid,
        )

    with transaction.atomic():

        proposal = get_object_or_404(
            DissertationProposal.objects.select_for_update(),
            phd_student=phd_student,
        )

        if proposal.status != "REJECTED":

            messages.warning(
                request,
                (
                    "A resubmission request can only be submitted "
                    "for a rejected dissertation proposal."
                ),
            )

            return redirect(
                "Student:student_dissertation_proposal_detail",
                uuid=uuid,
            )

        pending_request = (
            DissertationProposalResubmissionRequest.objects.select_for_update()
            .filter(
                proposal=proposal,
                status="PENDING",
            )
            .order_by(
                "-requested_at",
                "-request_id",
            )
            .first()
        )

        if pending_request:

            messages.info(
                request,
                (
                    "A resubmission request has already been submitted "
                    "and is awaiting review."
                ),
            )

            return redirect(
                "Student:student_dissertation_proposal_detail",
                uuid=uuid,
            )

        last_request = (
            DissertationProposalResubmissionRequest.objects.filter(
                proposal=proposal,
            )
            .order_by(
                "-submission_number",
                "-request_id",
            )
            .first()
        )

        submission_number = last_request.submission_number + 1 if last_request else 1

        DissertationProposalResubmissionRequest.objects.create(
            proposal=proposal,
            submission_number=submission_number,
            reason=reason,
            assurance=assurance,
            student_declaration=True,
            status="PENDING",
        )

    messages.success(
        request,
        (
            "Your dissertation proposal resubmission request has been "
            "submitted successfully and is now awaiting Chair Faculty review."
        ),
    )

    return redirect(
        "Student:student_dissertation_proposal_detail",
        uuid=uuid,
    )


# ============================================================
# Research Milestones - Student
# ============================================================
@login_required
def student_research_milestone_list(
    request,
    uuid,
):
    phd_student = get_object_or_404(
        PhDStudent.objects.select_related(
            "student",
            "student__user",
            "phd_program",
            "advisor",
            "advisor__user",
        ),
        student__user__uuid=uuid,
    )

    if request.user != phd_student.student.user:
        messages.error(
            request,
            "You are not authorized to access these research milestones.",
        )

        return redirect(
            "phd_dashboard",
            uuid=uuid,
        )

    milestones = list(
        ResearchMilestone.objects.filter(
            phd_student=phd_student,
        )
        .select_related(
            "chair_faculty",
            "chair_faculty__user",
        )
        .prefetch_related(
            "submissions",
            "submissions__evaluations",
            "submissions__advisor_advices",
        )
        .order_by(
            "sequence_number",
        )
    )

    current_milestone = None

    for milestone in milestones:
        submissions = list(
            milestone.submissions.all().order_by(
                "-submission_number",
                "-submitted_at",
            )
        )

        milestone.latest_submission = submissions[0] if submissions else None

        milestone.submission_count = len(submissions)

        milestone.latest_evaluation = None
        milestone.latest_advice = None
        milestone.is_current = False
        milestone.can_submit = False
        milestone.action_type = None

        if milestone.latest_submission:
            evaluations = list(
                milestone.latest_submission.evaluations.all().order_by(
                    "-evaluated_at",
                )
            )

            milestone.latest_evaluation = evaluations[0] if evaluations else None

            advices = list(
                milestone.latest_submission.advisor_advices.all().order_by(
                    "-submitted_at",
                    "-created_at",
                )
            )

            milestone.latest_advice = advices[0] if advices else None

        if milestone.status in [
            "PENDING",
            "IN_PROGRESS",
            "REVISION_REQUIRED",
        ]:
            if milestone.latest_submission:
                submission_status = milestone.latest_submission.status

                if submission_status == "REVISION_REQUIRED":
                    milestone.can_submit = True
                    milestone.action_type = "RESUBMIT"

                elif submission_status in [
                    "SUBMITTED",
                    "UNDER_REVIEW",
                ]:
                    milestone.can_submit = False
                    milestone.action_type = "WAITING_EVALUATION"

                elif submission_status == "EVALUATED":
                    milestone.can_submit = False
                    milestone.action_type = "EVALUATED"

                else:
                    milestone.can_submit = True
                    milestone.action_type = "SUBMIT"

            else:
                milestone.can_submit = True
                milestone.action_type = "SUBMIT"

    active_milestones = [
        milestone for milestone in milestones if milestone.status != "COMPLETED"
    ]

    if active_milestones:
        current_milestone = max(
            active_milestones,
            key=lambda milestone: milestone.sequence_number,
        )

        current_milestone.is_current = True

    total_milestones = len(milestones)

    completed_milestones = sum(
        1 for milestone in milestones if milestone.status == "COMPLETED"
    )

    total_submissions = sum(milestone.submission_count for milestone in milestones)

    active_milestone_count = sum(
        1 for milestone in milestones if milestone.status != "COMPLETED"
    )

    overall_progress = max(
        (float(milestone.current_progress_percentage or 0) for milestone in milestones),
        default=0,
    )

    overall_progress = min(
        max(
            round(overall_progress),
            0,
        ),
        100,
    )

    current_milestone_progress = (
        float(current_milestone.current_progress_percentage or 0)
        if current_milestone
        else overall_progress
    )

    completed_progress = max(
        (
            float(milestone.current_progress_percentage or 0)
            for milestone in milestones
            if milestone.status == "COMPLETED"
        ),
        default=0,
    )

    remaining_progress = max(
        100 - overall_progress,
        0,
    )

    context = {
        "phd_student": phd_student,
        "student": phd_student.student,
        "milestones": milestones,
        "current_milestone": current_milestone,
        "total_milestones": total_milestones,
        "completed_milestones": completed_milestones,
        "active_milestones": active_milestone_count,
        "total_submissions": total_submissions,
        "total_progress": overall_progress,
        "overall_progress": overall_progress,
        "current_milestone_progress": current_milestone_progress,
        "completed_progress": completed_progress,
        "remaining_progress": remaining_progress,
    }
    print(
        "DEBUG RESEARCH PROGRESS:",
        overall_progress,
        current_milestone_progress,
        completed_progress,
        remaining_progress,
    )
    return render(
        request,
        "Leo_Student/Research/phdstudent_research_milestone_list.html",
        context,
    )


@login_required
def student_research_milestone_detail(
    request,
    uuid,
    milestone_id,
):

    phd_student = get_object_or_404(
        PhDStudent.objects.select_related(
            "student",
            "student__user",
            "phd_program",
            "advisor",
            "advisor__user",
        ),
        student__user__uuid=uuid,
    )

    if request.user != phd_student.student.user:
        messages.error(
            request,
            "You are not authorized to view this research milestone.",
        )

        return redirect(
            "phd_dashboard",
            uuid=uuid,
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
        phd_student=phd_student,
    )

    submissions = milestone.submissions.all().order_by(
        "-submission_number",
        "-submitted_at",
    )

    latest_submission = submissions.first()

    latest_evaluation = None
    chair_evaluation = None
    committee_evaluations = []

    latest_advice = None

    if latest_submission:

        evaluations = latest_submission.evaluations.all().order_by(
            "-evaluated_at",
        )

        latest_evaluation = evaluations.first()

        chair_evaluation = evaluations.filter(
            evaluator_role="CHAIR",
        ).first()

        committee_evaluations = evaluations.filter(
            evaluator_role="COMMITTEE_MEMBER",
        )

        latest_advice = (
            latest_submission.advisor_advices.all()
            .order_by(
                "-submitted_at",
                "-created_at",
            )
            .first()
        )

    can_submit = (
        milestone.status
        in [
            "PENDING",
            "IN_PROGRESS",
        ]
        and latest_submission is None
    )

    can_resubmit = (
        milestone.status == "IN_PROGRESS"
        and latest_submission is not None
        and latest_submission.status == "REVISION_REQUIRED"
    )

    has_submission_under_review = (
        latest_submission is not None
        and latest_submission.status
        in [
            "SUBMITTED",
            "UNDER_REVIEW",
        ]
    )

    is_completed = milestone.status == "COMPLETED"

    context = {
        "phd_student": phd_student,
        "student": phd_student.student,
        "advisor": phd_student.advisor,
        "milestone": milestone,
        "submissions": submissions,
        "latest_submission": latest_submission,
        "latest_evaluation": latest_evaluation,
        "chair_evaluation": chair_evaluation,
        "committee_evaluations": committee_evaluations,
        "latest_advice": latest_advice,
        "can_submit": can_submit,
        "can_resubmit": can_resubmit,
        "has_submission_under_review": has_submission_under_review,
        "is_completed": is_completed,
    }

    return render(
        request,
        "Leo_Student/Research/phdstudent_research_milestone_detail.html",
        context,
    )


@login_required
def student_research_milestone_submit(
    request,
    uuid,
    milestone_id,
):
    phd_student = get_object_or_404(
        PhDStudent.objects.select_related(
            "student",
            "student__user",
            "phd_program",
            "advisor",
            "advisor__user",
        ),
        student__user__uuid=uuid,
    )

    if request.user != phd_student.student.user:
        messages.error(
            request,
            "You are not authorized to submit research work for this student.",
        )

        return redirect(
            f"/student/{uuid}/research-milestones/",
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
        phd_student=phd_student,
    )

    milestone_detail_url = (
        f"/student/{uuid}/research-milestones/{milestone.milestone_id}/"
    )

    if milestone.status == "COMPLETED":
        messages.warning(
            request,
            "This research milestone has already been completed and cannot accept new submissions.",
        )

        return redirect(
            milestone_detail_url,
        )

    if milestone.status not in [
        "PENDING",
        "IN_PROGRESS",
    ]:
        messages.warning(
            request,
            "This research milestone is not currently active for submission.",
        )

        return redirect(
            milestone_detail_url,
        )

    latest_submission = (
        ResearchMilestoneSubmission.objects.filter(
            milestone=milestone,
        )
        .order_by(
            "-submission_number",
            "-submitted_at",
        )
        .first()
    )

    if latest_submission:
        if latest_submission.status in [
            "SUBMITTED",
            "UNDER_REVIEW",
        ]:
            messages.warning(
                request,
                "Your latest research submission is currently under evaluation.",
            )

            return redirect(
                milestone_detail_url,
            )

        if latest_submission.status == "EVALUATED":
            messages.info(
                request,
                "Your latest research submission has already been evaluated.",
            )

            return redirect(
                milestone_detail_url,
            )

        if latest_submission.status == "REVISION_REQUIRED":
            messages.info(
                request,
                "Your previous submission requires revision. Please use the resubmission option.",
            )

            return redirect(
                "student_research_milestone_resubmit",
                uuid=uuid,
                milestone_id=milestone.milestone_id,
            )

    if request.method == "POST":
        form = ResearchMilestoneSubmissionForm(
            request.POST,
            request.FILES,
            phd_student=phd_student,
            milestone=milestone,
            is_resubmission=False,
        )

        if form.is_valid():
            try:
                submission = form.save(
                    commit=True,
                )

                messages.success(
                    request,
                    "Research milestone submitted successfully.",
                )

                return redirect(
                    f"/student/{uuid}/research-milestones/{milestone.milestone_id}/",
                )

            except IntegrityError:
                messages.error(
                    request,
                    "This submission could not be created because the submission number already exists. Please try again.",
                )

        else:
            messages.error(
                request,
                "Unable to submit your research work. Please review the highlighted fields.",
            )

    else:
        form = ResearchMilestoneSubmissionForm(
            phd_student=phd_student,
            milestone=milestone,
            is_resubmission=False,
        )

    context = {
        "phd_student": phd_student,
        "student": phd_student.student,
        "milestone": milestone,
        "form": form,
        "latest_submission": latest_submission,
        "is_resubmission": False,
    }

    return render(
        request,
        "Leo_Student/Research/phdstudent_research_milestone_submit.html",
        context,
    )


@login_required
def student_research_milestone_submission_list(
    request,
    uuid,
    milestone_id=None,
    submission_id=None,
):
    phd_student = get_object_or_404(
        PhDStudent.objects.select_related(
            "student",
            "student__user",
        ),
        student__user__uuid=uuid,
    )

    if request.user != phd_student.student.user:
        messages.error(
            request,
            "You are not authorized to access these research submissions.",
        )

        return redirect(
            "phd_dashboard",
            uuid=uuid,
        )

    if milestone_id is not None:
        milestones = list(
            ResearchMilestone.objects.filter(
                pk=milestone_id,
                phd_student=phd_student,
            )
            .select_related(
                "chair_faculty",
                "chair_faculty__user",
            )
            .order_by(
                "sequence_number",
            )
        )
    else:
        milestones = list(
            ResearchMilestone.objects.filter(
                phd_student=phd_student,
            )
            .select_related(
                "chair_faculty",
                "chair_faculty__user",
            )
            .order_by(
                "sequence_number",
            )
        )

    milestone_ids = [milestone.milestone_id for milestone in milestones]

    all_submissions = list(
        ResearchMilestoneSubmission.objects.filter(
            milestone_id__in=milestone_ids,
        )
        .select_related(
            "milestone",
            "milestone__phd_student",
            "milestone__chair_faculty",
            "milestone__chair_faculty__user",
        )
        .prefetch_related(
            "evaluations",
            "evaluations__evaluator",
            "evaluations__evaluator__user",
            "advisor_advices",
            "advisor_advices__advisor",
            "advisor_advices__advisor__user",
        )
        .order_by(
            "milestone__sequence_number",
            "submission_number",
            "submitted_at",
        )
    )

    submissions_by_milestone = {}

    for submission in all_submissions:
        submissions_by_milestone.setdefault(
            submission.milestone_id,
            [],
        ).append(
            submission,
        )

    def get_field_value(obj, field):
        try:
            value = getattr(
                obj,
                field.name,
            )
        except Exception:
            return ""

        if value is None:
            return ""

        if field.choices:
            try:
                return getattr(
                    obj,
                    f"get_{field.name}_display",
                )()
            except Exception:
                pass

        if field.name.endswith("_id"):
            return value

        if field.get_internal_type() in [
            "DateTimeField",
            "DateField",
            "TimeField",
        ]:
            try:
                return value.strftime(
                    "%d %b %Y, %I:%M %p",
                )
            except Exception:
                return str(value)

        if field.get_internal_type() in [
            "FileField",
            "ImageField",
        ]:
            try:
                return value.name.split("/")[-1]
            except Exception:
                return str(value)

        if field.name in [
            "id",
            "evaluation_id",
            "advice_id",
            "submission_id",
        ]:
            return str(value)

        return str(value)

    def build_model_details(obj, excluded_fields=None):
        excluded_fields = excluded_fields or []

        details = []

        for field in obj._meta.fields:
            if field.name in excluded_fields:
                continue

            if field.name.endswith("_id"):
                continue

            value = get_field_value(
                obj,
                field,
            )

            if value in [
                "",
                None,
                "None",
            ]:
                continue

            details.append(
                {
                    "label": str(
                        field.verbose_name,
                    )
                    .replace(
                        "_",
                        " ",
                    )
                    .title(),
                    "value": value,
                }
            )

        return details

    milestone_groups = []

    total_versions = 0
    evaluated_count = 0
    revision_count = 0

    for milestone in milestones:
        milestone_submissions = submissions_by_milestone.get(
            milestone.milestone_id,
            [],
        )

        latest_submission = milestone_submissions[-1] if milestone_submissions else None

        version_history = []

        for submission in reversed(milestone_submissions):
            evaluations = list(
                submission.evaluations.all().order_by(
                    "-evaluated_at",
                )
            )

            advisor_advices = list(
                submission.advisor_advices.all().order_by(
                    "-submitted_at",
                    "-created_at",
                )
            )

            if evaluations:
                evaluated_count += 1

            if submission.status == "REVISION_REQUIRED":
                revision_count += 1

            evaluation_history = []

            for evaluation in evaluations:
                evaluator_name = "Faculty Evaluator"

                if getattr(
                    evaluation,
                    "evaluator",
                    None,
                ):
                    evaluator = evaluation.evaluator

                    if getattr(
                        evaluator,
                        "user",
                        None,
                    ):
                        evaluator_name = (
                            evaluator.user.get_full_name() or evaluator.user.username
                        )

                evaluation_history.append(
                    {
                        "role": (
                            evaluation.get_evaluator_role_display()
                            if hasattr(
                                evaluation,
                                "get_evaluator_role_display",
                            )
                            else getattr(
                                evaluation,
                                "evaluator_role",
                                "Faculty Evaluation",
                            )
                        ),
                        "evaluator_name": evaluator_name,
                        "evaluated_at": (
                            evaluation.evaluated_at.strftime(
                                "%d %b %Y, %I:%M %p",
                            )
                            if getattr(
                                evaluation,
                                "evaluated_at",
                                None,
                            )
                            else "-"
                        ),
                        "details": build_model_details(
                            evaluation,
                            excluded_fields=[
                                "id",
                                "evaluation_id",
                                "evaluator",
                                "evaluator_role",
                                "evaluated_at",
                                "created_at",
                                "updated_at",
                            ],
                        ),
                    }
                )

            advice_history = []

            for advice in advisor_advices:
                advisor_name = "Advisor"

                if getattr(
                    advice,
                    "advisor",
                    None,
                ):
                    advisor = advice.advisor

                    if getattr(
                        advisor,
                        "user",
                        None,
                    ):
                        advisor_name = (
                            advisor.user.get_full_name() or advisor.user.username
                        )

                advice_history.append(
                    {
                        "advisor_name": advisor_name,
                        "submitted_at": (
                            advice.submitted_at.strftime(
                                "%d %b %Y, %I:%M %p",
                            )
                            if getattr(
                                advice,
                                "submitted_at",
                                None,
                            )
                            else "-"
                        ),
                        "details": build_model_details(
                            advice,
                            excluded_fields=[
                                "id",
                                "advice_id",
                                "advisor",
                                "submitted_at",
                                "created_at",
                                "updated_at",
                            ],
                        ),
                    }
                )

            documents = []

            document_fields = [
                (
                    "Main Research Document",
                    "main_document",
                ),
                (
                    "Additional Document 1",
                    "additional_file_1",
                ),
                (
                    "Additional Document 2",
                    "additional_file_2",
                ),
                (
                    "Additional Document 3",
                    "additional_file_3",
                ),
            ]

            for label, field_name in document_fields:
                document = getattr(
                    submission,
                    field_name,
                    None,
                )

                if document:
                    documents.append(
                        {
                            "label": label,
                            "name": document.name.split("/")[-1],
                            "url": document.url,
                        }
                    )

            version_history.append(
                {
                    "submission": submission,
                    "evaluations": evaluation_history,
                    "advices": advice_history,
                    "documents": documents,
                    "remarks": (
                        submission.student_remarks
                        or "No remarks were added for this submission."
                    ),
                }
            )

        total_versions += len(milestone_submissions)

        can_resubmit = bool(
            latest_submission
            and latest_submission.status == "REVISION_REQUIRED"
            and milestone.status == "IN_PROGRESS"
        )

        milestone_groups.append(
            {
                "milestone": milestone,
                "latest_submission": latest_submission,
                "versions": version_history,
                "version_count": len(milestone_submissions),
                "can_resubmit": can_resubmit,
            }
        )

    context = {
        "phd_student": phd_student,
        "student": phd_student.student,
        "milestones": milestones,
        "milestone_groups": milestone_groups,
        "total_milestones": len(milestones),
        "total_versions": total_versions,
        "evaluated_count": evaluated_count,
        "revision_count": revision_count,
    }

    return render(
        request,
        "Leo_Student/Research/phdstudent_research_milestone_submission_list.html",
        context,
    )


@login_required
def student_research_milestone_submission_detail(
    request,
    uuid,
    milestone_id,
    submission_id,
):

    phd_student = get_object_or_404(
        PhDStudent.objects.select_related(
            "student",
            "student__user",
            "phd_program",
            "advisor",
            "advisor__user",
        ),
        student__user__uuid=uuid,
    )

    if request.user != phd_student.student.user:
        messages.error(
            request,
            "You are not authorized to access this research submission.",
        )

        return redirect(
            "phd_dashboard",
            uuid=uuid,
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
        phd_student=phd_student,
    )

    submission = get_object_or_404(
        ResearchMilestoneSubmission.objects.select_related(
            "milestone",
            "milestone__phd_student",
            "milestone__phd_student__student",
            "milestone__phd_student__student__user",
            "milestone__chair_faculty",
            "milestone__chair_faculty__user",
        ).prefetch_related(
            "evaluations",
            "evaluations__evaluator",
            "evaluations__evaluator__user",
            "advisor_advices",
            "advisor_advices__advisor",
            "advisor_advices__advisor__user",
        ),
        pk=submission_id,
        milestone=milestone,
    )

    submissions = ResearchMilestoneSubmission.objects.filter(
        milestone=milestone,
    ).order_by(
        "-submission_number",
        "-submitted_at",
    )

    evaluations = submission.evaluations.all().order_by(
        "-evaluated_at",
    )

    latest_evaluation = evaluations.first()

    chair_evaluation = evaluations.filter(
        evaluator_role="CHAIR",
    ).first()

    committee_evaluations = evaluations.filter(
        evaluator_role="COMMITTEE_MEMBER",
    )

    advisor_advices = submission.advisor_advices.all().order_by(
        "-submitted_at",
        "-created_at",
    )

    latest_advice = advisor_advices.first()

    can_resubmit = (
        submission == submissions.first()
        and submission.status == "REVISION_REQUIRED"
        and milestone.status == "IN_PROGRESS"
    )

    context = {
        "phd_student": phd_student,
        "student": phd_student.student,
        "advisor": phd_student.advisor,
        "milestone": milestone,
        "submissions": submissions,
        "submission": submission,
        "selected_submission": submission,
        "latest_submission": submissions.first(),
        "evaluations": evaluations,
        "latest_evaluation": latest_evaluation,
        "chair_evaluation": chair_evaluation,
        "committee_evaluations": committee_evaluations,
        "advisor_advices": advisor_advices,
        "latest_advice": latest_advice,
        "can_resubmit": can_resubmit,
        "is_view_mode": True,
    }

    return render(
        request,
        "Leo_Student/Research/phdstudent_research_milestone_submission_detail.html",
        context,
    )


@login_required
def student_research_milestone_resubmit(
    request,
    uuid,
    milestone_id,
):

    phd_student = get_object_or_404(
        PhDStudent.objects.select_related(
            "student",
            "student__user",
        ),
        student__user__uuid=uuid,
    )

    if request.user != phd_student.student.user:
        messages.error(
            request,
            "You are not authorized to resubmit research work for this student.",
        )

        return redirect(
            "Student:phd_dashboard",
            uuid=uuid,
        )

    milestone = get_object_or_404(
        ResearchMilestone.objects.select_related(
            "phd_student",
            "phd_student__student",
            "chair_faculty",
            "chair_faculty__user",
        ),
        pk=milestone_id,
        phd_student=phd_student,
    )

    latest_submission = (
        ResearchMilestoneSubmission.objects.filter(
            milestone=milestone,
        )
        .order_by(
            "-submission_number",
        )
        .first()
    )

    if not latest_submission:
        messages.error(
            request,
            "No previous research submission was found.",
        )

        return redirect(
            "Student:student_research_milestone_detail",
            uuid=uuid,
            milestone_id=milestone.milestone_id,
        )

    if latest_submission.status != "REVISION_REQUIRED":
        messages.warning(
            request,
            "Resubmission is available only when revision is required.",
        )

        return redirect(
            "Student:student_research_milestone_submission_detail",
            uuid=uuid,
            milestone_id=milestone.milestone_id,
            submission_id=latest_submission.submission_id,
        )

    if milestone.status != "IN_PROGRESS":
        messages.warning(
            request,
            "This research milestone is not currently active for resubmission.",
        )

        return redirect(
            "Student:student_research_milestone_submission_detail",
            uuid=uuid,
            milestone_id=milestone.milestone_id,
            submission_id=latest_submission.submission_id,
        )

    if request.method == "POST":

        form = ResearchMilestoneSubmissionForm(
            request.POST,
            request.FILES,
            phd_student=phd_student,
            milestone=milestone,
            is_resubmission=True,
        )

        if form.is_valid():

            try:

                submission = form.save(
                    commit=True,
                )

                messages.success(
                    request,
                    (
                        f"Research milestone resubmission "
                        f"#{submission.submission_number} submitted successfully."
                    ),
                )

                return redirect(
                    "Student:student_research_milestone_submission_list",
                    uuid=uuid,
                    milestone_id=milestone.milestone_id,
                )

            except IntegrityError:

                messages.error(
                    request,
                    "Unable to submit the revised research work. Please try again.",
                )

                return redirect(
                    "Student:student_research_milestone_submission_list",
                    uuid=uuid,
                    milestone_id=milestone.milestone_id,
                )

            except Exception:

                messages.error(
                    request,
                    "Unable to submit the revised research work. Please try again.",
                )

        else:

            messages.error(
                request,
                (
                    "Unable to submit the revised research work. "
                    "Please check the submitted information."
                ),
            )

    else:

        form = ResearchMilestoneSubmissionForm(
            phd_student=phd_student,
            milestone=milestone,
            is_resubmission=True,
        )

    context = {
        "phd_student": phd_student,
        "student": phd_student.student,
        "milestone": milestone,
        "latest_submission": latest_submission,
        "form": form,
        "is_resubmission": True,
    }

    return render(
        request,
        "Leo_Student/Research/phdstudent_research_milestone_submit.html",
        context,
    )


# ============================================================
# Research Publications - Student
# ============================================================


@login_required
def phdstudent_research_publication_list(request, uuid):

    phd_student = get_object_or_404(
        PhDStudent.objects.select_related(
            "student",
            "student__user",
            "phd_program",
        ),
        student__user__uuid=uuid,
    )

    if request.user != phd_student.student.user:

        messages.error(
            request,
            "You are not authorized to access research publications.",
        )

        return redirect(
            "phd_dashboard",
            uuid=uuid,
        )

    publications = (
        ResearchPublication.objects.filter(
            phd_student=phd_student,
        )
        .select_related(
            "phd_student",
            "milestone",
        )
        .order_by(
            "-publication_date",
            "-publication_id",
        )
    )

    return render(
        request,
        "Leo_Student/ResearchPublications/phdstudent_research_publication_list.html",
        {
            "phd_student": phd_student,
            "student": phd_student.student,
            "publications": publications,
        },
    )


@login_required
def phdstudent_research_publication_create(request, uuid):

    phd_student = get_object_or_404(
        PhDStudent.objects.select_related(
            "student",
            "student__user",
            "phd_program",
        ),
        student__user__uuid=uuid,
    )

    if request.user != phd_student.student.user:

        messages.error(
            request,
            "You are not authorized to create research publications.",
        )

        return redirect(
            "Student:phd_dashboard",
            uuid=uuid,
        )

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

    candidacy_approved = DoctoralCandidacy.objects.filter(
        phd_student=phd_student,
        candidacy_status="APPROVED",
    ).exists()

    completed_milestones = (
        ResearchMilestone.objects.filter(
            phd_student=phd_student,
            status="COMPLETED",
        )
        .exclude(
            milestone_id__in=ResearchPublication.objects.filter(
                phd_student=phd_student,
                milestone__isnull=False,
            ).values_list(
                "milestone_id",
                flat=True,
            )
        )
        .order_by(
            "sequence_number",
        )
    )

    checkpoint_errors = []

    if not coursework_completed:

        checkpoint_errors.append("Required PhD coursework has not been completed.")

    if not preliminary_exam_passed:

        checkpoint_errors.append(
            "Preliminary / Qualifying Examination has not been successfully completed and published."
        )

    if not proposal_approved:

        checkpoint_errors.append("Dissertation Proposal has not been approved.")

    if not candidacy_approved:

        checkpoint_errors.append("Doctoral Candidacy has not been approved.")

    if not completed_milestones.exists():

        checkpoint_errors.append(
            "At least one research milestone must be completed and available for publication linking."
        )

    if checkpoint_errors:

        messages.error(
            request,
            "Research publication cannot be added yet. " + " ".join(checkpoint_errors),
        )

        return redirect(
            "Student:phdstudent_research_publication_list",
            uuid=uuid,
        )

    if request.method == "POST":

        form = ResearchPublicationForm(
            request.POST,
            request.FILES,
            phd_student=phd_student,
            completed_milestones=completed_milestones,
        )

        if form.is_valid():

            try:

                publication = form.save(
                    commit=False,
                )

                publication.phd_student = phd_student

                publication.save()

                messages.success(
                    request,
                    "Research publication added successfully.",
                )

                return redirect(
                    "Student:phdstudent_research_publication_detail",
                    uuid=uuid,
                    publication_id=publication.publication_id,
                )

            except IntegrityError:

                messages.error(
                    request,
                    (
                        "Unable to add the research publication. "
                        "The selected milestone may already be linked to another publication."
                    ),
                )

        else:

            messages.error(
                request,
                (
                    "Unable to add the research publication. "
                    "Please correct the highlighted fields."
                ),
            )

    else:

        form = ResearchPublicationForm(
            phd_student=phd_student,
            completed_milestones=completed_milestones,
        )

    context = {
        "phd_student": phd_student,
        "student": phd_student.student,
        "form": form,
        "is_create": True,
        "is_update": False,
        "required_credits": required_credits,
        "completed_credits": completed_credits,
        "coursework_completed": coursework_completed,
        "preliminary_exam": preliminary_exam,
        "preliminary_exam_passed": preliminary_exam_passed,
        "proposal_approved": proposal_approved,
        "candidacy_approved": candidacy_approved,
        "completed_milestones": completed_milestones,
        "checkpoint_errors": checkpoint_errors,
    }

    return render(
        request,
        "Leo_Student/ResearchPublications/phdstudent_research_publication_form.html",
        context,
    )


@login_required
def phdstudent_research_publication_update(
    request,
    uuid,
    publication_id,
):

    phd_student = get_object_or_404(
        PhDStudent.objects.select_related(
            "student",
            "student__user",
            "phd_program",
        ),
        student__user__uuid=uuid,
    )

    if request.user != phd_student.student.user:

        messages.error(
            request,
            "You are not authorized to update this research publication.",
        )

        return redirect(
            "Student:phd_dashboard",
            uuid=uuid,
        )

    publication = get_object_or_404(
        ResearchPublication.objects.select_related(
            "phd_student",
            "milestone",
        ),
        publication_id=publication_id,
        phd_student=phd_student,
    )

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

    candidacy_approved = DoctoralCandidacy.objects.filter(
        phd_student=phd_student,
        candidacy_status="APPROVED",
    ).exists()

    completed_milestones = (
        ResearchMilestone.objects.filter(
            phd_student=phd_student,
            status="COMPLETED",
        )
        .filter(
            Q(milestone_id=publication.milestone_id)
            | ~Q(
                milestone_id__in=ResearchPublication.objects.filter(
                    phd_student=phd_student,
                    milestone__isnull=False,
                )
                .exclude(
                    publication_id=publication.publication_id,
                )
                .values_list(
                    "milestone_id",
                    flat=True,
                )
            )
        )
        .order_by(
            "sequence_number",
        )
    )

    if not coursework_completed:

        messages.error(
            request,
            "Publication update is unavailable because required coursework is incomplete.",
        )

        return redirect(
            "Student:phdstudent_research_publication_detail",
            uuid=uuid,
            publication_id=publication.publication_id,
        )

    if not preliminary_exam_passed:

        messages.error(
            request,
            "Publication update is unavailable because the Preliminary / Qualifying Examination is not successfully completed.",
        )

        return redirect(
            "Student:phdstudent_research_publication_detail",
            uuid=uuid,
            publication_id=publication.publication_id,
        )

    if not proposal_approved:

        messages.error(
            request,
            "Publication update is unavailable because the Dissertation Proposal is not approved.",
        )

        return redirect(
            "Student:phdstudent_research_publication_detail",
            uuid=uuid,
            publication_id=publication.publication_id,
        )

    if not candidacy_approved:

        messages.error(
            request,
            "Publication update is unavailable because Doctoral Candidacy is not approved.",
        )

        return redirect(
            "Student:phdstudent_research_publication_detail",
            uuid=uuid,
            publication_id=publication.publication_id,
        )

    if not completed_milestones.exists():

        messages.error(
            request,
            "Publication update is unavailable because no completed research milestone exists.",
        )

        return redirect(
            "Student:phdstudent_research_publication_detail",
            uuid=uuid,
            publication_id=publication.publication_id,
        )

    if request.method == "POST":

        form = ResearchPublicationForm(
            request.POST,
            request.FILES,
            instance=publication,
            phd_student=phd_student,
            completed_milestones=completed_milestones,
        )

        if form.is_valid():

            try:

                publication = form.save(
                    commit=False,
                )

                publication.phd_student = phd_student

                publication.save()

                messages.success(
                    request,
                    "Research publication updated successfully.",
                )

                return redirect(
                    "Student:phdstudent_research_publication_detail",
                    uuid=uuid,
                    publication_id=publication.publication_id,
                )

            except IntegrityError:

                messages.error(
                    request,
                    (
                        "Unable to update the research publication. "
                        "The selected milestone may already be linked to another publication."
                    ),
                )

        else:

            messages.error(
                request,
                (
                    "Unable to update the research publication. "
                    "Please correct the highlighted fields."
                ),
            )

    else:

        form = ResearchPublicationForm(
            instance=publication,
            phd_student=phd_student,
            completed_milestones=completed_milestones,
        )

    context = {
        "phd_student": phd_student,
        "student": phd_student.student,
        "publication": publication,
        "form": form,
        "is_create": False,
        "is_update": True,
        "required_credits": required_credits,
        "completed_credits": completed_credits,
        "coursework_completed": coursework_completed,
        "preliminary_exam": preliminary_exam,
        "preliminary_exam_passed": preliminary_exam_passed,
        "proposal_approved": proposal_approved,
        "candidacy_approved": candidacy_approved,
        "completed_milestones": completed_milestones,
    }

    return render(
        request,
        "Leo_Student/ResearchPublications/phdstudent_research_publication_form.html",
        context,
    )


@login_required
def phdstudent_research_publication_detail(
    request,
    uuid,
    publication_id,
):

    phd_student = get_object_or_404(
        PhDStudent.objects.select_related(
            "student",
            "student__user",
        ),
        student__user__uuid=uuid,
    )

    if request.user != phd_student.student.user:

        messages.error(
            request,
            "You are not authorized to view this research publication.",
        )

        return redirect(
            "phd_dashboard",
            uuid=uuid,
        )

    publication = get_object_or_404(
        ResearchPublication.objects.select_related(
            "phd_student",
            "milestone",
            "milestone__chair_faculty",
            "milestone__chair_faculty__user",
        ),
        publication_id=publication_id,
        phd_student=phd_student,
    )

    return render(
        request,
        "Leo_Student/ResearchPublications/phdstudent_research_publication_detail.html",
        {
            "phd_student": phd_student,
            "student": phd_student.student,
            "publication": publication,
        },
    )


# ============================================================
# FINAL DISSERTATION SUBMISSION - Student
# ============================================================


@login_required
def student_final_dissertation_submit(
    request,
    uuid,
):
    phd_student = get_object_or_404(
        PhDStudent.objects.select_related(
            "student",
            "student__user",
            "phd_program",
            "advisor",
            "advisor__user",
        ),
        student__user__uuid=uuid,
    )

    if request.user != phd_student.student.user:
        messages.error(
            request,
            "You are not authorized to submit a final dissertation.",
        )

        return redirect(
            "Student:phd_dashboard",
            uuid=uuid,
        )

    total_credits_required = phd_student.phd_program.total_credits_required

    completed_courseworks = FacultyCoursework.objects.filter(
        phd_student=phd_student,
        status="COMPLETED",
    ).select_related(
        "coursework",
    )

    completed_credits = sum(
        coursework.coursework.credits
        for coursework in completed_courseworks
        if coursework.coursework and coursework.coursework.credits
    )

    coursework_completed = completed_credits >= total_credits_required

    qualifying_exam_passed = PreliminaryExamination.objects.filter(
        phd_student=phd_student,
        exam_type__in=[
            "QUALIFYING",
            "PRELIMINARY",
        ],
        result="PASS",
        status="COMPLETED",
        is_published=True,
    ).exists()

    dissertation_proposal_approved = DissertationProposal.objects.filter(
        phd_student=phd_student,
        result="APPROVED",
    ).exists()

    candidacy_approved = DoctoralCandidacy.objects.filter(
        phd_student=phd_student,
        candidacy_status="APPROVED",
    ).exists()

    latest_research_milestone = (
        ResearchMilestone.objects.filter(
            phd_student=phd_student,
        )
        .order_by(
            "-sequence_number",
            "-created_at",
        )
        .first()
    )

    if latest_research_milestone:
        research_progress = min(
            max(
                round(
                    float(latest_research_milestone.current_progress_percentage or 0)
                ),
                0,
            ),
            100,
        )
    else:
        research_progress = 0

    research_completed = research_progress >= 100

    final_dissertation_eligible = all(
        [
            coursework_completed,
            qualifying_exam_passed,
            dissertation_proposal_approved,
            candidacy_approved,
            research_completed,
        ]
    )

    latest_submission = (
        FinalDissertationSubmission.objects.filter(
            phd_student=phd_student,
        )
        .order_by(
            "-submission_number",
            "-created_at",
        )
        .first()
    )

    if latest_submission and latest_submission.status in [
        "SUBMITTED",
        "ADVISOR_REVIEW",
        "COMMITTEE_EVALUATION",
        "CHAIR_REVIEW",
        "APPROVED",
    ]:
        messages.warning(
            request,
            (
                "Your latest final dissertation submission is "
                "already under review or has been approved."
            ),
        )

        return redirect(
            "Student:student_final_dissertation_detail",
            uuid=uuid,
        )

    if not final_dissertation_eligible:
        messages.error(
            request,
            (
                "You have not yet completed all requirements "
                "for final dissertation submission."
            ),
        )

        return redirect(
            "Student:phd_dashboard",
            uuid=uuid,
        )

    is_resubmission = latest_submission is not None and latest_submission.status in [
        "REVISION_REQUIRED",
        "REJECTED",
    ]

    if request.method == "POST":
        form = FinalDissertationSubmissionForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            submission = form.save(
                commit=False,
            )

            submission.phd_student = phd_student

            if latest_submission:
                submission.submission_number = latest_submission.submission_number + 1

                submission.resubmission_count = latest_submission.resubmission_count + 1

                submission.version = f"Version {submission.submission_number}.0"
            else:
                submission.submission_number = 1
                submission.resubmission_count = 0
                submission.version = "Version 1.0"

            submission.submission_date = timezone.localdate()
            submission.submitted_at = timezone.now()
            submission.status = "ADVISOR_REVIEW"

            submission.save()

            messages.success(
                request,
                (
                    "Your final dissertation has been submitted successfully "
                    "and sent to your advisor for review."
                ),
            )

            return redirect(
                "Student:student_final_dissertation_detail",
                uuid=uuid,
            )
    else:
        form = FinalDissertationSubmissionForm()

    context = {
        "phd_student": phd_student,
        "form": form,
        "latest_submission": latest_submission,
        "is_resubmission": is_resubmission,
        "coursework_completed": coursework_completed,
        "completed_credits": completed_credits,
        "total_credits_required": total_credits_required,
        "qualifying_exam_passed": qualifying_exam_passed,
        "dissertation_proposal_approved": dissertation_proposal_approved,
        "candidacy_approved": candidacy_approved,
        "research_completed": research_completed,
        "research_progress": research_progress,
        "final_dissertation_eligible": final_dissertation_eligible,
    }

    return render(
        request,
        "Leo_Student/FinalDissertation/student_final_dissertation_submit.html",
        context,
    )


@login_required
def student_final_dissertation_detail(
    request,
    uuid,
):
    phd_student = get_object_or_404(
        PhDStudent.objects.select_related(
            "student",
            "student__user",
            "phd_program",
            "advisor",
            "advisor__user",
            "doctoral_committee",
            "doctoral_committee__chair_faculty",
            "doctoral_committee__chair_faculty__user",
        ).prefetch_related(
            Prefetch(
                "doctoral_committee__committee_members",
                queryset=CommitteeMember.objects.select_related(
                    "faculty",
                    "faculty__user",
                ).order_by("role"),
            )
        ),
        student__user__uuid=uuid,
    )

    # =========================================================
    # AUTHORIZATION
    # =========================================================

    if request.user != phd_student.student.user:
        messages.error(
            request,
            "You are not authorized to access final dissertation details.",
        )

        return redirect(
            "Student:phd_dashboard",
            uuid=uuid,
        )

    # =========================================================
    # SUBMISSIONS
    # =========================================================

    submissions = list(
        FinalDissertationSubmission.objects.filter(
            phd_student=phd_student,
        ).order_by(
            "-submission_number",
            "-created_at",
        )
    )

    latest_submission = submissions[0] if submissions else None

    # =========================================================
    # DOCTORAL COMMITTEE
    # =========================================================

    committee = getattr(
        phd_student,
        "doctoral_committee",
        None,
    )

    committee_members = []

    if committee:
        committee_members = list(committee.committee_members.all())

    # Dynamic committee total
    #
    # Example:
    # Chair + Co-Chair              = 2
    # Chair + Co-Chair + Member     = 3
    # Chair + Co-Chair + 2 Members  = 4
    #
    committee_member_count = len(committee_members)

    # =========================================================
    # DEFAULT VALUES
    # =========================================================

    advisor_evaluation = None
    committee_evaluations = []

    submitted_committee_evaluation_count = 0
    advisor_completed = False
    committee_evaluation_completed = False
    chair_completed = False

    # =========================================================
    # CURRENT SUBMISSION EVALUATIONS
    # =========================================================

    if latest_submission:

        # -----------------------------------------------------
        # ADVISOR EVALUATION
        # -----------------------------------------------------

        advisor_evaluation = (
            FinalDissertationAdvisorEvaluation.objects.filter(
                submission=latest_submission,
            )
            .select_related(
                "advisor",
                "advisor__user",
            )
            .order_by(
                "-submitted_at",
                "-created_at",
            )
            .first()
        )

        advisor_completed = bool(advisor_evaluation and advisor_evaluation.is_submitted)

        # -----------------------------------------------------
        # COMMITTEE EVALUATIONS
        # -----------------------------------------------------

        committee_evaluations = list(
            FinalDissertationCommitteeEvaluation.objects.filter(
                submission=latest_submission,
            )
            .select_related(
                "committee_member",
                "committee_member__faculty",
                "committee_member__faculty__user",
            )
            .order_by(
                "-submitted_at",
                "-created_at",
            )
        )

        # Only submitted evaluations count
        submitted_committee_evaluation_count = sum(
            1 for evaluation in committee_evaluations if evaluation.is_submitted
        )

        # Committee is completed only when
        # EVERY committee member has submitted
        committee_evaluation_completed = (
            committee_member_count > 0
            and submitted_committee_evaluation_count >= committee_member_count
        )

        # -----------------------------------------------------
        # CHAIR FINALIZATION
        # -----------------------------------------------------

        chair_completed = (
            latest_submission.status == "APPROVED"
            and latest_submission.finalized_at is not None
            and latest_submission.finalized_by_id is not None
        )

    # =========================================================
    # CURRENT WORKFLOW STAGE
    # =========================================================

    current_stage_map = {
        "SUBMITTED": "Submitted",
        "ADVISOR_REVIEW": "Advisor Review",
        "COMMITTEE_EVALUATION": "Committee Evaluation",
        "CHAIR_REVIEW": "Chair Finalization",
        "APPROVED": "Completed",
        "REVISION_REQUIRED": "Revision Required",
        "REJECTED": "Rejected",
    }

    current_stage = (
        current_stage_map.get(
            latest_submission.status,
            "Review In Progress",
        )
        if latest_submission
        else "Not Submitted"
    )

    # =========================================================
    # SUBMISSION HISTORY
    # =========================================================

    submission_history = []

    for submission in submissions:

        history_advisor_evaluation = (
            FinalDissertationAdvisorEvaluation.objects.filter(
                submission=submission,
                is_submitted=True,
            )
            .order_by(
                "-submitted_at",
                "-created_at",
            )
            .first()
        )

        history_advisor_completed = history_advisor_evaluation is not None

        history_committee_evaluations = list(
            FinalDissertationCommitteeEvaluation.objects.filter(
                submission=submission,
                is_submitted=True,
            )
        )

        history_committee_count = len(history_committee_evaluations)

        history_committee_completed = (
            committee_member_count > 0
            and history_committee_count >= committee_member_count
        )

        submission_history.append(
            {
                "submission": submission,
                "advisor_completed": history_advisor_completed,
                "committee_completed": history_committee_completed,
            }
        )

    # =========================================================
    # CONTEXT
    # =========================================================

    context = {
        # -----------------------------------------------------
        # STUDENT
        # -----------------------------------------------------
        "phd_student": phd_student,
        # -----------------------------------------------------
        # SUBMISSIONS
        # -----------------------------------------------------
        "submissions": submissions,
        "latest_submission": latest_submission,
        "submission_count": len(submissions),
        "submission_history": submission_history,
        # -----------------------------------------------------
        # WORKFLOW
        # -----------------------------------------------------
        "current_stage": current_stage,
        # -----------------------------------------------------
        # ADVISOR
        # -----------------------------------------------------
        "advisor_evaluation": advisor_evaluation,
        "advisor_completed": advisor_completed,
        # -----------------------------------------------------
        # COMMITTEE
        # -----------------------------------------------------
        "committee": committee,
        "committee_members": committee_members,
        "committee_member_count": committee_member_count,
        "committee_evaluations": committee_evaluations,
        "submitted_committee_evaluation_count": (submitted_committee_evaluation_count),
        "committee_evaluation_completed": (committee_evaluation_completed),
        # -----------------------------------------------------
        # CHAIR
        # -----------------------------------------------------
        "chair_completed": chair_completed,
    }

    return render(
        request,
        "Leo_Student/FinalDissertation/student_final_dissertation_detail.html",
        context,
    )


@login_required
def phdstudent_defense_detail(
    request,
    uuid,
):
    student = get_object_or_404(
        StudentProfile.objects.select_related(
            "user",
        ),
        user__uuid=uuid,
        user=request.user,
    )

    phd_student = get_object_or_404(
        PhDStudent.objects.select_related(
            "student",
            "student__user",
            "advisor",
            "advisor__user",
            "advisor__faculty_rank",
            "advisor__department",
            "phd_program",
            "phd_program__department",
            "doctoral_committee",
            "doctoral_committee__chair_faculty",
            "doctoral_committee__chair_faculty__user",
            "doctoral_committee__chair_faculty__faculty_rank",
            "doctoral_committee__chair_faculty__department",
        ),
        student=student,
    )

    defense = get_object_or_404(
        DissertationDefense.objects.select_related(
            "phd_student",
            "phd_student__student",
            "phd_student__student__user",
        ).prefetch_related(
            "evaluations",
        ),
        phd_student=phd_student,
    )

    committee = getattr(
        phd_student,
        "doctoral_committee",
        None,
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

    required_members = []

    if committee:
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

    required_member_ids = [member.pk for member in required_members]

    evaluations = defense.evaluations.all()

    submitted_evaluations = evaluations.filter(
        committee_member_id__in=required_member_ids,
        is_submitted=True,
    ).count()

    total_evaluations = len(required_members)

    pending_evaluations = max(
        total_evaluations - submitted_evaluations,
        0,
    )

    evaluation_percentage = (
        round(submitted_evaluations / total_evaluations * 100)
        if total_evaluations
        else 0
    )

    final_result = defense.result

    committee_decision = defense.committee_decision

    final_comments = defense.final_comments

    defense_finalized = final_result in {
        "PASS",
        "FAIL",
    }

    if defense_finalized:
        submitted_evaluations = total_evaluations
        pending_evaluations = 0
        evaluation_percentage = 100

    chair_faculty = committee.chair_faculty if committee else None

    context = {
        "student": student,
        "phd_student": phd_student,
        "defense": defense,
        "committee": committee,
        "committee_members": committee_members,
        "required_members": required_members,
        "chair_faculty": chair_faculty,
        "advisor": phd_student.advisor,
        "evaluations": evaluations,
        "total_evaluations": total_evaluations,
        "submitted_evaluations": submitted_evaluations,
        "pending_evaluations": pending_evaluations,
        "evaluation_percentage": evaluation_percentage,
        "final_result": final_result,
        "committee_decision": committee_decision,
        "final_comments": final_comments,
        "defense_finalized": defense_finalized,
    }

    return render(
        request,
        "Leo_Student/FinalDissertation/Defense/phdstudent_defense_detail.html",
        context,
    )


from django.http import JsonResponse


@login_required
def student_advisor_message_list(request, uuid):
    student = get_object_or_404(
        StudentProfile,
        user__uuid=uuid,
        user=request.user,
    )

    phd_student = get_object_or_404(
        PhDStudent.objects.select_related(
            "student",
            "student__user",
            "advisor",
            "advisor__user",
            "advisor__faculty_rank",
            "advisor__department",
        ),
        student=student,
    )

    advisor = phd_student.advisor

    if not advisor:
        if request.method == "POST" or request.GET.get("chat_poll") == "1":
            return JsonResponse(
                {
                    "success": False,
                    "error": "No advisor is assigned to this PhD student.",
                },
                status=400,
            )

        return render(
            request,
            "Leo_Student/student_advisor_message_list.html",
            {
                "student": student,
                "phd_student": phd_student,
                "advisor": advisor,
                "messages": AdvisorStudentMessage.objects.none(),
                "unread_count": 0,
            },
        )

    if request.method == "GET" and request.GET.get("chat_poll") == "1":
        after_id = request.GET.get("after_id", "0")
        mark_read = request.GET.get("mark_read") == "1"

        try:
            after_id = int(after_id)
        except (TypeError, ValueError):
            after_id = 0

        if mark_read:
            AdvisorStudentMessage.objects.filter(
                phd_student=phd_student,
                advisor=advisor,
                sender_role="ADVISOR",
                is_read=False,
            ).update(
                is_read=True,
                read_at=timezone.now(),
            )

        new_messages = (
            AdvisorStudentMessage.objects.filter(
                phd_student=phd_student,
                advisor=advisor,
                message_id__gt=after_id,
            )
            .prefetch_related("attachments")
            .order_by("message_id")
        )

        serialized_messages = []

        for chat_message in new_messages:
            attachments = []

            for attachment in chat_message.attachments.all():
                attachments.append(
                    {
                        "attachment_id": attachment.attachment_id,
                        "attachment_url": attachment.attachment.url,
                        "attachment_name": attachment.original_name,
                        "file_size": attachment.file_size,
                        "content_type": attachment.content_type or "",
                    }
                )

            created_at = timezone.localtime(chat_message.created_at)

            serialized_messages.append(
                {
                    "message_id": chat_message.message_id,
                    "sender_role": chat_message.sender_role,
                    "message": chat_message.message or "",
                    "attachments": attachments,
                    "created_at": created_at.strftime("%I:%M %p"),
                    "created_date": created_at.strftime("%Y-%m-%d"),
                }
            )

        unread_count = AdvisorStudentMessage.objects.filter(
            phd_student=phd_student,
            advisor=advisor,
            sender_role="ADVISOR",
            is_read=False,
        ).count()

        return JsonResponse(
            {
                "success": True,
                "messages": serialized_messages,
                "unread_count": unread_count,
            }
        )

    if request.method == "POST":
        message_text = request.POST.get(
            "message",
            "",
        ).strip()

        attachments = request.FILES.getlist("attachments")

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
            advisor=advisor,
            sender_role="STUDENT",
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
                "message": chat_message.message or "",
                "attachments": attachment_data,
                "created_at": created_at.strftime("%I:%M %p"),
                "created_date": created_at.strftime("%Y-%m-%d"),
            }
        )

    messages = (
        AdvisorStudentMessage.objects.filter(
            phd_student=phd_student,
            advisor=advisor,
        )
        .prefetch_related("attachments")
        .order_by("-created_at")
    )

    unread_count = messages.filter(
        sender_role="ADVISOR",
        is_read=False,
    ).count()

    context = {
        "student": student,
        "phd_student": phd_student,
        "advisor": advisor,
        "messages": messages,
        "unread_count": unread_count,
    }

    return render(
        request,
        "Leo_Student/student_advisor_message_list.html",
        context,
    )


# ===========================================================
# Leo's Code End
# ============================================================
