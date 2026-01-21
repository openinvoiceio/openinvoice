from rest_framework import serializers

from .choices import FilePurpose
from .validators import SUPPORTED_FILE_VALIDATORS


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

    def validate(self, data):
        file = data["file"]
        purpose = data["purpose"]
        validator = SUPPORTED_FILE_VALIDATORS[purpose]

        if file.content_type is None:
            raise serializers.ValidationError("Unknown file content type")

        if file.content_type not in validator.allowed_content_types:
            raise serializers.ValidationError("Invalid file type")

        if file.size > validator.max_size:
            raise serializers.ValidationError("File size exceeded")

        return data
