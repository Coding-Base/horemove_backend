from common.permissions import IsAdminOrReadOnly
from django.db.models import Q
from rest_framework import filters, status, viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Sermon, SermonCategory, Speaker
from .serializers import SermonCategorySerializer, SermonSerializer, SpeakerSerializer
from .supabase_storage import upload_sermon_audio


class SermonAudioUploadView(APIView):
    """
    Receives an uploaded audio file (mp3, wav, m4a, etc.),
    uploads directly to Supabase Storage ('sermons' bucket),
    and returns the public CDN streaming URL.
    """
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [AllowAny]

    def post(self, request):
        file_obj = request.FILES.get("file") or request.FILES.get("audio")
        if not file_obj:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "NO_FILE_PROVIDED",
                        "message": "Please attach a valid audio file (e.g. MP3, M4A, WAV).",
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 200MB size limit for audio
        if file_obj.size > 209715200:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "FILE_TOO_LARGE",
                        "message": "The uploaded audio exceeds the maximum file size limit of 200MB.",
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = upload_sermon_audio(file_obj, original_name=file_obj.name)
            if result.get("public_url") and result["public_url"].startswith("/"):
                result["public_url"] = request.build_absolute_uri(result["public_url"])
            return Response(
                {
                    "success": True,
                    "data": result,
                },
                status=status.HTTP_201_CREATED if result.get("success") else status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "UPLOAD_FAILED",
                        "message": f"An error occurred while uploading audio: {str(e)}",
                    },
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SermonCategoryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    queryset = SermonCategory.objects.all()
    serializer_class = SermonCategorySerializer
    lookup_field = "slug"


class SpeakerViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    queryset = Speaker.objects.all()
    serializer_class = SpeakerSerializer


class SermonViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = SermonSerializer
    lookup_field = "slug"
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "summary", "scripture_references", "speaker__name"]
    ordering_fields = ["date_preached", "view_count", "created_at"]
    ordering = ["-date_preached"]

    def get_queryset(self):
        user = self.request.user
        if user and user.is_authenticated and user.is_staff:
            queryset = Sermon.objects.all()
        else:
            queryset = Sermon.objects.published()

        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(Q(category__slug=category) | Q(category__name=category))

        speaker = self.request.query_params.get("speaker")
        if speaker:
            queryset = queryset.filter(speaker_id=speaker)

        is_featured = self.request.query_params.get("featured")
        if is_featured is not None:
            queryset = queryset.filter(is_featured=is_featured.lower() == "true")

        return queryset.select_related("speaker", "category")
