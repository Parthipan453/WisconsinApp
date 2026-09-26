from pathlib import Path
from email.mime.image import MIMEImage
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.core.cache import cache
from django.urls import get_resolver, URLPattern, URLResolver

# Password
def send_otp_email(user, otp):
    subject = "Your Password Reset Code"

    context = {
        "user": user,
        "otp": otp,
        "validity_minutes": 10,
    }

    html_message = render_to_string("Dominic/otp_email.html", context)

    plain_message = (
        f"Hi {user.first_name or user.username},\n\n"
        f"Your password reset code is: {otp}\n"
        f"This code expires in 10 minutes.\n"
        f"If you didn't request this, please ignore this email."
    )

    email = EmailMultiAlternatives(
        subject=subject,
        body=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )

    email.attach_alternative(html_message, "text/html")

    logo_path = (
        Path(settings.BASE_DIR)
        / "Admin"
        / "static"
        / "images"
        / "white-logo.png"
    )

    with open(logo_path, "rb") as f:
        logo = MIMEImage(f.read())
        logo.add_header("Content-ID", "<uw_logo>")
        logo.add_header(
            "Content-Disposition",
            "inline",
            filename="white-logo.png",
        )
        email.attach(logo)

    email.mixed_subtype = "related"

    email.send()
    
# Search

EXCLUDED_NAMES = {
    "admin_search",
    "login", "logout",
}

ADMIN_URL_PREFIX = ("/dashboard/", "/permission/", "/colleges/", "/department/")

EXCLUDED_NAMES_SUFFIXES = ("_json", "_api")

CACHE_KEY = "admin_search_index"
CACHE_TTL = 60 * 15


def _humanize(name):
    return name.replace("_", " ").replace("-", " ").title()


def _guess_group(app_name, url_name):
    if app_name:
        return app_name.replace("_", " ").title()
    return url_name.split("_")[0].title()


def _has_params(path):
    return "<" in path or "(?P" in path


def _walk(patterns, prefix, app_name, results):
    for pattern in patterns:
        if isinstance(pattern, URLResolver):
            _walk(
                pattern.url_patterns,
                prefix + str(pattern.pattern),
                pattern.app_name or app_name,
                results,
            )
        elif isinstance(pattern, URLPattern):
            full_path = "/" + (prefix + str(pattern.pattern)).lstrip("/")
            name = pattern.name

            if not name or name in EXCLUDED_NAMES:
                continue
            if name.endswith(EXCLUDED_NAMES_SUFFIXES):
                continue
            if _has_params(full_path):
                continue
            if not full_path.startswith(ADMIN_URL_PREFIX):
                continue

            extra = getattr(pattern.callback, "search_meta", {}) if pattern.callback else {}

            results.append({
                "title": extra.get("search_title", _humanize(name)),
                "path": full_path,
                "group": extra.get("search_group", _guess_group(app_name, name)),
                "icon": extra.get("search_icon", "file"),
            })


def build_admin_pages():
    resolver = get_resolver()
    results = []
    _walk(resolver.url_patterns, prefix="", app_name=None, results=results)

    seen = set()
    deduped = []
    for page in results:
        if page["path"] not in seen:
            seen.add(page["path"])
            deduped.append(page)
    return deduped


def get_admin_pages(force_refresh=False):
    if settings.DEBUG:
        return build_admin_pages()

    if force_refresh:
        cache.delete(CACHE_KEY)

    pages = cache.get(CACHE_KEY)
    if pages is None:
        pages = build_admin_pages()
        cache.set(CACHE_KEY, pages, CACHE_TTL)


    return pages

