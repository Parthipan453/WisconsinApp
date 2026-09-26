import json

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from pywebpush import webpush, WebPushException
from Medical.models import PushSubscription
from Medical.Dominic.push import PUSH_TTL_SECONDS


class Command(BaseCommand):
    help = "Send a real test push to a user's saved subscriptions and print full diagnostics."

    def add_arguments(self, parser):
        parser.add_argument("user", help="username or numeric user id")

    def handle(self, *args, **options):
        User = get_user_model()
        identifier = options["user"]

        user = None
        if identifier.isdigit():
            user = User.objects.filter(pk=int(identifier)).first()
        if user is None:
            user = User.objects.filter(username=identifier).first()
        if user is None:
            raise CommandError(f"No user found for '{identifier}'")

        subs = PushSubscription.objects.filter(user=user)
        if not subs.exists():
            self.stdout.write(self.style.WARNING(f"No PushSubscription rows for {user}. Nothing to test."))
            return

        for sub in subs:
            self.stdout.write(self.style.NOTICE(f"\n--- Subscription id={sub.pk} ---"))
            self.stdout.write(f"endpoint: {sub.endpoint}")
            self.stdout.write(f"endpoint length: {len(sub.endpoint)}")
            self.stdout.write(f"p256dh length: {len(sub.p256dh)}  auth length: {len(sub.auth)}")

            subscription_info = {
                "endpoint": sub.endpoint,
                "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
            }
            payload = json.dumps({
                "title": "Test push",
                "body": "This is a diagnostic test push.",
                "url": "/",
                "icon": "/static/images/logo.png",
                "tag": "test-push",
            })
            vapid_claims = dict(settings.VAPID_CLAIMS)

            # 1) Print the equivalent curl command - useful to replay outside Django
            #    to rule out anything Django/network-specific on this machine.
            try:
                curl_cmd = webpush(
                    subscription_info=subscription_info,
                    data=payload,
                    vapid_private_key=settings.VAPID_PRIVATE_KEY,
                    vapid_claims=dict(vapid_claims),
                    ttl=PUSH_TTL_SECONDS,
                    curl=True,
                )
                self.stdout.write(self.style.NOTICE("\nEquivalent curl command:"))
                self.stdout.write(curl_cmd)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Could not build curl command: {e!r}"))

            # 2) Actually send it and print the *real* response.
            try:
                resp = webpush(
                    subscription_info=subscription_info,
                    data=payload,
                    vapid_private_key=settings.VAPID_PRIVATE_KEY,
                    vapid_claims=dict(vapid_claims),
                    ttl=PUSH_TTL_SECONDS,
                    verbose=True,
                )
                self.stdout.write(self.style.SUCCESS(f"\nSUCCESS: status={resp.status_code}"))
            except WebPushException as ex:
                self.stdout.write(self.style.ERROR("\nFAILED:"))
                resp = ex.response
                if resp is not None:
                    self.stdout.write(f"  status_code: {resp.status_code}")
                    self.stdout.write(f"  reason: {resp.reason}")
                    self.stdout.write(f"  request url: {resp.request.url}")
                    self.stdout.write("  request headers:")
                    for k, v in resp.request.headers.items():
                        self.stdout.write(f"    {k}: {v}")
                    self.stdout.write("  response headers:")
                    for k, v in resp.headers.items():
                        self.stdout.write(f"    {k}: {v}")
                    self.stdout.write(f"  response body: {resp.text!r}")
                else:
                    self.stdout.write(f"  no response object. message: {ex.message}")