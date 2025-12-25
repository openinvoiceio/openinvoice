from rest_framework import serializers

from .enums import IntegrationType


class IntegrationConnectionSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    type = serializers.ChoiceField(choices=IntegrationType.choices)
    created_at = serializers.DateTimeField(read_only=True)
