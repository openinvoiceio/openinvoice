from django_countries.serializer_fields import CountryField
from rest_framework import serializers

from .choices import TaxRateStatus
from .models import TaxRate


class TaxRateSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    account_id = serializers.UUIDField()
    name = serializers.CharField()
    description = serializers.CharField(allow_null=True)
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    country = CountryField(allow_null=True)
    status = serializers.ChoiceField(choices=TaxRateStatus.choices)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    archived_at = serializers.DateTimeField(allow_null=True)

    def to_representation(self, instance: TaxRate) -> dict:
        representation = super().to_representation(instance)
        representation["country"] = str(instance.country) if instance.country else None
        return representation


class TaxRateCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(allow_null=True, required=False)
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    country = CountryField(allow_null=True, required=False)


class TaxRateUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(allow_null=True, required=False)
    country = CountryField(allow_null=True, required=False)
