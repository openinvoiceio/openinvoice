from itertools import pairwise

from rest_framework import serializers


class PriceIsActive:
    message = "Given price is archived"

    def __call__(self, value):
        if not value.is_active:
            raise serializers.ValidationError(self.message)

        return value


class PriceProductIsActive:
    message = "Given price product is archived"

    def __call__(self, value):
        if not value.product.is_active:
            raise serializers.ValidationError(self.message)

        return value


class PriceTiersContinuousValidator:
    message = "Tiers must be continuous without gaps"

    def __call__(self, value):
        ranges = sorted((t["from_value"], t["to_value"]) for t in value)

        # they must be exactly continuous: [a,b], [b+1,c], ...
        if any(prev_end + 1 != next_start for (_, prev_end), (next_start, _) in pairwise(ranges)):
            raise serializers.ValidationError(self.message)

        return value
