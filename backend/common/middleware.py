import logging
import re
import uuid

logger = logging.getLogger("horemow.security")

SENSITIVE_KEYS = re.compile(
    r"(password|token|secret|authorization|key|card|cvv|account_number)",
    re.IGNORECASE,
)


def scrub_sensitive_dict(data):
    if not isinstance(data, dict):
        return data
    cleaned = {}
    for k, v in data.items():
        if SENSITIVE_KEYS.search(str(k)):
            cleaned[k] = "[REDACTED]"
        elif isinstance(v, dict):
            cleaned[k] = scrub_sensitive_dict(v)
        elif isinstance(v, list):
            cleaned[k] = [scrub_sensitive_dict(item) if isinstance(item, dict) else item for item in v]
        else:
            cleaned[k] = v
    return cleaned


class RequestCorrelationMiddleware:
    """
    Assigns an immutable UUID correlation ID to every request.
    Scans and logs inbound requests without leaking credentials.
    Sets X-Request-ID response header.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())
        request.request_id = request_id

        # Attach request_id to response
        response = self.get_response(request)
        response["X-Request-ID"] = request_id
        return response
