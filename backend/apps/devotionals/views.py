from common.permissions import IsAdminOrReadOnly
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Devotional
from .serializers import DevotionalSerializer


class DevotionalViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = DevotionalSerializer
    lookup_field = "date"

    def get_queryset(self):
        user = self.request.user
        if user and user.is_authenticated and user.is_staff:
            return Devotional.objects.all()
        return Devotional.objects.published()


class TodayDevotionalView(APIView):
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request):
        today = timezone.localdate()
        devotional = Devotional.objects.published().filter(date=today).first()
        if not devotional:
            # Fallback to the latest available published devotional if today isn't published yet
            devotional = Devotional.objects.published().order_by("-date").first()

        if not devotional:
            return Response(
                {"success": False, "message": "No devotionals currently available."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({"success": True, "data": DevotionalSerializer(devotional).data})
