from decimal import Decimal

from rest_framework import serializers

from .models import DonationProject, DonationTransaction


class DonationProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = DonationProject
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "target_amount",
            "currency",
            "is_active",
            "order",
        ]


class DonationCheckoutSerializer(serializers.Serializer):
    project_id = serializers.UUIDField(required=False, allow_null=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("1.00"))
    currency = serializers.ChoiceField(choices=["NGN", "USD", "GBP", "EUR"], default="NGN")
    donor_name = serializers.CharField(max_length=255)
    donor_email = serializers.EmailField()
    donor_phone = serializers.CharField(max_length=64, required=False, allow_blank=True)
    is_anonymous = serializers.BooleanField(default=False)
    provider = serializers.ChoiceField(choices=["PAYSTACK", "PAYPAL"])

    def validate_donor_email(self, value):
        email = value.strip().lower()
        if not email:
            raise serializers.ValidationError("A valid email address is required to receive your donation receipt.")
        return email


class DonationTransactionAdminSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True)

    class Meta:
        model = DonationTransaction
        fields = [
            "id",
            "project",
            "project_name",
            "amount",
            "currency",
            "donor_name",
            "donor_email",
            "donor_phone",
            "is_anonymous",
            "provider",
            "provider_reference",
            "idempotency_key",
            "status",
            "appreciation_email_sent",
            "created_at",
            "completed_at",
        ]
        read_only_fields = fields
