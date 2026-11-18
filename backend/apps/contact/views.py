from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .models import ContactSubmission
from .serializers import (
    ContactSubmissionAdminSerializer,
    ContactSubmissionCreateSerializer,
)


class ContactSubmitView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "contact"

    def post(self, request):
        serializer = ContactSubmissionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Honeypot inspection: if filled, quietly drop spam without persisting
        if serializer.validated_data.get("hp_website"):
            return Response(
                {"success": True, "message": "Thank you for contacting us. We have received your message."},
                status=status.HTTP_200_OK,
            )

        ip_address = request.META.get("HTTP_X_FORWARDED_FOR")
        if ip_address:
            ip_address = ip_address.split(",")[0].strip()
        else:
            ip_address = request.META.get("REMOTE_ADDR")

        validated_data = serializer.validated_data.copy()
        validated_data.pop("hp_website", None)

        ContactSubmission.objects.create(
            **validated_data,
            ip_address=ip_address,
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
        )

        return Response(
            {
                "success": True,
                "message": "Thank you for contacting Holiness Revival Movement Worldwide. Our team will get back to you soon.",
            },
            status=status.HTTP_201_CREATED,
        )


class ContactSubmissionAdminViewSet(viewsets.ModelViewSet):
    """
    Inquiry management for administrators.
    """

    permission_classes = [IsAdminUser]
    queryset = ContactSubmission.objects.all().order_by("-created_at")
    serializer_class = ContactSubmissionAdminSerializer
