from django.conf import settings
from rest_framework import serializers

from .choices import FilePurpose


class FileUploadPolicyValidator:
    requires_context = True

    def __init__(self) -> None:
        self.policies = {
            FilePurpose.ACCOUNT_LOGO: settings.FILE_UPLOAD_ACCOUNT_LOGO_POLICY,
            FilePurpose.PRODUCT_IMAGE: settings.FILE_UPLOAD_PRODUCT_IMAGE_POLICY,
            FilePurpose.PROFILE_AVATAR: settings.FILE_UPLOAD_PROFILE_AVATAR_POLICY,
            FilePurpose.CUSTOMER_LOGO: settings.FILE_UPLOAD_CUSTOMER_LOGO_POLICY,
        }

    def __call__(self, attrs, _) -> None:
        file = attrs.get("file")
        purpose = attrs.get("purpose")

        if not file or not purpose:
            return

        validator = self.policies[purpose]
        allowed_content_types = validator["allowed_content_types"]
        max_size = validator["max_size"]

        if file.content_type is None:
            raise serializers.ValidationError("Unknown file content type")

        if file.content_type not in allowed_content_types:
            raise serializers.ValidationError("Invalid file type")

        if file.size > max_size:
            raise serializers.ValidationError("File size exceeded")
