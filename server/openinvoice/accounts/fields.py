from rest_framework import serializers

from openinvoice.addresses.models import Address

from .models import BusinessProfile


class BusinessProfileRelatedField(serializers.PrimaryKeyRelatedField):
    def __init__(self, **kwargs):
        kwargs.setdefault("pk_field", serializers.UUIDField())
        super().__init__(**kwargs)

    def get_queryset(self):
        account = self.context["request"].account
        return BusinessProfile.objects.for_account(account)


class AccountAddressRelatedField(serializers.PrimaryKeyRelatedField):
    def __init__(self, **kwargs):
        kwargs.setdefault("pk_field", serializers.UUIDField())
        super().__init__(**kwargs)

    def get_queryset(self):
        request = self.context.get("request")
        account = getattr(request, "account", None) if request else None
        if not account:
            return Address.objects.none()
        return account.addresses.all()
