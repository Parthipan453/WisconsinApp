""" Dominic Code """
from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin
from .models import PageAccess, PermissionAuditLog
from PermissionAccess.utils import log_audit, get_client_ip
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.shortcuts import render

DEFAULT_OPEN_PATHS = [
    "/login/",
    "/logout/",
    "/admin/",
    "/static/",
    "/media/",
    "/favicon.ico",
    "/permission/setup/",
    "/medical/staff/my-shifts/",
    "/medical/staff/push/",
    "/medical/staff/notifications/",
    "/medical/staff/notifications/due-reminders/",
    "/medical/staff/my-shifts/notes/",
]

_CACHE_KEY = "permissionaccess:page_access_prefixes"
_CACHE_TIMEOUT = 300

class PageAccessMiddleware(MiddlewareMixin):
    def process_request(self, request):
        path = request.path

        open_paths = getattr(settings, "PERMISSION_OPEN_PATHS", DEFAULT_OPEN_PATHS)
        if any(path.startswith(p) for p in open_paths):
            return None

        page = self._match_page(path)
        if page is None:
            return None

        if not request.user.is_authenticated:
            login_url = getattr(settings, "PERMISSION_LOGIN_URL", "/login/")
            if self._is_api_request(request):
                return JsonResponse({
                    "error": "Authentication required.",
                    "code": "not_authenticated"
                }, status=401)
            return redirect(f"{login_url}?next={path}")

        if getattr(request.user, "is_administrator", False):
            request.current_page_key = page["page_key"]
            return None

        role_id = getattr(request.user, "role_id", None)
        medical_role_id = getattr(request.user, "medical_role_id", None)

        has_access = (role_id is not None and role_id in page["role_ids"]) or \
                     (medical_role_id is not None and medical_role_id in page["medical_role_ids"])

        if not has_access:
            self._log_blocked(request, page["page_key"])
            if self._is_api_request(request):
                return JsonResponse({
                    "error": "You do not have access to this page.",
                    "code": "forbidden"
                }, status=403)
            return render(request, "permission_denied.html", {
                "page_title": "Access Denied",
                "message": f"You do not have access to \"{page['display_name']}\". "
                           f"Contact your Administrator if you think this is a mistake.",
            }, status=403)

        request.current_page_key = page["page_key"]
        return None

    def _match_page(self, path):
        entries = cache.get(_CACHE_KEY)
        if entries is None:
            entries = self._load_entries()
            cache.set(_CACHE_KEY, entries, _CACHE_TIMEOUT)

        best = None
        for entry in entries:
            if path.startswith(entry["path_prefix"]):
                if best is None or len(entry["path_prefix"]) > len(best["path_prefix"]):
                    best = entry

        return best

    def _load_entries(self):
        try:
            return [
                {
                    "page_key": pa.page_key,
                    "path_prefix": pa.path_prefix,
                    "display_name": pa.display_name,
                    "role_ids": set(pa.roles.values_list("id", flat=True)),
                    "medical_role_ids": set(pa.medical_roles.values_list("id", flat=True)),
                }
                for pa in PageAccess.objects.prefetch_related("roles", "medical_roles").all()
            ]
        except Exception:
            return []

    def _is_api_request(self, request) -> bool:
        return (
            request.headers.get("Accept", "") == "application/json"
            or request.headers.get("Content-Type", "") == "application/json"
            or request.path.startswith("/api/")
        )

    def _log_blocked(self, request, page_key: str):
        try:
            log_audit(
                action_by=request.user,
                action=PermissionAuditLog.ActionType.UNAUTHORIZED_ATTEMPT,
                description=(
                    f"Blocked access to page '{page_key}' by "
                    f"'{request.user}' at path '{request.path}'."
                ),
                ip_address=get_client_ip(request)
            )
        except Exception:
            pass

def invalidate_page_access_cache(*args, **kwargs):
    cache.delete(_CACHE_KEY)

try:
    post_save.connect(invalidate_page_access_cache, sender=PageAccess)
    post_delete.connect(invalidate_page_access_cache, sender=PageAccess)
    m2m_changed.connect(invalidate_page_access_cache, sender=PageAccess.roles.through)
    m2m_changed.connect(invalidate_page_access_cache, sender=PageAccess.medical_roles.through)
except Exception:
    pass