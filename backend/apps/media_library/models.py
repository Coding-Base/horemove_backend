import uuid

from django.conf import settings
from django.db import models


class MediaAsset(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    public_id = models.CharField(max_length=255, unique=True, db_index=True)
    secure_url = models.URLField(max_length=1000)
    resource_type = models.CharField(max_length=32, default="image")
    format = models.CharField(max_length=16, blank=True)
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    bytes = models.PositiveIntegerField(null=True, blank=True)
    title = models.CharField(max_length=255, blank=True)
    alt_text = models.CharField(max_length=255, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_media",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title or self.public_id} ({self.resource_type})"
