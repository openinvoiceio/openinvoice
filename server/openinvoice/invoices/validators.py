from django.conf import settings
from rest_framework import serializers

from common.access import has_feature
from common.choices import FeatureCode

from .choices import InvoiceDeliveryMethod


class AutomaticDeliveryMethodValidator:
    message = "Automatic delivery is forbidden for your account."
    requires_context = True

    def __call__(self, value, serializer):
        account = serializer.context["request"].account

        if value == InvoiceDeliveryMethod.AUTOMATIC and not has_feature(
            account, FeatureCode.AUTOMATIC_INVOICE_DELIVERY
        ):
            raise serializers.ValidationError(self.message)

        return value


class MaxTaxRatesValidator:
    message = "Ensure this list contains at most {maximum} items."

    def __call__(self, value):
        if len(value) >= settings.MAX_INVOICE_TAX_RATES:
            raise serializers.ValidationError(self.message.format(maximum=settings.MAX_INVOICE_TAX_RATES))
        return value


class MaxCouponsValidator:
    message = "Ensure this list contains at most {maximum} items."

    def __call__(self, value):
        if len(value) >= settings.MAX_INVOICE_COUPONS:
            raise serializers.ValidationError(self.message.format(maximum=settings.MAX_INVOICE_COUPONS))
        return value


def validate_coupons_currency(coupons, currency):
    errors = {}
    for idx, coupon in enumerate(coupons):
        if coupon.currency != currency:
            errors[idx] = "Invalid coupon currency for this invoice."

    if errors:
        raise serializers.ValidationError({"coupons": errors})


class CouponsCurrencyValidator:
    message = "Invalid coupon currency for this invoice."
    requires_context = True

    def __call__(self, attrs, serializer):
        coupons = attrs.get("coupons") or []
        if not coupons:
            return attrs

        currency = self.resolve_currency(attrs, serializer)

        errors = {}
        for idx, coupon in enumerate(coupons):
            if coupon.currency != currency:
                errors[idx] = self.message

        if errors:
            raise serializers.ValidationError({"coupons": errors})

        return attrs

    def resolve_currency(self, attrs, serializer):
        # Update case
        if serializer.instance:
            return attrs.get("currency", serializer.instance.currency)

        customer = attrs["customer"]
        return attrs.get("currency") or customer.currency or customer.account.default_currency
