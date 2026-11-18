from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CommentAdminViewSet, PostCategoryViewSet, PostViewSet

router = DefaultRouter()
router.register(r"categories", PostCategoryViewSet, basename="post-category")
router.register(r"moderation/comments", CommentAdminViewSet, basename="comment-moderation")
router.register(r"", PostViewSet, basename="post")

urlpatterns = [
    path("", include(router.urls)),
]
