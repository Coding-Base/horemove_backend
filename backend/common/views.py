from django.db import connection
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """
    Lightweight health check probe for load balancers.
    Reveals zero infrastructure or secret details.
    """
    return JsonResponse({"status": "healthy", "service": "horemow-backend"})


@api_view(["GET"])
@permission_classes([AllowAny])
def readiness_check(request):
    """
    Readiness check verifying database connectivity.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            cursor.fetchone()
        return JsonResponse({"status": "ready", "database": "connected"})
    except Exception:
        return JsonResponse({"status": "unready", "database": "disconnected"}, status=503)


def custom_404_view(request, exception=None):
    request_id = getattr(request, "request_id", None)
    return JsonResponse(
        {
            "success": False,
            "error": {
                "code": "NOT_FOUND",
                "message": "The requested resource could not be found.",
                "details": None,
            },
            "request_id": request_id,
        },
        status=404,
    )


def custom_500_view(request):
    request_id = getattr(request, "request_id", None)
    return JsonResponse(
        {
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred.",
                "details": None,
            },
            "request_id": request_id,
        },
        status=500,
    )
