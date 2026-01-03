from rest_framework import serializers


class IntegrationSerializer(serializers.Serializer):
    name = serializers.CharField()
    slug = serializers.CharField()
    description = serializers.CharField()
    is_enabled = serializers.BooleanField()
