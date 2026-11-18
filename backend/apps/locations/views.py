from common.permissions import IsAdminOrReadOnly
from rest_framework import filters, viewsets

from .models import Fellowship, Region
from .serializers import FellowshipSerializer, RegionSerializer


class RegionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    queryset = Region.objects.all()
    serializer_class = RegionSerializer


class FellowshipViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = FellowshipSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "city_or_lga", "address", "region__country", "region__state_or_province"]
    ordering_fields = ["name", "city_or_lga"]

    def get_queryset(self):
        user = self.request.user
        if user and user.is_authenticated and user.is_staff:
            queryset = Fellowship.objects.all()
        else:
            queryset = Fellowship.objects.filter(is_active=True)

        continent = self.request.query_params.get("continent")
        if continent:
            queryset = queryset.filter(region__continent__iexact=continent)

        country = self.request.query_params.get("country")
        if country:
            queryset = queryset.filter(region__country__iexact=country)

        state = self.request.query_params.get("state")
        if state:
            queryset = queryset.filter(region__state_or_province__iexact=state)

        return queryset.select_related("region")
