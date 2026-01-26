from rest_framework import serializers

from .models import NumberingSystem


class NumberingSystemRelatedField(serializers.PrimaryKeyRelatedField):
    def __init__(self, **kwargs):
        self.applies_to = kwargs.pop("applies_to")
        kwargs.setdefault("pk_field", serializers.UUIDField())
        super().__init__(**kwargs)

    def get_queryset(self):
        account = self.context["request"].account
        return NumberingSystem.objects.for_account(account).for_applies_to(self.applies_to)
