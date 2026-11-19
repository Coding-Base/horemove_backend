from django.db import models


class PageViewEvent(models.Model):
    DEVICE_CHOICES = (
        ("mobile", "Mobile"),
        ("desktop", "Desktop"),
        ("tablet", "Tablet"),
    )

    session_id = models.CharField(max_length=64, db_index=True)
    path = models.CharField(max_length=255, db_index=True)
    title = models.CharField(max_length=255, blank=True)
    country_code = models.CharField(max_length=2, default="XX", db_index=True)
    country_name = models.CharField(max_length=64, default="Unknown")
    device_type = models.CharField(max_length=20, choices=DEVICE_CHOICES, default="desktop")
    duration_seconds = models.PositiveIntegerField(default=0)
    is_bounce = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Page View Event"
        verbose_name_plural = "Page View Events"
        indexes = [
            models.Index(fields=["created_at", "session_id"]),
            models.Index(fields=["created_at", "path"]),
        ]

    def __str__(self):
        return f"{self.path} ({self.country_code}) - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class DailyAnalyticsSummary(models.Model):
    """
    Summary table for long-term historical aggregation and fast dashboard queries.
    """
    date = models.DateField(unique=True, db_index=True)
    total_pageviews = models.PositiveIntegerField(default=0)
    unique_visitors = models.PositiveIntegerField(default=0)
    avg_session_seconds = models.PositiveIntegerField(default=0)
    bounce_rate = models.FloatField(default=0.0)
    top_pages_json = models.JSONField(default=list)
    countries_json = models.JSONField(default=list)
    devices_json = models.JSONField(default=list)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date"]
        verbose_name = "Daily Analytics Summary"
        verbose_name_plural = "Daily Analytics Summaries"

    def __str__(self):
        return f"Summary {self.date}: {self.total_pageviews} views, {self.unique_visitors} visitors"
