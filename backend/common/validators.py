import re
from urllib.parse import urlparse

import bleach
from rest_framework.exceptions import ValidationError

ALLOWED_MEDIA_DOMAINS = {
    "youtube.com",
    "www.youtube.com",
    "youtu.be",
    "vimeo.com",
    "player.vimeo.com",
    "t.me",
    "telegram.me",
    "res.cloudinary.com",
}


def validate_media_url(url: str) -> str:
    """
    Prevents SSRF and unauthorized external embeds by validating scheme and host.
    """
    if not url:
        return url
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValidationError("Invalid URL scheme. Only HTTP and HTTPS are permitted.")

    hostname = (parsed.hostname or "").lower()
    if hostname not in ALLOWED_MEDIA_DOMAINS and not any(hostname.endswith("." + d) for d in ALLOWED_MEDIA_DOMAINS):
        raise ValidationError(f"Domain '{hostname}' is not in the allowed media hosts whitelist.")
    return url


ALLOWED_HTML_TAGS = ["p", "b", "i", "u", "em", "strong", "a", "ul", "ol", "li", "blockquote", "h2", "h3", "h4", "br"]
ALLOWED_HTML_ATTRIBUTES = {
    "a": ["href", "title", "target", "rel"],
}


def sanitize_user_html(raw_html: str) -> str:
    """
    Defangs XSS in user-submitted markdown or formatted text.
    Completely removes script and style tags along with their inner contents.
    """
    if not raw_html:
        return ""
    # Strip script and style blocks entirely
    cleaned = re.sub(r"<script.*?>.*?</script>", "", raw_html, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"<style.*?>.*?</style>", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
    return bleach.clean(
        cleaned,
        tags=ALLOWED_HTML_TAGS,
        attributes=ALLOWED_HTML_ATTRIBUTES,
        strip=True,
    )
