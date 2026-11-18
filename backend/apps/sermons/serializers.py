from common.validators import validate_media_url
from rest_framework import serializers

from .models import Sermon, SermonCategory, Speaker


class SermonCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SermonCategory
        fields = "__all__"


class SpeakerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Speaker
        fields = "__all__"


class SermonSerializer(serializers.ModelSerializer):
    speaker_name = serializers.CharField(source="speaker.name", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Sermon
        fields = "__all__"

    def validate_audio_url(self, value):
        return validate_media_url(value)

    def validate_video_url(self, value):
        return validate_media_url(value)

    def validate_telegram_download_url(self, value):
        return validate_media_url(value)
