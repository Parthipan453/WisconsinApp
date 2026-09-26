from django.urls import path

from . import views

app_name = "Leo_Staff"


urlpatterns = [
    path(
        "graduation/",
        views.graduation_list,
        name="graduation_list",
    ),
    path(
        "graduation/create/",
        views.graduation_create,
        name="graduation_create",
    ),
    path(
        "graduation/<int:graduation_id>/",
        views.graduation_detail,
        name="graduation_detail",
    ),
    path(
        "graduation/<int:graduation_id>/update/",
        views.graduation_update,
        name="graduation_update",
    ),
    path(
        "graduation/check-eligibility/",
        views.graduation_check_eligibility,
        name="graduation_check_eligibility",
    ),
    path(
        "video-evidence/<uuid:uuid>/",
        views.video_evidence_dashboard,
        name="video_evidence_dashboard",
    ),
    path(
        "video-evidence/<uuid:uuid>/add/",
        views.video_evidence_create,
        name="video_evidence_create",
    ),
    path(
        "video-evidence/<uuid:uuid>/<int:video_evidence_id>/edit/",
        views.video_evidence_update,
        name="video_evidence_update",
    ),
]
