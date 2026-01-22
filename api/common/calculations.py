from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from djmoney.money import Money
from moneyed import Currency

MAX_AMOUNT = Decimal("999999999.99")
CENT = Decimal("0.01")


def zero(currency: str | Currency) -> Money:
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


def allocate_proportionally(money: Money, bases: list[Money]) -> list[Money]:
    """Allocate `money` proportionally across `bases`."""
    if len(bases) == 0:
        return []

    amount = money.amount
    base_amounts = [base.amount for base in bases]

    if amount <= 0:
        return [zero(money.currency) for _ in bases]

    total_base_amount = sum(base_amounts, Decimal("0"))
    if total_base_amount <= 0:
        return [zero(money.currency) for _ in bases]

    # Raw proportional shares (unrounded)
    raw = [amount * (b / total_base_amount) for b in base_amounts]

    # First rounding pass
    rounded_amounts = [r.quantize(CENT, rounding=ROUND_HALF_UP) for r in raw]

    total_rounded_amount = sum(rounded_amounts, Decimal("0"))
    remainder_amount = (amount - total_rounded_amount).quantize(CENT, rounding=ROUND_HALF_UP)

    if remainder_amount != 0:
        # Largest remainder method: distribute leftover cents to the largest fractional parts
        fractions = [(i, raw[i] - rounded_amounts[i]) for i in range(len(base_amounts))]
        fractions.sort(key=lambda t: t[1], reverse=(remainder_amount > 0))

        step = CENT if remainder_amount > 0 else -CENT
        steps = int((remainder_amount / step).to_integral_value(rounding=ROUND_HALF_UP))

        for k in range(abs(steps)):
            idx = fractions[k % len(fractions)][0]
            rounded_amounts[idx] += step

    return [Money(amount, money.currency) for amount in rounded_amounts]
