from rest_framework import serializers

from .enums import FeatureCode, LimitCode


class PlanFeatureSerializer(serializers.Serializer):
    code = serializers.ChoiceField(choices=FeatureCode.choices)
    is_enabled = serializers.BooleanField()


class PlanLimitSerializer(serializers.Serializer):
    code = serializers.ChoiceField(choices=LimitCode.choices)
    limit = serializers.IntegerField()


class PlanSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    code = serializers.CharField(max_length=100)
    features = PlanFeatureSerializer(many=True)
    limits = PlanLimitSerializer(many=True)


class ConfigSerializer(serializers.Serializer):
    is_billing_enabled = serializers.BooleanField()
    plans = PlanSerializer(many=True)
