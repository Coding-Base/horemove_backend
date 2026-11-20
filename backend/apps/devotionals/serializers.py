from django.utils.text import slugify
from rest_framework import serializers

from common.validators import validate_media_url

from .models import AutoPublishSettings, Devotional, DevotionalBatch, DevotionalParsedEntry


class DevotionalParsedEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = DevotionalParsedEntry
        fields = "__all__"


class DevotionalBatchSerializer(serializers.ModelSerializer):
    entries_count = serializers.IntegerField(source="entries.count", read_only=True)
    uploaded_by_email = serializers.EmailField(source="uploaded_by.email", read_only=True)

    class Meta:
        model = DevotionalBatch
        fields = "__all__"


class DevotionalBatchDetailSerializer(DevotionalBatchSerializer):
    entries = DevotionalParsedEntrySerializer(many=True, read_only=True)

    class Meta(DevotionalBatchSerializer.Meta):
        fields = "__all__"


class DevotionalCalendarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Devotional
        fields = ["id", "date", "title", "slug", "status", "card_template", "card_bg_color", "card_accent_color"]


class DevotionalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Devotional
        fields = "__all__"
        extra_kwargs = {
            "slug": {"required": False},
        }

    def validate_audio_url(self, value):
        return validate_media_url(value)

    def validate_image_url(self, value):
        return validate_media_url(value)

    def create(self, validated_data):
        if not validated_data.get("slug"):
            base_slug = slugify(validated_data.get("title", "devotional"))
            date_str = str(validated_data.get("date", ""))
            validated_data["slug"] = f"{date_str}-{base_slug}"[:280]
        # Mirror memory verse / scripture fields if not explicitly provided
        if not validated_data.get("scripture_reading") and validated_data.get("text_reference"):
            validated_data["scripture_reading"] = validated_data["text_reference"]
        if not validated_data.get("memory_verse_reference") and validated_data.get("key_verse_reference"):
            validated_data["memory_verse_reference"] = validated_data["key_verse_reference"]
        if not validated_data.get("memory_verse_text") and validated_data.get("key_verse_text"):
            validated_data["memory_verse_text"] = validated_data["key_verse_text"]

        return super().create(validated_data)

    def update(self, instance, validated_data):
        if "title" in validated_data and not validated_data.get("slug"):
            base_slug = slugify(validated_data.get("title", instance.title))
            date_str = str(validated_data.get("date", instance.date))
            validated_data["slug"] = f"{date_str}-{base_slug}"[:280]
        return super().update(instance, validated_data)


class AutoPublishSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutoPublishSettings
        fields = "__all__"


class DevotionalUploadSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)
    author_attribution = serializers.CharField(max_length=255, required=False, default="Pastor Paul Rika")
    default_template = serializers.CharField(max_length=50, required=False, default="classic")
    target_year = serializers.IntegerField(required=False, default=2026)
    start_page = serializers.IntegerField(required=False, default=1)
    end_page = serializers.IntegerField(required=False, default=184)

    def validate_file(self, value):
        name = value.name.lower()
        if not name.endswith(".pdf"):
            raise serializers.ValidationError("Only PDF (.pdf) files are supported for bulk devotional ingestion.")
        # Support up to 500MB for publication and scanned book PDFs
        if value.size > 500 * 1024 * 1024:
            raise serializers.ValidationError("File size cannot exceed 500MB.")
        return value
