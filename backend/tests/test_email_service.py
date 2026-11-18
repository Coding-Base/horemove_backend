from unittest.mock import patch

import pytest
from common.email.service import mask_email, sanitize_header, send_transactional_email


def test_mask_email():
    assert mask_email("deborah@example.com") == "d*****h@example.com"
    assert mask_email("ed@example.com") == "e*@example.com"
    assert mask_email("invalid") == "[INVALID_EMAIL]"


def test_sanitize_header():
    dirty = "Subject line\r\nBcc: evil@hacker.com\nInjection"
    clean = sanitize_header(dirty)
    assert "\r" not in clean
    assert "\n" not in clean
    assert clean == "Subject lineBcc: evil@hacker.comInjection"


@pytest.mark.django_db
def test_send_transactional_email_django_fallback(mailoutbox):
    result = send_transactional_email(
        to="donor@test.com",
        subject="Donation Receipt",
        html_content="<h1>Thank you for your offering</h1>",
    )
    assert result["success"] is True
    assert result["provider"] == "django"
    assert len(mailoutbox) == 1
    assert "donor@test.com" in mailoutbox[0].to
    assert mailoutbox[0].subject == "Donation Receipt"


@pytest.mark.django_db
def test_send_transactional_email_via_resend(settings):
    settings.RESEND_API_KEY = "re_live_valid_api_key_123"
    settings.EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

    with patch("resend.Emails.send") as mock_resend:
        mock_resend.return_value = {"id": "msg_resend_98765"}
        result = send_transactional_email(
            to="donor@test.com",
            subject="Verified Receipt",
            html_content="<p>Blessings</p>",
            plain_text="Blessings",
        )
        assert result["success"] is True
        assert result["provider"] == "resend"
        assert result["message_id"] == "msg_resend_98765"
        mock_resend.assert_called_once()
