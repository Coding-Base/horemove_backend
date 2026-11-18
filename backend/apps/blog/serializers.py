from common.validators import sanitize_user_html
from rest_framework import serializers

from .models import Comment, Post, PostCategory


class PostCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PostCategory
        fields = "__all__"


class CommentPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["id", "author_name", "content", "created_at"]
        read_only_fields = fields


class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["author_name", "author_email", "content"]

    def validate_content(self, value):
        sanitized = sanitize_user_html(value)
        if not sanitized.strip():
            raise serializers.ValidationError("Comment cannot be empty.")
        return sanitized


class CommentAdminSerializer(serializers.ModelSerializer):
    post_title = serializers.CharField(source="post.title", read_only=True)

    class Meta:
        model = Comment
        fields = "__all__"


class PostSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    comments = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = "__all__"

    def get_comments(self, obj):
        # Only approved comments are visible to the public
        approved_comments = obj.comments.filter(status="APPROVED")
        return CommentPublicSerializer(approved_comments, many=True).data
