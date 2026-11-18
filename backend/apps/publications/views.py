from common.permissions import IsAdminOrReadOnly
from rest_framework import filters, viewsets

from .models import Publication, PublicationCategory
from .serializers import PublicationCategorySerializer, PublicationSerializer


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
