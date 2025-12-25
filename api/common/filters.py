from django_filters import BaseInFilter, CharFilter, ChoiceFilter
from djmoney import settings


class CharInFilter(BaseInFilter, CharFilter):
    pass


class CurrencyFilter(ChoiceFilter):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("choices", settings.CURRENCY_CHOICES)
        super().__init__(*args, **kwargs)
