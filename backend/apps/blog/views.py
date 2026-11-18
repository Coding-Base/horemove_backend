from common.permissions import IsAdminOrReadOnly
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from .models import Comment, Post, PostCategory
from .serializers import (
    CommentAdminSerializer,
    CommentCreateSerializer,
    PostCategorySerializer,
    PostSerializer,
)


class PostCategoryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    queryset = PostCategory.objects.all()
    serializer_class = PostCategorySerializer
    lookup_field = "slug"


class PostViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = PostSerializer
    lookup_field = "slug"
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "excerpt", "body_markdown", "author_name"]
    ordering_fields = ["published_at", "view_count", "created_at"]
    ordering = ["-published_at"]

    def get_queryset(self):
        user = self.request.user
        if user and user.is_authenticated and user.is_staff:
            queryset = Post.objects.all()
        else:
            queryset = Post.objects.published()

        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category__slug=category)

        is_featured = self.request.query_params.get("featured")
        if is_featured is not None:
            queryset = queryset.filter(is_featured=is_featured.lower() == "true")

        return queryset.select_related("category")

    @action(
        detail=True,
        methods=["POST"],
        permission_classes=[AllowAny],
        throttle_classes=[ScopedRateThrottle],
    )
    def comments(self, request, slug=None):
        """
        Public comment submission: strictly throttled, defaults to PENDING moderation.
        """
        self.throttle_scope = "comments"
        post = self.get_object()
        serializer = CommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ip_address = request.META.get("HTTP_X_FORWARDED_FOR")
        if ip_address:
            ip_address = ip_address.split(",")[0].strip()
        else:
            ip_address = request.META.get("REMOTE_ADDR")

        serializer.save(
            post=post,
            status="PENDING",
            ip_address=ip_address,
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
        )

        return Response(
            {
                "success": True,
                "message": "Thank you! Your comment has been submitted and will appear once approved by our moderation team.",
            },
            status=status.HTTP_201_CREATED,
        )


class CommentAdminViewSet(viewsets.ModelViewSet):
    """
    Moderation queue: strictly restricted to admin/moderator roles.
    """

    permission_classes = [IsAdminUser]
    queryset = Comment.objects.all().order_by("-created_at")
    serializer_class = CommentAdminSerializer

    @action(detail=True, methods=["POST"])
    def approve(self, request, pk=None):
        comment = self.get_object()
        comment.status = "APPROVED"
        comment.save(update_fields=["status"])
        return Response({"success": True, "message": "Comment approved."})

    @action(detail=True, methods=["POST"])
    def reject(self, request, pk=None):
        comment = self.get_object()
        comment.status = "REJECTED"
        comment.save(update_fields=["status"])
        return Response({"success": True, "message": "Comment rejected."})
