from rest_framework import serializers

from .models import CreditNote


class CreditNoteRelatedField(serializers.PrimaryKeyRelatedField):
    def __init__(self, **kwargs):
        kwargs.setdefault("pk_field", serializers.UUIDField())
        super().__init__(**kwargs)

    def get_queryset(self):
        account = self.context["request"].account
        return CreditNote.objects.filter(account=account)
