""" Dominic Code """
import re
from .models import Permission, PageAccess

_ON_PATH_RE = re.compile(r"on '(?P<attempted>.*?)' at path '(?P<path>.*?)'\.$")
_BLOCKED_PAGE_RE = re.compile(r"^Blocked access to page '(?P<page_key>.*?)'")


def build_lookup_maps():
    perm_lookup = dict(Permission.objects.values_list("codename", "name"))
    page_lookup = dict(PageAccess.objects.values_list("page_key", "display_name"))
    page_prefix_lookup = list(PageAccess.objects.values_list("path_prefix", "display_name"))
    return perm_lookup, page_lookup, page_prefix_lookup

def _permission_label(codename: str, perm_lookup: dict) -> str:
    if codename in perm_lookup:
        label = perm_lookup[codename]
        if label.lower().startswith("can "):
            label = label[4:]
        return label
    parts = codename.rsplit("_", 1)
    if len(parts) == 2:
        model, action = parts
        return f"{action.replace('_', ' ').title()} {model.replace('_', ' ').title()}"
    return codename.replace("_", " ").title()


def _page_label(page_key: str, page_lookup: dict) -> str:
    return page_lookup.get(page_key, page_key.replace("_", " ").title())


def _path_label(path: str, page_prefix_lookup) -> str:
    best = None
    for prefix, name in page_prefix_lookup:
        if path.startswith(prefix):
            if best is None or len(prefix) > len(best[0]):
                best = (prefix, name)
    return best[1] if best else None


def _display_user(log) -> str:
    user = log.action_by
    if not user:
        return "A user"
    full_name = user.get_full_name() if hasattr(user, "get_full_name") else ""
    return (full_name or getattr(user, "username", "A user")).strip()


def humanize_description(log, perm_lookup, page_lookup, page_prefix_lookup) -> str:
    desc = log.description or ""
    user_label = _display_user(log)

    if desc.startswith("Unauthorized access attempt by"):
        match = _ON_PATH_RE.search(desc)
        if not match:
            return desc

        attempted = match.group("attempted")
        path = match.group("path")

        if attempted.startswith("permission:"):
            label = _permission_label(attempted.split(":", 1)[1], perm_lookup)
            return f'{user_label} tried to "{label}" but does not have permission.'

        if attempted.startswith("page:"):
            label = _page_label(attempted.split(":", 1)[1], page_lookup)
            return f'{user_label} tried to open "{label}" but does not have access.'

        if attempted.startswith("any_of:") or attempted.startswith("all_of:"):
            codenames = [c for c in attempted.split(":", 1)[1].split(",") if c]
            labels = [_permission_label(c, perm_lookup) for c in codenames]
            joiner = " or " if attempted.startswith("any_of:") else " and "
            return f'{user_label} tried to "{joiner.join(labels)}" but does not have permission.'

        if attempted == "administrator_only":
            return f"{user_label} tried to open an Administrator-only page."

        label = _path_label(path, page_prefix_lookup) or "a restricted page"
        return f'{user_label} tried to open "{label}" but does not have access.'

    if desc.startswith("Blocked access to page"):
        match = _BLOCKED_PAGE_RE.search(desc)
        if match:
            label = _page_label(match.group("page_key"), page_lookup)
            return f'{user_label} tried to open "{label}" but does not have access.'

    return desc