from django_countries.serializer_fields import CountryField
from rest_framework import serializers

from apps.addresses.models import Address


class AddressSerializer(serializers.Serializer):
    line1 = serializers.CharField(allow_null=True, required=False, max_length=255)
    line2 = serializers.CharField(allow_null=True, required=False, max_length=255)
    locality = serializers.CharField(allow_null=True, required=False, max_length=255)
    state = serializers.CharField(allow_null=True, required=False, max_length=255)
    postal_code = serializers.CharField(allow_null=True, required=False, max_length=255)
    country = CountryField(allow_null=True, required=False)

    def to_representation(self, instance: Address) -> dict:
        representation = super().to_representation(instance)
        representation["country"] = str(instance.country) if instance.country else None
        return representation
