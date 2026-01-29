from allauth.account.utils import user_display
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from openinvoice.users.models import User

from .choices import NoteVisibility


class NoteAuthorSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.SerializerMethodField()
    avatar_url = serializers.FileField(source="avatar.data", use_url=True, allow_null=True)

    @extend_schema_field(OpenApiTypes.STR)
    def get_name(self, obj: User) -> str:
        return obj.name or user_display(obj)


class NoteSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    content = serializers.CharField(max_length=2048)
    visibility = serializers.ChoiceField(choices=NoteVisibility.choices)
    created_at = serializers.DateTimeField()
    author = NoteAuthorSerializer()


class NoteCreateSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=2048)
    visibility = serializers.ChoiceField(choices=NoteVisibility.choices)
