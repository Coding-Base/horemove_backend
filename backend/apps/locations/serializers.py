from rest_framework import serializers

from .models import Fellowship, Region


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = "__all__"


class FellowshipSerializer(serializers.ModelSerializer):
    continent = serializers.CharField(source="region.continent", read_only=True)
    country = serializers.CharField(source="region.country", read_only=True)
    state_or_province = serializers.CharField(source="region.state_or_province", read_only=True)

    class Meta:
        model = Fellowship
        fields = "__all__"
