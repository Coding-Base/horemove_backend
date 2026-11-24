from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    SermonAudioUploadView,
    SermonCategoryViewSet,
    SermonViewSet,
    SpeakerViewSet,
)

router = DefaultRouter()
router.register(r"categories", SermonCategoryViewSet, basename="sermon-category")
router.register(r"speakers", SpeakerViewSet, basename="speaker")
router.register(r"", SermonViewSet, basename="sermon")

urlpatterns = [
    path("upload-audio/", SermonAudioUploadView.as_view(), name="sermon-upload-audio"),
    path("", include(router.urls)),
]
