from common.permissions import IsAdminOrReadOnly
from django.db.models import Q
from rest_framework import filters, viewsets

from .models import Sermon, SermonCategory, Speaker
from .serializers import SermonCategorySerializer, SermonSerializer, SpeakerSerializer


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
