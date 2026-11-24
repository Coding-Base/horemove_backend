import uuid

from common.models import PublishableModel
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


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
    slug = models.SlugField(max_length=280, unique=True, db_index=True, blank=True)
    author = models.CharField(max_length=255, default="Pastor Paul Rika")
    category = models.ForeignKey(
        PublicationCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="publications",
    )
    description = models.TextField(blank=True)
    isbn = models.CharField(max_length=32, blank=True)
    language = models.CharField(max_length=64, default="English")
    format = models.CharField(max_length=150, blank=True, default="PDF & Paperback")
    price = models.CharField(max_length=150, blank=True, default="Free Download / Ministry Gift")
    cover_image_url = models.URLField(max_length=1000, blank=True)
    preview_pdf_url = models.URLField(max_length=1000, blank=True)
    purchase_enquiry_url = models.URLField(max_length=1000, blank=True)
    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or "publication"
            slug = base_slug
            counter = 1
            while Publication.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        if not self.status or self.status == "DRAFT":
            self.status = "PUBLISHED"
        if self.status == "PUBLISHED" and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)
