from djmoney import settings as djmoney_settings
from rest_framework import serializers

from .validators import (
    MetadataKeyValidator,
    MetadataLengthValidator,
    MetadataValueValidator,
)


class MetadataField(serializers.JSONField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.validators.extend(
            [
                MetadataLengthValidator(limit_value=20),
                MetadataKeyValidator(limit_value=50),
                MetadataValueValidator(limit_value=300),
            ]
        )


class CurrencyField(serializers.ChoiceField):
    """Serializer field for ISO 4217 currency codes."""

    def __init__(self, **kwargs):
        kwargs.setdefault("choices", djmoney_settings.CURRENCY_CHOICES)
        super().__init__(**kwargs)
