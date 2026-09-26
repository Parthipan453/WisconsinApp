import json
import logging
from django.conf import settings
from pywebpush import webpush, WebPushException

logger = logging.getLogger(__name__)

PUSH_TTL_SECONDS = 86400

def send_push_to_user(user, title, body, url="/", icon=None, tag=None, ttl=PUSH_TTL_SECONDS, notif_id=None):
    from Medical.models import PushSubscription

    subscriptions = PushSubscription.objects.filter(user=user)
    if not subscriptions.exists():
        logger.warning("send_push_to_user: no PushSubscription rows for %s - nothing to send", user)
        return

    payload = json.dumps({
        "title": title,
        "body": body,
        "url": url,
        "icon": icon or "/static/images/logo.png",
        "tag": tag or "medical-notification",
        "id": notif_id,
    })

    for sub in subscriptions:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {
                        "p256dh": sub.p256dh,
                        "auth": sub.auth,
                    },
                },
                data=payload, vapid_private_key=settings.VAPID_PRIVATE_KEY, vapid_claims=dict(settings.VAPID_CLAIMS), ttl=ttl)
            logger.info("PUSH SUCCESS | user=%s | subscription_id=%s | tag=%s", user, sub.pk, tag)

        except WebPushException as ex:
            logger.error("========== WEB PUSH ERROR ==========")
            logger.error("User: %s", user)
            logger.error("Subscription ID: %s", sub.pk)
            logger.error("Tag: %s", tag)
            logger.error("Exception: %s", str(ex))
            logger.error("Exception repr: %r", ex)

            response = getattr(ex, "response", None)

            if response is not None:
                status_code = getattr(response, "status_code", None)

                logger.error("HTTP Status Code: %s", status_code)

                try:
                    logger.error("Response Headers: %s", dict(response.headers))
                except Exception:
                    pass

                try:
                    body_detail = response.json()
                    logger.error("Response JSON: %s", body_detail)
                except Exception:
                    try:
                        body_detail = response.text
                        logger.error("Response Text: %s", body_detail)
                    except Exception:
                        body_detail = None

            else:
                status_code = None
                logger.error("No HTTP response received from push service.")

            logger.error("Endpoint: %s", sub.endpoint)
            logger.error("===================================")

            if status_code in (404, 410):
                logger.warning("Deleting expired/stale subscription | subscription_id=%s", sub.pk,)
                sub.delete()

            elif status_code in (401, 403):
                logger.warning("Push authentication/authorization failed | " "status=%s | subscription_id=%s", status_code, sub.pk)

            elif status_code == 400:
                logger.warning("Push request rejected | status=%s | subscription_id=%s", status_code, sub.pk)

            else:
                logger.warning("Unknown WebPush failure | status=%s | subscription_id=%s", status_code, sub.pk)

        except Exception as ex:

            logger.exception("========== UNEXPECTED PUSH ERROR ==========")
            logger.exception("User=%s | Subscription ID=%s | Tag=%s | Error=%s", user, sub.pk, tag, str(ex))