import datetime
import uuid

from django.conf import settings
from django.db import models

from common.models import PublishableModel


class DevotionalBatch(models.Model):
    STATUS_CHOICES = [
        ("UPLOADING", "Uploading"),
        ("PARSING", "Parsing"),
        ("REVIEW", "Awaiting Review"),
        ("CONFIRMED", "Confirmed"),
        ("FAILED", "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file_name = models.CharField(max_length=500)
    file = models.FileField(upload_to="devotionals/batches/", null=True, blank=True)
    file_url = models.URLField(max_length=1000, blank=True)
    date_range_start = models.DateField(null=True, blank=True)
    date_range_end = models.DateField(null=True, blank=True)
    total_entries = models.IntegerField(default=0)
    parsed_entries = models.IntegerField(default=0)
    total_pages = models.IntegerField(default=0)
    processed_pages = models.IntegerField(default=0)
    target_year = models.IntegerField(default=2026)
    start_page = models.IntegerField(default=1)
    end_page = models.IntegerField(default=184)
    is_scanned_ocr = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="UPLOADING")
    error_log = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="devotional_batches",
    )

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.file_name} ({self.status})"


class DevotionalParsedEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(DevotionalBatch, on_delete=models.CASCADE, related_name="entries")
    date = models.DateField()
    title = models.CharField(max_length=255)
    text_reference = models.CharField(max_length=255, blank=True)
    text_body = models.TextField(blank=True)
    key_verse_reference = models.CharField(max_length=255, blank=True)
    key_verse_text = models.TextField(blank=True)
    reflection_body = models.TextField(blank=True)
    thought_for_day = models.TextField(blank=True)
    song_for_day = models.TextField(blank=True)
    bible_reading_for_day = models.CharField(max_length=255, blank=True)
    author_attribution = models.CharField(max_length=255, default="Pastor Paul Rika")
    prayer_points = models.JSONField(default=list, blank=True)
    action_point = models.TextField(blank=True)
    has_parsing_issues = models.BooleanField(default=False)
    parsing_notes = models.TextField(blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["date", "order"]
        unique_together = ["batch", "date"]

    def __str__(self):
        return f"{self.date} - {self.title}"


class Devotional(PublishableModel):
    date = models.DateField(unique=True, db_index=True)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, db_index=True)
    scripture_reading = models.CharField(max_length=255, blank=True)
    memory_verse_text = models.TextField(blank=True)
    memory_verse_reference = models.CharField(max_length=255, blank=True)
    reflection_body = models.TextField()
    prayer_points = models.JSONField(default=list, blank=True)
    action_point = models.TextField(blank=True)
    author_attribution = models.CharField(max_length=255, default="Pastor Paul Rika")
    image_url = models.URLField(max_length=1000, blank=True)
    is_audio_available = models.BooleanField(default=False)
    audio_url = models.URLField(max_length=1000, blank=True)

    # Expanded fields for complete daily devotional structure
    text_reference = models.CharField(max_length=255, blank=True)
    text_body = models.TextField(blank=True)
    key_verse_reference = models.CharField(max_length=255, blank=True)
    key_verse_text = models.TextField(blank=True)
    thought_for_day = models.TextField(blank=True)
    song_for_day = models.TextField(blank=True)
    bible_reading_for_day = models.CharField(max_length=255, blank=True)

    # Card customisation and templates
    card_template = models.CharField(max_length=50, default="classic")
    card_bg_color = models.CharField(max_length=30, blank=True)
    card_accent_color = models.CharField(max_length=30, blank=True)
    card_bg_image = models.URLField(max_length=1000, blank=True)

    batch = models.ForeignKey(
        DevotionalBatch,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="devotionals",
    )

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.date} - {self.title}"


class AutoPublishSettings(models.Model):
    publish_time = models.TimeField(default=datetime.time(5, 0))
    timezone_name = models.CharField(max_length=50, default="Africa/Lagos")
    is_enabled = models.BooleanField(default=True)
    default_template = models.CharField(max_length=50, default="classic")
    default_author = models.CharField(max_length=255, default="Pastor Paul Rika")
    gemini_api_key = models.CharField(max_length=255, blank=True)
    ocr_model = models.CharField(max_length=100, default="gemini-3.1-flash-lite-preview")
    ocr_api_key = models.CharField(max_length=500, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="devotional_settings_updated",
    )

    class Meta:
        verbose_name = "Auto-publish setting"
        verbose_name_plural = "Auto-publish settings"

    def __str__(self):
        return f"Auto-publish at {self.publish_time} ({self.timezone_name})"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
