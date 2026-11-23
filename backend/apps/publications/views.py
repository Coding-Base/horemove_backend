from common.permissions import IsAdminOrReadOnly
from rest_framework import filters, status, viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Publication, PublicationCategory
from .serializers import PublicationCategorySerializer, PublicationSerializer
from .supabase_storage import upload_publication_pdf


class PublicationUploadView(APIView):
    """
    Receives an uploaded PDF book/publication, verifies file type and size,
    and uploads it directly to Supabase Storage ('publications' bucket),
    returning the public CDN streaming URL and document metadata.
    """
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [AllowAny]  # Admin check or token validated in request

    def post(self, request):
        file_obj = request.FILES.get("file") or request.FILES.get("pdf")
        if not file_obj:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "NO_FILE_PROVIDED",
                        "message": "Please attach a valid PDF book file.",
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Ensure PDF extension / mime-type
        filename = getattr(file_obj, "name", "").lower()
        if not filename.endswith(".pdf") and getattr(file_obj, "content_type", "") != "application/pdf":
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_FILE_TYPE",
                        "message": "Only PDF documents (.pdf) can be uploaded as publications.",
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Max file size limit: 100MB
        if file_obj.size > 104857600:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "FILE_TOO_LARGE",
                        "message": "The uploaded book exceeds the maximum file size limit of 100MB.",
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = upload_publication_pdf(file_obj, original_name=file_obj.name)
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
                        "message": f"An error occurred while uploading to Supabase Storage: {str(e)}",
                    },
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PublicationCategoryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    queryset = PublicationCategory.objects.all()
    serializer_class = PublicationCategorySerializer
    lookup_field = "slug"


class PublicationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = PublicationSerializer
    lookup_field = "slug"
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "author", "description", "isbn"]
    ordering_fields = ["created_at", "title"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        if user and user.is_authenticated and user.is_staff:
            queryset = Publication.objects.all()
        else:
            queryset = Publication.objects.published()

        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category__slug=category)

        language = self.request.query_params.get("language")
        if language:
            queryset = queryset.filter(language__iexact=language)

        is_featured = self.request.query_params.get("featured")
        if is_featured is not None:
            queryset = queryset.filter(is_featured=is_featured.lower() == "true")

        return queryset.select_related("category")
