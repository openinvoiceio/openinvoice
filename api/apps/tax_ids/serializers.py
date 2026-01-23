from django_countries.serializer_fields import CountryField
from rest_framework import serializers

from .choices import TaxIdType
from .models import TaxId


class TaxIdSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    type = serializers.ChoiceField(choices=TaxIdType.choices)
    number = serializers.CharField()
    country = CountryField(allow_null=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

    def to_representation(self, instance: TaxId) -> dict:
        representation = super().to_representation(instance)
        representation["country"] = str(instance.country) if instance.country else None
        return representation


class TaxIdCreateSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=TaxIdType.choices)
    number = serializers.CharField(max_length=255)
    country = CountryField(allow_null=True, required=False)
