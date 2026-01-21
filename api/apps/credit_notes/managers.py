from __future__ import annotations

from collections.abc import Iterable, Mapping
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from django.db import models
from djmoney.money import Money

from apps.accounts.models import Account
from apps.invoices.models import Invoice
from apps.numbering_systems.models import NumberingSystem
from common.calculations import clamp_money, zero

from .calculations import calculate_credit_note_line_amounts
from .enums import CreditNoteDeliveryMethod, CreditNoteReason, CreditNoteStatus
from .querysets import CreditNoteQuerySet

if TYPE_CHECKING:
    from apps.invoices.models import InvoiceLine

    from .models import CreditNote, CreditNoteLine


class CreditNoteManager(models.Manager.from_queryset(CreditNoteQuerySet)):
    def total_for_invoice(self, invoice: Invoice, *, exclude: CreditNote | None = None) -> Money:
        queryset = self.filter(invoice=invoice).issued()
        if exclude:
            queryset = queryset.exclude(id=exclude.id)

        return queryset.total_amount(currency=invoice.currency)

    def create_draft(
        self,
        account: Account,
        invoice: Invoice,
        number: str | None = None,
        numbering_system: NumberingSystem | None = None,
        reason: CreditNoteReason | None = None,
        metadata: Mapping[str, Any] | None = None,
        description: str | None = None,
        delivery_method: CreditNoteDeliveryMethod | None = None,
        recipients: Iterable[str] | None = None,
    ) -> CreditNote:
        resolved_numbering_system = None
        if number is None:
            resolved_numbering_system = (
                numbering_system
                or invoice.customer.credit_note_numbering_system
                or invoice.account.credit_note_numbering_system
            )

        default_recipients = [invoice.customer.email] if invoice.customer.email else []

        credit_note = self.create(
            account=account,
            customer=invoice.customer,
            invoice=invoice,
            number=number,
            numbering_system=resolved_numbering_system,
            currency=invoice.currency,
            status=CreditNoteStatus.DRAFT,
            reason=reason or CreditNoteReason.OTHER,
            metadata=dict(metadata or {}),
            description=description,
            subtotal_amount=zero(invoice.currency),
            total_amount_excluding_tax=zero(invoice.currency),
            total_tax_amount=zero(invoice.currency),
            total_amount=zero(invoice.currency),
            payment_provider=invoice.payment_provider,
            payment_connection_id=invoice.payment_connection_id,
            delivery_method=delivery_method or CreditNoteDeliveryMethod.MANUAL,
            recipients=recipients or default_recipients,
        )

        invoice_lines = invoice.lines.order_by("created_at").prefetch_related("tax_rates")
        for invoice_line in invoice_lines:
            if invoice_line.outstanding_amount.amount <= 0:
                continue

            amounts = calculate_credit_note_line_amounts(invoice_line)
            (
                _amount,
                _excluding_tax,
                _tax_amount,
                total_amount,
                _ratio,
            ) = amounts

            if not credit_note.can_apply_total(new_total=total_amount):
                continue

            credit_note.lines.from_invoice_line(
                credit_note,
                invoice_line,
                amounts=amounts,
            )

        credit_note.refresh_from_db()
        return credit_note


class CreditNoteLineManager(models.Manager["CreditNoteLine"]):
    def from_invoice_line(
        self,
        credit_note: CreditNote,
        invoice_line: InvoiceLine,
        quantity: int | None = None,
        amount: Money | None = None,
        ratio: Decimal | None = None,
        amounts: tuple[Money, Money, Money, Money, Decimal] | None = None,
    ) -> CreditNoteLine:
        if amounts is None:
            (
                amount_value,
                total_excluding_tax,
                total_tax_amount,
                total_amount,
                computed_ratio,
            ) = calculate_credit_note_line_amounts(
                invoice_line,
                quantity=quantity,
                amount=amount,
            )
        else:
            amount_value, total_excluding_tax, total_tax_amount, total_amount, computed_ratio = amounts

        ratio = ratio if ratio is not None else computed_ratio

        if amount is not None:
            resolved_quantity = None
        elif quantity is not None:
            resolved_quantity = quantity
        else:
            resolved_quantity = invoice_line.outstanding_quantity
            if resolved_quantity is None or resolved_quantity <= 0:
                resolved_quantity = invoice_line.quantity

            if invoice_line.quantity:
                expected_quantity_decimal = Decimal(invoice_line.quantity) * ratio
                integral_candidate = expected_quantity_decimal.to_integral_value()
                if expected_quantity_decimal == integral_candidate:
                    resolved_quantity = int(integral_candidate)
                elif resolved_quantity == invoice_line.quantity:
                    resolved_quantity = None

            if resolved_quantity == 0:
                resolved_quantity = None

        credit_note_line = self.create(
            credit_note=credit_note,
            invoice_line=invoice_line,
            description=invoice_line.description,
            quantity=resolved_quantity,
            currency=credit_note.currency,
            unit_amount=invoice_line.unit_amount,
            amount=amount_value,
            total_amount_excluding_tax=total_excluding_tax,
            total_tax_amount=total_tax_amount,
            total_amount=total_amount,
        )

        for tax_rate in invoice_line.tax_rates.all():
            credit_note_line.taxes.create(
                credit_note=credit_note,
                credit_note_line=credit_note_line,
                tax_rate=tax_rate,
                name=tax_rate.name,
                description=tax_rate.description,
                rate=tax_rate.percentage,
                currency=credit_note.currency,
                amount=Decimal("0"),
            )

        credit_note_line.recalculate()
        credit_note.recalculate()
        credit_note_line.refresh_from_db()
        return credit_note_line

    def create_line(
        self,
        credit_note: CreditNote,
        description: str | None = None,
        quantity: int | None = None,
        unit_amount: Money | None = None,
    ) -> CreditNoteLine:
        quantity = quantity or 1
        unit_amount_value = unit_amount or zero(credit_note.currency)
        amount = clamp_money(unit_amount_value * quantity)

        credit_note_line = self.create(
            credit_note=credit_note,
            description=description or "",
            quantity=quantity,
            currency=credit_note.currency,
            unit_amount=unit_amount_value,
            amount=amount,
            total_amount_excluding_tax=amount,
            total_tax_amount=zero(credit_note.currency),
            total_amount=amount,
        )

        credit_note.recalculate()
        credit_note_line.refresh_from_db()
        return credit_note_line
