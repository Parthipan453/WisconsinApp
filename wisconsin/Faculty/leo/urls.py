## Leo's Code Start ##
from django.urls import path

from . import views

urlpatterns = [
    path(
        "attendance/start/<str:section_id>/<int:schedule_id>/",
        views.student_attendance_start,
        name="student_attendance_start",
    ),
    path(
        "student-attendance/",
        views.student_attendance_list,
        name="student_attendance_list",
    ),
    path(
        "student-attendance/take/<int:session_id>/",
        views.student_attendance_take,
        name="student_attendance_take",
    ),
    path(
        "student-attendance/view/<int:session_id>/",
        views.student_attendance_view,
        name="student_attendance_view",
    ),
    path(
        "attendance/edit/<int:session_id>/",
        views.student_attendance_edit,
        name="student_attendance_edit",
    ),
    path(
        "phd-management/<uuid:uuid>/",
        views.faculty_phd_management,
        name="faculty_phd_management",
    ),
    path(
        "phd-management/<uuid:uuid>/doctoral-committee/",
        views.faculty_doctoral_committee,
        name="faculty_doctoral_committee",
    ),
    path(
        "phd-management/<uuid:uuid>/<int:committee_id>/committee-members/create/",
        views.committee_member_create,
        name="committee_member_create",
    ),
    path(
        "phd-management/<uuid:uuid>/<int:committee_id>/committee-members/update/<int:member_id>/",
        views.committee_member_update,
        name="committee_member_update",
    ),
    path(
        "phd-management/<uuid:uuid>/<int:committee_id>/committee-members/delete/<int:member_id>/",
        views.committee_member_delete,
        name="committee_member_delete",
    ),
    path(
        "phd-management/<uuid:uuid>/doctoral-committee/<int:committee_id>/",
        views.committee_detail,
        name="committee_detail",
    ),  # ==============================
    # Coursework
    # ==============================
    path(
        "phd-management/<uuid:uuid>/coursework/",
        views.faculty_coursework_list,
        name="faculty_coursework_list",
    ),
    path(
        "phd-management/<uuid:uuid>/coursework/create/",
        views.faculty_coursework_create,
        name="faculty_coursework_create",
    ),
    path(
        "phd-management/<uuid:uuid>/coursework/<int:coursework_id>/update/",
        views.faculty_coursework_update,
        name="faculty_coursework_update",
    ),
    path(
        "phd-management/<uuid:uuid>/coursework/<int:coursework_id>/delete/",
        views.faculty_coursework_delete,
        name="faculty_coursework_delete",
    ),
    path(
        "faculty/<uuid:uuid>/coursework/<int:coursework_id>/",
        views.faculty_coursework_view,
        name="faculty_coursework_view",
    ),
    path(
        "coursework/<uuid:uuid>/<int:coursework_id>/evaluate/",
        views.faculty_coursework_evaluate,
        name="faculty_coursework_evaluate",
    ),
    path(
        "phd-management/<uuid:uuid>/coursework/by-program/",
        views.faculty_coursework_by_program,
        name="faculty_coursework_by_program",
    ),
    path(
        "phd-management/<uuid:uuid>/coursework/assign-data/",
        views.faculty_coursework_assign_data,
        name="faculty_coursework_assign_data",
    ),
    path(
        "phd-management/<uuid:uuid>/coursework/master/",
        views.faculty_coursework_master_list,
        name="faculty_coursework_master_list",
    ),
    path(
        "phd-management/<uuid:uuid>/coursework/master/create/",
        views.faculty_coursework_create_master,
        name="faculty_coursework_create_master",
    ),
    path(
        "phd-management/<uuid:uuid>/coursework/master/<int:coursework_id>/update/",
        views.faculty_coursework_master_update,
        name="faculty_coursework_master_update",
    ),
    path(
        "phd-management/<uuid:uuid>/coursework/master/<int:coursework_id>/delete/",
        views.faculty_coursework_master_delete,
        name="faculty_coursework_master_delete",
    ),
    path(
        "my-preliminary-examinations/<uuid:uuid>/",
        views.faculty_my_preliminary_examinations,
        name="faculty_my_preliminary_examinations",
    ),
    path(
        "preliminary-examination/<uuid:uuid>/<int:exam_id>/evaluate/",
        views.faculty_submit_preliminary_evaluation,
        name="faculty_submit_preliminary_evaluation",
    ),
    path(
        "preliminary-examination/<uuid:uuid>/<int:exam_id>/evaluation/",
        views.faculty_view_preliminary_evaluation,
        name="faculty_view_preliminary_evaluation",
    ),
    path(
        "preliminary-examinations/<uuid:uuid>/",
        views.faculty_preliminary_exam_list,
        name="faculty_preliminary_exam_list",
    ),
    path(
        "preliminary-examinations/<uuid:uuid>/create/",
        views.faculty_preliminary_exam_create,
        name="faculty_preliminary_exam_create",
    ),
    path(
        "preliminary-examinations/<uuid:uuid>/<int:exam_id>/update/",
        views.faculty_preliminary_exam_update,
        name="faculty_preliminary_exam_update",
    ),
    path(
        "preliminary-examinations/<uuid:uuid>/<int:exam_id>/delete/",
        views.faculty_preliminary_exam_delete,
        name="faculty_preliminary_exam_delete",
    ),
    path(
        "preliminary-examinations/<uuid:uuid>/<int:exam_id>/detail/",
        views.faculty_preliminary_exam_detail,
        name="faculty_preliminary_exam_detail",
    ),
    path(
        "preliminary-examinations/<uuid:uuid>/<int:exam_id>/publish/",
        views.faculty_preliminary_exam_publish,
        name="faculty_preliminary_exam_publish",
    ),
    path(
        "preliminary-examinations/<uuid:uuid>/<int:exam_id>/result/",
        views.faculty_preliminary_exam_result,
        name="faculty_preliminary_exam_result",
    ),
    # Advisor Dashboard - My PhD Students
    path(
        "phd-management/<uuid:uuid>/advisor/",
        views.faculty_advisor_list,
        name="faculty_advisor_list",
    ),
    path(
        "phd-management/<uuid:uuid>/advisor/<int:phd_student_id>/",
        views.faculty_advisor_workspace,
        name="faculty_advisor_workspace",
    ),
    # ==============================
    # Dissertation Proposal
    # ==============================
    # ==============================
    # Dissertation Proposal - Advisor
    # ==============================
    path(
        "phd-management/<uuid:uuid>/advisor/dissertation-proposals/",
        views.faculty_advisor_dissertation_proposal_list,
        name="faculty_advisor_dissertation_proposal_list",
    ),
    path(
        "phd-management/<uuid:uuid>/advisor/dissertation-proposals/<int:proposal_id>/",
        views.faculty_advisor_dissertation_proposal_detail,
        name="faculty_advisor_dissertation_proposal_detail",
    ),
    path(
        "phd-management/<uuid:uuid>/advisor/dissertation-proposals/<int:proposal_id>/review/",
        views.faculty_advisor_dissertation_proposal_review,
        name="faculty_advisor_dissertation_proposal_review",
    ),
    # ==============================
    # Dissertation Proposal - Committee
    # ==============================
    path(
        "phd-management/<uuid:uuid>/committee/dissertation-proposals/",
        views.faculty_committee_dissertation_proposal_list,
        name="faculty_committee_dissertation_proposal_list",
    ),
    path(
        "phd-management/<uuid:uuid>/committee/dissertation-proposals/<int:proposal_id>/",
        views.faculty_committee_dissertation_proposal_detail,
        name="faculty_committee_dissertation_proposal_detail",
    ),
    path(
        "phd-management/<uuid:uuid>/committee/dissertation-proposals/<int:proposal_id>/review/",
        views.faculty_committee_dissertation_proposal_evaluate,
        name="faculty_committee_dissertation_proposal_evaluate",
    ),
    # Chair Faculty
    path(
        "phd-management/<uuid:uuid>/chair/dissertation-proposals/<int:proposal_id>/finalize/",
        views.faculty_chair_dissertation_proposal_finalize,
        name="faculty_chair_dissertation_proposal_finalize",
    ),
    # ==============================
    # Doctoral Candidacy
    # ==============================
    path(
        "phd-management/<uuid:uuid>/doctoral-candidacy/",
        views.faculty_doctoral_candidacy_list,
        name="faculty_doctoral_candidacy_list",
    ),
    path(
        "phd-management/<uuid:uuid>/doctoral-candidacy/create/",
        views.faculty_doctoral_candidacy_create,
        name="faculty_doctoral_candidacy_create",
    ),
    path(
        "phd-management/<uuid:uuid>/doctoral-candidacy/check-status/",
        views.faculty_doctoral_candidacy_check_status,
        name="faculty_doctoral_candidacy_check_status",
    ),
    path(
        "phd-management/<uuid:uuid>/doctoral-candidacy/<int:candidacy_id>/hold/",
        views.faculty_doctoral_candidacy_hold,
        name="faculty_doctoral_candidacy_hold",
    ),
    path(
        "phd-management/<uuid:uuid>/doctoral-candidacy/<int:candidacy_id>/",
        views.faculty_doctoral_candidacy_detail,
        name="faculty_doctoral_candidacy_detail",
    ),
    path(
        "phd-management/<uuid:uuid>/doctoral-candidacy/<int:candidacy_id>/update/",
        views.faculty_doctoral_candidacy_update,
        name="faculty_doctoral_candidacy_update",
    ),
    path(
        "phd-management/<uuid:uuid>/doctoral-candidacy/<int:candidacy_id>/approve/",
        views.faculty_doctoral_candidacy_approve,
        name="faculty_doctoral_candidacy_approve",
    ),
    path(
        "phd-management/<uuid:uuid>/doctoral-candidacy/<int:candidacy_id>/reject/",
        views.faculty_doctoral_candidacy_reject,
        name="faculty_doctoral_candidacy_reject",
    ),
    path(
        "phd-management/<uuid:uuid>/doctoral-candidacy/<int:candidacy_id>/activate/",
        views.faculty_doctoral_candidacy_activate,
        name="faculty_doctoral_candidacy_activate",
    ),
    path(
        "faculty/<uuid:uuid>/annual-progress/",
        views.faculty_annual_progress_list,
        name="faculty_annual_progress_list",
    ),
    path(
        "faculty/<uuid:uuid>/annual-progress/create/<int:phd_student_id>/",
        views.faculty_annual_progress_create,
        name="faculty_annual_progress_create",
    ),
    path(
        "faculty/<uuid:uuid>/annual-progress/<int:phd_student_id>/",
        views.faculty_annual_progress_detail,
        name="faculty_annual_progress_detail",
    ),
    path(
        "faculty/<uuid:uuid>/annual-progress/review/<int:review_id>/update/",
        views.faculty_annual_progress_update,
        name="faculty_annual_progress_update",
    ),
    path(
        "phd-management/<uuid:uuid>/advisor/<int:phd_student_id>/annual-progress/all/",
        views.faculty_advisor_annual_progress_all_reviews,
        name="faculty_advisor_annual_progress_all_reviews",
    ),
    # ==============================
    # PhD Milestones - Chair / Committee
    # ==============================
    path(
        "phd-management/<uuid:uuid>/milestones/",
        views.faculty_milestone_list,
        name="faculty_milestone_list",
    ),
    path(
        "phd-management/<uuid:uuid>/milestones/advisor/",
        views.faculty_milestone_advisor,
        name="faculty_milestone_advisor",
    ),
    path(
        "phd-management/<uuid:uuid>/milestones/<int:phd_student_id>/",
        views.faculty_milestone_detail,
        name="faculty_milestone_detail",
    ),
    # ==============================
    # Research Milestones
    # ==============================
    path(
        "phd-management/<uuid:uuid>/research-milestones/",
        views.research_milestone_list,
        name="research_milestone_list",
    ),
    path(
        "phd-management/<uuid:uuid>/research-milestones/create/",
        views.research_milestone_create,
        name="research_milestone_create",
    ),
    path(
        "phd-management/<uuid:uuid>/research-milestones/<int:milestone_id>/",
        views.research_milestone_detail,
        name="research_milestone_detail",
    ),
    path(
        "phd-management/<uuid:uuid>/research-milestones/<int:milestone_id>/update/",
        views.research_milestone_update,
        name="research_milestone_update",
    ),
    path(
        "phd-management/<uuid:uuid>/research-milestones/<int:milestone_id>/hold/",
        views.research_milestone_hold,
        name="research_milestone_hold",
    ),
    path(
        "phd-management/<uuid:uuid>/research-milestones/<int:milestone_id>/activate/",
        views.research_milestone_activate,
        name="research_milestone_activate",
    ),
    # ==============================
    # Research Milestone Evaluation
    # ==============================
    path(
        "phd-management/<uuid:uuid>/research-milestones/<int:milestone_id>/evaluate/",
        views.research_milestone_evaluate,
        name="research_milestone_evaluate",
    ),
    path(
        "phd-management/<uuid:uuid>/research-milestones/<int:milestone_id>/evaluation/<int:evaluation_id>/",
        views.research_milestone_evaluation_detail,
        name="research_milestone_evaluation_detail",
    ),
    # ==============================
    # Advisor Research Milestones
    # ==============================
    path(
        "phd-management/<uuid:uuid>/advisor/research-milestones/",
        views.advisor_research_milestone_list,
        name="advisor_research_milestone_list",
    ),
    path(
        "phd-management/<uuid:uuid>/advisor/research-milestones/<int:milestone_id>/",
        views.advisor_research_milestone_detail,
        name="advisor_research_milestone_detail",
    ),
    # ==============================
    # Advisor Research Advice
    # ==============================
    path(
        "phd-management/<uuid:uuid>/research-milestones/<int:milestone_id>/advice/create/",
        views.advisor_research_advice_create,
        name="advisor_research_advice_create",
    ),
    path(
        "phd-management/<uuid:uuid>/research-milestones/<int:milestone_id>/advice/<int:advice_id>/",
        views.advisor_research_advice_detail,
        name="advisor_research_advice_detail",
    ),
    path(
        "phd-management/<uuid:uuid>/research-milestones/<int:milestone_id>/advice/<int:advice_id>/update/",
        views.advisor_research_advice_update,
        name="advisor_research_advice_update",
    ),
    # ==============================
    # Research Milestone Second Chance
    # ==============================
    path(
        "phd-management/<uuid:uuid>/research-milestones/<int:milestone_id>/second-chance/",
        views.research_milestone_second_chance,
        name="research_milestone_second_chance",
    ),
    # ==============================
    # Research Publication Advisor view
    # ==============================
    path(
        "phd-management/<uuid:uuid>/advisor/publications/",
        views.faculty_advisor_publication_list,
        name="faculty_advisor_publication_list",
    ),
    path(
        "phd-management/<uuid:uuid>/advisor/publications/<int:publication_id>/",
        views.faculty_advisor_publication_detail,
        name="faculty_advisor_publication_detail",
    ),
    # ==============================
    # Research Publication Committee Member view
    # ==============================
    path(
        "phd-management/<uuid:uuid>/committee-member/publications/",
        views.faculty_committee_member_publication_list,
        name="faculty_committee_member_publication_list",
    ),
    path(
        "phd-management/<uuid:uuid>/committee-member/publications/<int:publication_id>/",
        views.faculty_committee_member_publication_detail,
        name="faculty_committee_member_publication_detail",
    ),
    # =============================================
    # Final Dissertation evaluation - Advisor Side
    # ==============================================
    path(
        "phd-management/<uuid:uuid>/advisor/final-dissertations/",
        views.faculty_advisor_final_dissertation_list,
        name="faculty_advisor_final_dissertation_list",
    ),
    path(
        "phd-management/<uuid:uuid>/advisor/final-dissertations/<int:submission_id>/",
        views.faculty_advisor_final_dissertation_detail,
        name="faculty_advisor_final_dissertation_detail",
    ),
    path(
        "phd-management/<uuid:uuid>/advisor/final-dissertations/<int:submission_id>/evaluate/",
        views.faculty_advisor_final_dissertation_evaluate,
        name="faculty_advisor_final_dissertation_evaluate",
    ),
    path(
        "phd-management/<uuid:uuid>/advisor/final-dissertations/<int:submission_id>/evaluation/<int:evaluation_id>/",
        views.faculty_advisor_final_dissertation_evaluation_detail,
        name="faculty_advisor_final_dissertation_evaluation_detail",
    ),
    # ========================================================
    # Final Dissertation evaluation - Committee and Chair Side
    # ========================================================
    path(
        "phd-management/<uuid:uuid>/committee/final-dissertations/",
        views.faculty_committee_final_dissertation_list,
        name="faculty_committee_final_dissertation_list",
    ),
    path(
        "phd-management/<uuid:uuid>/committee/final-dissertations/<int:submission_id>/",
        views.faculty_committee_final_dissertation_detail,
        name="faculty_committee_final_dissertation_detail",
    ),
    path(
        "phd-management/<uuid:uuid>/committee/final-dissertations/<int:submission_id>/evaluate/",
        views.faculty_committee_final_dissertation_evaluate,
        name="faculty_committee_final_dissertation_evaluate",
    ),
    path(
        "phd-management/<uuid:uuid>/committee/final-dissertations/<int:submission_id>/evaluation/<int:evaluation_id>/",
        views.faculty_committee_final_dissertation_evaluation_detail,
        name="faculty_committee_final_dissertation_evaluation_detail",
    ),
    path(
        "phd-management/<uuid:uuid>/chair/final-dissertations/<int:submission_id>/review/",
        views.faculty_chair_final_dissertation_review,
        name="faculty_chair_final_dissertation_review",
    ),
    path(
        "<uuid:uuid>/chair/final-dissertations/<int:submission_id>/final-detail/",
        views.faculty_chair_final_dissertation_final_detail,
        name="faculty_chair_final_dissertation_final_detail",
    ),
    # ========================================================
    # Final Dissertation  Defense - Chair Faculty
    # ========================================================
    path(
        "phd-management/<uuid:uuid>/chair/final-dissertation/<int:phd_student_id>/defense/schedule/",
        views.faculty_chair_dissertation_defense_schedule,
        name="faculty_chair_dissertation_defense_schedule",
    ),
    path(
        "phd-management/<uuid:uuid>/chair/final-dissertation/defense/<int:defense_id>/",
        views.faculty_chair_dissertation_defense_detail,
        name="faculty_chair_dissertation_defense_detail",
    ),
    # ========================================================
    # Final Dissertation Defense - Advisor
    # ========================================================
    path(
        "phd-management/<uuid:uuid>/advisor/defense/",
        views.faculty_advisor_dissertation_defense_list,
        name="faculty_advisor_dissertation_defense_list",
    ),
    path(
        "phd-management/<uuid:uuid>/advisor/defense/<int:defense_id>/",
        views.faculty_advisor_dissertation_defense_detail,
        name="faculty_advisor_dissertation_defense_detail",
    ),
    # ========================================================
    # Final Dissertation Defense - Committee
    # ========================================================
    path(
        "phd-management/<uuid:uuid>/committee/final-dissertation/defense/<int:defense_id>/",
        views.faculty_committee_dissertation_defense_detail,
        name="faculty_committee_dissertation_defense_detail",
    ),
    path(
        "phd-management/<uuid:uuid>/defense/",
        views.faculty_dissertation_defense_list,
        name="faculty_dissertation_defense_list",
    ),
    path(
        "phd-management/<uuid:uuid>/chair/defense/location/add/",
        views.chair_add_defense_location,
        name="chair_add_defense_location",
    ),
    # ========================================================
    # Final Dissertation Defense - Chair Faculty
    # ========================================================
    path(
        "phd-management/<uuid:uuid>/chair/final-dissertation/defense/<int:defense_id>/finalize/",
        views.faculty_chair_dissertation_defense_finalize,
        name="faculty_chair_dissertation_defense_finalize",
    ),
    path(
        "phd-management/<uuid:uuid>/chair/final-dissertation/defense/<int:defense_id>/final-detail/",
        views.faculty_chair_dissertation_defense_final_detail,
        name="faculty_chair_dissertation_defense_final_detail",
    ),
    # ========================================================
    # Final Dissertation Defense - Committee
    # ========================================================
    path(
        "phd-management/<uuid:uuid>/committee/final-dissertation/defense/<int:defense_id>/evaluate/",
        views.faculty_committee_dissertation_defense_evaluate,
        name="faculty_committee_dissertation_defense_evaluate",
    ),
    path(
        "phd-management/<uuid:uuid>/committee/final-dissertation/defense/<int:defense_id>/evaluation/<int:evaluation_id>/",
        views.faculty_committee_dissertation_defense_evaluation_detail,
        name="faculty_committee_dissertation_defense_evaluation_detail",
    ),
    # ========================================================
    # Graduation - Committee
    # ========================================================
    path(
        "phd-management/<uuid:uuid>/graduation/",
        views.committee_graduation_student_list,
        name="committee_graduation_student_list",
    ),
    path(
        "phd-management/<uuid:uuid>/graduation/<int:graduation_id>/",
        views.committee_graduation_student_detail,
        name="committee_graduation_student_detail",
    ),
    # ========================================================
    # Graduation - Advisor side
    # ========================================================
    path(
        "phd-management/<uuid:uuid>/advisor/graduation/",
        views.faculty_advisor_graduation_list,
        name="faculty_advisor_graduation_list",
    ),
    path(
        "phd-management/<uuid:uuid>/advisor/graduation/<int:graduation_id>/",
        views.faculty_advisor_graduation_detail,
        name="faculty_advisor_graduation_detail",
    ),
    path(
        "phd-management/<uuid:uuid>/advisor/messages/",
        views.faculty_advisor_message_list,
        name="faculty_advisor_message_list",
    ),
    path(
        "preliminary-examination/<uuid:uuid>/<int:exam_id>/evaluation-ready/",
        views.faculty_preliminary_exam_evaluation_ready,
        name="faculty_preliminary_exam_evaluation_ready",
    ),
]
## Leo's Code End  ##
