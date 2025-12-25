from rest_framework import serializers

from .models import File


class FileRelatedField(serializers.PrimaryKeyRelatedField):
    def __init__(self, *, for_user: bool = False, **kwargs):
        self.for_user = for_user
        kwargs.setdefault("pk_field", serializers.UUIDField())
        super().__init__(**kwargs)

    def get_queryset(self):
        request = self.context["request"]

        if self.for_user:
            return File.objects.for_user(request.user)

        return File.objects.for_account(request.account)
