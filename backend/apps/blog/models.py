import uuid

from common.models import PublishableModel
from django.db import models


class PostCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=160, unique=True)

    class Meta:
        verbose_name_plural = "Post Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Post(PublishableModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, db_index=True)
    category = models.ForeignKey(PostCategory, on_delete=models.SET_NULL, null=True, related_name="posts")
    author_name = models.CharField(max_length=255, default="HOREMOW Editorial Team")
    excerpt = models.TextField()
    body_markdown = models.TextField()
    cover_image_url = models.URLField(max_length=1000, blank=True)
    is_featured = models.BooleanField(default=False)
    view_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-published_at", "-created_at"]

    def __str__(self):
        return self.title


class Comment(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending Moderation"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
        ("FLAGGED", "Flagged"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author_name = models.CharField(max_length=150)
    author_email = models.EmailField()
    content = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING", db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Comment by {self.author_name} on {self.post.title} [{self.status}]"
