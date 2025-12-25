from django.core.validators import BaseValidator


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


class MutuallyExclusiveValidator:
    def __init__(self, *fields: str):
        self.fields = fields

    def __call__(self, data):
        present_fields = [field for field in self.fields if field in data and data[field] is not None]
        if len(present_fields) > 1:
            raise ValueError(f"Fields {', '.join(present_fields)} are mutually exclusive.")


class AtLeastOneFieldValidator:
    def __init__(self, *fields: str):
        self.fields = fields

    def __call__(self, data):
        if not any(field in data and data[field] is not None for field in self.fields):
            raise ValueError(f"At least one of the fields {', '.join(self.fields)} must be provided.")
