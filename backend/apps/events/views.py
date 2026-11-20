from common.permissions import IsAdminOrReadOnly
from django.utils import timezone
from rest_framework import filters, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Event, HomepageAnnouncement
from .serializers import EventSerializer, HomepageAnnouncementSerializer


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


class HomepageAnnouncementView(APIView):
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request):
        announcement, _ = HomepageAnnouncement.objects.get_or_create(pk=1)
        user = request.user
        is_staff = bool(user and user.is_authenticated and user.is_staff)

        # For non-staff public visitors, if not enabled, return enabled=False
        if not is_staff and not announcement.enabled:
            return Response({
                "enabled": False,
                "eyebrow": announcement.eyebrow,
                "title": "",
                "message": "",
                "image_url": "",
                "action_label": "",
                "action_url": "",
                "updated_at": announcement.updated_at.isoformat() if announcement.updated_at else "",
            })

        return Response(HomepageAnnouncementSerializer(announcement).data)

    def put(self, request):
        announcement, _ = HomepageAnnouncement.objects.get_or_create(pk=1)
        serializer = HomepageAnnouncementSerializer(
            announcement,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
