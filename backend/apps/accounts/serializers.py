from datetime import timedelta

from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "capabilities",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class UserAdminCreateUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, min_length=10)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "capabilities",
            "is_active",
            "password",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User.objects.create_user(password=password, **validated_data)
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email", "").lower()
        password = attrs.get("password")

        user = User.objects.filter(email=email).first()
        if not user:
            raise serializers.ValidationError("Invalid email or password.")

        if user.is_locked:
            raise serializers.ValidationError(
                "Account is temporarily locked due to multiple failed login attempts. Please try again later."
            )

        if not user.is_active:
            raise serializers.ValidationError("Account is deactivated.")

        authenticated_user = authenticate(username=email, password=password)
        if not authenticated_user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 3:
                user.locked_until = timezone.now() + timedelta(minutes=15)
            user.save(update_fields=["failed_login_attempts", "locked_until"])
            raise serializers.ValidationError("Invalid email or password.")

        # Reset failed attempts upon successful login
        if user.failed_login_attempts > 0 or user.locked_until:
            user.failed_login_attempts = 0
            user.locked_until = None
            user.save(update_fields=["failed_login_attempts", "locked_until"])

        attrs["user"] = authenticated_user
        return attrs
