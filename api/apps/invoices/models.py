from __future__ import annotations

import uuid
from collections.abc import Mapping
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from dateutil.relativedelta import relativedelta
from django.contrib.postgres.fields import ArrayField
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import models
from django.db.models import DecimalField, F, IntegerField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.functional import cached_property
from djmoney.models.fields import MoneyField
from djmoney.money import Money

from apps.accounts.models import Account
from apps.coupons.models import Coupon
from apps.credit_notes.enums import CreditNoteStatus
from apps.customers.models import Customer
from apps.files.enums import FilePurpose
from apps.files.models import File
from apps.integrations.enums import PaymentProvider
from apps.numbering_systems.models import NumberingSystem
from apps.payments.models import Payment
from apps.prices.models import Price
from apps.taxes.models import TaxRate
from common.calculations import clamp_money, zero
from common.pdf import generate_pdf

from .enums import InvoiceDeliveryMethod, InvoiceStatus
from .managers import (
    InvoiceAccountManager,
    InvoiceCustomerManager,
    InvoiceDiscountManager,
    InvoiceLineManager,
    InvoiceManager,
    InvoiceTaxManager,
)


class InvoiceCustomer(models.Model):
    """Immutable customer data captured for finalized invoices."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    legal_name = models.CharField(max_length=255, null=True)
    legal_number = models.CharField(max_length=255, null=True)
    email = models.CharField(max_length=255, null=True)
    phone = models.CharField(max_length=255, null=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    billing_address = models.OneToOneField(
        "addresses.Address",
        on_delete=models.PROTECT,
        related_name="invoice_customer_billing_address",
    )
    shipping_address = models.OneToOneField(
        "addresses.Address",
        on_delete=models.PROTECT,
        related_name="invoice_customer_shipping_address",
    )
    logo = models.ForeignKey(
        "files.File",
        on_delete=models.SET_NULL,
        null=True,
        related_name="invoice_customer_logo",
    )
    tax_ids = models.ManyToManyField("taxes.TaxId", related_name="invoice_customers")

    objects = InvoiceCustomerManager()


class InvoiceAccount(models.Model):
    """Immutable account data captured for finalized invoices."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    legal_name = models.CharField(max_length=255, null=True)
    legal_number = models.CharField(max_length=255, null=True)
    email = models.CharField(max_length=255, null=True)
    phone = models.CharField(max_length=255, null=True)
    address = models.OneToOneField(
        "addresses.Address",
        on_delete=models.PROTECT,
        related_name="invoice_account_address",
    )
    logo = models.ForeignKey(
        "files.File",
        on_delete=models.SET_NULL,
        null=True,
        related_name="invoice_account_logo",
    )
    tax_ids = models.ManyToManyField("taxes.TaxId", related_name="invoice_accounts")

    objects = InvoiceAccountManager()


class Invoice(models.Model):  # type: ignore[django-manager-missing]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    number = models.CharField(max_length=255, null=True)
    numbering_system = models.ForeignKey(
        "numbering_systems.NumberingSystem", on_delete=models.PROTECT, related_name="invoices", null=True
    )
    currency = models.CharField(max_length=3)
    status = models.CharField(max_length=50, choices=InvoiceStatus.choices)
    issue_date = models.DateField(null=True)
    sell_date = models.DateField(null=True)
    due_date = models.DateField(null=True)
    net_payment_term = models.IntegerField(default=7)
    customer_on_invoice = models.OneToOneField(
        "InvoiceCustomer",
        on_delete=models.PROTECT,
        null=True,
        related_name="invoice",
    )
    account_on_invoice = models.OneToOneField(
        "InvoiceAccount",
        on_delete=models.PROTECT,
        null=True,
        related_name="invoice",
    )
    customer = models.ForeignKey("customers.Customer", on_delete=models.PROTECT, related_name="invoices")
    account = models.ForeignKey("accounts.Account", on_delete=models.PROTECT, related_name="invoices")
    footer = models.CharField(max_length=500, null=True, blank=True)
    description = models.CharField(max_length=500, null=True, blank=True)
    subtotal_amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    total_discount_amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    total_amount_excluding_tax = MoneyField(
        max_digits=19,
        decimal_places=2,
        currency_field_name="currency",
    )
    total_tax_amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    total_amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    total_credit_amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    total_paid_amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    outstanding_amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    updated_at = models.DateTimeField(auto_now=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    opened_at = models.DateTimeField(null=True)
    paid_at = models.DateTimeField(null=True)
    voided_at = models.DateTimeField(null=True)
    pdf = models.OneToOneField("files.File", on_delete=models.SET_NULL, null=True, related_name="invoices_pdf")
    metadata = models.JSONField(default=dict)
    custom_fields = models.JSONField(default=dict)
    payment_provider = models.CharField(max_length=50, choices=PaymentProvider.choices, null=True)
    payment_connection_id = models.UUIDField(null=True)
    delivery_method = models.CharField(
        max_length=20,
        choices=InvoiceDeliveryMethod.choices,
        default=InvoiceDeliveryMethod.MANUAL,
    )
    recipients = ArrayField(
        base_field=models.EmailField(max_length=254),
        default=list,
        blank=True,
    )
    previous_revision = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        related_name="revisions",
        null=True,
    )
    latest_revision = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        related_name="latest_revision_sources",
        null=True,
    )

    objects = InvoiceManager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["account_id", "number"], name="account_id_number_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                name="invoice_number_required_if_not_draft",
                condition=Q(status=InvoiceStatus.DRAFT) | (Q(number__isnull=False) & ~Q(number="")),
            ),
            models.CheckConstraint(
                name="invoice_cannot_reference_itself",
                condition=Q(previous_revision__isnull=True) | ~Q(previous_revision=F("id")),
            ),
        ]

    @property
    def effective_customer(self):
        return self.customer_on_invoice or self.customer

    @property
    def effective_account(self):
        return self.account_on_invoice or self.account

    def generate_number(self) -> str | None:
        # TODO: add much more tests for this method
        if self.numbering_system is None:
            return None

        timestamp = timezone.now()
        start_at, end_at = self.numbering_system.calculate_bounds(effective_at=timestamp)

        query = Q(numbering_system=self.numbering_system) & ~Q(status=InvoiceStatus.DRAFT)
        if start_at:
            query &= Q(opened_at__gte=start_at)
        if end_at:
            query &= Q(opened_at__lt=end_at)

        finalized_count = Invoice.objects.filter(query).count()

        draft_offset = 0
        if self.status == InvoiceStatus.DRAFT:
            draft_query = Q(numbering_system=self.numbering_system, status=InvoiceStatus.DRAFT)
            if start_at:
                draft_query &= Q(created_at__gte=start_at)
            if end_at:
                draft_query &= Q(created_at__lt=end_at)

            drafts = Invoice.objects.filter(draft_query)
            earlier_condition = Q(created_at__lt=self.created_at) | (Q(created_at=self.created_at) & Q(pk__lt=self.pk))
            draft_offset = drafts.filter(earlier_condition).count()

        return self.numbering_system.render_number(count=finalized_count + draft_offset, effective_at=timestamp)

    @cached_property
    def effective_number(self) -> str | None:
        if self.number is not None:
            return self.number

        return self.generate_number()

    @property
    def is_payable(self) -> bool:
        return self.lines.exists() and self.total_amount.amount > 0

    @staticmethod
    def calculate_due_date(account: Account, customer: Customer) -> date:
        today = timezone.now().date()
        net_payment_term = (
            customer.net_payment_term if customer.net_payment_term is not None else account.net_payment_term
        )
        return today + relativedelta(days=net_payment_term)

    def calculate_outstanding_amount(self) -> Money:
        return max(
            self.total_amount - self.total_paid_amount - self.total_credit_amount,
            zero(self.currency),
        )

    def recalculate(self) -> None:
        subtotal_amount = zero(self.currency)
        lines_discount_amount = zero(self.currency)
        lines_tax_amount = zero(self.currency)
        lines_amount_excluding_tax = zero(self.currency)
        taxed_lines_amount_excluding_tax = zero(self.currency)

        for line in self.lines.all():
            subtotal_amount += line.amount
            lines_discount_amount += line.total_discount_amount
            lines_tax_amount += line.total_tax_amount
            lines_amount_excluding_tax += line.total_amount_excluding_tax
            if line.taxes.all():
                taxed_lines_amount_excluding_tax += line.total_amount_excluding_tax

        # Calculate discounts

        invoice_discount_amount = zero(self.currency)
        total_amount_excluding_tax = lines_amount_excluding_tax
        discounts = self.discounts.select_related("coupon").for_invoice()
        for discount in discounts:
            discount.amount = discount.calculate_amount(total_amount_excluding_tax)
            invoice_discount_amount += discount.amount
            total_amount_excluding_tax = max(total_amount_excluding_tax - discount.amount, zero(self.currency))

        InvoiceDiscount.objects.bulk_update(discounts, ["amount"])

        # Adjust taxed lines amount after distributing invoice-level discounts
        invoice_taxable_amount = taxed_lines_amount_excluding_tax
        if (
            lines_amount_excluding_tax.amount > 0
            and taxed_lines_amount_excluding_tax.amount > 0
            and invoice_discount_amount.amount > 0
        ):
            ratio = taxed_lines_amount_excluding_tax.amount / lines_amount_excluding_tax.amount
            shared_discount = min(invoice_discount_amount * ratio, taxed_lines_amount_excluding_tax)
            invoice_taxable_amount = max(taxed_lines_amount_excluding_tax - shared_discount, zero(self.currency))

        invoice_taxable_amount = max(total_amount_excluding_tax - invoice_taxable_amount, zero(self.currency))

        # Calculate taxes

        invoice_tax_amount = zero(self.currency)
        taxes = self.taxes.select_related("tax_rate").for_invoice()
        for tax in taxes:
            tax.amount = tax.calculate_amount(invoice_taxable_amount)
            invoice_tax_amount += tax.amount

        InvoiceTax.objects.bulk_update(taxes, ["amount"])

        # Final totals

        total_discount_amount = lines_discount_amount + invoice_discount_amount
        total_tax_amount = lines_tax_amount + invoice_tax_amount
        total_amount = total_amount_excluding_tax + total_tax_amount

        self.subtotal_amount = clamp_money(subtotal_amount)
        self.total_discount_amount = clamp_money(total_discount_amount)
        self.total_amount_excluding_tax = clamp_money(total_amount_excluding_tax)
        self.total_tax_amount = clamp_money(total_tax_amount)
        self.total_amount = clamp_money(total_amount)
        self.outstanding_amount = self.calculate_outstanding_amount()
        self.save(
            update_fields=[
                "subtotal_amount",
                "total_discount_amount",
                "total_amount_excluding_tax",
                "total_tax_amount",
                "total_amount",
                "outstanding_amount",
            ]
        )

    def recalculate_credit(self) -> None:
        lines = self.lines.annotate(
            credited_amount=Coalesce(
                Sum(
                    "credit_note_lines__total_amount",
                    filter=Q(credit_note_lines__credit_note__status=CreditNoteStatus.ISSUED),
                ),
                Value(0),
                output_field=DecimalField(max_digits=19, decimal_places=2),
            ),
            credited_quantity=Coalesce(
                Sum(
                    "credit_note_lines__quantity",
                    filter=Q(credit_note_lines__credit_note__status=CreditNoteStatus.ISSUED),
                ),
                Value(0),
                output_field=IntegerField(),
            ),
        )

        for line in lines:
            line.apply_credit(
                amount=Money(line.credited_amount, self.currency),
                quantity=line.credited_quantity,
            )

        total_credit_amount = self.credit_notes.issued().total_amount(currency=self.currency)
        self.total_credit_amount = clamp_money(total_credit_amount)
        self.outstanding_amount = self.calculate_outstanding_amount()
        self.save(update_fields=["total_credit_amount", "outstanding_amount", "updated_at"])

    def recalculate_paid(self) -> None:
        total_paid_amount = self.payments.succeeded().aggregate(
            total=Coalesce(
                Sum("amount"),
                Value(0),
                output_field=DecimalField(max_digits=19, decimal_places=2),
            )
        )["total"]

        self.total_paid_amount = Money(total_paid_amount or 0, self.currency)
        self.outstanding_amount = self.calculate_outstanding_amount()
        self.save(update_fields=["total_paid_amount", "outstanding_amount", "updated_at"])

        if self.outstanding_amount.amount == 0:
            self.mark_as_paid()

    def add_tax(self, tax_rate: TaxRate) -> InvoiceTax:
        tax = self.taxes.create(
            tax_rate=tax_rate,
            name=tax_rate.name,
            description=tax_rate.description,
            rate=tax_rate.percentage,
            currency=self.currency,
            amount=zero(self.currency),
        )
        self.recalculate()
        tax.refresh_from_db()
        return tax

    def add_discount(self, coupon: Coupon) -> InvoiceDiscount:
        discount = self.discounts.create(
            coupon=coupon,
            currency=self.currency,
            amount=zero(self.currency),
        )
        self.recalculate()
        discount.refresh_from_db()
        return discount

    def generate_pdf(self) -> File:
        invoice = Invoice.objects.for_pdf().get(id=self.id)
        filename = f"{invoice.id}.pdf"
        html = render_to_string("invoices/pdf/classic.html", {"invoice": invoice})
        pdf_content = generate_pdf(html)

        pdf_file = File.objects.upload_for_account(
            account=invoice.account,
            purpose=FilePurpose.INVOICE_PDF,
            filename=filename,
            data=SimpleUploadedFile(
                name=filename,
                content=pdf_content,
                content_type="application/pdf",
            ),
            content_type="application/pdf",
        )

        self.pdf = pdf_file
        self.save(update_fields=["pdf"])

        return pdf_file

    def mark_as_paid(self) -> None:
        self.status = InvoiceStatus.PAID
        self.paid_at = timezone.now()
        self.outstanding_amount = zero(self.currency)
        self.save(update_fields=["status", "paid_at", "outstanding_amount"])

    def finalize(self) -> None:
        self.status = InvoiceStatus.OPEN

        if self.number is None and self.numbering_system is not None:
            self.number = self.generate_number()

        self.customer_on_invoice = InvoiceCustomer.objects.from_customer(self.customer)
        self.account_on_invoice = InvoiceAccount.objects.from_account(self.account)

        if self.issue_date is None:
            self.issue_date = timezone.now().date()
        if self.due_date is None:
            self.due_date = timezone.now().date() + relativedelta(days=self.net_payment_term)
        self.save()

        if self.previous_revision and self.previous_revision.status == InvoiceStatus.OPEN:
            self.previous_revision.void()

        Invoice.objects.sync_latest_revision(self)

        self.generate_pdf()
        self.opened_at = timezone.now()
        self.save(update_fields=["opened_at"])

        if not self.is_payable:
            self.mark_as_paid()
        elif self.payment_provider and self.payment_connection_id:
            Payment.objects.checkout_invoice(invoice=self)

    def void(self) -> None:
        self.status = InvoiceStatus.VOIDED
        self.voided_at = timezone.now()
        self.save()

        updates: list[Invoice] = []
        if self.latest_revision_id != self.id:
            self.latest_revision = self
            updates.append(self)

        previous = self.previous_revision
        if previous is not None:
            if previous.latest_revision_id != previous.id:
                previous.latest_revision = previous
                updates.append(previous)

            current = previous.previous_revision
            while current is not None:
                if current.latest_revision_id != previous.id:
                    current.latest_revision = previous
                    updates.append(current)
                current = current.previous_revision

        if updates:
            Invoice.objects.bulk_update(updates, ["latest_revision"])

    def mark_paid(self, timestamp: datetime | None = None) -> None:
        self.status = InvoiceStatus.PAID
        self.paid_at = timestamp or timezone.now()
        self.save(update_fields=["status", "paid_at"])

    # TODO: fix typing
    def update(
        self,
        customer: Customer,
        currency: str,
        net_payment_term: int,
        number: str | None = None,
        numbering_system: NumberingSystem | None = None,
        issue_date: date | None = None,
        sell_date: date | None = None,
        due_date: date | None = None,
        metadata: Mapping[str, Any] | None = None,
        custom_fields: Mapping[str, Any] | None = None,
        footer: str | None = None,
        description: str | None = None,
        payment_provider: PaymentProvider | None = None,
        payment_connection_id: uuid.UUID | None = None,
        delivery_method: InvoiceDeliveryMethod | None = None,
        recipients: list[str] | None = None,
    ) -> None:
        original_currency = self.currency
        currency = currency or customer.currency or self.account.default_currency
        resolved_numbering_system: NumberingSystem | None = None
        if number is None:
            resolved_numbering_system = (
                numbering_system or customer.invoice_numbering_system or customer.account.invoice_numbering_system
            )

        self.number = number
        self.numbering_system = resolved_numbering_system
        self.currency = currency
        self.issue_date = issue_date
        self.sell_date = sell_date
        self.due_date = due_date
        self.net_payment_term = net_payment_term
        self.metadata = dict(metadata or self.metadata)
        self.custom_fields = dict(custom_fields or self.custom_fields)
        self.footer = footer
        self.description = description
        self.payment_provider = payment_provider
        self.payment_connection_id = payment_connection_id
        self.customer = customer
        self.delivery_method = delivery_method
        self.recipients = recipients

        if currency != original_currency:
            self.lines.all().delete()
            self.recalculate()

        self.save()


class InvoiceLine(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    description = models.CharField(max_length=255)
    quantity = models.BigIntegerField()
    currency = models.CharField(max_length=3)
    unit_amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    total_amount_excluding_tax = MoneyField(
        max_digits=19,
        decimal_places=2,
        currency_field_name="currency",
    )
    total_amount = MoneyField(
        max_digits=19,
        decimal_places=2,
        currency_field_name="currency",
    )
    total_discount_amount = MoneyField(
        max_digits=19,
        decimal_places=2,
        currency_field_name="currency",
    )
    total_tax_amount = MoneyField(
        max_digits=19,
        decimal_places=2,
        currency_field_name="currency",
    )
    total_tax_rate = models.DecimalField(max_digits=5, decimal_places=2)
    total_credit_amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    credit_quantity = models.BigIntegerField(default=0)
    outstanding_amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    outstanding_quantity = models.BigIntegerField(default=0)
    invoice = models.ForeignKey("Invoice", on_delete=models.CASCADE, related_name="lines")
    price = models.ForeignKey("prices.Price", on_delete=models.PROTECT, related_name="invoice_lines", null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = InvoiceLineManager()

    class Meta:
        ordering = ["created_at"]

    def recalculate(self) -> None:
        if self.price:
            self.unit_amount = self.price.calculate_unit_amount(self.quantity)
            amount = self.price.calculate_amount(self.quantity)
        else:
            amount = self.unit_amount * self.quantity

        # Calculate discounts

        total_discount_amount = zero(self.currency)
        total_amount_excluding_tax = amount
        discounts = self.discounts.select_related("coupon").for_lines()
        for discount in discounts:
            discount.amount = discount.calculate_amount(total_amount_excluding_tax)
            total_discount_amount += discount.amount
            total_amount_excluding_tax = max(total_amount_excluding_tax - discount.amount, zero(self.currency))

        InvoiceDiscount.objects.bulk_update(discounts, ["amount"])

        # Calculate taxes

        total_tax_amount = zero(self.currency)
        total_tax_rate = Decimal(0)
        taxes = self.taxes.select_related("tax_rate").for_lines()
        for tax in taxes:
            tax.amount = tax.calculate_amount(total_amount_excluding_tax)
            total_tax_amount += tax.amount
            total_tax_rate += tax.rate

        InvoiceTax.objects.bulk_update(taxes, ["amount"])

        # Final totals

        total_amount = total_amount_excluding_tax + total_tax_amount
        outstanding_amount = max(total_amount - self.total_credit_amount, zero(self.currency))
        outstanding_quantity = max(self.quantity - self.credit_quantity, 0)

        self.amount = clamp_money(amount)
        self.total_discount_amount = clamp_money(total_discount_amount)
        self.total_amount_excluding_tax = clamp_money(total_amount_excluding_tax)
        self.total_tax_amount = clamp_money(total_tax_amount)
        self.total_tax_rate = total_tax_rate
        self.total_amount = clamp_money(total_amount)
        self.outstanding_amount = clamp_money(outstanding_amount)
        self.outstanding_quantity = outstanding_quantity
        self.save(
            update_fields=[
                "unit_amount",
                "amount",
                "total_discount_amount",
                "total_amount_excluding_tax",
                "total_tax_amount",
                "total_tax_rate",
                "total_amount",
                "outstanding_amount",
                "outstanding_quantity",
            ]
        )

        self.invoice.recalculate()

    def add_tax(self, tax_rate: TaxRate) -> InvoiceTax:
        tax = self.taxes.create(
            invoice=self.invoice,
            tax_rate=tax_rate,
            name=tax_rate.name,
            description=tax_rate.description,
            rate=tax_rate.percentage,
            currency=self.currency,
            amount=zero(self.currency),
        )
        self.recalculate()
        tax.refresh_from_db()
        return tax

    def add_discount(self, coupon: Coupon) -> InvoiceDiscount:
        discount = self.discounts.create(
            invoice=self.invoice,
            coupon=coupon,
            currency=self.currency,
            amount=zero(self.currency),
        )
        self.recalculate()
        discount.refresh_from_db()
        return discount

    def apply_credit(self, amount: Money, quantity: int) -> None:
        self.total_credit_amount = clamp_money(amount)
        self.credit_quantity = quantity or 0
        self.outstanding_amount = clamp_money(max(self.total_amount - self.total_credit_amount, zero(self.currency)))
        self.outstanding_quantity = max(self.quantity - self.credit_quantity, 0)
        self.save(
            update_fields=[
                "total_credit_amount",
                "credit_quantity",
                "outstanding_amount",
                "outstanding_quantity",
            ]
        )

    def update(
        self,
        description: str,
        quantity: int,
        unit_amount: Decimal | None,
        price: Price | None,
    ) -> None:
        self.description = description
        self.quantity = quantity
        self.unit_amount = price.calculate_unit_amount(quantity) if price else unit_amount
        self.price = price
        self.save()
        self.recalculate()

        if self.price:
            self.price.mark_as_used()


class InvoiceDiscount(models.Model):  # type: ignore[django-manager-missing]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey("Invoice", on_delete=models.CASCADE, related_name="discounts")
    invoice_line = models.ForeignKey(
        "InvoiceLine",
        on_delete=models.CASCADE,
        related_name="discounts",
        null=True,
    )
    coupon = models.ForeignKey("coupons.Coupon", on_delete=models.PROTECT, related_name="invoice_discounts")
    currency = models.CharField(max_length=3)
    amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    created_at = models.DateTimeField(auto_now_add=True)

    objects = InvoiceDiscountManager()

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["invoice_line", "coupon"],
                condition=models.Q(invoice_line__isnull=False),
                name="unique_invoice_line_coupon",
            ),
            models.UniqueConstraint(
                fields=["invoice", "coupon"],
                condition=models.Q(invoice_line__isnull=True),
                name="unique_invoice_coupon",
            ),
        ]

    def calculate_amount(self, base_amount: Money) -> Money:
        if self.coupon.amount is not None:
            if self.coupon.amount <= zero(self.currency):
                return zero(self.currency)
            return min(self.coupon.amount, base_amount)

        if self.coupon.percentage is not None:
            percentage_amount = base_amount * (self.coupon.percentage / Decimal(100))
            if percentage_amount <= zero(self.currency):
                return zero(self.currency)
            return min(percentage_amount, base_amount)

        return zero(self.currency)


class InvoiceTax(models.Model):  # type: ignore[django-manager-missing]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey("Invoice", on_delete=models.CASCADE, related_name="taxes")
    invoice_line = models.ForeignKey(
        "InvoiceLine",
        on_delete=models.CASCADE,
        related_name="taxes",
        null=True,
    )
    tax_rate = models.ForeignKey("taxes.TaxRate", on_delete=models.SET_NULL, related_name="invoice_taxes", null=True)
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, null=True)
    rate = models.DecimalField(max_digits=5, decimal_places=2)
    currency = models.CharField(max_length=3)
    amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    created_at = models.DateTimeField(auto_now_add=True)

    objects = InvoiceTaxManager()

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["invoice_line", "tax_rate"],
                condition=models.Q(invoice_line__isnull=False, tax_rate__isnull=False),
                name="unique_invoice_line_tax_rate",
            ),
            models.UniqueConstraint(
                fields=["invoice", "tax_rate"],
                condition=models.Q(invoice_line__isnull=True, tax_rate__isnull=False),
                name="unique_invoice_tax_rate",
            ),
        ]

    def calculate_amount(self, base_amount: Money) -> Money:
        if self.rate <= 0:
            return zero(self.currency)

        return base_amount * (self.rate / Decimal(100))
