from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ContactSubmissionAdminViewSet, ContactSubmitView

router = DefaultRouter()
router.register(r"inquiries", ContactSubmissionAdminViewSet, basename="contact-inquiry")

urlpatterns = [
    path("submit/", ContactSubmitView.as_view(), name="contact-submit"),
    path("", include(router.urls)),
]
