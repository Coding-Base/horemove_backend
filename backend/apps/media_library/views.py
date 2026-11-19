import time
import uuid

import cloudinary.uploader
import cloudinary.utils
from django.conf import settings
from rest_framework import status, viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import MediaAsset
from .serializers import MediaAssetSerializer


class MediaUploadView(APIView):
    """
    Direct authenticated media upload to Cloudinary via backend.
    Saves a MediaAsset record and returns the public secure_url.
    """

    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        file_obj = request.FILES.get("file")
        if not file_obj:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "NO_FILE",
                        "message": "No file was uploaded.",
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        api_secret = settings.CLOUDINARY_CONFIG.get("api_secret")
        api_key = settings.CLOUDINARY_CONFIG.get("api_key")
        cloud_name = settings.CLOUDINARY_CONFIG.get("cloud_name")

        if not (api_secret and api_key and cloud_name):
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "CLOUDINARY_NOT_CONFIGURED",
                        "message": "Cloudinary credentials (CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET) are not configured in backend environment.",
                    },
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        folder = request.data.get("folder", "horemow_media")
        folder = folder.replace("..", "").strip("/ ") or "horemow_media"

        try:
            upload_result = cloudinary.uploader.upload(
                file_obj,
                folder=folder,
                resource_type="auto",
                cloud_name=cloud_name,
                api_key=api_key,
                api_secret=api_secret,
            )
        except Exception as exc:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "CLOUDINARY_UPLOAD_FAILED",
                        "message": f"Cloudinary upload failed: {str(exc)}",
                    },
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        asset = MediaAsset.objects.create(
            public_id=upload_result.get("public_id", str(uuid.uuid4())),
            secure_url=upload_result.get("secure_url", ""),
            resource_type=upload_result.get("resource_type", "image"),
            format=upload_result.get("format", ""),
            width=upload_result.get("width"),
            height=upload_result.get("height"),
            bytes=upload_result.get("bytes", file_obj.size),
            title=request.data.get("title", file_obj.name),
            alt_text=request.data.get("alt_text", ""),
            uploaded_by=request.user,
        )

        return Response(
            {
                "success": True,
                "url": asset.secure_url,
                "public_id": asset.public_id,
                "asset_id": str(asset.id),
                "format": asset.format,
                "bytes": asset.bytes,
            },
            status=status.HTTP_201_CREATED,
        )


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
