import time
from collections import defaultdict
from typing import Callable

from django.http import HttpRequest, HttpResponse


class RateLimitMiddleware:
    """Limits request frequency per IP to prevent abuse of applicant endpoints."""

    REQUEST_WINDOW = 60
    MAX_REQUESTS = 30
    MAX_POST_REQUESTS = 10

    def __init__(self, get_response: Callable) -> None:
        self.get_response = get_response
        self.store: dict[str, list[float]] = defaultdict(list)

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.path.startswith("/applicants/"):
            ip = self._get_ip(request)
            now = time.time()

            key = f"{ip}:{request.path}"
            self.store[key] = [
                t for t in self.store[key]
                if now - t < self.REQUEST_WINDOW
            ]
            if len(self.store[key]) >= self.MAX_REQUESTS:
                return HttpResponse("Too many requests. Try again later.", status=429)
            self.store[key].append(now)

            if request.method == "POST":
                post_key = f"{ip}:POST"
                self.store[post_key] = [
                    t for t in self.store[post_key]
                    if now - t < self.REQUEST_WINDOW
                ]
                if len(self.store[post_key]) >= self.MAX_POST_REQUESTS:
                    return HttpResponse("Too many submissions. Try again later.", status=429)
                self.store[post_key].append(now)

        return self.get_response(request)

    @staticmethod
    def _get_ip(request: HttpRequest) -> str:
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            return xff.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "127.0.0.1")
