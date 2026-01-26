from __future__ import annotations

from decimal import Decimal

from djmoney.money import Money

from openinvoice.invoices.models import InvoiceLine


def calculate_credit_note_line_amounts(
    invoice_line: InvoiceLine,
    *,
    quantity: int | None = None,
    amount: Money | None = None,
) -> tuple[Money, Money, Money, Money, Decimal]:
    """Return proportional amounts for ``quantity`` or ``amount`` based on ``invoice_line``."""

    if amount is not None and amount.currency != invoice_line.currency:
        amount = Money(amount.amount, invoice_line.currency)

    available_quantity = invoice_line.outstanding_quantity
    if available_quantity is None:
        available_quantity = invoice_line.quantity

    if amount is not None and invoice_line.amount.amount:
        ratio = Decimal(amount.amount) / Decimal(invoice_line.amount.amount)
    elif amount is not None:
        ratio = Decimal(0)
    else:
        default_quantity = available_quantity
        resolved_quantity = quantity if quantity is not None else default_quantity
        base_quantity = Decimal(default_quantity) if default_quantity else None

        if base_quantity and resolved_quantity is not None:
            ratio = Decimal(resolved_quantity) / base_quantity
        else:
            ratio = Decimal(0)

    ratio = max(Decimal(0), min(ratio, Decimal(1)))

    if invoice_line.total_amount.amount:
        outstanding_ratio = Decimal(invoice_line.outstanding_amount.amount) / Decimal(invoice_line.total_amount.amount)
        ratio = min(ratio, max(Decimal(0), outstanding_ratio))

    if invoice_line.quantity:
        outstanding_quantity = invoice_line.outstanding_quantity
        if outstanding_quantity is not None:
            quantity_ratio = Decimal(outstanding_quantity) / Decimal(invoice_line.quantity)
            ratio = min(ratio, max(Decimal(0), quantity_ratio))

    amount_value = invoice_line.amount * ratio
    total_amount = invoice_line.total_amount * ratio
    total_amount_excluding_tax = invoice_line.total_excluding_tax_amount * ratio
    total_tax_amount = invoice_line.total_tax_amount * ratio

    return amount_value, total_amount_excluding_tax, total_tax_amount, total_amount, ratio
