from django.apps import apps
from rest_framework import serializers

from .choices import IntegrationType


class IntegrationConnectionField(serializers.PrimaryKeyRelatedField):
    mapper = {
        IntegrationType.STRIPE: "stripe_integrations.StripeConnection",
    }

    def __init__(self, **kwargs):
        self.type_field = kwargs.pop("type_field", None)
        kwargs.setdefault("pk_field", serializers.UUIDField())
        super().__init__(**kwargs)

    def _get_type(self) -> IntegrationType | None:
        if self.parent is None:
            return None

        data = getattr(self.parent, "initial_data", None) or {}
        if self.type_field in data and data[self.type_field] not in (None, ""):
            return data[self.type_field]

        instance = getattr(self.parent, "instance", None)
        if instance is not None:
            return getattr(instance, self.type_field, None)

        return None

    def get_queryset(self):
        integration_type = self._get_type()
        if integration_type is None:
            self.fail("missing_type")

        model_label = self.mapper.get(integration_type)
        if not model_label:
            self.fail("unsupported_type")

        account = self.context["request"].account

        connection_cls = apps.get_model(model_label)
        return connection_cls.objects.filter(account_id=account.id)
