from rest_framework import serializers

from openinvoice.core.fields import UniqueManyRelatedField

from .models import TaxId


class TaxIdRelatedField(serializers.PrimaryKeyRelatedField):
    def __init__(self, **kwargs):
        kwargs.setdefault("pk_field", serializers.UUIDField())
        super().__init__(**kwargs)

    def get_queryset(self):
        account = self.context["request"].account
        return TaxId.objects.filter(accounts=account)

    @classmethod
    def many_init(cls, *args, **kwargs):
        kwargs["child_relation"] = cls()
        return UniqueManyRelatedField(*args, **kwargs)
