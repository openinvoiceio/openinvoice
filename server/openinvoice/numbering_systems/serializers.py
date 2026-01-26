from rest_framework import serializers

from .choices import NumberingSystemAppliesTo, NumberingSystemResetInterval, NumberingSystemStatus
from .validators import numbering_system_template_validator


class NumberingSystemSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    template = serializers.CharField(max_length=100)
    description = serializers.CharField(allow_null=True)
    applies_to = serializers.ChoiceField(choices=NumberingSystemAppliesTo.choices)
    reset_interval = serializers.ChoiceField(choices=NumberingSystemResetInterval.choices)
    status = serializers.ChoiceField(choices=NumberingSystemStatus.choices)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField(allow_null=True)
    archived_at = serializers.DateTimeField(allow_null=True)


class NumberingSystemCreateSerializer(serializers.Serializer):
    template = serializers.CharField(max_length=100, validators=[numbering_system_template_validator])
    description = serializers.CharField(max_length=255, allow_null=True, required=False)
    applies_to = serializers.ChoiceField(choices=NumberingSystemAppliesTo.choices)
    reset_interval = serializers.ChoiceField(
        choices=NumberingSystemResetInterval.choices, allow_null=True, required=False
    )


class NumberingSystemUpdateSerializer(serializers.Serializer):
    template = serializers.CharField(max_length=100, validators=[numbering_system_template_validator])
    description = serializers.CharField(max_length=255, allow_null=True)
    reset_interval = serializers.ChoiceField(choices=NumberingSystemResetInterval.choices, allow_null=True)
