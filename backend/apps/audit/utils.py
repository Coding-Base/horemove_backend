from .models import AuditLog


def record_audit_log(
    action: str,
    resource_type: str,
    resource_id: str = "",
    request=None,
    actor=None,
    details: dict = None,
):
    actor_obj = actor or (request.user if request and request.user.is_authenticated else None)
    actor_email = actor_obj.email if actor_obj else ""
    ip_address = None
    user_agent = ""
    request_id = ""

    if request:
        ip_address = request.META.get("HTTP_X_FORWARDED_FOR")
        if ip_address:
            ip_address = ip_address.split(",")[0].strip()
        else:
            ip_address = request.META.get("REMOTE_ADDR")
        user_agent = request.META.get("HTTP_USER_AGENT", "")[:500]
        request_id = getattr(request, "request_id", "")

    return AuditLog.objects.create(
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id),
        actor=actor_obj,
        actor_email=actor_email,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details or {},
        request_id=request_id,
    )
