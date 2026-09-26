from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.contenttypes.models import ContentType
from Staff.models import StaffProfile

from django.core.paginator import Paginator

from Faculty.leo.models import (
    FacultyCoursework,
    ResearchMilestone,
)

from Students.Leo_Student.models import (
    DissertationDefense,
    DissertationProposal,
    DoctoralCandidacy,
    DoctoralCommittee,
    FinalDissertationSubmission,
    Graduation,
    PhDStudent,
    PreliminaryExamination,
    PhDVideoEvidence,
)

from .forms import GraduationCreationForm


def get_current_staff(request):

    return get_object_or_404(
        StaffProfile.objects.select_related("user"),
        user=request.user,
        employment_status="ACTIVE",
    )


def get_graduation_checkpoints(student):

    checkpoints = []

    admission_completed = bool(student.admission_date)

    checkpoints.append(
        {
            "key": "admission",
            "label": "Admission Completed",
            "completed": admission_completed,
            "message": (
                "Admission record is available."
                if admission_completed
                else "Admission record has not been completed."
            ),
        }
    )

    advisor = getattr(
        student,
        "advisor",
        None,
    )

    advisor_completed = bool(advisor)

    checkpoints.append(
        {
            "key": "advisor",
            "label": "Advisor Assigned",
            "completed": advisor_completed,
            "message": (
                f"Advisor assigned: {advisor}"
                if advisor_completed
                else "Advisor has not been assigned."
            ),
        }
    )

    committee = getattr(
        student,
        "doctoral_committee",
        None,
    )

    chair_faculty = committee.chair_faculty if committee else None

    chair_assigned = bool(committee and chair_faculty)

    checkpoints.append(
        {
            "key": "chair_faculty",
            "label": "Chair Faculty Assigned",
            "completed": chair_assigned,
            "message": (
                f"Chair Faculty assigned: {chair_faculty}"
                if chair_assigned
                else "Chair Faculty has not been assigned."
            ),
        }
    )

    committee_formed = bool(committee and committee.committee_members.exists())

    checkpoints.append(
        {
            "key": "committee",
            "label": "Doctoral Committee Formed",
            "completed": committee_formed,
            "message": (
                "Doctoral committee has been formed."
                if committee_formed
                else "Doctoral committee has not been formed."
            ),
        }
    )

    required_credits = int(
        getattr(
            student.phd_program,
            "total_credits_required",
            0,
        )
        or 0
    )

    completed_credits = (
        FacultyCoursework.objects.filter(
            phd_student=student,
            status="COMPLETED",
        )
        .aggregate(total=Sum("coursework__credits"))
        .get("total")
        or 0
    )

    coursework_assigned = FacultyCoursework.objects.filter(
        phd_student=student,
    ).exists()

    coursework_completed = bool(
        required_credits > 0 and completed_credits >= required_credits
    )

    checkpoints.append(
        {
            "key": "coursework_assigned",
            "label": "Coursework Assigned",
            "completed": coursework_assigned,
            "message": (
                "Required coursework has been assigned."
                if coursework_assigned
                else "Coursework has not been assigned."
            ),
        }
    )

    checkpoints.append(
        {
            "key": "coursework_completed",
            "label": "Coursework Completed",
            "completed": coursework_completed,
            "message": (
                f"Completed {completed_credits} of {required_credits} required credits."
            ),
        }
    )

    examinations = PreliminaryExamination.objects.filter(
        phd_student=student,
        exam_type__in=[
            "QUALIFYING",
            "PRELIMINARY",
        ],
    ).order_by(
        "-exam_date",
        "-prelim_exam_id",
    )

    exam_assigned = examinations.exists()

    exam_passed = examinations.filter(
        result="PASS",
        status="COMPLETED",
        is_published=True,
    ).exists()

    checkpoints.append(
        {
            "key": "exam_assigned",
            "label": "Preliminary / Qualifying Examination Assigned",
            "completed": exam_assigned,
            "message": (
                "Preliminary / Qualifying examination is assigned."
                if exam_assigned
                else "Preliminary / Qualifying examination has not been assigned."
            ),
        }
    )

    checkpoints.append(
        {
            "key": "exam_passed",
            "label": "Preliminary / Qualifying Examination Passed",
            "completed": exam_passed,
            "message": (
                "Preliminary / Qualifying examination was completed, passed, and published."
                if exam_passed
                else "Preliminary / Qualifying examination has not been successfully completed and published."
            ),
        }
    )

    proposal = getattr(
        student,
        "dissertation_proposal",
        None,
    )

    proposal_submitted = bool(
        proposal
        and (
            proposal.submission_date
            or proposal.status
            in [
                "SUBMITTED",
                "ADVISOR_REVIEW",
                "COMMITTEE_EVALUATION",
                "FINAL_REVIEW",
                "APPROVED",
                "REJECTED",
                "REVISION_REQUIRED",
            ]
        )
    )

    proposal_approved = bool(proposal and proposal.result == "APPROVED")

    checkpoints.append(
        {
            "key": "proposal_submitted",
            "label": "Dissertation Proposal Submitted",
            "completed": proposal_submitted,
            "message": (
                "Dissertation proposal has been submitted."
                if proposal_submitted
                else "Dissertation proposal has not been submitted."
            ),
        }
    )

    checkpoints.append(
        {
            "key": "proposal_approved",
            "label": "Dissertation Proposal Approved",
            "completed": proposal_approved,
            "message": (
                "Dissertation proposal has been approved."
                if proposal_approved
                else "Dissertation proposal has not been approved."
            ),
        }
    )

    candidacy = getattr(
        student,
        "doctoral_candidacy",
        None,
    )

    candidacy_approved = bool(candidacy and candidacy.candidacy_status == "APPROVED")

    checkpoints.append(
        {
            "key": "candidacy",
            "label": "Doctoral Candidacy Approved",
            "completed": candidacy_approved,
            "message": (
                "Doctoral candidacy has been approved."
                if candidacy_approved
                else "Doctoral candidacy has not been approved."
            ),
        }
    )

    milestones = list(
        ResearchMilestone.objects.filter(
            phd_student=student,
        ).order_by(
            "-sequence_number",
            "-created_at",
        )
    )

    milestones_assigned = bool(milestones)

    latest_milestone = milestones[0] if milestones else None

    research_progress = (
        min(
            max(
                round(float(latest_milestone.current_progress_percentage or 0)),
                0,
            ),
            100,
        )
        if latest_milestone
        else 0
    )

    research_completed = research_progress >= 100

    checkpoints.append(
        {
            "key": "research_milestones",
            "label": "Research Milestones Assigned",
            "completed": milestones_assigned,
            "message": (
                f"{len(milestones)} research milestone(s) assigned."
                if milestones_assigned
                else "No research milestones have been assigned."
            ),
        }
    )

    checkpoints.append(
        {
            "key": "research_progress",
            "label": "Research Progress Reached 100%",
            "completed": research_completed,
            "message": (f"Current research progress: {research_progress}%."),
        }
    )

    latest_final_dissertation = (
        FinalDissertationSubmission.objects.filter(
            phd_student=student,
        )
        .order_by(
            "-submission_number",
            "-created_at",
        )
        .first()
    )

    final_dissertation_approved = bool(
        latest_final_dissertation and latest_final_dissertation.status == "APPROVED"
    )

    checkpoints.append(
        {
            "key": "final_dissertation",
            "label": "Final Dissertation Approved",
            "completed": final_dissertation_approved,
            "message": (
                "Final dissertation has been approved."
                if final_dissertation_approved
                else "Final dissertation has not been approved."
            ),
        }
    )

    defense = getattr(
        student,
        "dissertation_defense",
        None,
    )

    defense_passed = bool(defense and defense.result == "PASS")

    checkpoints.append(
        {
            "key": "defense",
            "label": "Dissertation Defense Passed",
            "completed": defense_passed,
            "message": (
                "Dissertation defense was passed."
                if defense_passed
                else "Dissertation defense has not been passed."
            ),
        }
    )

    eligible = all(checkpoint["completed"] for checkpoint in checkpoints)

    return {
        "eligible": eligible,
        "checkpoints": checkpoints,
        "research_progress": research_progress,
        "completed_credits": completed_credits,
        "required_credits": required_credits,
        "latest_final_dissertation": latest_final_dissertation,
        "defense": defense,
        "committee": committee,
    }


@login_required
def graduation_list(request):
    get_current_staff(request)

    base_graduations = Graduation.objects.select_related(
        "phd_student__student__user",
        "created_by__user",
        "chair_approved_by__user",
    )

    search = request.GET.get(
        "search",
        "",
    ).strip()

    status = request.GET.get(
        "status",
        "",
    ).strip()

    graduations = base_graduations

    if search:
        graduations = graduations.filter(
            Q(phd_student__student__user__first_name__icontains=search)
            | Q(phd_student__student__user__last_name__icontains=search)
            | Q(phd_student__student__user__email__icontains=search)
        )

    if status:
        graduations = graduations.filter(
            status=status,
        )

    graduations = graduations.order_by(
        "-created_at",
    )

    paginator = Paginator(
        graduations,
        8,
    )

    page_number = request.GET.get(
        "page",
        1,
    )

    page_obj = paginator.get_page(
        page_number,
    )

    context = {
        "graduations": page_obj,
        "page_obj": page_obj,
        "is_paginated": page_obj.has_other_pages(),
        "search": search,
        "status": status,
        "status_choices": Graduation.STATUS_CHOICES,
        "total_count": base_graduations.count(),
        "pending_count": base_graduations.filter(
            status="PENDING_CHAIR_APPROVAL",
        ).count(),
        "approved_count": base_graduations.filter(
            status="APPROVED",
        ).count(),
        "completed_count": base_graduations.filter(
            status="COMPLETED",
        ).count(),
    }

    return render(
        request,
        "Leo_staff/graduation/graduation_list.html",
        context,
    )


@login_required
def graduation_create(request):

    staff = get_current_staff(request)

    if request.method == "POST":

        form = GraduationCreationForm(
            request.POST,
        )

        if form.is_valid():

            student = form.cleaned_data["phd_student"]

            eligibility = get_graduation_checkpoints(student)

            if not eligibility["eligible"]:
                failed_checkpoints = [
                    checkpoint["label"]
                    for checkpoint in eligibility["checkpoints"]
                    if not checkpoint["completed"]
                ]

                messages.error(
                    request,
                    (
                        "Graduation cannot be created. "
                        "The following requirements are incomplete: "
                        + ", ".join(failed_checkpoints)
                    ),
                )

                return render(
                    request,
                    "Leo_staff/graduation/graduation_form.html",
                    {
                        "form": form,
                        "is_create": True,
                        "is_update": False,
                        "eligibility": eligibility,
                    },
                )

            if Graduation.objects.filter(
                phd_student=student,
            ).exists():

                messages.error(
                    request,
                    "A graduation record already exists for this student.",
                )

                return redirect(
                    "Leo_Staff:graduation_list",
                )

            graduation = form.save(
                commit=False,
            )

            graduation.phd_student = student
            graduation.dissertation_accepted = True
            graduation.defense_passed = True
            graduation.created_by = staff
            graduation.status = "PENDING_CHAIR_APPROVAL"
            graduation.save()

            messages.success(
                request,
                "Graduation record created and sent to the Chair Faculty for approval.",
            )

            return redirect(
                "Leo_Staff:graduation_detail",
                graduation_id=graduation.graduation_id,
            )

    else:

        form = GraduationCreationForm()

    context = {
        "form": form,
        "is_create": True,
        "is_update": False,
        "eligibility": None,
    }

    return render(
        request,
        "Leo_staff/graduation/graduation_form.html",
        context,
    )


@login_required
def graduation_update(
    request,
    graduation_id,
):

    get_current_staff(request)

    graduation = get_object_or_404(
        Graduation.objects.select_related(
            "phd_student__student__user",
            "created_by__user",
        ),
        graduation_id=graduation_id,
    )

    if graduation.status != "PENDING_CHAIR_APPROVAL":
        messages.error(
            request,
            "Only graduations pending Chair approval can be updated.",
        )

        return redirect(
            "Leo_Staff:graduation_detail",
            graduation_id=graduation.graduation_id,
        )

    if request.method == "POST":

        form = GraduationCreationForm(
            request.POST,
            instance=graduation,
        )

        if form.is_valid():

            student = form.cleaned_data["phd_student"]

            eligibility = get_graduation_checkpoints(student)

            if not eligibility["eligible"]:

                failed_checkpoints = [
                    checkpoint["label"]
                    for checkpoint in eligibility["checkpoints"]
                    if not checkpoint["completed"]
                ]

                messages.error(
                    request,
                    (
                        "Graduation cannot be updated because "
                        "the following requirements are incomplete: "
                        + ", ".join(failed_checkpoints)
                    ),
                )

                return render(
                    request,
                    "Leo_staff/graduation/graduation_form.html",
                    {
                        "form": form,
                        "is_create": False,
                        "is_update": True,
                        "graduation": graduation,
                        "eligibility": eligibility,
                    },
                )

            graduation = form.save(
                commit=False,
            )

            graduation.dissertation_accepted = True
            graduation.defense_passed = True
            graduation.status = "PENDING_CHAIR_APPROVAL"
            graduation.save()

            messages.success(
                request,
                "Graduation details updated successfully.",
            )

            return redirect(
                "Leo_Staff:graduation_detail",
                graduation_id=graduation.graduation_id,
            )

    else:

        form = GraduationCreationForm(
            instance=graduation,
        )

    context = {
        "form": form,
        "graduation": graduation,
        "is_create": False,
        "is_update": True,
        "eligibility": None,
    }

    return render(
        request,
        "Leo_staff/graduation/graduation_form.html",
        context,
    )


@login_required
def graduation_detail(
    request,
    graduation_id,
):

    get_current_staff(request)

    graduation = get_object_or_404(
        Graduation.objects.select_related(
            "phd_student__student__user",
            "phd_student__phd_program",
            "created_by__user",
            "chair_approved_by__user",
        ),
        graduation_id=graduation_id,
    )

    student = graduation.phd_student

    eligibility = get_graduation_checkpoints(student)

    latest_final_dissertation = (
        FinalDissertationSubmission.objects.filter(
            phd_student=student,
        )
        .order_by(
            "-submission_number",
            "-created_at",
        )
        .first()
    )

    defense = getattr(
        student,
        "dissertation_defense",
        None,
    )

    committee = getattr(
        student,
        "doctoral_committee",
        None,
    )

    graduation_content_type = ContentType.objects.get_for_model(
        graduation,
    )

    video_evidence = (
        PhDVideoEvidence.objects.filter(
            phd_student=student,
            evidence_type="GRADUATION",
            target_content_type=graduation_content_type,
            target_object_id=graduation.pk,
        )
        .select_related(
            "uploaded_by",
        )
        .first()
    )

    graduation_approved = graduation.status == "APPROVED"

    context = {
        "graduation": graduation,
        "phd_student": student,
        "student": student.student,
        "eligibility": eligibility,
        "latest_final_dissertation": latest_final_dissertation,
        "defense": defense,
        "committee": committee,
        "video_evidence": video_evidence,
        "graduation_approved": graduation_approved,
    }

    return render(
        request,
        "Leo_staff/graduation/graduation_detail.html",
        context,
    )


@login_required
def graduation_check_eligibility(
    request,
):

    get_current_staff(request)

    student_id = request.GET.get(
        "student_id",
    )

    if not student_id:
        return JsonResponse(
            {
                "success": False,
                "message": "Please select a PhD student.",
            },
            status=400,
        )

    student = get_object_or_404(
        PhDStudent.objects.select_related(
            "student__user",
            "phd_program",
            "advisor",
            "doctoral_committee",
            "doctoral_committee__chair_faculty",
        ),
        pk=student_id,
    )

    eligibility = get_graduation_checkpoints(student)

    existing_graduation = Graduation.objects.filter(
        phd_student=student,
    ).first()

    return JsonResponse(
        {
            "success": True,
            "eligible": eligibility["eligible"],
            "student": {
                "id": student.pk,
                "name": str(student.student),
            },
            "checkpoints": eligibility["checkpoints"],
            "research_progress": eligibility["research_progress"],
            "completed_credits": eligibility["completed_credits"],
            "required_credits": eligibility["required_credits"],
            "existing_graduation": bool(existing_graduation),
        }
    )


ALLOWED_VIDEO_EVIDENCE_TYPES = {
    "PRELIMINARY_EXAMINATION": {
        "model": PreliminaryExamination,
        "label": "Preliminary / Qualifying Examination",
    },
    "DISSERTATION_PROPOSAL": {
        "model": DissertationProposal,
        "label": "Dissertation Proposal Submission / Hearing",
    },
    "DOCTORAL_CANDIDACY": {
        "model": DoctoralCandidacy,
        "label": "Doctoral Candidacy",
    },
    "DISSERTATION_DEFENSE": {
        "model": DissertationDefense,
        "label": "Dissertation Defense",
    },
    "FINAL_DISSERTATION_SUBMISSION": {
        "model": FinalDissertationSubmission,
        "label": "Final Dissertation Submission / Approval",
    },
    "GRADUATION": {
        "model": Graduation,
        "label": "Graduation",
    },
}


def get_current_staff(request):
    return get_object_or_404(
        StaffProfile.objects.select_related("user"),
        user=request.user,
        employment_status="ACTIVE",
    )


def get_preliminary_exam_evaluation_state(examination):
    committee = getattr(examination.phd_student, "doctoral_committee", None)
    required_ids = set()

    if committee:
        required_ids.update(
            committee.committee_members.values_list("faculty_id", flat=True)
        )

    advisor_id = examination.phd_student.advisor_id
    chair_id = committee.chair_faculty_id if committee else None

    if advisor_id and advisor_id != chair_id:
        required_ids.add(advisor_id)

    submitted_count = PreliminaryExamEvaluation.objects.filter(
        examination=examination,
        faculty_id__in=required_ids,
        is_submitted=True,
    ).count()

    total = len(required_ids)

    return {
        "total": total,
        "submitted": submitted_count,
        "pending": max(total - submitted_count, 0),
        "all_submitted": total > 0 and submitted_count == total,
    }


def get_video_evidence_targets(phd_student_id, evidence_type):
    config = ALLOWED_VIDEO_EVIDENCE_TYPES.get(evidence_type)

    if not config:
        return {
            "targets": [],
            "message": "Select a valid evidence type.",
            "state": "INVALID_TYPE",
        }

    model = config["model"]

    if model is PreliminaryExamination:
        records = list(
            PreliminaryExamination.objects.filter(
                phd_student_id=phd_student_id,
                status="COMPLETED",
            ).order_by(
                "-exam_date",
                "-start_time",
            )
        )

        if not records:
            return {
                "targets": [],
                "message": "No completed examination is available for this student.",
                "state": "NO_COMPLETED_EXAM",
            }

        eligible = []

        for record in records:
            eligible.append(
                {
                    "id": record.pk,
                    "title": record.title
                    or f"{record.get_exam_type_display()} Examination",
                    "date": record.exam_date.isoformat() if record.exam_date else "",
                    "status": record.get_status_display(),
                    "meta": record.get_result_display(),
                    "eligible": True,
                }
            )

        return {
            "targets": eligible,
            "message": (
                "Only completed examinations are shown."
                if eligible
                else "No completed examination is available for video evidence."
            ),
            "state": "AVAILABLE" if eligible else "NO_COMPLETED_EXAM",
        }

    if model is DissertationProposal:
        records = list(
            DissertationProposal.objects.filter(
                phd_student_id=phd_student_id,
            ).order_by(
                "-submission_date",
                "-proposal_id",
            )
        )

        if not records:
            return {
                "targets": [],
                "message": "No dissertation proposal record has been created for this student.",
                "state": "NO_RECORD",
            }

        eligible = []

        for record in records:
            result = getattr(record, "result", None)

            if result == "PENDING":
                continue

            eligible.append(
                {
                    "id": record.pk,
                    "title": record.proposal_title,
                    "date": (
                        record.hearing_date.isoformat()
                        if record.hearing_date
                        else (
                            record.submission_date.isoformat()
                            if record.submission_date
                            else ""
                        )
                    ),
                    "status": record.get_result_display(),
                    "meta": (
                        record.submission_date.isoformat()
                        if record.submission_date
                        else ""
                    ),
                    "eligible": True,
                }
            )

        return {
            "targets": eligible,
            "message": (
                "No completed dissertation proposal is available for this student."
                if not eligible
                else "Completed dissertation proposal records are available."
            ),
            "state": "AVAILABLE" if eligible else "NOT_COMPLETED",
        }

    if model is DoctoralCandidacy:
        record = DoctoralCandidacy.objects.filter(
            phd_student_id=phd_student_id,
        ).first()

        if not record:
            return {
                "targets": [],
                "message": "No doctoral candidacy record has been created for this student.",
                "state": "NO_RECORD",
            }

        if record.candidacy_status != "APPROVED":
            return {
                "targets": [],
                "message": "Doctoral candidacy has not been approved yet.",
                "state": "NOT_COMPLETED",
            }

        return {
            "targets": [
                {
                    "id": record.pk,
                    "title": "Doctoral Candidacy",
                    "date": (
                        record.candidacy_date.isoformat()
                        if record.candidacy_date
                        else ""
                    ),
                    "status": record.get_candidacy_status_display(),
                    "meta": (
                        record.approval_date.isoformat() if record.approval_date else ""
                    ),
                    "eligible": True,
                }
            ],
            "message": "Approved doctoral candidacy record is available.",
            "state": "AVAILABLE",
        }

    if model is DissertationDefense:
        record = DissertationDefense.objects.filter(
            phd_student_id=phd_student_id,
        ).first()

        if not record:
            return {
                "targets": [],
                "message": "No dissertation defense record has been created for this student.",
                "state": "NO_RECORD",
            }

        if not record.defense_date:
            return {
                "targets": [],
                "message": "The dissertation defense has not been completed yet.",
                "state": "NOT_COMPLETED",
            }

        result = getattr(record, "result", None)
        if result == "PENDING":
            return {
                "targets": [],
                "message": "The dissertation defense result is still pending.",
                "state": "RESULT_PENDING",
            }

        return {
            "targets": [
                {
                    "id": record.pk,
                    "title": "Dissertation Defense",
                    "date": record.defense_date.isoformat(),
                    "status": record.get_result_display(),
                    "meta": record.location or "Location not available",
                    "eligible": True,
                }
            ],
            "message": "Completed dissertation defense record is available.",
            "state": "AVAILABLE",
        }

    if model is FinalDissertationSubmission:
        records = list(
            FinalDissertationSubmission.objects.filter(
                phd_student_id=phd_student_id,
            ).order_by(
                "-submission_number",
                "-created_at",
            )
        )

        if not records:
            return {
                "targets": [],
                "message": "No final dissertation submission record has been created for this student.",
                "state": "NO_RECORD",
            }

        eligible = []
        for record in records:
            status_value = getattr(record, "status", None)
            if status_value in {"PENDING", "DRAFT", "UNDER_REVIEW", "REJECTED"}:
                continue
            eligible.append(
                {
                    "id": record.pk,
                    "title": record.dissertation_title,
                    "date": (
                        record.submission_date.isoformat()
                        if record.submission_date
                        else ""
                    ),
                    "status": record.get_status_display(),
                    "meta": f"Version {record.version}",
                    "eligible": True,
                }
            )

        return {
            "targets": eligible,
            "message": (
                "No completed final dissertation submission is available."
                if not eligible
                else "Completed final dissertation submission records are available."
            ),
            "state": "AVAILABLE" if eligible else "NOT_COMPLETED",
        }

    if model is Graduation:
        record = Graduation.objects.filter(
            phd_student_id=phd_student_id,
            status="APPROVED",
        ).first()

        if not record:
            return {
                "targets": [],
                "message": "No approved graduation is available for this student.",
                "state": "NOT_APPROVED",
            }

        return {
            "targets": [
                {
                    "id": record.pk,
                    "title": "Graduation",
                    "date": (
                        record.graduation_date.isoformat()
                        if getattr(record, "graduation_date", None)
                        else ""
                    ),
                    "status": "Approved",
                    "meta": "",
                    "eligible": True,
                }
            ],
            "message": "Approved graduation is available for video evidence.",
            "state": "AVAILABLE",
        }
    return {
        "targets": [],
        "message": "No target records are available for the selected evidence type.",
        "state": "NO_RECORD",
    }


def get_video_evidence_target(evidence_type, phd_student_id, target_id):
    config = ALLOWED_VIDEO_EVIDENCE_TYPES.get(evidence_type)

    if not config:
        return None

    return get_object_or_404(
        config["model"],
        pk=target_id,
        phd_student_id=phd_student_id,
    )


def is_video_evidence_target_eligible(evidence_type, target):
    if evidence_type == "PRELIMINARY_EXAMINATION":
        return target.status == "COMPLETED"

    if evidence_type == "DISSERTATION_PROPOSAL":
        return getattr(target, "result", None) != "PENDING"

    if evidence_type == "DOCTORAL_CANDIDACY":
        return target.candidacy_status == "APPROVED"

    if evidence_type == "DISSERTATION_DEFENSE":
        return (
            bool(target.defense_date) and getattr(target, "result", None) != "PENDING"
        )

    if evidence_type == "FINAL_DISSERTATION_SUBMISSION":
        status_value = getattr(target, "status", None)
        return status_value not in {
            None,
            "PENDING",
            "DRAFT",
            "UNDER_REVIEW",
            "REJECTED",
        }

    if evidence_type == "GRADUATION":
        return target.status == "APPROVED"

    return False


def validate_video_file(video):
    if not video:
        return "Please select a video file."

    allowed_extensions = {".mp4", ".webm", ".ogg", ".mov"}
    allowed_content_types = {
        "video/mp4",
        "video/webm",
        "video/ogg",
        "video/quicktime",
    }

    file_name = video.name.lower()
    extension = file_name[file_name.rfind(".") :] if "." in file_name else ""

    if extension not in allowed_extensions:
        return "Only MP4, WebM, OGG and MOV video files are allowed."

    if video.content_type and video.content_type not in allowed_content_types:
        return "The selected file is not recognized as a supported video format."

    return None


@login_required
def video_evidence_dashboard(request, uuid):
    staff = get_current_staff(request)

    if request.user.uuid != uuid:
        return redirect(
            "Leo_Staff:video_evidence_dashboard",
            uuid=request.user.uuid,
        )

    video_evidences = PhDVideoEvidence.objects.select_related(
        "phd_student__student__user",
        "phd_student__phd_program",
        "uploaded_by",
    ).order_by("-uploaded_at")

    search = request.GET.get("search", "").strip()
    evidence_type = request.GET.get("evidence_type", "").strip()

    if search:
        video_evidences = video_evidences.filter(
            Q(phd_student__student__user__first_name__icontains=search)
            | Q(phd_student__student__user__last_name__icontains=search)
            | Q(phd_student__student__user__email__icontains=search)
        )

    if evidence_type:
        video_evidences = video_evidences.filter(evidence_type=evidence_type)

    paginator = Paginator(video_evidences, 8)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "staff": staff,
        "video_evidences": page_obj,
        "page_obj": page_obj,
        "is_paginated": page_obj.has_other_pages(),
        "search": search,
        "evidence_type": evidence_type,
        "evidence_type_choices": PhDVideoEvidence.EVIDENCE_TYPE_CHOICES,
        "total_count": paginator.count,
    }

    return render(
        request,
        "Leo_staff/video_evidence/video_evidence_dashboard.html",
        context,
    )


@login_required
def video_evidence_create(request, uuid):
    staff = get_current_staff(request)

    if request.user.uuid != uuid:
        return redirect(
            "Leo_Staff:video_evidence_create",
            uuid=request.user.uuid,
        )

    if request.GET.get("load_targets"):
        student_id = request.GET.get("student_id")
        evidence_type = request.GET.get("evidence_type")

        if not student_id or not evidence_type:
            return JsonResponse(
                {
                    "success": True,
                    "targets": [],
                    "message": "Select a student and evidence type.",
                    "state": "INCOMPLETE",
                }
            )

        get_object_or_404(PhDStudent, pk=student_id)
        target_state = get_video_evidence_targets(
            student_id,
            evidence_type,
        )

        return JsonResponse(
            {
                "success": True,
                **target_state,
            }
        )

    allowed_evidence_types = list(ALLOWED_VIDEO_EVIDENCE_TYPES.keys())

    phd_students = PhDStudent.objects.select_related(
        "student__user",
        "phd_program",
    ).order_by(
        "student__user__first_name",
        "student__user__last_name",
    )

    evidence_type_choices = [
        choice
        for choice in PhDVideoEvidence.EVIDENCE_TYPE_CHOICES
        if choice[0] in allowed_evidence_types
    ]

    form_errors = []

    if request.method == "POST":
        student_id = request.POST.get("phd_student")
        evidence_type = request.POST.get("evidence_type")
        target_id = request.POST.get("target")
        video = request.FILES.get("video")
        return_url = request.POST.get("return_url")

        student = None
        target = None

        if not student_id:
            form_errors.append("Please select a PhD student.")
        else:
            student = get_object_or_404(
                PhDStudent,
                pk=student_id,
            )

        if evidence_type not in allowed_evidence_types:
            form_errors.append("Please select a valid evidence type.")

        if not target_id:
            form_errors.append("Please select a completed target record.")

        video_error = validate_video_file(video)

        if video_error:
            form_errors.append(video_error)

        if student and evidence_type in allowed_evidence_types and target_id:
            try:
                target = get_video_evidence_target(
                    evidence_type,
                    student.pk,
                    target_id,
                )
            except Exception:
                target = None

            if target is None:
                form_errors.append(
                    "The selected target record does not belong to the selected student."
                )
            elif not is_video_evidence_target_eligible(
                evidence_type,
                target,
            ):
                form_errors.append(
                    "The selected target record is not yet eligible for video evidence."
                )

        if not form_errors:
            content_type = ContentType.objects.get_for_model(
                target,
            )

            PhDVideoEvidence.objects.create(
                phd_student=student,
                evidence_type=evidence_type,
                target_content_type=content_type,
                target_object_id=target.pk,
                video=video,
                uploaded_by=request.user,
            )

            messages.success(
                request,
                "Video evidence uploaded successfully.",
            )

            if return_url and url_has_allowed_host_and_scheme(
                return_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(return_url)

            return redirect(
                "Leo_Staff:video_evidence_dashboard",
                uuid=request.user.uuid,
            )

    context = {
        "staff": staff,
        "phd_students": phd_students,
        "evidence_type_choices": evidence_type_choices,
        "allowed_evidence_types": allowed_evidence_types,
        "is_update": False,
        "video_evidence": None,
        "form_errors": form_errors,
    }

    return render(
        request,
        "Leo_staff/video_evidence/video_evidence_form.html",
        context,
    )


@login_required
def video_evidence_update(request, uuid, video_evidence_id):
    staff = get_current_staff(request)

    if request.user.uuid != uuid:
        return redirect(
            "Leo_Staff:video_evidence_update",
            uuid=request.user.uuid,
            video_evidence_id=video_evidence_id,
        )

    video_evidence = get_object_or_404(
        PhDVideoEvidence.objects.select_related(
            "phd_student__student__user",
            "phd_student__phd_program",
            "target_content_type",
            "uploaded_by",
        ),
        video_evidence_id=video_evidence_id,
    )

    allowed_evidence_types = list(ALLOWED_VIDEO_EVIDENCE_TYPES.keys())
    phd_students = PhDStudent.objects.select_related(
        "student__user",
        "phd_program",
    ).order_by(
        "student__user__first_name",
        "student__user__last_name",
    )

    evidence_type_choices = [
        choice
        for choice in PhDVideoEvidence.EVIDENCE_TYPE_CHOICES
        if choice[0] in allowed_evidence_types
    ]

    form_errors = []

    if request.method == "POST":
        student_id = request.POST.get("phd_student")
        evidence_type = request.POST.get("evidence_type")
        target_id = request.POST.get("target")
        video = request.FILES.get("video")

        student = None
        target = None

        if not student_id:
            form_errors.append("Please select a PhD student.")
        else:
            student = get_object_or_404(PhDStudent, pk=student_id)

        if evidence_type not in allowed_evidence_types:
            form_errors.append("Please select a valid evidence type.")

        if not target_id:
            form_errors.append("Please select a completed target record.")

        if video:
            video_error = validate_video_file(video)
            if video_error:
                form_errors.append(video_error)

        if student and evidence_type in allowed_evidence_types and target_id:
            try:
                target = get_video_evidence_target(
                    evidence_type,
                    student.pk,
                    target_id,
                )
            except Exception:
                target = None

            if target is None:
                form_errors.append(
                    "The selected target record does not belong to the selected student."
                )
            elif not is_video_evidence_target_eligible(evidence_type, target):
                form_errors.append(
                    "The selected target record is not yet eligible for video evidence."
                )

        if not form_errors:
            video_evidence.phd_student = student
            video_evidence.evidence_type = evidence_type
            video_evidence.target_content_type = ContentType.objects.get_for_model(
                target
            )
            video_evidence.target_object_id = target.pk

            if video:
                video_evidence.video = video

            video_evidence.save()

            messages.success(request, "Video evidence updated successfully.")

            return redirect(
                "Leo_Staff:video_evidence_dashboard",
                uuid=request.user.uuid,
            )

    context = {
        "staff": staff,
        "phd_students": phd_students,
        "evidence_type_choices": evidence_type_choices,
        "allowed_evidence_types": allowed_evidence_types,
        "is_update": True,
        "video_evidence": video_evidence,
        "form_errors": form_errors,
    }

    return render(
        request,
        "Leo_staff/video_evidence/video_evidence_form.html",
        context,
    )

    staff = get_current_staff(request)

    if request.user.uuid != uuid:
        return redirect(
            "Leo_Staff:video_evidence_dashboard",
            uuid=request.user.uuid,
        )

    video_evidences = PhDVideoEvidence.objects.select_related(
        "phd_student__student__user",
        "phd_student__phd_program",
        "uploaded_by",
    ).order_by("-uploaded_at")

    search = request.GET.get("search", "").strip()
    evidence_type = request.GET.get("evidence_type", "").strip()

    if search:
        video_evidences = video_evidences.filter(
            Q(phd_student__student__user__first_name__icontains=search)
            | Q(phd_student__student__user__last_name__icontains=search)
            | Q(phd_student__student__user__email__icontains=search)
        )

    if evidence_type:
        video_evidences = video_evidences.filter(evidence_type=evidence_type)

    paginator = Paginator(video_evidences, 8)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "staff": staff,
        "video_evidences": page_obj,
        "page_obj": page_obj,
        "is_paginated": page_obj.has_other_pages(),
        "search": search,
        "evidence_type": evidence_type,
        "evidence_type_choices": PhDVideoEvidence.EVIDENCE_TYPE_CHOICES,
        "total_count": paginator.count,
    }

    return render(
        request,
        "Leo_staff/video_evidence/video_evidence_dashboard.html",
        context,
    )

    staff = get_current_staff(request)

    if request.user.uuid != uuid:
        return redirect(
            "Leo_Staff:video_evidence_update",
            uuid=request.user.uuid,
            video_evidence_id=video_evidence_id,
        )

    allowed_evidence_types = [
        "PRELIMINARY_EXAMINATION",
        "DISSERTATION_PROPOSAL",
        "DOCTORAL_CANDIDACY",
        "DISSERTATION_DEFENSE",
        "FINAL_DISSERTATION_SUBMISSION",
    ]

    video_evidence = get_object_or_404(
        PhDVideoEvidence.objects.select_related(
            "phd_student__student__user",
            "phd_student__phd_program",
            "uploaded_by",
        ),
        video_evidence_id=video_evidence_id,
    )

    if video_evidence.evidence_type not in allowed_evidence_types:
        messages.error(
            request,
            "This video evidence type cannot be managed from the Staff portal.",
        )

        return redirect(
            "Leo_Staff:video_evidence_dashboard",
            uuid=request.user.uuid,
        )

    phd_students = PhDStudent.objects.select_related(
        "student__user",
        "phd_program",
    ).order_by(
        "student__user__first_name",
        "student__user__last_name",
    )

    evidence_type_choices = [
        choice
        for choice in PhDVideoEvidence.EVIDENCE_TYPE_CHOICES
        if choice[0] in allowed_evidence_types
    ]

    form_errors = []

    if request.method == "POST":
        student_id = request.POST.get("phd_student")
        evidence_type = request.POST.get("evidence_type")
        target_id = request.POST.get("target")
        video = request.FILES.get("video")

        student = None

        if not student_id:
            form_errors.append("Please select a PhD student.")
        else:
            student = get_object_or_404(
                PhDStudent,
                pk=student_id,
            )

        if evidence_type not in allowed_evidence_types:
            form_errors.append("Please select a valid evidence type.")

        if not target_id:
            form_errors.append("Please select a target record.")

        target = None

        if student and evidence_type in allowed_evidence_types and target_id:
            try:
                target = get_video_evidence_target(
                    evidence_type,
                    student.pk,
                    target_id,
                )
            except Exception:
                target = None

            if target is None:
                form_errors.append(
                    "The selected target record does not belong to the selected student."
                )

        if video:
            video_error = validate_video_file(video)

            if video_error:
                form_errors.append(video_error)

        if not form_errors:
            content_type = ContentType.objects.get_for_model(target)

            video_evidence.phd_student = student
            video_evidence.evidence_type = evidence_type
            video_evidence.target_content_type = content_type
            video_evidence.target_object_id = target.pk

            if video:
                video_evidence.video = video

            video_evidence.save()

            messages.success(
                request,
                "Video evidence updated successfully.",
            )

            return redirect(
                "Leo_Staff:video_evidence_dashboard",
                uuid=request.user.uuid,
            )

    context = {
        "staff": staff,
        "phd_students": phd_students,
        "evidence_type_choices": evidence_type_choices,
        "allowed_evidence_types": allowed_evidence_types,
        "is_update": True,
        "video_evidence": video_evidence,
        "form_errors": form_errors,
    }

    return render(
        request,
        "Leo_staff/video_evidence/video_evidence_form.html",
        context,
    )
