""" Dominic code """
from django.urls import path
from .views import *

app_name = "Permission"

urlpatterns = [
    # Administrator Setup URL
    path("setup/", AdministratorSetupView.as_view(), name="permission_setup"),

    # Permission URL's
    path('roles/', RoleListView.as_view(), name="permission_role_list"),
    path('dashboard/', DashboardView.as_view(), name="permission_dashboard"),
    path('roles/<str:role_type>/<int:pk>/permissions/', RolePermissionsView.as_view(), name="permission_role_permissions"),
    path("audit-log/", AuditLogView.as_view(), name="permission_audit_log"),
    path("my-permissions/", MyPermissionsView.as_view(), name="permission_my_permissions"),
    path("page-access/", PageAccessView.as_view(), name="permission_page_access_list"),
    path("page-access/sync/", SyncPageAccessView.as_view(), name="permission_page_access_sync"),
    path("page-access/<uuid:pk>/update/", PageAccessUpdateView.as_view(), name="permission_page_access_update"),
]