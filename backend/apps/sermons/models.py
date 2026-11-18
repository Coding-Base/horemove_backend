import uuid

from common.models import PublishableModel
from django.db import models


class SermonCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=160, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Sermon Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Speaker(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    title = models.CharField(max_length=255, blank=True)
    bio = models.TextField(blank=True)
    portrait_url = models.URLField(max_length=1000, blank=True)

    def __str__(self):
        return self.name


class Sermon(PublishableModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, db_index=True)
    speaker = models.ForeignKey(Speaker, on_delete=models.SET_NULL, null=True, related_name="sermons")
    category = models.ForeignKey(SermonCategory, on_delete=models.SET_NULL, null=True, related_name="sermons")
    date_preached = models.DateField(db_index=True)
    summary = models.TextField(blank=True)
    scripture_references = models.CharField(max_length=255, blank=True)
    audio_url = models.URLField(max_length=1000, blank=True)
    video_url = models.URLField(max_length=1000, blank=True)
    telegram_download_url = models.URLField(max_length=1000, blank=True)
    thumbnail_url = models.URLField(max_length=1000, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    view_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-date_preached", "-created_at"]

    def __str__(self):
        return f"{self.title} ({self.date_preached})"
