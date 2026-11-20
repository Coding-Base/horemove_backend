import uuid

from django.db import models


class MinistryProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, default="Holiness Revival Movement Worldwide")
    acronym = models.CharField(max_length=32, default="HOREMOW")
    motto = models.CharField(max_length=500, default="Holiness without which no man shall see the Lord")
    vision_statement = models.TextField(blank=True)
    mission_statement = models.TextField(blank=True)
    history = models.TextField(blank=True)
    headquarters_address = models.TextField(blank=True)
    primary_phone = models.CharField(max_length=64, blank=True)
    primary_email = models.EmailField(blank=True)
    social_links = models.JSONField(default=dict, blank=True)
    email_settings = models.JSONField(default=dict, blank=True)
    seo_settings = models.JSONField(default=dict, blank=True)
    styling_settings = models.JSONField(default=dict, blank=True)
    gathering_times = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Ministry Profile"
        verbose_name_plural = "Ministry Profiles"

    def __str__(self):
        return self.name


class Leader(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=255)  # e.g., "International Director"
    biography = models.TextField()
    portrait_url = models.URLField(max_length=1000, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return f"{self.title} - {self.name}"


class Doctrine(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    biblical_reference = models.CharField(max_length=500)
    summary = models.TextField()
    full_text = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "title"]

    def __str__(self):
        return self.title


class HomepageSection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    section_key = models.SlugField(max_length=64, unique=True)
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=500, blank=True)
    content_payload = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "section_key"]

    def __str__(self):
        return f"{self.section_key} ({'Active' if self.is_active else 'Disabled'})"
