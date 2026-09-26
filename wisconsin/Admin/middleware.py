"""
Usage in a view:

    def my_view(request):
        ctx = request.audit_context
        ctx.ip_address      # "203.0.113.5"
        ctx.browser         # "Chrome 120.0.0"
        ctx.operating_system  # "Windows 10"
        ctx.device          # "Desktop" / "Mobile" / "Tablet" / "Other"
        ctx.request_method  # "POST"
        ctx.request_url     # "/api/users/42/update/"
        ctx.session_key     # request.session.session_key
        ctx.request_id      # uuid4 hex string, unique per request
        ctx.user            # request.user or None


"""
                                                                    
import uuid

from user_agents import parse as parse_user_agent


class AuditContext:
    """Plain data holder for per-request audit metadata. No DB access here."""

    __slots__ = (
        "user",
        "ip_address",
        "browser",
        "operating_system",
        "device",
        "request_method",
        "request_url",
        "session_key",
        "request_id",
    )

    def __init__(self, user, ip_address, browser, operating_system,
                 device, request_method, request_url, session_key, request_id):
        self.user = user
        self.ip_address = ip_address
        self.browser = browser
        self.operating_system = operating_system
        self.device = device
        self.request_method = request_method
        self.request_url = request_url
        self.session_key = session_key
        self.request_id = request_id


def _get_client_ip(request):
    """
    x-Forwarded-For can contain a chain of IPs; the first one is the original client.
    """
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _get_device_type(ua):
    if ua.is_mobile:
        return "Mobile"
    if ua.is_tablet:
        return "Tablet"
    if ua.is_pc:
        return "Desktop"
    return "Other"


class AuditMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.audit_context = self._build_context(request)
        return self.get_response(request)

    def _build_context(self, request):
        ua_string = request.META.get("HTTP_USER_AGENT", "")
        ua = parse_user_agent(ua_string)

        user = getattr(request, "user", None)
        if user is not None and not user.is_authenticated:
            user = None

        session_key = ""
        if hasattr(request, "session"):
            session_key = request.session.session_key or ""

        return AuditContext(
            user=user,
            ip_address=_get_client_ip(request),
            browser=f"{ua.browser.family} {ua.browser.version_string}".strip(),
            operating_system=f"{ua.os.family} {ua.os.version_string}".strip(),
            device=_get_device_type(ua),
            request_method=request.method,
            request_url=request.path,
            session_key=session_key,
            request_id=uuid.uuid4().hex,
        )