from django.core.validators import BaseValidator
from rest_framework import serializers


class MetadataLengthValidator(BaseValidator):
    message = "Invalid metadata length."
    code = "invalid_metadata_length"

    def compare(self, a, b):
        return len(a) > b


class MetadataKeyValidator(BaseValidator):
    message = "Invalid metadata key."
    code = "invalid_metadata_key"

    def compare(self, a, b):
        if not isinstance(a, dict):
            return True
        return any(not isinstance(key, str) or len(key) > b for key in a)


class MetadataValueValidator(BaseValidator):
    message = "Invalid metadata value."
    code = "invalid_metadata_value"

    def compare(self, a, b):
        if not isinstance(a, dict):
            return True
        return any(not isinstance(value, str) or len(value) > b for value in a.values())


class AllOrNoneValidator:
    message = "Fields {fields} must be provided together."
    requires_context = True

    def __init__(self, *fields) -> None:
        self.fields = fields

    def __call__(self, attrs, serializer) -> None:
        present = [s for s in self.fields if attrs.get(s) is not None]

        if present and len(present) != len(self.fields):
            field_names = []
            for name, field in serializer.fields.items():
                source = field.source or name
                if source in self.fields:
                    field_names.append(name)

            raise serializers.ValidationError(self.message.format(fields=", ".join(field_names)))


class ExactlyOneValidator:
    message = "Exactly one of the fields {fields} must be provided."
    requires_context = True

    def __init__(self, *fields: str) -> None:
        self.fields = fields

    def __call__(self, attrs, serializer) -> None:
        present = [f for f in self.fields if attrs.get(f) is not None]

        if len(present) != 1:
            field_names = []
            for name, field in serializer.fields.items():
                source = field.source or name
                if source in self.fields:
                    field_names.append(name)

            raise serializers.ValidationError(self.message.format(fields=", ".join(field_names)))
