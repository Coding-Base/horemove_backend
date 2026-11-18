import logging
import re
from typing import List, Optional, Union

import resend
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags

logger = logging.getLogger("horemow.email")


def mask_email(email: str) -> str:
    """
    Masks email for safe logging (e.g., d***h@example.com).
    """
    if not email or "@" not in email:
        return "[INVALID_EMAIL]"
    name, domain = email.split("@", 1)
    if len(name) <= 2:
        masked_name = name[0] + "*"
    else:
        masked_name = name[0] + "*" * (len(name) - 2) + name[-1]
    return f"{masked_name}@{domain}"


def sanitize_header(header_val: str) -> str:
    """
    Protects against SMTP header injection by removing CRLF characters.
    """
    if not header_val:
        return ""
    return re.sub(r"[\r\n]", "", header_val).strip()


def send_transactional_email(
    to: Union[str, List[str]],
    subject: str,
    html_content: str,
    plain_text: Optional[str] = None,
    reply_to: Optional[str] = None,
    from_email: Optional[str] = None,
) -> dict:
    """
    Sends a transactional email via Resend API (production)
    with seamless fallback to Django EmailBackend for test/dev environments.
    """
    recipients = [to] if isinstance(to, str) else list(to)
    recipients = [r.strip() for r in recipients if r and "@" in r]
    if not recipients:
        logger.warning("Email dispatch skipped: no valid recipients provided.")
        return {"success": False, "error": "No valid recipients"}

    subject = sanitize_header(subject)
    sender = from_email or settings.DEFAULT_FROM_EMAIL
    if not plain_text:
        plain_text = strip_tags(html_content)

    resend_api_key = getattr(settings, "RESEND_API_KEY", "")
    use_resend = bool(
        resend_api_key
        and not resend_api_key.startswith("re_placeholder")
        and getattr(settings, "EMAIL_BACKEND", "") != "django.core.mail.backends.locmem.EmailBackend"
    )

    if use_resend:
        try:
            resend.api_key = resend_api_key
            params = {
                "from": sender,
                "to": recipients,
                "subject": subject,
                "html": html_content,
                "text": plain_text,
            }
            if reply_to:
                params["reply_to"] = sanitize_header(reply_to)

            response = resend.Emails.send(params)
            message_id = response.get("id") or str(response)
            logger.info(
                "Successfully dispatched email via Resend (ID: %s) to %s",
                message_id,
                [mask_email(e) for e in recipients],
            )
            return {"success": True, "message_id": message_id, "provider": "resend"}
        except Exception as e:
            logger.error(
                "Resend API dispatch failed for %s: %s. Falling back to Django email backend.",
                [mask_email(e) for e in recipients],
                e,
            )
            # Fall through to standard Django backend on failure

    # Fallback / Local / Test delivery via Django EmailBackend
    try:
        reply_to_list = [sanitize_header(reply_to)] if reply_to else None
        msg = EmailMultiAlternatives(
            subject=subject,
            body=plain_text,
            from_email=sender,
            to=recipients,
            reply_to=reply_to_list,
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)
        logger.info(
            "Successfully dispatched email via Django backend to %s",
            [mask_email(e) for e in recipients],
        )
        return {"success": True, "message_id": "django-local", "provider": "django"}
    except Exception as e:
        logger.error(
            "Failed to send email to %s via Django backend: %s",
            [mask_email(e) for e in recipients],
            e,
        )
        return {"success": False, "error": str(e), "provider": "failed"}
