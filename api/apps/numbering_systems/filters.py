import django_filters

from .choices import NumberingSystemAppliesTo
from .models import NumberingSystem


class NumberingSystemFilter(django_filters.FilterSet):
    applies_to = django_filters.ChoiceFilter(
        field_name="applies_to",
        choices=NumberingSystemAppliesTo.choices,
        error_messages={"invalid_choice": "Invalid document type"},
    )

    class Meta:
        model = NumberingSystem
        fields: list[str] = []
