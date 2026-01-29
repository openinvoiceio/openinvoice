from __future__ import annotations

from collections.abc import Callable, Iterable
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Protocol, TypeVar

from djmoney.money import Money
from moneyed import Currency

CENT = Decimal("0.01")

T = TypeVar("T")
K = TypeVar("K")
R = TypeVar("R", bound=dict[str, Any])


class SupportsOrdering(Protocol):
    def __lt__(self, other: Any, /) -> bool: ...


class SupportsTaxRate(Protocol):
    def calculate_amount(self, base_amount: Money) -> Money: ...


def zero(currency: str | Currency) -> Money:
    """Return a zero-valued :class:`Money` in ``currency``."""

    return Money(0, currency)


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


def aggregate_allocations(
    items: Iterable[T],
    key: Callable[[T], K],
    build: Callable[[T], R],
    order: Callable[[T], SupportsOrdering] | None = None,
) -> list[R]:
    if order is not None:
        items = sorted(items, key=order)

    aggregated: dict[K, R] = {}
    for item in items:
        item_key = key(item)
        if item_key in aggregated:
            aggregated[item_key]["amount"] += item.amount
        else:
            aggregated[item_key] = build(item)

    return list(aggregated.values())


def calculate_tax_amounts(
    base_amount: Money,
    taxable_amount: Money,
    tax_multiplier: Decimal,
    tax_rates: Iterable[SupportsTaxRate],
) -> list[Money]:
    tax_rates = list(tax_rates)
    if not tax_rates:
        return []

    tax_amounts = [tax_rate.calculate_amount(base_amount).round(2) for tax_rate in tax_rates]
    if tax_multiplier > Decimal(1) and tax_amounts:
        total_tax_amount = sum(tax_amounts, zero(base_amount.currency))
        target_total_tax_amount = max(taxable_amount - base_amount, zero(base_amount.currency))
        adjustment = target_total_tax_amount - total_tax_amount
        tax_amounts[-1] = max(tax_amounts[-1] + adjustment, zero(base_amount.currency))

    return tax_amounts
