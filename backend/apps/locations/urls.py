from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import FellowshipViewSet, RegionViewSet

router = DefaultRouter()
router.register(r"regions", RegionViewSet, basename="location-region")
router.register(r"", FellowshipViewSet, basename="fellowship")

urlpatterns = [
    path("", include(router.urls)),
]
