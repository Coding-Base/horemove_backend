from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import EventViewSet, HomepageAnnouncementView

router = DefaultRouter()
router.register(r"", EventViewSet, basename="event")

urlpatterns = [
    path("homepage-announcement/", HomepageAnnouncementView.as_view(), name="homepage-announcement"),
    path("", include(router.urls)),
]
