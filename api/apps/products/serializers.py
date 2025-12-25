from djmoney.contrib.django_rest_framework import MoneyField
from rest_framework import serializers

from apps.files.fields import FileRelatedField
from apps.prices.enums import PriceModel
from apps.prices.fields import PriceRelatedField
from apps.prices.serializers import PriceTierSerializer
from common.fields import CurrencyField, MetadataField


class DefaultPriceSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    currency = CurrencyField()
    amount = MoneyField(max_digits=19, decimal_places=2)
    metadata = MetadataField()
    code = serializers.CharField(allow_null=True, max_length=255)
    model = serializers.ChoiceField(choices=PriceModel.choices)
    tiers = PriceTierSerializer(many=True)


class ProductSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    account_id = serializers.UUIDField()
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(allow_null=True, max_length=600)
    is_active = serializers.BooleanField()
    url = serializers.URLField(allow_null=True)
    image_url = serializers.FileField(use_url=True, source="image.data", allow_null=True)
    image_id = serializers.UUIDField(allow_null=True)
    default_price = DefaultPriceSerializer(allow_null=True)
    prices_count = serializers.IntegerField(read_only=True)
    metadata = MetadataField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField(allow_null=True)


class DefaultPriceCreateSerializer(serializers.Serializer):
    currency = CurrencyField()
    amount = MoneyField(max_digits=19, decimal_places=2)
    metadata = MetadataField(allow_null=True)
    code = serializers.CharField(max_length=255, allow_null=True)

    def validate_amount(self, value):
        if value < 0:
            raise serializers.ValidationError("Amount must be greater than 0")

        return value


class ProductCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(max_length=600, allow_null=True, required=False)
    url = serializers.URLField(max_length=255, allow_null=True, required=False)
    default_price = DefaultPriceCreateSerializer(allow_null=True, required=False)
    image_id = FileRelatedField(source="image", allow_null=True, required=False)
    metadata = MetadataField(allow_null=True, required=False)


class ProductUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(max_length=600, allow_null=True, required=False)
    url = serializers.URLField(allow_null=True, required=False)
    image_id = FileRelatedField(source="image", allow_null=True, required=False)
    default_price_id = PriceRelatedField(source="default_price", allow_null=True, required=False)
    metadata = MetadataField(required=False)

    def validate_default_price_id(self, value):
        if value is None:
            return value

        if value.product_id != self.instance.id:
            raise serializers.ValidationError("Default price not found")

        return value
