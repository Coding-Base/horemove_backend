from common.models import PublishableModel
from django.db import models


class Event(PublishableModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, db_index=True)
    theme = models.CharField(max_length=255, blank=True)
    description = models.TextField()
    start_datetime = models.DateTimeField(db_index=True)
    end_datetime = models.DateTimeField(db_index=True)
    timezone_name = models.CharField(max_length=64, default="Africa/Lagos")
    is_online = models.BooleanField(default=False)
    is_in_person = models.BooleanField(default=True)
    stream_url = models.URLField(max_length=1000, blank=True)
    venue_name = models.CharField(max_length=255, blank=True)
    venue_address = models.TextField(blank=True)
    venue_coordinates = models.JSONField(default=dict, blank=True)
    registration_url = models.URLField(max_length=1000, blank=True)
    banner_image_url = models.URLField(max_length=1000, blank=True)
    is_featured = models.BooleanField(default=False)

    class Meta:
        ordering = ["start_datetime"]

    def __str__(self):
        return f"{self.title} ({self.start_datetime.strftime('%Y-%m-%d')})"


class HomepageAnnouncement(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    enabled = models.BooleanField(default=False)
    eyebrow = models.CharField(max_length=100, default="Latest update")
    title = models.CharField(max_length=255, blank=True)
    message = models.TextField(blank=True)
    image_url = models.URLField(max_length=1000, blank=True)
    action_label = models.CharField(max_length=100, blank=True)
    action_url = models.CharField(max_length=1000, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Homepage announcement"
