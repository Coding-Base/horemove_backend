import uuid

from django.utils import timezone
from django.utils.text import slugify
from rest_framework import serializers

from .models import Publication, PublicationCategory


class PublicationCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PublicationCategory
        fields = "__all__"


class PublicationSerializer(serializers.ModelSerializer):
    category = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    slug = serializers.SlugField(required=False, allow_blank=True)
    coverUrl = serializers.CharField(source="cover_image_url", required=False, allow_blank=True)
    fileUrl = serializers.CharField(source="preview_pdf_url", required=False, allow_blank=True)
    telegramUrl = serializers.CharField(source="purchase_enquiry_url", required=False, allow_blank=True)

    class Meta:
        model = Publication
        fields = [
            "id",
            "title",
            "slug",
            "author",
            "category",
            "category_name",
            "description",
            "isbn",
            "language",
            "format",
            "price",
            "cover_image_url",
            "preview_pdf_url",
            "purchase_enquiry_url",
            "coverUrl",
            "fileUrl",
            "telegramUrl",
            "is_available",
            "is_featured",
            "status",
            "published_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Ensure category is returned as the readable string name for frontend compatibility
        if instance.category:
            ret["category"] = instance.category.name
        elif not ret.get("category"):
            ret["category"] = "Holiness & Christian Living"
        ret["coverUrl"] = instance.cover_image_url or ""
        ret["fileUrl"] = instance.preview_pdf_url or ""
        ret["telegramUrl"] = instance.purchase_enquiry_url or ""
        return ret

    def _resolve_category(self, cat_val):
        if not cat_val:
            return None
        # Check if UUID
        try:
            val_uuid = uuid.UUID(str(cat_val))
            cat = PublicationCategory.objects.filter(id=val_uuid).first()
            if cat:
                return cat
        except (ValueError, AttributeError):
            pass
        # Resolve by name or slug
        cat_name = str(cat_val).strip()
        cat = PublicationCategory.objects.filter(name__iexact=cat_name).first()
        if not cat:
            cat_slug = slugify(cat_name) or "general"
            cat, _ = PublicationCategory.objects.get_or_create(
                name=cat_name,
                defaults={"slug": cat_slug}
            )
        return cat

    def create(self, validated_data):
        cat_val = validated_data.pop("category", None)
        if cat_val:
            validated_data["category"] = self._resolve_category(cat_val)

        if not validated_data.get("status"):
            validated_data["status"] = "PUBLISHED"
        if validated_data["status"] == "PUBLISHED" and not validated_data.get("published_at"):
            validated_data["published_at"] = timezone.now()

        # If user is authenticated, attach created_by
        request = self.context.get("request")
        if request and request.user and request.user.is_authenticated:
            validated_data["created_by"] = request.user
            validated_data["updated_by"] = request.user

        return super().create(validated_data)

    def update(self, instance, validated_data):
        if "category" in validated_data:
            cat_val = validated_data.pop("category")
            instance.category = self._resolve_category(cat_val)

        request = self.context.get("request")
        if request and request.user and request.user.is_authenticated:
            validated_data["updated_by"] = request.user

        return super().update(instance, validated_data)
