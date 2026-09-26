""" Dominic Code """
import re
from django.urls import get_resolver, URLPattern, URLResolver

_ICON_BY_KEYWORD = {
    "dashboard": "layout-dashboard",
    "role": "shield",
    "permission": "key",
    "audit": "file-text",
    "user": "users",
    "page": "lock",
    "report": "bar-chart-2",
    "student": "graduation-cap",
    "faculty": "briefcase",
    "department": "building-2",
    "news": "newspaper",
    "sport": "trophy",
    "team": "users-round",
    "facility": "building",
}

def _guess_icon(page_key: str) -> str:
    for keyword, icon in _ICON_BY_KEYWORD.items():
        if keyword in page_key:
            return icon
    return "file"

def _humanize_key(page_key: str) -> str:
    return page_key.replace("_", " ").replace("-", " ").title()

def _clean_route(pattern) -> str:
    route = getattr(pattern.pattern, "_route", None)
    if route is None:
        route = str(pattern.pattern)
    return route

def _iter_patterns(resolver, prefix=""):
    for pattern in resolver.url_patterns:
        if isinstance(pattern, URLResolver):
            yield from _iter_patterns(pattern, prefix + _clean_route(pattern))
        elif isinstance(pattern, URLPattern):
            yield prefix + _clean_route(pattern), pattern

def discover_protected_pages():
    from .views import PageAccessMixin

    resolver = get_resolver()
    found = {}

    for raw_path, pattern in _iter_patterns(resolver):
        callback = pattern.callback
        page_key = None
        app_label = callback.__module__.split(".")[0]
        shared_with_user_roles = False
        user_types = []
        page_path = ""

        view_class = getattr(callback, "view_class", None)
        if view_class and issubclass(view_class, PageAccessMixin) and getattr(view_class, "page_key", ""):
            page_key = view_class.page_key
            shared_with_user_roles = bool(getattr(view_class, "shared_with_user_roles", False))
            user_types = list(getattr(view_class, "user_types", []) or [])
            page_path = getattr(view_class, "page_path", "") or ""
        elif hasattr(callback, "page_access_key"):
            page_key = callback.page_access_key
            shared_with_user_roles = bool(getattr(callback, "shared_with_user_roles", False))
            user_types = list(getattr(callback, "page_user_types", []) or [])
            page_path = getattr(callback, "page_path", "") or ""

        if not page_key or page_key in found:
            continue

        clean_path = "/" + re.sub(r"<[^>]+>", "", raw_path).strip("/")
        found[page_key] = {
            "page_key": page_key,
            "path_prefix": (clean_path.rstrip("/") + "/") if clean_path != "/" else "/",
            "app_label": app_label,
            "shared_with_user_roles": shared_with_user_roles,
            "user_types": user_types,
            "page_path": page_path,
        }

    return list(found.values())

def sync_page_access():
    from .models import PageAccess

    created = []

    for entry in discover_protected_pages():
        category = entry["app_label"].replace("_", " ").title()

        is_medical = category.strip().lower() == "medical"
        shared_with_user_roles = bool(entry["shared_with_user_roles"]) if is_medical else False
        user_types = [] if is_medical else list(entry.get("user_types") or [])

        page_path = (entry.get("page_path") or "").strip()
        if page_path:
            segments = [s.strip() for s in page_path.split(">") if s.strip()]
            breadcrumb = " › ".join(segments) if segments else page_path
        else:
            breadcrumb = ""

        page, was_created = PageAccess.objects.update_or_create(
            path_prefix=entry["path_prefix"],
            defaults={
                "page_key": entry["page_key"],
                "display_name": _humanize_key(entry["page_key"]),
                "description": f"Auto-discovered page from the '{entry['app_label']}' app.",
                "category": category,
                "icon": _guess_icon(entry["page_key"]),
                "is_auto_discovered": True,
                "shared_with_user_roles": shared_with_user_roles,
                "user_types": user_types,
                "breadcrumb": breadcrumb,
            },
        )

        if was_created:
            created.append(page)

    return created