## Leo's Code Start ##
from django.urls import path
from . import views

urlpatterns = [
    path(
        "academic-standing/",
        views.academic_standing_list,
        name="academic_standing_list",
    ),
    path(
        "academic-standing/create/",
        views.academic_standing_create,
        name="academic_standing_create",
    ),
    path(
        "academic-standing/update/<int:standing_id>/",
        views.academic_standing_update,
        name="academic_standing_update",
    ),
    path(
        "academic-standing/deactivate/<int:standing_id>/",
        views.academic_standing_deactivate,
        name="academic_standing_deactivate",
    ),
    path(
        "academic-standing/activate/<int:standing_id>/",
        views.academic_standing_activate,
        name="academic_standing_activate",
    ),
    path(
        "academic-standing/export/",
        views.academic_standing_export,
        name="academic_standing_export",
    ),
    path(
        "academic-standing/print/",
        views.academic_standing_print,
        name="academic_standing_print",
    ),
    path(
        "phd-program/",
        views.phd_program_list,
        name="phd_program_list",
    ),
    path(
        "phd-program/create/",
        views.phd_program_create,
        name="phd_program_create",
    ),
    path(
        "phd-program/update/<int:phd_program_id>/",
        views.phd_program_update,
        name="phd_program_update",
    ),
    path(
        "phd-program/deactivate/<int:phd_program_id>/",
        views.phd_program_deactivate,
        name="phd_program_deactivate",
    ),
    path(
        "phd-program/activate/<int:phd_program_id>/",
        views.phd_program_activate,
        name="phd_program_activate",
    ),
    path(
        "phd-program/export/",
        views.phd_program_export,
        name="phd_program_export",
    ),
    path(
        "phd-program/print/",
        views.phd_program_print,
        name="phd_program_print",
    ),
    path(
        "phd-student/",
        views.phd_student_list,
        name="phd_student_list",
    ),
    path(
        "phd-student/create/",
        views.phd_student_create,
        name="phd_student_create",
    ),
    path(
        "phd-student/update/<int:phd_student_id>/",
        views.phd_student_update,
        name="phd_student_update",
    ),
    path(
        "phd-student/deactivate/<int:phd_student_id>/",
        views.phd_student_deactivate,
        name="phd_student_deactivate",
    ),
    path(
        "phd-student/activate/<int:phd_student_id>/",
        views.phd_student_activate,
        name="phd_student_activate",
    ),
    path(
        "phd-student/export/",
        views.phd_student_export,
        name="phd_student_export",
    ),
    path(
        "phd-student/print/",
        views.phd_student_print,
        name="phd_student_print",
    ),
    path(
        "phd-student/view/<int:pk>/",
        views.phd_student_view,
        name="phd_student_view",
    ),
    path(
        "doctoral-committee/",
        views.doctoral_committee_list,
        name="doctoral_committee_list",
    ),
    path(
        "doctoral-committee/create/",
        views.doctoral_committee_create,
        name="doctoral_committee_create",
    ),
    path(
        "doctoral-committee/update/<int:committee_id>/",
        views.doctoral_committee_update,
        name="doctoral_committee_update",
    ),
    path(
        "doctoral-committee/delete/<int:committee_id>/",
        views.doctoral_committee_delete,
        name="doctoral_committee_delete",
    ),
    # path(
    #     "doctoral-committee/export/",
    #     views.doctoral_committee_export,
    #     name="doctoral_committee_export",
    # ),
    # path(
    #     "doctoral-committee/print/",
    #     views.doctoral_committee_print,
    #     name="doctoral_committee_print",
    # ),
    path(
        "doctoral-committee/get-form/",
        views.doctoral_committee_get_form,
        name="doctoral_committee_get_form",
    ),
]

## Leo's Code End ##