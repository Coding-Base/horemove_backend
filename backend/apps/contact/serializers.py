from common.validators import sanitize_user_html
from rest_framework import serializers

from .models import ContactSubmission


class ContactSubmissionCreateSerializer(serializers.ModelSerializer):
    # Honeypot field: automated bots fill this, humans won't see it
    hp_website = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = ContactSubmission
        fields = ["name", "email", "phone", "subject", "message", "hp_website"]

    def validate_message(self, value):
        sanitized = sanitize_user_html(value)
        if not sanitized.strip():
            raise serializers.ValidationError("Message cannot be empty.")
        return sanitized


class ContactSubmissionAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactSubmission
        fields = "__all__"
