from django import template
from PermissionAccess.models import PageAccess
from PermissionAccess.utils import has_page_access as _has_page_access, has_permission as _has_permission
import re

register = template.Library()

@register.simple_tag(takes_context=True)
def has_page_access(context, page_key: str) -> bool:
    request = context.get("request")
    user = getattr(request, "user", None) if request else None
    
    if not user or not getattr(user, "is_authenticated", False):
        return False
    
    if getattr(user, "is_administrator", False):
        return True
    
    if not PageAccess.objects.filter(page_key=page_key).exists():
        return True
    
    return _has_page_access(user, page_key)


@register.simple_tag(takes_context=True)
def has_permission(context, codename: str) -> bool:
    request = context.get("request")
    user = getattr(request, "user", None) if request else None
    
    if not user or not getattr(user, "is_authenticated", False):
        return False
    
    if getattr(user, "is_administrator", False):
        return True
    
    return _has_permission(user, codename)


@register.simple_tag(takes_context=True)
def is_administrator(context) -> bool:
    request = context.get("request")
    user = getattr(request, "user", None) if request else None
    
    if not user or not getattr(user, "is_authenticated", False):
        return False
    
    return getattr(user, "is_administrator", False)

@register.filter
def get_item(mapping, key):
    try:
        return mapping.get(key, set())
    except (AttributeError, TypeError):
        return set()
    
@register.simple_tag
def get_item_tuple(mapping, app_label, model_label):
    _default = {'create': False, "read": False, "update": False, "delete": False}
    try:
        return mapping.get((app_label, model_label), _default)
    except (AttributeError, TypeError):
        return _default
    
@register.filter
def crumb_parts(value):
    if not value:
        return []
    parts = re.split(r"\s*(?:›|>|/|→|\|)\s*", str(value))
    return [p.strip() for p in parts if p.strip()]