from django.urls import path

from .views import *

app_name = "Password"

urlpatterns = [
    # Password Reset
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot_password"),
    path("verify-otp/", VerifyOTPView.as_view(), name="verify_otp"),
    path("reset-password/", ResetPasswordView.as_view(), name="reset_password"),
    path("reset-complete/", ResetCompleteView.as_view(), name="reset_complete"),
    # Announcement
    path('announcements/list/', AnnouncementListView.as_view(), name='announcement_list'),
    path('announcements/create/', AnnouncementCreateView.as_view(), name='announcement_create'),
    path('announcements/<int:pk>/edit/', AnnouncementUpdateView.as_view(), name='announcement_edit'),
    path('announcements/<int:pk>/toggle/', AnnouncementToggleStatusView.as_view(), name='announcement_toggle'),
    # Search
    path("search/", admin_search, name="admin_search"),
    # Notification
    path('notifications/', NotificationListView.as_view(), name='notification_list'),
    path('notifications/mark-read/', NotificationMarkReadView.as_view(), name='notification_mark_read'),
    path('notifications/history/', NotificationHistoryView.as_view(), name='notification_history'),

] 