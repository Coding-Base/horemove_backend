from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DevotionalViewSet, TodayDevotionalView

router = DefaultRouter()
router.register(r"", DevotionalViewSet, basename="devotional")

urlpatterns = [
    path("today/", TodayDevotionalView.as_view(), name="devotional-today"),
    path("", include(router.urls)),
]
