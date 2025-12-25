from rest_framework import serializers


class StripeConnectionSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    connected_account_id = serializers.CharField()
    redirect_url = serializers.URLField(allow_null=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class StripeConnectionUpdateSerializer(serializers.Serializer):
    redirect_url = serializers.URLField(required=False, allow_null=True)
