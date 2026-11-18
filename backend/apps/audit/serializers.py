from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = [
            "id",
            "timestamp",
            "actor_email",
            "ip_address",
            "action",
            "resource_type",
            "resource_id",
            "details",
            "request_id",
        ]
        read_only_fields = fields
