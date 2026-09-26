""" Dominic code """
from functools import wraps
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect
from .models import PermissionAuditLog
from .utils import log_audit, get_client_ip, has_all_permission, has_any_permission, has_page_access, has_permission
from django.shortcuts import render

def require_permission(codename: str, redirect_url: str = None):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return _unauthenticated_response(request)
            
            if getattr(request.user, "is_administrator", False):
                return view_func(request, *args, **kwargs)
            
            if not has_permission(request.user, codename):
                _log_denied(request, f"permission:{codename}")
                return _denied_response(request, "You do not have permission to perform this action.", redirect_url)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def require_any_permission(*codenames: str, redirect_url: str = None):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return _unauthenticated_response(request)
            
            if not has_any_permission(request.user, *codenames):
                _log_denied(request, f"any_of:{','.join(codenames)}")
                return _denied_response(request, "You do not have permission to perform this action.", redirect_url)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def require_all_permissions(*codenames: str, redirect_url: str = None):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return _unauthenticated_response(request)
                
            if not has_all_permission(request.user, *codenames):
                _log_denied(request, f"all_of:{','.join(codenames)}")
                return _denied_response(request, "You do not have permission to perform this action.", redirect_url)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def require_page_access(page_key: str, redirect_url: str = None, shared_with_user_roles: bool = False, user_types: list = None, page_path: str = None):

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return _unauthenticated_response(request)

            if getattr(request.user, "is_administrator", False):
                return view_func(request, *args, **kwargs)

            if not has_page_access(request.user, page_key):
                _log_denied(request, f"page:{page_key}")
                return _denied_response(request, "You don not have access to this page.", redirect_url)

            return view_func(request, *args, **kwargs)
        wrapper.page_access_key = page_key
        wrapper.shared_with_user_roles = shared_with_user_roles
        wrapper.page_user_types = list(user_types or [])
        wrapper.page_path = page_path or ""
        return wrapper
    return decorator

def administrator_only(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return _unauthenticated_response(request)
        
        if not getattr(request.user, "is_administrator", False):
            _log_denied(request, "administrator_only")
            return _denied_response(request, "Administrator access required.", None)
        
        return view_func(request, *args, **kwargs)
    return wrapper

def _is_api_request(request) -> bool:
    return (
        request.headers.get("Accept", "") == "application/json"
        or request.headers.get("Content-Type", "") == "application/json"
        or request.path.startswith("/api/")
    )

def _unauthenticated_response(request):
    if _is_api_request(request):
        return JsonResponse({
            "error": "Authentication required.",
            "code": "not_authenticated"
        }, status = 401)
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
        action_by = request.user if request.user.is_authenticated else None,
        action = PermissionAuditLog.ActionType.UNAUTHORIZED_ATTEMPT,
        description = (
            f"Unauthorized access attempt by '{request.user}' "
            f"on '{attempted}' at path '{request.path}'."
        ),
        ip_address = get_client_ip(request),
    )