from rest_framework import serializers


class StripeCheckoutSerializer(serializers.Serializer):
    price_id = serializers.CharField()


class StripeCheckoutSessionSerializer(serializers.Serializer):
    url = serializers.CharField()


class StripeBillingPortalSerializer(serializers.Serializer):
    url = serializers.CharField()


class StripeSubscriptionSerializer(serializers.Serializer):
    price_id = serializers.CharField()
    started_at = serializers.DateTimeField()
    ended_at = serializers.DateTimeField(allow_null=True)
    canceled_at = serializers.DateTimeField(allow_null=True)
    status = serializers.CharField()
