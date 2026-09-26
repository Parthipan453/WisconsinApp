from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_http_methods

from Applicants.models import Application
from Students.Eric.services import create_student_from_application


@login_required
@require_http_methods(["POST"])
def create_student(request: HttpRequest, application_id: int) -> HttpResponse:
    """
    POST handler — convert an admitted+enrolled applicant into a student.

    Expected POST fields:
        None required (application_id comes from the URL).

    On success: redirects to the admin application detail page with a
    success message including the new student number and university email.
    On failure: redirects back with an error message.
    """
    app = get_object_or_404(
        Application.objects.select_related("applicant", "program"),
        application_id=application_id,
    )

    # Guard: must be offer_accepted or enrolled
    if app.status not in ("offer_accepted", "enrolled"):
        messages.error(
            request,
            f"Cannot create student -- application is '{app.get_status_display()}', "
            f"must be 'Offer Accepted'.",
        )
        return redirect("application_detail", application_id=application_id)

    # Guard: already converted
    if app.applicant.converted_to_user_id:
        messages.warning(
            request,
            f"This applicant is already linked to user account "
            f"#{app.applicant.converted_to_user_id}.",
        )
        return redirect("application_detail", application_id=application_id)

    try:
        result = create_student_from_application(
            application_id=application_id,
            created_by=request.user.get_full_name() or request.user.username,
        )
    except Exception as exc:
        messages.error(request, f"Failed to create student account: {exc}")
        return redirect("application_detail", application_id=application_id)

    messages.success(
        request,
        f"Student account created — {result['student_number']} "
        f"({result['university_email']}). Welcome email sent.",
    )
    return redirect("application_detail", application_id=application_id)
