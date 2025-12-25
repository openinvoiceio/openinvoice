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
from common.calculations import calculate_percentage_amount, clamp_money, zero
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

    @staticmethod
    def _distribute_discount_to_taxed_lines(
        pre_discount_total: Money,
        taxed_line_total: Money,
        invoice_discount_amount: Money,
    ) -> Money:
        if pre_discount_total.amount <= 0 or taxed_line_total.amount <= 0 or invoice_discount_amount.amount <= 0:
            return clamp_money(taxed_line_total)

        ratio = taxed_line_total.amount / pre_discount_total.amount
        shared_discount = clamp_money(invoice_discount_amount * ratio)
        if shared_discount > taxed_line_total:
            shared_discount = taxed_line_total
        return clamp_money(max(taxed_line_total - shared_discount, zero(taxed_line_total.currency)))

    def calculate_outstanding_amount(self) -> Money:
        return max(
            self.total_amount - self.total_paid_amount - self.total_credit_amount,
            zero(self.currency),
        )

    def recalculate(self) -> None:
        subtotal = zero(self.currency)
        total_line_discount_amount = zero(self.currency)
        total_line_tax_amount = zero(self.currency)
        total_line_amount_excluding_tax = zero(self.currency)
        taxed_line_amount_excluding_tax = zero(self.currency)

        for line in self.lines.all():
            subtotal += line.amount
            total_line_discount_amount += line.total_discount_amount
            total_line_tax_amount += line.total_tax_amount
            total_line_amount_excluding_tax += line.total_amount_excluding_tax
            if line.taxes.all():
                taxed_line_amount_excluding_tax += line.total_amount_excluding_tax

        subtotal = clamp_money(subtotal)
        total_line_discount_amount = clamp_money(total_line_discount_amount)
        total_line_amount_excluding_tax = clamp_money(total_line_amount_excluding_tax)
        taxed_line_amount_excluding_tax = clamp_money(taxed_line_amount_excluding_tax)

        invoice_discount_amount, total_amount_excluding_tax = self.discounts.for_invoice().recalculate(
            total_line_amount_excluding_tax
        )
        total_amount_excluding_tax = clamp_money(total_amount_excluding_tax)

        taxed_line_amount_excluding_tax_after_discounts = self._distribute_discount_to_taxed_lines(
            total_line_amount_excluding_tax,
            taxed_line_amount_excluding_tax,
            invoice_discount_amount,
        )

        invoice_taxable_amount = clamp_money(
            max(
                total_amount_excluding_tax - taxed_line_amount_excluding_tax_after_discounts,
                zero(self.currency),
            )
        )

        invoice_tax_amount, _ = self.taxes.for_invoice().recalculate(invoice_taxable_amount)

        total_discount_amount = clamp_money(total_line_discount_amount + invoice_discount_amount)
        total_tax_amount = clamp_money(total_line_tax_amount + invoice_tax_amount)
        total_amount = clamp_money(total_amount_excluding_tax + total_tax_amount)

        self.subtotal_amount = subtotal
        self.total_discount_amount = total_discount_amount
        self.total_amount_excluding_tax = total_amount_excluding_tax
        self.total_tax_amount = total_tax_amount
        self.total_amount = total_amount
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
        elif self.payment_provider:
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
        """Recalculate cached totals for the invoice line and its parent invoice."""

        if self.price:
            amount = self.price.calculate_amount(self.quantity)
            self.unit_amount = self.price.calculate_unit_amount(self.quantity)
        else:
            amount = clamp_money(self.unit_amount * self.quantity)

        total_discount_amount, total_amount_excluding_tax = (
            self.discounts.select_related("coupon").for_lines().recalculate(amount)
        )

        total_tax_amount, total_tax_rate = self.taxes.for_lines().recalculate(total_amount_excluding_tax)

        self.amount = amount
        self.total_discount_amount = clamp_money(total_discount_amount)
        self.total_amount_excluding_tax = clamp_money(total_amount_excluding_tax)
        self.total_tax_amount = clamp_money(total_tax_amount)
        self.total_tax_rate = total_tax_rate
        self.total_amount = clamp_money(total_amount_excluding_tax + total_tax_amount)
        self.outstanding_amount = clamp_money(max(self.total_amount - self.total_credit_amount, zero(self.currency)))
        self.outstanding_quantity = max(self.quantity - self.credit_quantity, 0)
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

    @staticmethod
    def calculate_amount(base: Money, coupon: Coupon) -> Money:
        if coupon.amount is not None:
            if coupon.amount <= zero(base.currency):
                return zero(base.currency)
            return clamp_money(min(coupon.amount, base))

        if coupon.percentage is not None:
            percentage_amount = calculate_percentage_amount(base, coupon.percentage)
            return clamp_money(min(percentage_amount, base))

        return zero(base.currency)


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

    @staticmethod
    def calculate_amount(base: Money, rate: TaxRate | Decimal) -> Money:
        percentage = rate if isinstance(rate, Decimal) else rate.percentage

        if percentage <= 0:
            return zero(base.currency)

        return clamp_money(calculate_percentage_amount(base, percentage))
