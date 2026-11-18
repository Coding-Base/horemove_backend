from common.validators import validate_media_url
from rest_framework import serializers

from .models import Devotional


class DevotionalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Devotional
        fields = "__all__"

    def validate_audio_url(self, value):
        return validate_media_url(value)
