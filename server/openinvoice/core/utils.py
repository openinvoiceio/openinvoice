from contextlib import contextmanager
from decimal import InvalidOperation

import moneyed
from django.db import DataError
from rest_framework.exceptions import ValidationError

from openinvoice.core.db import is_numeric_out_of_range_error


def country_to_currency(country_code: str) -> str:
    for currency in moneyed.CURRENCIES.values():
        if country_code in currency.country_codes:
            return currency.code
    raise ValueError(f"Currency not found for country code {country_code}")


@contextmanager
def numeric_overflow():
    try:
        yield
    except InvalidOperation as e:
        raise ValidationError("Amount exceeds the maximum allowed value") from e
    except DataError as e:
        if is_numeric_out_of_range_error(e):
            raise ValidationError("Amount exceeds the maximum allowed value") from e
        raise
