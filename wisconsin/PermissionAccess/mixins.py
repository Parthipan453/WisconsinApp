""" Dominic Code """
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect, render
from .models import PermissionAuditLog
from .utils import (
    log_audit, get_client_ip,
    has_permission, has_any_permission, has_all_permission, has_page_access,
)


def _is_api_request(request) -> bool:
    return (
        request.headers.get("Accept", "") == "application/json"
        or request.headers.get("Content-Type", "") == "application/json"
        or request.path.startswith("/api/")
    )


def _unauthenticated_response(request):
    if _is_api_request(request):
        return JsonResponse({"error": "Authentication required.", "code": "not_authenticated"}, status=401)
    login_url = getattr(settings, "PERMISSION_LOGIN_URL", "/login/")
    return redirect(f'{login_url}?next={request.path}')


def _denied_response(request, message: str, redirect_url: str = None):
    if _is_api_request(request):
        return JsonResponse({"error": message, "code": "forbidden"}, status=403)
    if redirect_url:
        messages.error(request, message)
        return redirect(redirect_url)
    return render(request, "permission_denied.html", {
        "page_title": "Access Denied",
        "message": message,
    }, status=403)


def _log_denied(request, attempted: str):
    log_audit(
        action_by=request.user if request.user.is_authenticated else None,
        action=PermissionAuditLog.ActionType.UNAUTHORIZED_ATTEMPT,
        description=(
            f"Unauthorized access attempt by '{request.user}' "
            f"on '{attempted}' at path '{request.path}'."
        ),
        ip_address=get_client_ip(request),
    )


class PageAccessMixin:
    page_key = None
    redirect_url = None
    shared_with_user_roles = False
    user_types = []
    page_path = ""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return _unauthenticated_response(request)

        if getattr(request.user, "is_administrator", False):
            return super().dispatch(request, *args, **kwargs)

        if not has_page_access(request.user, self.page_key):
            _log_denied(request, f"page:{self.page_key}")
            return _denied_response(request, "You do not have access to this page.", self.redirect_url)

        return super().dispatch(request, *args, **kwargs)


class PermissionRequiredMixin:
    permission_required = None
    redirect_url = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return _unauthenticated_response(request)

        if getattr(request.user, "is_administrator", False):
            return super().dispatch(request, *args, **kwargs)

        if not has_permission(request.user, self.permission_required):
            _log_denied(request, f"permission:{self.permission_required}")
            return _denied_response(request, "You do not have permission to perform this action.", self.redirect_url)

        return super().dispatch(request, *args, **kwargs)


class AnyPermissionRequiredMixin:
    permissions_required = ()
    redirect_url = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return _unauthenticated_response(request)

        if not has_any_permission(request.user, *self.permissions_required):
            _log_denied(request, f"any_of:{','.join(self.permissions_required)}")
            return _denied_response(request, "You do not have permission to perform this action.", self.redirect_url)

        return super().dispatch(request, *args, **kwargs)


class AllPermissionsRequiredMixin:
    permissions_required = ()
    redirect_url = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return _unauthenticated_response(request)

        if not has_all_permission(request.user, *self.permissions_required):
            _log_denied(request, f"all_of:{','.join(self.permissions_required)}")
            return _denied_response(request, "You do not have permission to perform this action.", self.redirect_url)

        return super().dispatch(request, *args, **kwargs)


class AdministratorOnlyMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return _unauthenticated_response(request)

        if not getattr(request.user, "is_administrator", False):
            _log_denied(request, "administrator_only")
            return _denied_response(request, "Administrator access required.", None)

        return super().dispatch(request, *args, **kwargs)