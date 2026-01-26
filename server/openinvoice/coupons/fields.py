from rest_framework import serializers

from common.fields import UniqueManyRelatedField

from .models import Coupon


class CouponRelatedField(serializers.PrimaryKeyRelatedField):
    def __init__(self, **kwargs):
        kwargs.setdefault("pk_field", serializers.UUIDField())
        super().__init__(**kwargs)

    def get_queryset(self):
        account = self.context["request"].account
        return Coupon.objects.filter(account=account)

    @classmethod
    def many_init(cls, *args, **kwargs):
        kwargs["child_relation"] = cls()
        return UniqueManyRelatedField(*args, **kwargs)
