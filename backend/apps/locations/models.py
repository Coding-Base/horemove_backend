import uuid

from django.db import models


class Region(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    continent = models.CharField(max_length=64, db_index=True)
    country = models.CharField(max_length=100, db_index=True)
    state_or_province = models.CharField(max_length=100, db_index=True)

    class Meta:
        unique_together = ("continent", "country", "state_or_province")
        ordering = ["continent", "country", "state_or_province"]

    def __str__(self):
        return f"{self.country} - {self.state_or_province} ({self.continent})"


class Fellowship(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name="fellowships")
    city_or_lga = models.CharField(max_length=150, db_index=True)
    address = models.TextField()
    meeting_schedule = models.TextField()
    contact_person = models.CharField(max_length=150, blank=True)
    contact_phone = models.CharField(max_length=64, blank=True)
    contact_email = models.EmailField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["region__country", "region__state_or_province", "city_or_lga", "name"]

    def __str__(self):
        return f"{self.name} - {self.city_or_lga}, {self.region.country}"
