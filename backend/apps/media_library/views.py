import time

import cloudinary.utils
from django.conf import settings
from rest_framework import status, viewsets
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import MediaAsset
from .serializers import MediaAssetSerializer


class CloudinarySignUploadView(APIView):
    """
    Generates a secure, temporary Cloudinary signed upload signature.
    Allows frontend to upload directly to Cloudinary without exposing API Secret.
    """

    permission_classes = [IsAdminUser]

    def post(self, request):
        folder = request.data.get("folder", "horemow_media")
        # Sanitize folder to avoid path traversal
        folder = folder.replace("..", "").strip("/ ") or "horemow_media"
        timestamp = int(time.time())

        params_to_sign = {
            "folder": folder,
            "timestamp": timestamp,
        }

        api_secret = settings.CLOUDINARY_CONFIG.get("api_secret")
        api_key = settings.CLOUDINARY_CONFIG.get("api_key")
        cloud_name = settings.CLOUDINARY_CONFIG.get("cloud_name")

        if not (api_secret and api_key and cloud_name):
            # If Cloudinary is not configured in local environment, provide clear notice
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "CLOUDINARY_NOT_CONFIGURED",
                        "message": "Cloudinary credentials are not configured in backend environment.",
                    },
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        signature = cloudinary.utils.api_sign_request(params_to_sign, api_secret)

        return Response(
            {
                "success": True,
                "signature": signature,
                "timestamp": timestamp,
                "folder": folder,
                "api_key": api_key,
                "cloud_name": cloud_name,
            }
        )


class MediaAssetViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = MediaAsset.objects.all()
    serializer_class = MediaAssetSerializer

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)
