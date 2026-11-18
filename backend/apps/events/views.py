from common.permissions import IsAdminOrReadOnly
from django.utils import timezone
from rest_framework import filters, viewsets

from .models import Event
from .serializers import EventSerializer


class EventViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = EventSerializer
    lookup_field = "slug"
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "theme", "venue_name", "description"]
    ordering_fields = ["start_datetime", "end_datetime", "created_at"]
    ordering = ["start_datetime"]

    def get_queryset(self):
        user = self.request.user
        if user and user.is_authenticated and user.is_staff:
            queryset = Event.objects.all()
        else:
            queryset = Event.objects.published()

        timeframe = self.request.query_params.get("timeframe")
        now = timezone.now()

        if timeframe == "upcoming":
            queryset = queryset.filter(start_datetime__gte=now)
        elif timeframe == "past":
            queryset = queryset.filter(end_datetime__lt=now).order_by("-start_datetime")
        elif timeframe == "ongoing":
            queryset = queryset.filter(start_datetime__lte=now, end_datetime__gte=now)

        is_featured = self.request.query_params.get("featured")
        if is_featured is not None:
            queryset = queryset.filter(is_featured=is_featured.lower() == "true")

        return queryset
