import json
import logging

from django.utils import timezone

logger = logging.getLogger("audit")


class AuditLogger:
    @classmethod
    def log(cls, request=None, *, action, module, object_type,
             object_id="", description="", before_data=None, after_data=None,
             status="SUCCESS", user=None):
        
        from Admin.models import UserAuditLog

        try:
            ctx = getattr(request, "audit_context", None) if request is not None else None

            resolved_user = user if user is not None else (ctx.user if ctx else None)

            UserAuditLog.objects.create(
                user=resolved_user,
                action=action,
                module=module,
                object_type=object_type,
                object_id=str(object_id) if object_id != "" else "",
                description=description,
                ip_address=ctx.ip_address if ctx else None,
                browser=ctx.browser if ctx else "",
                operating_system=ctx.operating_system if ctx else "",
                device=ctx.device if ctx else "",
                request_method=ctx.request_method if ctx else "",
                request_url=ctx.request_url if ctx else "",
                status=status,
                before_data=cls._safe_json(before_data),
                after_data=cls._safe_json(after_data),
                session_key=ctx.session_key if ctx else "",
                request_id=ctx.request_id if ctx else "",
            )
        except Exception:
           
            logger.exception(
                "AuditLogger.log failed | action=%s module=%s object_type=%s object_id=%s",
                action, module, object_type, object_id,
            )
            return None

    @staticmethod
    def _safe_json(data):
       
        if data is None:
            return None
        try:
            json.dumps(data)
            return data
        except (TypeError, ValueError):
            safe = {}
            for key, value in data.items():
                try:
                    json.dumps(value)
                    safe[key] = value
                except (TypeError, ValueError):
                    safe[key] = str(value)
            return safe

    @staticmethod
    def model_to_dict(instance, fields):
       
        snapshot = {}
        for field_name in fields:
            value = getattr(instance, field_name, None)
            if hasattr(value, "pk"):  
                snapshot[field_name] = str(value) if value is not None else None
            elif hasattr(value, "isoformat"):  # date/datetime
                snapshot[field_name] = value.isoformat()
            else:
                snapshot[field_name] = value
        return snapshot




from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver


@receiver(user_logged_in)
def _on_user_logged_in(sender, request, user, **kwargs):
    AuditLogger.log(
        request=request,
        action="LOGIN",
        module="Auth",
        object_type="User",
        object_id=user.id,
        description=f"User '{user.username}' logged in.",
        status="SUCCESS",
        user=user,
    )


@receiver(user_logged_out)
def _on_user_logged_out(sender, request, user, **kwargs):
    
    AuditLogger.log(
        request=request,
        action="LOGOUT",
        module="Auth",
        object_type="User",
        object_id=user.id if user else "",
        description=f"User '{user.username}' logged out." if user else "Unknown user logged out.",
        status="SUCCESS",
        user=user,
    )
 

@receiver(user_login_failed)
def _on_user_login_failed(sender, credentials, request=None, **kwargs):
    attempted_username = credentials.get("username", "unknown")
    AuditLogger.log(
        request=request,
        action="LOGIN",
        module="Auth",
        object_type="User",
        object_id="",
        description=f"Failed login attempt for username '{attempted_username}'.",
        status="FAILED",
        user=None,
    )