from common.api.mixins import AuditedModelViewSetMixin
from common.permissions import IsAdminOrReadOnly
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Doctrine, HomepageSection, Leader, MinistryProfile
from .serializers import (
    DoctrineSerializer,
    HomepageSectionSerializer,
    LeaderSerializer,
    MinistryProfileSerializer,
)


class MinistryProfileView(APIView):
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request):
        profile, _ = MinistryProfile.objects.get_or_create(id="00000000-0000-0000-0000-000000000001")
        return Response({"success": True, "data": MinistryProfileSerializer(profile).data})

    def put(self, request):
        profile, _ = MinistryProfile.objects.get_or_create(id="00000000-0000-0000-0000-000000000001")
        serializer = MinistryProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True, "data": serializer.data})


class LeaderViewSet(AuditedModelViewSetMixin, viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = LeaderSerializer

    def get_queryset(self):
        if self.request.user and self.request.user.is_authenticated and self.request.user.is_staff:
            return Leader.objects.all()
        return Leader.objects.filter(is_active=True)


class DoctrineViewSet(AuditedModelViewSetMixin, viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = DoctrineSerializer

    def get_queryset(self):
        if self.request.user and self.request.user.is_authenticated and self.request.user.is_staff:
            return Doctrine.objects.all()
        return Doctrine.objects.filter(is_active=True)


class HomepageSectionViewSet(AuditedModelViewSetMixin, viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = HomepageSectionSerializer
    lookup_field = "section_key"

    def get_queryset(self):
        if self.request.user and self.request.user.is_authenticated and self.request.user.is_staff:
            return HomepageSection.objects.all()
        return HomepageSection.objects.filter(is_active=True)
