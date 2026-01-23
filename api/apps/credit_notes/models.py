from __future__ import annotations

import uuid
from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal

from django.contrib.postgres.fields import ArrayField
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import models
from django.db.models import Q, Sum
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.functional import cached_property
from djmoney import settings as djmoney_settings
from djmoney.models.fields import MoneyField
from djmoney.money import Money

from apps.files.choices import FilePurpose
from apps.files.models import File
from apps.integrations.choices import PaymentProvider
from apps.invoices.choices import InvoiceStatus
from apps.invoices.models import InvoiceLine
from apps.numbering_systems.models import NumberingSystem
from apps.tax_rates.models import TaxRate
from common.calculations import clamp_money, zero
from common.pdf import generate_pdf

from .calculations import calculate_credit_note_line_amounts
from .choices import CreditNoteDeliveryMethod, CreditNoteReason, CreditNoteStatus
from .managers import CreditNoteLineManager, CreditNoteManager
from .querysets import CreditNoteQuerySet, CreditNoteTaxQuerySet


class CreditNote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    number = models.CharField(max_length=255, null=True)
    numbering_system = models.ForeignKey(
        "numbering_systems.NumberingSystem",
        on_delete=models.SET_NULL,
        related_name="credit_notes",
        null=True,
    )
    currency = models.CharField(max_length=3, choices=djmoney_settings.CURRENCY_CHOICES)
    status = models.CharField(max_length=50, choices=CreditNoteStatus.choices)
    reason = models.CharField(max_length=50, choices=CreditNoteReason.choices, default=CreditNoteReason.OTHER)
    issue_date = models.DateField(null=True)
    invoice = models.ForeignKey("invoices.Invoice", on_delete=models.CASCADE, related_name="credit_notes")
    customer = models.ForeignKey("customers.Customer", on_delete=models.CASCADE, related_name="credit_notes")
    account = models.ForeignKey("accounts.Account", on_delete=models.CASCADE, related_name="credit_notes")
    description = models.CharField(max_length=500, null=True, blank=True)
    subtotal_amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    total_amount_excluding_tax = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    total_tax_amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    total_amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    payment_provider = models.CharField(max_length=50, choices=PaymentProvider.choices, null=True)
    payment_connection_id = models.UUIDField(null=True)
    metadata = models.JSONField(default=dict)
    delivery_method = models.CharField(
        max_length=20,
        choices=CreditNoteDeliveryMethod.choices,
        default=CreditNoteDeliveryMethod.MANUAL,
    )
    recipients = ArrayField(
        base_field=models.EmailField(max_length=254),
        default=list,
        blank=True,
    )
    updated_at = models.DateTimeField(auto_now=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    issued_at = models.DateTimeField(null=True)
    voided_at = models.DateTimeField(null=True)
    pdf = models.OneToOneField("files.File", on_delete=models.SET_NULL, null=True, related_name="credit_notes_pdf")

    objects = CreditNoteManager.from_queryset(CreditNoteQuerySet)()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["account_id", "number"], name="credit_note_account_number_idx"),
            models.Index(fields=["invoice_id", "created_at"], name="credit_note_inv_created_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                name="credit_note_number_required_if_not_draft",
                condition=Q(status=CreditNoteStatus.DRAFT) | (Q(number__isnull=False) & ~Q(number="")),
            ),
            models.UniqueConstraint(
                fields=["invoice"],
                condition=Q(status=CreditNoteStatus.DRAFT),
                name="unique_draft_credit_note_per_invoice",
            ),
        ]

    def generate_number(self) -> str | None:
        if self.numbering_system is None:
            return None

        timestamp = timezone.now()
        start_at, end_at = self.numbering_system.calculate_bounds(effective_at=timestamp)

        query = Q(numbering_system=self.numbering_system) & ~Q(status=CreditNoteStatus.DRAFT)
        if start_at:
            query &= Q(issued_at__gte=start_at)
        if end_at:
            query &= Q(issued_at__lt=end_at)

        issued_count = CreditNote.objects.filter(query).count()

        draft_offset = 0
        if self.status == InvoiceStatus.DRAFT:
            draft_query = Q(numbering_system=self.numbering_system, status=CreditNoteStatus.DRAFT)
            if start_at:
                draft_query &= Q(created_at__gte=start_at)
            if end_at:
                draft_query &= Q(created_at__lt=end_at)

            drafts = CreditNote.objects.filter(draft_query)
            earlier_condition = Q(created_at__lt=self.created_at) | (Q(created_at=self.created_at) & Q(pk__lt=self.pk))
            draft_offset = drafts.filter(earlier_condition).count()

        return self.numbering_system.render_number(count=issued_count + draft_offset, effective_at=timestamp)

    @cached_property
    def effective_number(self) -> str | None:
        if self.number is not None:
            return self.number

        return self.generate_number()

    def can_apply_total(
        self,
        new_total: Money,
        exclude_line: CreditNoteLine | None = None,
    ) -> bool:
        current_total = self.total_amount
        if exclude_line is not None:
            current_total -= exclude_line.total_amount

        projected_total = clamp_money(max(current_total, zero(self.currency)) + new_total)
        available = self.invoice.outstanding_amount
        if exclude_line is not None:
            available += exclude_line.total_amount

        return projected_total <= available

    def recalculate(self) -> None:
        aggregates = self.lines.aggregate(
            subtotal=Sum("total_amount_excluding_tax"),
            total_tax=Sum("total_tax_amount"),
        )
        subtotal = Money(aggregates["subtotal"] or 0, self.currency)
        total_tax = Money(aggregates["total_tax"] or 0, self.currency)
        subtotal = clamp_money(subtotal)
        total_tax = clamp_money(total_tax)
        total_amount = clamp_money(subtotal + total_tax)

        self.subtotal_amount = subtotal
        self.total_amount_excluding_tax = subtotal
        self.total_tax_amount = total_tax
        self.total_amount = total_amount
        self.save(
            update_fields=[
                "subtotal_amount",
                "total_amount_excluding_tax",
                "total_tax_amount",
                "total_amount",
                "updated_at",
            ]
        )

    def update(
        self,
        number: str | None,
        numbering_system: NumberingSystem | None,
        reason: CreditNoteReason,
        metadata: Mapping[str, object] | None,
        description: str | None,
        delivery_method: CreditNoteDeliveryMethod,
        recipients: list[str],
    ) -> None:
        resolved_numbering_system: NumberingSystem | None = None
        if number is None:
            resolved_numbering_system = (
                numbering_system
                or self.invoice.customer.credit_note_numbering_system
                or self.invoice.account.credit_note_numbering_system
            )

        self.number = number
        self.numbering_system = resolved_numbering_system
        self.reason = reason
        self.metadata = metadata or self.metadata
        self.description = description
        self.delivery_method = delivery_method
        self.recipients = recipients
        self.save()

    def generate_pdf(self):
        filename = f"{self.id}.pdf"
        html = render_to_string("credit_notes/pdf/classic.html", {"credit_note": self})
        pdf_content = generate_pdf(html)

        return File.objects.upload_for_account(
            account=self.account,
            purpose=FilePurpose.CREDIT_NOTE_PDF,
            filename=filename,
            data=SimpleUploadedFile(
                name=filename,
                content=pdf_content,
                content_type="application/pdf",
            ),
            content_type="application/pdf",
        )

    def issue(self, issue_date: datetime | None = None) -> None:
        self.status = CreditNoteStatus.ISSUED

        if self.number is None and self.numbering_system is not None:
            self.number = self.generate_number()

        self.issue_date = issue_date or self.issue_date or timezone.now().date()
        self.issued_at = timezone.now()
        self.save()

        pdf_file = self.generate_pdf()
        self.pdf = pdf_file
        self.save(update_fields=["pdf", "updated_at"])

        self.invoice.recalculate_credit()

        if self.invoice.status == InvoiceStatus.OPEN and self.invoice.outstanding_amount.amount == 0:
            self.invoice.mark_paid()

    def void(self) -> None:
        self.status = CreditNoteStatus.VOIDED
        self.voided_at = timezone.now()
        self.save(update_fields=["status", "voided_at", "updated_at"])
        self.invoice.recalculate_credit()


class CreditNoteLine(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    credit_note = models.ForeignKey("CreditNote", on_delete=models.CASCADE, related_name="lines")
    invoice_line = models.ForeignKey(
        "invoices.InvoiceLine",
        on_delete=models.SET_NULL,
        related_name="credit_note_lines",
        null=True,
    )
    description = models.CharField(max_length=255)
    quantity = models.BigIntegerField(null=True)
    currency = models.CharField(max_length=3, choices=djmoney_settings.CURRENCY_CHOICES)
    unit_amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    total_amount_excluding_tax = MoneyField(
        max_digits=19,
        decimal_places=2,
        currency_field_name="currency",
    )
    total_tax_amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    total_amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    created_at = models.DateTimeField(auto_now_add=True)

    objects = CreditNoteLineManager()

    class Meta:
        ordering = ["created_at"]

    @property
    def total_tax_rate(self):
        prefetched = getattr(self, "_prefetched_objects_cache", {})
        taxes = prefetched.get("taxes")
        if taxes is None:
            taxes = self.taxes.all()

        return sum((Decimal(tax.rate or 0) for tax in taxes), Decimal("0"))

    def recalculate(self) -> None:
        total_tax = self.taxes.aggregate(total=Sum("amount")).get("total")
        total_tax_amount = Money(total_tax or 0, self.currency)
        self.total_tax_amount = clamp_money(total_tax_amount)
        self.total_amount = clamp_money(self.total_amount_excluding_tax + self.total_tax_amount)
        self.save(update_fields=["total_tax_amount", "total_amount"])

    def update(
        self,
        quantity: int | None = None,
        description: str | None = None,
        unit_amount: Money | None = None,
        amount: Money | None = None,
        amounts: tuple[Money, Money, Money, Money, Decimal] | None = None,
    ) -> None:
        quantity = self.quantity if quantity is None else quantity
        invoice_line: InvoiceLine | None = None

        if self.invoice_line_id:
            if amounts is None:
                (
                    amount_value,
                    total_excluding_tax,
                    total_tax_amount,
                    total_amount,
                    ratio,
                ) = calculate_credit_note_line_amounts(
                    self.invoice_line,
                    quantity=quantity,
                    amount=amount,
                )
            else:
                amount_value, total_excluding_tax, total_tax_amount, total_amount, ratio = amounts
            unit_amount_value = self.invoice_line.unit_amount
            description_value = self.invoice_line.description
            if amount is not None:
                quantity = None
        else:
            unit_amount_value = unit_amount or self.unit_amount
            amount_value = clamp_money(unit_amount_value * quantity)
            total_excluding_tax = amount_value
            total_tax_amount = zero(self.currency)
            total_amount = amount_value
            description_value = description or self.description

        self.description = description_value or ""
        self.quantity = quantity
        self.unit_amount = unit_amount_value
        self.amount = amount_value
        self.total_amount_excluding_tax = total_excluding_tax
        self.total_tax_amount = total_tax_amount
        self.total_amount = total_amount
        self.save()

        if invoice_line:
            self.taxes.all().delete()
            for tax_rate in invoice_line.tax_rates.all():
                CreditNoteTax.objects.create(
                    credit_note=self.credit_note,
                    credit_note_line=self,
                    tax_rate=tax_rate,
                    name=tax_rate.name,
                    description=tax_rate.description,
                    rate=tax_rate.percentage,
                    currency=self.currency,
                    amount=Decimal("0"),
                )
        else:
            for tax in self.taxes.all():
                tax.amount = clamp_money(self.total_amount_excluding_tax * (Decimal(tax.rate) / Decimal(100)))
                tax.currency = self.currency
                tax.save(update_fields=["amount", "currency"])

        self.recalculate()
        self.credit_note.recalculate()

    def add_tax(self, tax_rate: TaxRate) -> CreditNoteTax:
        tax_amount = clamp_money(self.total_amount_excluding_tax * (Decimal(tax_rate.percentage) / Decimal(100)))
        tax = CreditNoteTax.objects.create(
            credit_note=self.credit_note,
            credit_note_line=self,
            tax_rate=tax_rate,
            name=tax_rate.name,
            description=tax_rate.description,
            rate=tax_rate.percentage,
            currency=self.currency,
            amount=tax_amount,
        )

        self.recalculate()
        self.credit_note.recalculate()

        return tax


class CreditNoteTax(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    credit_note = models.ForeignKey("CreditNote", on_delete=models.CASCADE, related_name="taxes")
    credit_note_line = models.ForeignKey(
        "CreditNoteLine",
        on_delete=models.CASCADE,
        related_name="taxes",
        null=True,
    )
    tax_rate = models.ForeignKey(
        "tax_rates.TaxRate",
        on_delete=models.SET_NULL,
        related_name="credit_note_taxes",
        null=True,
    )
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, null=True)
    rate = models.DecimalField(max_digits=5, decimal_places=2)
    currency = models.CharField(max_length=3, choices=djmoney_settings.CURRENCY_CHOICES)
    amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    created_at = models.DateTimeField(auto_now_add=True)

    objects = CreditNoteTaxQuerySet.as_manager()

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["credit_note_line", "tax_rate"],
                condition=Q(credit_note_line__isnull=False, tax_rate__isnull=False),
                name="unique_credit_note_line_tax_rate",
            ),
            models.UniqueConstraint(
                fields=["credit_note", "tax_rate"],
                condition=Q(credit_note_line__isnull=True, tax_rate__isnull=False),
                name="unique_credit_note_tax_rate",
            ),
        ]
