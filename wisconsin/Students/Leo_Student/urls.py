## Leo's Code Start ##

from django.urls import path

from . import views

urlpatterns = [
    path(
        "phd-dashboard/<uuid:uuid>/",
        views.phd_dashboard,
        name="phd_dashboard",
    ),
    path(
        "<uuid:uuid>/coursework/",
        views.student_coursework_list,
        name="student_coursework_list",
    ),
    path(
        "<uuid:uuid>/coursework/<int:coursework_id>/submit/",
        views.student_coursework_submit,
        name="student_coursework_submit",
    ),
    path(
        "<uuid:uuid>/coursework/submissions/",
        views.student_coursework_submissions,
        name="student_coursework_submissions",
    ),
    path(
        "<uuid:uuid>/qualifying-examination/",
        views.student_qualifying_exam_list,
        name="student_qualifying_exam_list",
    ),
    path(
        "<uuid:uuid>/qualifying-examination/<int:exam_id>/",
        views.student_qualifying_exam_detail,
        name="student_qualifying_exam_detail",
    ),
    path(
        "<uuid:uuid>/dissertation/",
        views.student_dissertation_list,
        name="student_dissertation_list",
    ),
    path(
        "<uuid:uuid>/dissertation/proposal/create/",
        views.student_dissertation_proposal_create,
        name="student_dissertation_proposal_create",
    ),
    path(
        "<uuid:uuid>/dissertation/proposal/edit/",
        views.student_dissertation_proposal_edit,
        name="student_dissertation_proposal_edit",
    ),
    path(
        "<uuid:uuid>/dissertation/proposal/submit/",
        views.student_dissertation_proposal_submit,
        name="student_dissertation_proposal_submit",
    ),
    path(
        "<uuid:uuid>/dissertation/proposal/detail/",
        views.student_dissertation_proposal_detail,
        name="student_dissertation_proposal_detail",
    ),
    path(
        "<uuid:uuid>/advisory-committee/",
        views.student_advisory_committee,
        name="student_advisory_committee",
    ),
    path(
        "student/dissertation/detail/<uuid:uuid>/",
        views.student_dissertation_detail,
        name="student_dissertation_detail",
    ),
    path(
        "<uuid:uuid>/dissertation/proposal/",
        views.student_dissertation_proposal,
        name="student_dissertation_proposal",
    ),
    path(
        "dissertation/proposal/resubmission-request/<uuid:uuid>/",
        views.student_dissertation_proposal_resubmission_request,
        name="student_dissertation_proposal_resubmission_request",
    ),
    # ==============================
    # Research Milestones
    # ==============================
    path(
        "<uuid:uuid>/research-milestones/",
        views.student_research_milestone_list,
        name="student_research_milestone_list",
    ),
    path(
        "<uuid:uuid>/research-milestones/submissions/",
        views.student_research_milestone_submission_list,
        name="student_research_milestone_submission_list_all",
    ),
    path(
        "<uuid:uuid>/research-milestones/<int:milestone_id>/",
        views.student_research_milestone_detail,
        name="student_research_milestone_detail",
    ),
    path(
        "<uuid:uuid>/research-milestones/<int:milestone_id>/submit/",
        views.student_research_milestone_submit,
        name="student_research_milestone_submit",
    ),
    path(
        "<uuid:uuid>/research-milestones/<int:milestone_id>/submissions/",
        views.student_research_milestone_submission_list,
        name="student_research_milestone_submission_list",
    ),
    path(
        "<uuid:uuid>/research-milestones/<int:milestone_id>/resubmit/",
        views.student_research_milestone_resubmit,
        name="student_research_milestone_resubmit",
    ),
    path(
        "<uuid:uuid>/research-milestones/<int:milestone_id>/submissions/<int:submission_id>/",
        views.student_research_milestone_submission_detail,
        name="student_research_milestone_submission_detail",
    ),
    # ==============================
    # Research Publications
    # ==============================
    path(
        "<uuid:uuid>/phd-research-publications/",
        views.phdstudent_research_publication_list,
        name="phdstudent_research_publication_list",
    ),
    path(
        "<uuid:uuid>/phd-research-publications/create/",
        views.phdstudent_research_publication_create,
        name="phdstudent_research_publication_create",
    ),
    path(
        "<uuid:uuid>/phd-research-publications/<int:publication_id>/",
        views.phdstudent_research_publication_detail,
        name="phdstudent_research_publication_detail",
    ),
    path(
        "<uuid:uuid>/phd-research-publications/<int:publication_id>/update/",
        views.phdstudent_research_publication_update,
        name="phdstudent_research_publication_update",
    ),
    path(
        "<uuid:uuid>/final-dissertation/",
        views.student_final_dissertation_detail,
        name=" ",
    ),
    path(
        "<uuid:uuid>/final-dissertation/submit/",
        views.student_final_dissertation_submit,
        name="student_final_dissertation_submit",
    ),
    path(
        "phd/defense/<uuid:uuid>/",
        views.phdstudent_defense_detail,
        name="phdstudent_defense_detail",
    ),
    path(
    "<uuid:uuid>/messages/",
    views.student_advisor_message_list,
    name="student_advisor_message_list",
),
]

## Leo's Code End ##
