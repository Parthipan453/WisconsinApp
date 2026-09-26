from ipaddress import ip_address
from django.http import HttpResponseForbidden


class OfficeLoginMiddleware:
    """Block login POST if not from office network."""

    allowed_ips = [
        '192.168.1.54',
        '127.0.0.1',
        '192.168.1.63',
        '192.168.1.82',
        '::1',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def _get_client_ip(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        if xff:
            return xff.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')

    def _is_allowed(self, ip_str):
        try:
            ip = ip_address(ip_str)
        except ValueError:
            return False
        for allowed in self.allowed_ips:
            try:
                if '/' in allowed:
                    from ipaddress import ip_network
                    if ip in ip_network(allowed, strict=False):
                        return True
                elif ip == ip_address(allowed):
                    return True
            except ValueError:
                continue
        return False

    def __call__(self, request):
        if request.method == 'POST' and request.path == '/login/':
            client_ip = self._get_client_ip(request)
            if not self._is_allowed(client_ip):
                return HttpResponseForbidden(
                    '<h1>403 Forbidden</h1>'
                    '<p>Login is only allowed from the office network.</p>'
                )
        return self.get_response(request)