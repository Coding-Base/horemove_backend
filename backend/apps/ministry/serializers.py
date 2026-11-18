from rest_framework import serializers

from .models import Doctrine, HomepageSection, Leader, MinistryProfile


class MinistryProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MinistryProfile
        fields = "__all__"


class LeaderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leader
        fields = "__all__"


class DoctrineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctrine
        fields = "__all__"


class HomepageSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomepageSection
        fields = "__all__"
