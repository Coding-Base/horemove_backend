from rest_framework import serializers

from .models import Publication, PublicationCategory


class PublicationCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PublicationCategory
        fields = "__all__"


class PublicationSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Publication
        fields = "__all__"
