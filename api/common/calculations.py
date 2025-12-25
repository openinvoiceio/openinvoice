from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from djmoney.money import Money

MAX_AMOUNT = Decimal("999999999.99")


def zero(currency: str) -> Money:
    """Return a zero-valued :class:`Money` in ``currency``."""

    return Money(0, currency)


def round_money(amount: Money) -> Money:
    """Round ``amount`` to two decimal places using :data:`ROUND_HALF_UP`."""

    quantized = amount.amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return Money(quantized, amount.currency)


def clamp_money(amount: Money) -> Money:
    """Round ``amount`` and clamp it to the database limit."""

    capped = min(amount, Money(MAX_AMOUNT, amount.currency))
    return round_money(capped)


def calculate_percentage_amount(base: Money, percentage: Decimal) -> Money:
    """Return ``percentage`` percent of ``base``."""

    if percentage <= 0:
        return zero(base.currency)
    return base * (percentage / Decimal(100))
