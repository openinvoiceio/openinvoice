from allauth.account.utils import user_display
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from openinvoice.files.fields import FileRelatedField

from .models import User


class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.SerializerMethodField()
    email = serializers.EmailField()
    avatar_url = serializers.FileField(source="avatar.data", use_url=True, allow_null=True)
    avatar_id = serializers.UUIDField()
    active_account_id = serializers.SerializerMethodField()
    joined_at = serializers.DateTimeField(source="date_joined")
    has_usable_password = serializers.SerializerMethodField()

    @extend_schema_field(str)
    def get_name(self, obj: User) -> str:
        return obj.name or user_display(obj)

    @extend_schema_field(OpenApiTypes.UUID)
    def get_active_account_id(self, _: User) -> str | None:
        request = self.context.get("request")
        if request is None:
            return None

        active_account_id = request.session.get("active_account_id", None)
        if active_account_id is None:
            active_account = request.accounts.first()
            active_account_id = active_account.id if active_account else None
        return str(active_account_id) if active_account_id else None

    @extend_schema_field(bool)
    def get_has_usable_password(self, obj: User) -> bool:
        return obj.has_usable_password()


class UserUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, allow_null=True)
    avatar_id = FileRelatedField(
        source="avatar",
        allow_null=True,
        required=False,
        for_user=True,
    )
