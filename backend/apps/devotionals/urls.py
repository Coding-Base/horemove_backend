from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AutoPublishSettingsView,
    DevotionalBatchViewSet,
    DevotionalParsedEntryViewSet,
    DevotionalViewSet,
    TodayDevotionalView,
)

router = DefaultRouter()
router.register(r"batches", DevotionalBatchViewSet, basename="devotional-batch")
router.register(r"parsed-entries", DevotionalParsedEntryViewSet, basename="devotional-parsed-entry")
router.register(r"", DevotionalViewSet, basename="devotional")

urlpatterns = [
    path("today/", TodayDevotionalView.as_view(), name="devotional-today"),
    path("settings/auto-publish/", AutoPublishSettingsView.as_view(), name="devotional-auto-publish-settings"),
    path("", include(router.urls)),
]
