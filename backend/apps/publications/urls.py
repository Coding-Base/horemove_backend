from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    PublicationCategoryViewSet,
    PublicationUploadView,
    PublicationViewSet,
)

router = DefaultRouter()
router.register(r"categories", PublicationCategoryViewSet, basename="publication-category")
router.register(r"", PublicationViewSet, basename="publication")

urlpatterns = [
    path("upload/", PublicationUploadView.as_view(), name="publication-upload"),
    path("", include(router.urls)),
]
