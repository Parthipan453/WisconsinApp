from django.urls import path
from . import views
from . import review_views

urlpatterns = [
    # ── Admissions Review (Eric) ──────────────────────────────────
    path(
        "<uuid:user_uuid>/admissions/reviews/",
        review_views.my_reviews,
        name="my_reviews",
    ),
    path(
        "<uuid:user_uuid>/admissions/reviews/<int:application_id>/",
        review_views.review_detail,
        name="review_detail",
    ),
    path(
        "<uuid:user_uuid>/admissions/reviews/<int:application_id>/start/",
        review_views.start_review,
        name="start_review",
    ),
    path(
        "<uuid:user_uuid>/admissions/reviews/<int:application_id>/verify-document/<int:document_id>/",
        review_views.verify_document,
        name="verify_document",
    ),
    path(
        "<uuid:user_uuid>/admissions/reviews/<int:application_id>/request-material/",
        review_views.request_material,
        name="request_material",
    ),
    path(
        "<uuid:user_uuid>/admissions/reviews/<int:application_id>/request-missing-materials/",
        review_views.request_missing_materials,
        name="request_missing_materials",
    ),

    path(
        "<uuid:user_uuid>/admissions/reviews/<int:application_id>/mark-ready/",
        review_views.mark_ready,
        name="mark_ready",
    ),
    path(
        "<uuid:user_uuid>/admissions/reviews/<int:application_id>/section-review/",
        review_views.save_section_review,
        name="save_section_review",
    ),
    path(
        "<uuid:user_uuid>/admissions/reviews/<int:application_id>/extract-offline-pdf/",
        review_views.extract_offline_pdf,
        name="extract_offline_pdf",
    ),
    path(
        "<uuid:user_uuid>/admissions/reviews/<int:application_id>/fields/",
        review_views.field_review,
        name="field_review",
    ),
    path(
        "<uuid:user_uuid>/admissions/reviews/<int:application_id>/fields/verdict/",
        review_views.field_review_verdict,
        name="field_review_verdict",
    ),
    path(
        "<uuid:user_uuid>/admissions/reviews/<int:application_id>/fields/send-corrections/",
        review_views.send_field_corrections,
        name="send_field_corrections",
    ),
    # ── Existing attendance views ────────────────────────────────

    path("<uuid:user_uuid>/faculty-attendance/", views.faculty_attendance_view, name="faculty_attendance"),
    path("faculty-attendance/undo/", views.undo_mark_attendance, name="undo_mark_attendance"),
    path("faculty-attendance/mark/", views.mark_attendance, name="mark_attendance"),
    path("faculty-attendance/bulk-edit/", views.bulk_edit_attendance, name="bulk_edit_attendance"),

    path("<uuid:user_uuid>/attendance-records/", views.attendance_records_view, name="attendance_records"),
    path("attendance-records/faculty/<uuid:faculty_uuid>/", views.faculty_monthly_view, name="faculty_monthly"),
    path("attendance-records/<int:record_id>/edit/", views.edit_attendance_view, name="edit_attendance"),
    path("attendance-records/faculty/<uuid:faculty_uuid>/export/excel/", views.export_faculty_excel, name="export_faculty_excel"),
    path("attendance-records/faculty/<uuid:faculty_uuid>/export/pdf/", views.export_faculty_pdf, name="export_faculty_pdf"),
    
    path("<uuid:user_uuid>/attendance-records-view/", views.attendance_day_month_view, name="attendance_day_month"),
    path("<uuid:user_uuid>/attendance-records-view/export/excel/", views.export_day_month_excel, name="export_day_month_excel"),
    path("<uuid:user_uuid>/attendance-records-view/export/pdf/", views.export_day_month_pdf, name="export_day_month_pdf"),
    path("<uuid:user_uuid>/holiday-calendar/", views.holiday_calendar_view, name="holiday_calendar"),

    path("<uuid:user_uuid>/my-attendance/", views.my_attendance_view, name="my_attendance"),
    path("my-attendance/check-in/", views.my_attendance_checkin, name="my_attendance_checkin"),
    path("my-attendance/<int:pk>/check-out/", views.my_attendance_checkout, name="my_attendance_checkout"),
    path("<uuid:user_uuid>/my-attendance/export/excel/", views.my_attendance_export_excel, name="my_attendance_export_excel"),
    path("<uuid:user_uuid>/my-attendance/export/pdf/", views.my_attendance_export_pdf, name="my_attendance_export_pdf"),
]
