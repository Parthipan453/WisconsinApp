#<---------------------Blaze Code Start (11.08.26)------------------------->  

from Admin.models import User
from Staff.models import Notification
from django.urls import reverse




def notify_staff_new_faculty_leave_request(leave_request):
    """
    When faculty applies → Notify STAFF (for approval)
    This sends notification to ALL active staff members
    """
    try:
        faculty_name = leave_request.faculty.get_full_name()
        
        # Get all active staff members (except the faculty if they are also staff)
        staff_users = User.objects.filter(
            is_staff=True, 
            is_active=True
        ).exclude(id=leave_request.faculty.id)

        print(f" Sending notification to {staff_users.count()} staff members for faculty leave: {leave_request.id}")
        
        notifications = []
        for staff_user in staff_users:
            notifications.append(
                Notification(
                    user=staff_user,  # Sends to STAFF
                    title="New Faculty Leave Request",
                    message=f"{faculty_name} requested {leave_request.days_count} days of {leave_request.leave_type.name} leave.",
                    notification_type="LEAVE_REQUEST",
                    link=f"/staff/{staff_user.uuid}/requests/",
                    related_leave_id=leave_request.id
                )
            )

        if notifications:
            Notification.objects.bulk_create(notifications)
            print(f"Created {len(notifications)} notifications for staff")
            return True
        else:
            print("No staff users to notify")
            return False
            
    except Exception as e:
        print(f"Error sending notification: {e}")
        return False


def notify_faculty_leave_approved(leave_request):

    try:
        Notification.objects.create(
            user=leave_request.faculty,  
            title="Faculty Leave Request Approved",
            message=f"Your {leave_request.leave_type.name} leave request has been approved.",
            notification_type="LEAVE_APPROVED",
            link=f"/faculty/leave-dashboard/{leave_request.faculty.uuid}/",
            related_leave_id=leave_request.id
        )
        print(f"Approval notification sent to faculty: {leave_request.faculty.get_full_name()}")
        return True
    except Exception as e:
        print(f"Error sending approval notification: {e}")
        return False


def notify_faculty_leave_rejected(leave_request):
    """
     When staff rejects → Notify ONLY THE FACULTY (who applied)
    This sends notification ONLY to the faculty member who applied
    """
    try:
        rejection_reason = leave_request.approval_remarks or "No specific reason provided"
        
        Notification.objects.create(
            user=leave_request.faculty,  #
            title=" Faculty Leave Request Rejected",
            message=f"Your {leave_request.leave_type.name} leave request has been rejected. Reason: {rejection_reason}",
            notification_type="LEAVE_REJECTED",
            link=f"/faculty/leave-dashboard/{leave_request.faculty.uuid}/",
            related_leave_id=leave_request.id
        )
        print(f" Rejection notification sent to faculty: {leave_request.faculty.get_full_name()}")
        return True
    except Exception as e:
        print(f" Error sending rejection notification: {e}")
        return False


def notify_faculty_leave_under_review(leave_request):
    """
     When staff marks as under review → Notify ONLY THE FACULTY (who applied)
    """
    try:
        Notification.objects.create(
            user=leave_request.faculty,  # Sends to FACULTY (NOT staff)
            title=" Faculty Leave Request Under Review",
            message=f"Your {leave_request.leave_type.name} leave request has been marked for review.",
            notification_type="LEAVE_UNDER_REVIEW",
            link=f"/faculty/leave-dashboard/{leave_request.faculty.uuid}/",
            related_leave_id=leave_request.id
        )
        print(f" Under review notification sent to faculty: {leave_request.faculty.get_full_name()}")
        return True
    except Exception as e:
        print(f" Error sending under review notification: {e}")
        return False


#<---------------------Blaze Code End (11.08.26)------------------------->