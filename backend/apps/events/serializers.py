from common.validators import validate_media_url
from rest_framework import serializers

from .models import Event


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = "__all__"

    def validate_stream_url(self, value):
        return validate_media_url(value)
