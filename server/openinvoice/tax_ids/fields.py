from rest_framework import serializers

from openinvoice.core.fields import UniqueManyRelatedField

from .models import TaxId


class TaxIdRelatedField(serializers.PrimaryKeyRelatedField):
    def __init__(self, **kwargs):
        kwargs.setdefault("pk_field", serializers.UUIDField())
        super().__init__(**kwargs)

    def get_queryset(self):
        account = self.context["request"].account
        return TaxId.objects.for_account(account)

    @classmethod
    def many_init(cls, *args, **kwargs):
        kwargs["child_relation"] = cls()
        return UniqueManyRelatedField(*args, **kwargs)


class CustomerTaxIdRelatedField(serializers.PrimaryKeyRelatedField):
    def __init__(self, **kwargs):
        kwargs.setdefault("pk_field", serializers.UUIDField())
        super().__init__(**kwargs)

    def get_queryset(self):
        account = self.context["request"].account
        customer = self.context["customer"]
        if customer is None:
            return TaxId.objects.none()
        return TaxId.objects.for_customer(customer).filter(customers__account=account)

    @classmethod
    def many_init(cls, *args, **kwargs):
        kwargs["child_relation"] = cls()
        return UniqueManyRelatedField(*args, **kwargs)
