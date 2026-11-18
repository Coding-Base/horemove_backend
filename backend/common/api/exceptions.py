import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger("horemow.api")


def custom_exception_handler(exc, context):
    """
    Standardized, uniform error response format:
    {
      "success": false,
      "error": {
        "code": "ERROR_CODE",
        "message": "Human readable summary",
        "details": ...
      },
      "request_id": "uuid"
    }
    """
    response = exception_handler(exc, context)
    request = context.get("request")
    request_id = getattr(request, "request_id", None) if request else None

    if response is not None:
        error_code = "API_ERROR"
        message = "An error occurred while processing your request."
        details = response.data

        if response.status_code == status.HTTP_400_BAD_REQUEST:
            error_code = "VALIDATION_ERROR"
            message = "Invalid input data provided."
        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            error_code = "AUTHENTICATION_REQUIRED"
            message = "Authentication credentials were not provided or are invalid."
        elif response.status_code == status.HTTP_403_FORBIDDEN:
            error_code = "PERMISSION_DENIED"
            message = "You do not have permission to perform this action."
        elif response.status_code == status.HTTP_404_NOT_FOUND:
            error_code = "NOT_FOUND"
            message = "The requested resource could not be found."
        elif response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            error_code = "RATE_LIMIT_EXCEEDED"
            message = "Request rate limit exceeded. Please try again later."

        response.data = {
            "success": False,
            "error": {
                "code": error_code,
                "message": message,
                "details": details,
            },
            "request_id": request_id,
        }
    else:
        # Unhandled 500 server error - never leak traceback details to client in production
        logger.exception("Unhandled server exception occurred: %s", exc)
        response = Response(
            {
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An internal server error occurred.",
                    "details": None,
                },
                "request_id": request_id,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response
