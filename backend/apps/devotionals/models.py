from common.models import PublishableModel
from django.db import models


class Devotional(PublishableModel):
    date = models.DateField(unique=True, db_index=True)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, db_index=True)
    scripture_reading = models.CharField(max_length=255)
    memory_verse_text = models.TextField()
    memory_verse_reference = models.CharField(max_length=255)
    reflection_body = models.TextField()
    prayer_points = models.JSONField(default=list, blank=True)
    action_point = models.TextField(blank=True)
    author_attribution = models.CharField(max_length=255, default="Pastor Paul Rika")
    image_url = models.URLField(max_length=1000, blank=True)
    is_audio_available = models.BooleanField(default=False)
    audio_url = models.URLField(max_length=1000, blank=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.date} - {self.title}"
