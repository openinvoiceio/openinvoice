import django_filters

from .choices import NumberingSystemAppliesTo, NumberingSystemStatus
from .models import NumberingSystem


class NumberingSystemFilterSet(django_filters.FilterSet):
    applies_to = django_filters.ChoiceFilter(
        field_name="applies_to",
        choices=NumberingSystemAppliesTo.choices,
        error_messages={"invalid_choice": "Invalid document type"},
    )
    status = django_filters.ChoiceFilter(field_name="status", choices=NumberingSystemStatus.choices)

    class Meta:
        model = NumberingSystem
        fields = []
