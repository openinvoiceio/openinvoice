from rest_framework import serializers


class StripeConnectionSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    code = serializers.CharField()
    redirect_url = serializers.URLField(allow_null=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class StripeConnectionCreateSerializer(serializers.Serializer):
    name = serializers.CharField()
    code = serializers.CharField()
    api_key = serializers.CharField()
    redirect_url = serializers.URLField(required=False, allow_null=True)


class StripeConnectionUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(required=False)
    redirect_url = serializers.URLField(required=False, allow_null=True)
