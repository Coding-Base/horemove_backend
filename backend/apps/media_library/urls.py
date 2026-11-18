from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CloudinarySignUploadView, MediaAssetViewSet

router = DefaultRouter()
router.register(r"assets", MediaAssetViewSet, basename="media-asset")

urlpatterns = [
    path("sign-upload/", CloudinarySignUploadView.as_view(), name="cloudinary-sign-upload"),
    path("", include(router.urls)),
]
