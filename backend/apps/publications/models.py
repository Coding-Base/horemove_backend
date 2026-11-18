import uuid

from common.models import PublishableModel
from django.db import models


class PublicationCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=160, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Publication Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Publication(PublishableModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, db_index=True)
    author = models.CharField(max_length=255, default="Pastor Paul Rika")
    category = models.ForeignKey(
        PublicationCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name="publications",
    )
    description = models.TextField()
    isbn = models.CharField(max_length=32, blank=True)
    language = models.CharField(max_length=64, default="English")
    cover_image_url = models.URLField(max_length=1000, blank=True)
    preview_pdf_url = models.URLField(max_length=1000, blank=True)
    purchase_enquiry_url = models.URLField(max_length=1000, blank=True)
    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
