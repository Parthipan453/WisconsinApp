from django.urls import path
from Medical.Dominic.views import *

urlpatterns = [
    path('staff/', MedicalStaffDashboardView.as_view(), name="medical_staff_dashboard"),
    path('staff/assign/', AssignMedicalStaffView.as_view(), name="assign_medical_staff"),
    path('staff/roles/create/', MedicalStaffRoleCreateView.as_view(), name="create_medical_role"),

    path('staff/schedule/', StaffScheduleView.as_view(), name="staff_schedule"),
    path('staff/my-shifts/', MyShiftsView.as_view(), name="my_shifts"),
    path('staff/my-shifts/notes/save/', DailyNoteSaveView.as_view(), name="daily_note_save"),
    path('staff/my-shifts/notes/<int:pk>/delete/', DailyNoteDeleteView.as_view(), name="daily_note_delete"),
    path('staff/notifications/due-reminders/', DueRemindersView.as_view(), name="due_reminders"),

    path('staff/shifts/', ShiftManagementView.as_view(), name="shift_management"),
    path('staff/shifts/create/', ShiftCreateView.as_view(), name="shift_create"),
    path('staff/shifts/<int:pk>/edit/', ShiftUpdateView.as_view(), name="shift_edit"),
    path('staff/shifts/<int:pk>/delete/', ShiftDeleteView.as_view(), name="shift_delete"),
    path('staff/shifts/departments-by-hospital/<int:hospital_id>/', DepartmentsByHospitalView.as_view(), name="departments_by_hospital"),

    path('staff/shifts/<int:pk>/assignments/', ShiftAssignmentsView.as_view(), name="shift_assignments"),
    path('staff/shifts/<int:pk>/assignments/create/', ShiftAssignmentCreateView.as_view(), name="shift_assignment_create"),
    path('staff/shifts/assignments/<int:pk>/edit/', ShiftAssignmentUpdateView.as_view(), name="shift_assignment_edit"),
    path('staff/shifts/assignments/<int:pk>/delete/', ShiftAssignmentDeleteView.as_view(), name="shift_assignment_delete"),
    path('hospitals/<int:hospital_id>/working-hours/', HospitalWorkingHoursView.as_view(), name='hospital_working_hours'),

    path('staff/push/subscribe/', SavePushSubscriptionView.as_view(), name="push_subscribe"),
    path('staff/push/unsubscribe/', RemovePushSubscriptionView.as_view(), name="push_unsubscribe"),

    path('staff/notifications/', NotificationListView.as_view(), name="notification_list"),
    path('staff/notifications/<str:pk>/read/', NotificationMarkReadView.as_view(), name="notification_mark_read"),

    path('staff/reporting-options/', ReportingStaffOptionsView.as_view(), name="reporting_staff_options"),
    path('hospitals/<int:hospital_id>/facilities/', HospitalFacilitiesView.as_view(), name="hospital_facilities"),
]