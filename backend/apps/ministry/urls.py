from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    DoctrineViewSet,
    HomepageSectionViewSet,
    LeaderViewSet,
    MinistryProfileView,
)

router = DefaultRouter()
router.register(r"leaders", LeaderViewSet, basename="leader")
router.register(r"doctrine", DoctrineViewSet, basename="doctrine")
router.register(r"homepage-sections", HomepageSectionViewSet, basename="homepage-section")

urlpatterns = [
    path("profile/", MinistryProfileView.as_view(), name="ministry-profile"),
    path("", include(router.urls)),
]
