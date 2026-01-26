from djmoney.contrib.django_rest_framework.fields import MoneyField
from rest_framework import serializers

from common.fields import CurrencyField, MetadataField
from openinvoice.products.choices import ProductStatus
from openinvoice.products.fields import ProductRelatedField

from .choices import PriceModel, PriceStatus
from .validators import PriceTiersContinuousValidator


class PriceTierSerializer(serializers.Serializer):
    unit_amount = MoneyField(max_digits=19, decimal_places=2)
    from_value = serializers.IntegerField()
    to_value = serializers.IntegerField(allow_null=True)


class PriceTierInputSerializer(serializers.Serializer):
    unit_amount = MoneyField(max_digits=19, decimal_places=2)
    from_value = serializers.IntegerField(min_value=0)
    to_value = serializers.IntegerField(min_value=1, allow_null=True)

    def validate(self, attrs):
        to_value = attrs["to_value"]
        if to_value is not None and to_value < attrs["from_value"]:
            raise serializers.ValidationError({"to_value": "Upper bound must be greater than or equal to lower bound."})
        return attrs


class PriceProductSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(allow_blank=True, max_length=1000)
    status = serializers.ChoiceField(choices=ProductStatus.choices)
    default_price_id = serializers.UUIDField(allow_null=True)
    metadata = MetadataField(allow_null=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField(allow_null=True)
    archived_at = serializers.DateTimeField(allow_null=True)


class PriceSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    account_id = serializers.UUIDField()
    product = PriceProductSerializer()
    currency = CurrencyField()
    amount = MoneyField(max_digits=19, decimal_places=2, required=False)
    model = serializers.ChoiceField(choices=PriceModel.choices)
    status = serializers.ChoiceField(choices=PriceStatus.choices)
    metadata = MetadataField()
    code = serializers.CharField(allow_null=True, max_length=255)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField(allow_null=True)
    archived_at = serializers.DateTimeField(allow_null=True)
    tiers = PriceTierSerializer(many=True)


class PriceCreateSerializer(serializers.Serializer):
    product_id = ProductRelatedField(source="product")
    currency = CurrencyField()
    amount = MoneyField(max_digits=19, decimal_places=2, required=False)
    metadata = MetadataField(allow_null=True, required=False)
    code = serializers.CharField(allow_null=True, max_length=255, required=False)
    model = serializers.ChoiceField(choices=PriceModel.choices, default=PriceModel.FLAT)
    tiers = PriceTierInputSerializer(many=True, required=False)

    def validate(self, attrs):
        model = attrs["model"]
        if model == PriceModel.FLAT:
            attrs["tiers"] = []

        return attrs

    def validate_tiers(self, value):
        PriceTiersContinuousValidator()(value)
        return value


class PriceUpdateSerializer(serializers.Serializer):
    currency = CurrencyField(required=False)
    amount = MoneyField(max_digits=19, decimal_places=2, required=False)
    metadata = MetadataField(allow_null=True, required=False)
    code = serializers.CharField(allow_null=True, max_length=255, required=False)
    tiers = PriceTierInputSerializer(many=True, required=False)

    def validate(self, attrs):
        if self.instance and self.instance.model == PriceModel.FLAT:
            attrs["tiers"] = []

        return attrs

    def validate_tiers(self, value):
        PriceTiersContinuousValidator()(value)
        return value
