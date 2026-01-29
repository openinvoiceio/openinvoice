from rest_framework import serializers

from .choices import FilePurpose
from .validators import FileUploadPolicyValidator


class FileSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    account_id = serializers.UUIDField(allow_null=True)
    purpose = serializers.ChoiceField(choices=FilePurpose.choices)
    url = serializers.FileField(use_url=True, source="data")
    filename = serializers.CharField()
    size = serializers.IntegerField(source="data.size")
    content_type = serializers.CharField()
    created_at = serializers.DateTimeField()


class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    purpose = serializers.ChoiceField(
        choices=[
            FilePurpose.ACCOUNT_LOGO,
            FilePurpose.PRODUCT_IMAGE,
            FilePurpose.PROFILE_AVATAR,
            FilePurpose.CUSTOMER_LOGO,
        ]
    )

    class Meta:
        validators = [FileUploadPolicyValidator()]
