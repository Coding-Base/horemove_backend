from common.validators import validate_media_url
from django.core.validators import URLValidator
from rest_framework import serializers

from .models import Event, HomepageAnnouncement


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = "__all__"

    def validate_stream_url(self, value):
        return validate_media_url(value)


class HomepageAnnouncementSerializer(serializers.ModelSerializer):
    def validate_action_url(self, value):
        if not value or (value.startswith("/") and not value.startswith("//")):
            return value
        URLValidator(schemes=["http", "https"])(value)
        return value

    class Meta:
        model = HomepageAnnouncement
        fields = [
            "enabled",
            "eyebrow",
            "title",
            "message",
            "image_url",
            "action_label",
            "action_url",
            "updated_at",
        ]

    def validate(self, attrs):
        enabled = attrs.get("enabled", getattr(self.instance, "enabled", False))
        title = attrs.get("title", getattr(self.instance, "title", ""))
        message = attrs.get("message", getattr(self.instance, "message", ""))
        if enabled and (not title.strip() or not message.strip()):
            raise serializers.ValidationError(
                "An enabled announcement must have a title and message."
            )
        return attrs
