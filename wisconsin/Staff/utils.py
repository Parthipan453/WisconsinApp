# /* *********************************************** Arun code ********************************************************** */

from Admin.models import User
from Staff.models import Notification
from django.urls import reverse
from Students.models import StudentEnrollment

# rupa code starts******
from django.urls import reverse
from django.db.models import Q
from Admin.models import UserRoleAssignment
# rupa code ends ********

def notify_staff_new_ticket(ticket):
    """Creates a notification for every active staff member when a new
    support ticket is submitted by a student or faculty member."""
    submitter_role = "Faculty" if getattr(ticket.submitted_by, "is_faculty", False) else "Student"
    course_label = (
        ticket.course_section.course.course_code
        if ticket.course_section and ticket.course_section.course
        else "General"
    )

    staff_users = User.objects.filter(
        is_staff=True, is_active=True
    ).exclude(id=ticket.submitted_by_id)

    notifications = [
        Notification(
            user=staff_user,
            title="New Support Ticket",
            message=f"{ticket.submitted_by.get_full_name()} ({submitter_role}) — {course_label}: {ticket.subject}",
            notification_type="REQUEST",
            link=f"/staff/{staff_user.uuid}/course-support/tickets/",
        )
        for staff_user in staff_users
    ]

    if notifications:
        Notification.objects.bulk_create(notifications)


def notify_submitter_ticket_resolved(ticket):
    """Optional: notifies the student/faculty back when their ticket is resolved."""
    Notification.objects.create(
        user=ticket.submitted_by,
        title="Support Ticket Resolved",
        message=f"Your ticket \"{ticket.subject}\" has been marked as resolved.",
        notification_type="SUCCESS",
    )


def notify_submitter_ticket_in_progress(ticket):
    """Optional: notifies the student/faculty their ticket is being worked on."""
    Notification.objects.create(
        user=ticket.submitted_by,
        title="Support Ticket In Progress",
        message=f"Your ticket \"{ticket.subject}\" is now being reviewed by staff.",
        notification_type="INFO",
    )



from django.urls import reverse
from Admin.models import User
from Staff.models import Notification


def notify_staff_new_financial_aid(aid):
    """Notifies all active staff when a student submits a new financial
    aid application.""" 
    student_name = aid.student.user.get_full_name()

    staff_users = User.objects.filter(
        is_staff=True, is_active=True
    )

    notifications = []
    for staff_user in staff_users:
        try:
            link = reverse('staff_financial_aid_detail', kwargs={'uuid': staff_user.uuid, 'aid_id': aid.id})
        except Exception:
            link = ""

        notifications.append(Notification(
            user=staff_user,
            title="New Financial Aid Application",
            message=f"{student_name} submitted a {aid.get_aid_type_display()} application for {aid.academic_year}.",
            notification_type="REQUEST",
            link=link,
        ))

    if notifications:
        Notification.objects.bulk_create(notifications)


def notify_submitter_financial_aid_status(aid):
    """Notifies the student back when staff changes their financial aid
    application status (awarded, rejected, under review, cancelled)."""
    status_display = aid.get_status_display()

    type_map = {
        "AWARDED": "SUCCESS",
        "REJECTED": "ERROR",
        "UNDER_REVIEW": "INFO",
        "CANCELLED": "WARNING",
    }

    if aid.status == "AWARDED":
        message = f"Your {aid.get_aid_type_display()} application has been awarded ${aid.award_amount}."
    elif aid.status == "REJECTED":
        message = f"Your {aid.get_aid_type_display()} application was not approved."
    else:
        message = f"Your {aid.get_aid_type_display()} application status changed to {status_display}."

    try:
        link = reverse('Student:student_financial_aid', kwargs={'uuid': aid.student.user.uuid})
    except Exception:
        link = ""

    Notification.objects.create(
        user=aid.student.user,
        title="Financial Aid Update",
        message=message,
        notification_type=type_map.get(aid.status, "INFO"),
        link=link,
    )


#<---------------------Blaze Code Start(31.07.26)------------------------->    


def notify_staff_new_leave_request(leave_request):
    student_name = leave_request.student.get_full_name()
    
    staff_users = User.objects.filter(
        is_staff=True, 
        is_active=True
    ).exclude(id=leave_request.student.id)

    notifications = []
    for staff_user in staff_users:
        notifications.append(
            Notification(
                user=staff_user,
                title="New Leave Request",
                message=f"{student_name} requested {leave_request.days_count} days of {leave_request.leave_type.name} leave.",
                notification_type="LEAVE_REQUEST",
                link=f"/staff/leave-details/{leave_request.id}/",

            )
            )

    
    



def notify_student_leave_approved(leave_request):
    """Notifies the student when their leave request is approved."""
    try:
        link = f"/student/leave-dashboard/{leave_request.student.uuid}/"
    except Exception:
        link = ""

   
    approved_by_name = "Staff"
    if leave_request.approved_by:
        approved_by_name = leave_request.approved_by.get_full_name()
    
    Notification.objects.create(
        user=leave_request.student,
        title=" Leave Request Approved",
        message=f"Your {leave_request.leave_type.name} leave request has been approved by {approved_by_name}.",
        notification_type="LEAVE_APPROVED",
        link=link,
        related_leave_id=leave_request.id
    )


def notify_student_leave_rejected(leave_request):
    """Notifies the student when their leave request is rejected."""
    try:
        link = f"/student/leave-dashboard/{leave_request.student.uuid}/"
    except Exception:
        link = ""

    rejection_reason = leave_request.rejection_reason or "No specific reason provided"
    
   
    approved_by_name = "Staff"
    if leave_request.approved_by:
        approved_by_name = leave_request.approved_by.get_full_name()
    
    Notification.objects.create(
        user=leave_request.student,
        title=" Leave Request Rejected",
        message=f"Your {leave_request.leave_type.name} leave request has been rejected by {approved_by_name}. Reason: {rejection_reason}",
        notification_type="LEAVE_REJECTED",
        link=link,
        related_leave_id=leave_request.id
    )


def notify_student_leave_cancelled(leave_request):
    """Notifies the student when their leave request is cancelled."""
    try:
        link = f"/student/leave-dashboard/{leave_request.student.uuid}/"
    except Exception:
        link = ""

    Notification.objects.create(
        user=leave_request.student,
        title="ℹ Leave Request Cancelled",
        message=f"Your {leave_request.leave_type.name} leave request has been cancelled.",
        notification_type="INFO",
        link=link,
        related_leave_id=leave_request.id
    )

#<---------------------Blaze Code End (31.07.26)------------------------->  



#<---------------------Blaze Code Start (11.08.26)------------------------->  



# def notify_staff_new_faculty_leave_request(leave_request):
#     """When faculty applies → Notify STAFF (for approval)"""
#     faculty_name = leave_request.faculty.get_full_name()
    
#     staff_users = User.objects.filter(
#         is_staff=True, 
#         is_active=True
#     ).exclude(id=leave_request.faculty.id)

#     notifications = []
#     for staff_user in staff_users:
#         notifications.append(
#             Notification(
#                 user=staff_user,  # Sends to STAFF
#                 title="New Faculty Leave Request",
#                 message=f"{faculty_name} requested {leave_request.days_count} days of {leave_request.leave_type.name} leave.",
#                 notification_type="LEAVE_REQUEST",
#                 link=f"/staff/{staff_user.uuid}/requests/",
#                 related_leave_id=leave_request.id
#             )
#         )

#     if notifications:
#         Notification.objects.bulk_create(notifications)


# def notify_faculty_leave_approved(leave_request):
#     """ When staff approves → Notify FACULTY (who applied)"""
#     Notification.objects.create(
#         user=leave_request.faculty,  #  Sends to FACULTY (not staff)
#         title=" Faculty Leave Request Approved",
#         message=f"Your {leave_request.leave_type.name} leave request has been approved.",
#         notification_type="LEAVE_APPROVED",
#         link=f"/faculty/leave-dashboard/{leave_request.faculty.uuid}/",
#         related_leave_id=leave_request.id
#     )


# def notify_faculty_leave_rejected(leave_request):
#     """ When staff rejects → Notify FACULTY (who applied)"""
#     rejection_reason = leave_request.approval_remarks or "No specific reason provided"
    
#     Notification.objects.create(
#         user=leave_request.faculty,  #  Sends to FACULTY (not staff)
#         title=" Faculty Leave Request Rejected",
#         message=f"Your {leave_request.leave_type.name} leave request has been rejected. Reason: {rejection_reason}",
#         notification_type="LEAVE_REJECTED",
#         link=f"/faculty/leave-dashboard/{leave_request.faculty.uuid}/",
#         related_leave_id=leave_request.id
#     )


#<---------------------Blaze Code End (11.08.26)------------------------->  



# ************************ Rupa code starts ******************************************   
def notify_library_admin_new_borrow_request(borrow_request):

    library_admins = (
        User.objects.filter(
            is_staff=True,
            is_active=True,
            account_status="ACTIVE",
            role__isnull=False,
        )
        .filter(
            Q(role__role_name__icontains="library") |
            Q(role__role_name__icontains="librarian")
        )
        .distinct()
    )

    notifications = []

    requester = borrow_request.library_user.user

    requester_name = (
        f"{requester.first_name or ''} {requester.last_name or ''}".strip()
        or requester.username
    )

    for library_admin in library_admins:

        notifications.append(
            Notification(
                user=library_admin,
                title="New Borrow Request",
                message=(
                    f'{requester_name} requested '
                    f'"{borrow_request.resource.title}".'
                ),
                notification_type="REQUEST",
                link=reverse("borrow_requests"),
            )
        )

    if notifications:
        Notification.objects.bulk_create(notifications)
        
        
# ********************************** Rupa code ends *********************************************


from Staff.models import Resource, ResourceAlert, ResourceAlertSeen


def create_resource_alert(resource, posted_by, notify_staff, notify_faculty, notify_students, message=""):
    if not (notify_staff or notify_faculty or notify_students):
        return None

    alert = ResourceAlert.objects.create(
        resource=resource,
        posted_by=posted_by,
        message=message,
        visible_to_staff=notify_staff,
        visible_to_faculty=notify_faculty,
        visible_to_students=notify_students,
    )

    target_users = User.objects.none()
    if notify_staff:
        target_users = target_users | User.objects.filter(is_staff=True, is_active=True)
    if notify_faculty:
        target_users = target_users | User.objects.filter(is_faculty=True, is_active=True)
    if notify_students:
        target_users = target_users | User.objects.filter(is_student=True, is_active=True)

    target_users = target_users.exclude(id=posted_by.id if posted_by else None).distinct()

    notif_link = f"/staff/{{uuid}}/downloads/" 

    notifications = []
    for u in target_users:
        try:
            if getattr(u, "is_student", False):
                link = reverse('Student:student_downloads', kwargs={'uuid': u.uuid})
            elif getattr(u, "is_faculty", False):
                link = reverse('faculty_downloads', kwargs={'uuid': u.uuid})
            else:
                link = reverse('staff_downloads', kwargs={'uuid': u.uuid})
        except Exception:
            link = ""

        notifications.append(Notification(
            user=u,
            title="New Resource Uploaded",
            message=message or f"{resource.title} is now available for download.",
            notification_type="INFO",
            link=link,
        ))

    if notifications:
        Notification.objects.bulk_create(notifications)

    return alert


def get_resource_alerts_context(user, role_flag, limit=10):
    """
    role_flag: 'visible_to_staff' | 'visible_to_faculty' | 'visible_to_students'
    Returns recent alerts for that role plus an unread count, without
    ever writing a per-user notification row.
    """
    seen, _ = ResourceAlertSeen.objects.get_or_create(user=user)
    alerts_qs = ResourceAlert.objects.filter(**{role_flag: True}).select_related(
        "resource", "posted_by"
    )
    unread_count = alerts_qs.filter(posted_at__gt=seen.last_seen_at).count()
    return {
        "resource_alerts": alerts_qs[:limit],
        "resource_alerts_unread": unread_count,
    }


def mark_resource_alerts_seen(user):
    seen, _ = ResourceAlertSeen.objects.get_or_create(user=user)
    seen.save()  

def _get_exam_enrolled_users(exam):
    """All active students enrolled in the exam's specific section/semester."""
    return (
        StudentEnrollment.objects
        .filter(section_id=exam.course_section, semester_id=exam.semester_id)
        .exclude(enrollment_status__in=['WITHDRAWN', 'DROPPED'])
        .select_related('student__user')
    )


def notify_students_exam_scheduled(exam):
    from datetime import datetime
    from django.urls import reverse

    course = exam.course_section.course if exam.course_section else None
    course_text = (
        f"{course.course_code} - {course.course_name}"
        if course else "your course"
    )

    section = exam.course_section.section_number if exam.course_section else ""
    room = getattr(exam, "room", "")

    exam_date = exam.exam_date
    start_time = exam.start_time

    if isinstance(exam_date, str):
        exam_date = datetime.strptime(exam_date, "%Y-%m-%d")

    if isinstance(start_time, str):
        start_time = datetime.strptime(start_time, "%H:%M")

    message = (
        f"{exam.exam_name} for {course_text}"
        f"{' - Section ' + str(section) if section else ''} "
        f"has been scheduled on {exam_date.strftime('%b %d, %Y')} "
        f"at {start_time.strftime('%I:%M %p')}"
        f"{' in ' + str(room) if room else ''}."
    )

    notifications = []

    for enrollment in _get_exam_enrolled_users(exam):
        student_user = enrollment.student.user
        try:
            link = reverse('Student:student_exams', kwargs={'uuid': student_user.uuid})
        except Exception:
            link = ""

        notifications.append(Notification(
            user=student_user,
            title="Exam Scheduled",
            message=message,  
            notification_type="INFO",
            link=link,
        ))

    if notifications:
        Notification.objects.bulk_create(notifications)


def notify_students_exam_room_assigned(exam, room):
    """Notifies every enrolled student once a room is allocated to their exam."""
    course_code = (
        exam.course_section.course.course_code
        if exam.course_section and exam.course_section.course else 'your course'
    )

    notifications = []
    for enrollment in _get_exam_enrolled_users(exam):
        student_user = enrollment.student.user
        try:
            link = reverse('Student:student_exams', kwargs={'uuid': student_user.uuid})
        except Exception:
            link = ""
        notifications.append(Notification(
            user=student_user,
            title="Exam Room Assigned",
            message=(
                f"Room {room.room_number} has been assigned for {exam.exam_name} "
                f"({course_code}) on {exam.exam_date.strftime('%b %d, %Y')}."
            ),
            notification_type="INFO",
            link=link,
        ))

    if notifications:
        Notification.objects.bulk_create(notifications)


def notify_faculty_invigilation_assigned(exam, faculty):
    from datetime import datetime
    from django.urls import reverse

    course = exam.course_section.course if exam.course_section else None
    course_text = (
        f"{course.course_code} - {course.course_name}"
        if course else "a course"
    )

    section = exam.course_section.section_number if exam.course_section else ""

    exam_date = exam.exam_date
    start_time = exam.start_time

    if isinstance(exam_date, str):
        exam_date = datetime.strptime(exam_date, "%Y-%m-%d")

    if isinstance(start_time, str):
        start_time = datetime.strptime(start_time, "%H:%M")

    try:
        link = reverse('faculty_dashboard', kwargs={'uuid': faculty.user.uuid})
    except Exception:
        link = ""

    message = (
        f"You have been assigned as an invigilator for "
        f"{exam.exam_name} ({course_text})"
        f"{' - Section ' + str(section) if section else ''}.\n"
        f"Schedule: {exam_date.strftime('%b %d, %Y')} at {start_time.strftime('%I:%M %p')}.\n"
        f"Please be present at the exam venue on time."
    )

    Notification.objects.create(
        user=faculty.user,
        title="Invigilation Assigned",
        message=message,
        notification_type="REQUEST",
        link=link,
    )

def notify_exam_cancelled(exam):
    """Notifies enrolled students AND the assigned invigilator(s) that an exam was cancelled."""
    course_code = (
        exam.course_section.course.course_code
        if exam.course_section and exam.course_section.course else 'your course'
    )
    notifications = []

    for enrollment in _get_exam_enrolled_users(exam):
        student_user = enrollment.student.user
        try:
            link = reverse('Student:student_exams', kwargs={'uuid': student_user.uuid})
        except Exception:
            link = ""
        notifications.append(Notification(
            user=student_user,
            title="Exam Cancelled",
            message=(
                f"{exam.exam_name} ({course_code}), previously scheduled for "
                f"{exam.exam_date.strftime('%b %d, %Y')}, has been cancelled."
            ),
            notification_type="WARNING",
            link=link,
        ))

    for invig in exam.invigilators.select_related('faculty__user').all():
        faculty_user = invig.faculty.user
        try:
            link = reverse('faculty_dashboard', kwargs={'uuid': faculty_user.uuid})
        except Exception:
            link = ""
        notifications.append(Notification(
            user=faculty_user,
            title="Exam Cancelled",
            message=f"{exam.exam_name} ({course_code}), which you were assigned to invigilate, has been cancelled.",
            notification_type="WARNING",
            link=link,
        ))

    if notifications:
        Notification.objects.bulk_create(notifications)


def notify_exam_rescheduled(exam, old_date, old_start_time):
    """Notifies enrolled students AND the assigned invigilator(s) that an exam's date/time changed."""
    course_code = (
        exam.course_section.course.course_code
        if exam.course_section and exam.course_section.course else 'your course'
    )
    old_when = (
        f"{old_date.strftime('%b %d, %Y')} at {old_start_time.strftime('%I:%M %p')}"
        if old_date and old_start_time else "its previous time"
    )
    new_when = f"{exam.exam_date.strftime('%b %d, %Y')} at {exam.start_time.strftime('%I:%M %p')}"

    notifications = []

    for enrollment in _get_exam_enrolled_users(exam):
        student_user = enrollment.student.user
        try:
            link = reverse('Student:student_exams', kwargs={'uuid': student_user.uuid})
        except Exception:
            link = ""
        notifications.append(Notification(
            user=student_user,
            title="Exam Rescheduled",
            message=f"{exam.exam_name} ({course_code}) has been moved from {old_when} to {new_when}.",
            notification_type="WARNING",
            link=link,
        ))

    for invig in exam.invigilators.select_related('faculty__user').all():
        faculty_user = invig.faculty.user
        try:
            link = reverse('faculty_dashboard', kwargs={'uuid': faculty_user.uuid})
        except Exception:
            link = ""
        notifications.append(Notification(
            user=faculty_user,
            title="Exam Rescheduled",
            message=(
                f"{exam.exam_name} ({course_code}), which you are invigilating, "
                f"has been moved from {old_when} to {new_when}."
            ),
            notification_type="WARNING",
            link=link,
        ))

    if notifications:
        Notification.objects.bulk_create(notifications)


def notify_faculty_invigilation_removed(exam, faculty):
    """Notifies a faculty member they've been taken off an exam's invigilation (reassigned to someone else)."""
    course_code = (
        exam.course_section.course.course_code
        if exam.course_section and exam.course_section.course else 'a course'
    )
    try:
        link = reverse('faculty_dashboard', kwargs={'uuid': faculty.user.uuid})
    except Exception:
        link = ""
    Notification.objects.create(
        user=faculty.user,
        title="Invigilation Reassigned",
        message=f"You have been removed as invigilator for {exam.exam_name} ({course_code}); it has been reassigned to another faculty member.",
        notification_type="INFO",
        link=link,
    )

def notify_staff_new_org_join_request(membership):
    """Notify staff/advisors when a student requests to join an organization"""
    from Staff.models import Notification, StaffProfile

    staff_users = StaffProfile.objects.filter(
    ).select_related("user")

    for staff in staff_users:
        try:
            link = reverse('Staff:staff_org_dashboard', kwargs={'uuid': staff.user.uuid})
        except Exception:
            link = ""

        Notification.objects.create(
            user=staff.user,
            title="New Organization Join Request",
            message=f"{membership.student.user.get_full_name()} requested to join {membership.organization.organization_name}",
            notification_type="ORG_REQUEST",
            link=link,
        )
def notify_faculty_assigned_to_org(organization, faculty):
    """Notify a faculty member when they're assigned as advisor to an organization."""
    if not faculty:
        return
    try:
        link = reverse('faculty_dashboard', kwargs={'uuid': faculty.user.uuid})
    except Exception:
        link = ""

    Notification.objects.create(
        user=faculty.user,
        title="Assigned as Organization Advisor",
        message=f"You have been assigned as advisor for {organization.organization_name}.",
        notification_type="INFO",
        link=link,
    )
    
def notify_student_org_request_approved(membership):
    """Notify the student when their join request is approved by staff."""
    try:
        link = reverse('Student:student_organizations', kwargs={'uuid': membership.student.user.uuid})
    except Exception:
        link = ""

    Notification.objects.create(
        user=membership.student.user,
        title="Organization Request Approved",
        message=f"Your request to join {membership.organization.organization_name} has been approved.",
        notification_type="SUCCESS",
        link=link,
    )


def notify_student_added_to_org(membership):
    """Notify the student when staff directly adds them to an organization."""
    try:
        link = reverse('Student:student_organizations', kwargs={'uuid': membership.student.user.uuid})
    except Exception:
        link = ""

    Notification.objects.create(
        user=membership.student.user,
        title="Added to Organization",
        message=f"You have been added to {membership.organization.organization_name}.",
        notification_type="INFO",
        link=link,
    )
    

def notify_event_invited(event, user):
    Notification.objects.create(
        user=user,
        title="Event Invitation",
        message=f'You have been invited to "{event.event_title}" on {event.start_datetime.strftime("%b %d, %Y")}.',
        notification_type="INFO",
        link=reverse("event-detail", args=[event.event_id]),
        related_event_id=event.event_id,
    )

def notify_campus_event_published(event):
    """Notifies all active users when a Campus Only event is published."""
    campus_users = User.objects.filter(is_active=True).exclude(id=event.organizer_id)

    notifications = [
        Notification(
            user=user,
            title="New Campus Event",
            message=f'A new campus event "{event.event_title}" has been scheduled on {event.start_datetime.strftime("%b %d, %Y")}.',
            notification_type="INFO",
            link=reverse("event-detail", args=[event.event_id]),
            related_event_id=event.event_id,
        )
        for user in campus_users
    ]

    if notifications:
        Notification.objects.bulk_create(notifications)
        
def notify_event_cancelled(event):
    for user in event.invited_users.all():
        Notification.objects.create(
            user=user,
            title="Event Cancelled",
            message=f'"{event.event_title}" scheduled on {event.start_datetime.strftime("%b %d, %Y")} has been cancelled.',
            notification_type="WARNING",
            link=reverse("event-detail", args=[event.event_id]),
            related_event_id=event.event_id,
        )


# /* *********************************************** Arun code ********************************************************** */

############################### Kali code ########################
def notify_faculty_new_tournament_invitation(invitation):
    """Notifies a faculty member when their department is invited to a tournament."""
    tournament = invitation.tournament
    Notification.objects.create(
        user=invitation.receiver_faculty.user,
        title="Tournament Invitation",
        message=f"Your department has been invited to {tournament.tournament_name} ({tournament.tournament_code}).",
        notification_type="REQUEST",
        link=f"tournament_invitation:{invitation.invitation_uuid}",
    )

############################### Kali code ########################
