from __future__ import annotations

import uuid
from collections.abc import Iterable, Mapping
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import DecimalField, F, IntegerField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.functional import cached_property
from djmoney import settings as djmoney_settings
from djmoney.models.fields import MoneyField
from djmoney.money import Money

from openinvoice.addresses.models import Address
from openinvoice.core.calculations import aggregate_allocations, allocate_proportionally, calculate_tax_amounts, zero
from openinvoice.coupons.models import Coupon
from openinvoice.credit_notes.choices import CreditNoteStatus
from openinvoice.customers.models import Customer
from openinvoice.integrations.choices import PaymentProvider
from openinvoice.numbering_systems.models import NumberingSystem
from openinvoice.payments.models import Payment
from openinvoice.prices.models import Price
from openinvoice.shipping_rates.models import ShippingRate
from openinvoice.tax_rates.models import TaxRate

from .choices import (
    InvoiceDeliveryMethod,
    InvoiceDiscountSource,
    InvoiceDocumentAudience,
    InvoiceStatus,
    InvoiceTaxBehavior,
    InvoiceTaxSource,
)
from .managers import (
    InvoiceAccountManager,
    InvoiceCustomerManager,
    InvoiceDocumentManager,
    InvoiceLineManager,
    InvoiceManager,
)
from .querysets import (
    InvoiceDiscountAllocationQuerySet,
    InvoiceLineQuerySet,
    InvoiceQuerySet,
    InvoiceTaxAllocationQuerySet,
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
    address = models.OneToOneField(
        "addresses.Address",
        on_delete=models.PROTECT,
        related_name="invoice_customer_address",
    )
    logo = models.ForeignKey(
        "files.File",
        on_delete=models.SET_NULL,
        null=True,
        related_name="invoice_customer_logo",
    )
    tax_ids = models.ManyToManyField("tax_ids.TaxId", related_name="invoice_customers")

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
    tax_ids = models.ManyToManyField("tax_ids.TaxId", related_name="invoice_accounts")

    objects = InvoiceAccountManager()


class InvoiceHead(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    root = models.OneToOneField("invoices.Invoice", on_delete=models.PROTECT, null=True, related_name="+")
    current = models.OneToOneField("invoices.Invoice", on_delete=models.PROTECT, null=True, related_name="+")
    updated_at = models.DateTimeField(auto_now=True, null=True)


class Invoice(models.Model):  # type: ignore[django-manager-missing]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    number = models.CharField(max_length=255, null=True)
    numbering_system = models.ForeignKey(
        "numbering_systems.NumberingSystem", on_delete=models.PROTECT, related_name="invoices", null=True
    )
    currency = models.CharField(max_length=3, choices=djmoney_settings.CURRENCY_CHOICES)
    status = models.CharField(max_length=50, choices=InvoiceStatus.choices)
    issue_date = models.DateField(null=True)
    due_date = models.DateField(null=True)
    net_payment_term = models.PositiveIntegerField(default=7)
    invoice_customer = models.OneToOneField(
        "InvoiceCustomer",
        on_delete=models.PROTECT,
        null=True,
        related_name="invoice",
    )
    invoice_account = models.OneToOneField(
        "InvoiceAccount",
        on_delete=models.PROTECT,
        null=True,
        related_name="invoice",
    )
    customer = models.ForeignKey("customers.Customer", on_delete=models.PROTECT, related_name="invoices")
    account = models.ForeignKey("accounts.Account", on_delete=models.PROTECT, related_name="invoices")
    subtotal_amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    total_discount_amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    total_excluding_tax_amount = MoneyField(
        max_digits=19,
        decimal_places=2,
        currency_field_name="currency",
    )
    shipping_amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
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
    metadata = models.JSONField(default=dict)
    payment_provider = models.CharField(max_length=50, choices=PaymentProvider.choices, null=True)
    payment_connection_id = models.UUIDField(null=True)
    delivery_method = models.CharField(
        max_length=20,
        choices=InvoiceDeliveryMethod.choices,
        default=InvoiceDeliveryMethod.MANUAL,
    )
    tax_behavior = models.CharField(
        max_length=20,
        choices=InvoiceTaxBehavior.choices,
        default=InvoiceTaxBehavior.AUTOMATIC,
    )
    recipients = ArrayField(
        base_field=models.EmailField(max_length=254),
        default=list,
        blank=True,
    )
    comments = models.ManyToManyField("comments.Comment", related_name="invoices")
    coupons = models.ManyToManyField("coupons.Coupon", through="InvoiceCoupon", related_name="+")
    tax_rates = models.ManyToManyField("tax_rates.TaxRate", through="InvoiceTaxRate", related_name="+")
    shipping = models.OneToOneField(
        "InvoiceShipping",
        on_delete=models.SET_NULL,
        null=True,
        related_name="invoice",
    )
    head = models.ForeignKey(InvoiceHead, on_delete=models.PROTECT, related_name="revisions")
    previous_revision = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        related_name="revisions",
        null=True,
    )

    objects = InvoiceManager.from_queryset(InvoiceQuerySet)()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["account_id", "number"], name="account_id_number_idx"),
            models.Index(fields=["head_id"]),
            models.Index(fields=["previous_revision_id"]),
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
            models.UniqueConstraint(
                name="uniq_single_next_revision",
                fields=["previous_revision"],
                condition=Q(previous_revision__isnull=False),
            ),
        ]

    @property
    def is_draft(self) -> bool:
        return self.status == InvoiceStatus.DRAFT

    @property
    def effective_customer(self):
        return self.invoice_customer or self.customer

    @property
    def effective_account(self):
        return self.invoice_account or self.account

    @property
    def effective_tax_behavior(self) -> InvoiceTaxBehavior:
        if self.tax_behavior != InvoiceTaxBehavior.AUTOMATIC:
            return InvoiceTaxBehavior(self.tax_behavior)

        if self.currency.upper() in {"USD", "CAD"}:
            return InvoiceTaxBehavior.EXCLUSIVE
        return InvoiceTaxBehavior.INCLUSIVE

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
    def effective_due_date(self) -> date:
        if self.due_date is not None:
            return self.due_date

        return timezone.now().date() + relativedelta(days=self.net_payment_term)

    @property
    def discounts(self) -> list[dict[str, Any]]:
        allocations = [
            allocation
            for allocation in self.discount_allocations.all()
            if allocation.source == InvoiceDiscountSource.INVOICE
        ]
        return aggregate_allocations(
            allocations,
            key=lambda allocation: allocation.coupon_id,
            build=lambda allocation: {
                "coupon_id": allocation.coupon_id,
                "name": allocation.coupon.name,
                "amount": allocation.amount,
            },
            order=lambda allocation: (getattr(allocation, "position", 0)),
        )

    @property
    def total_discounts(self) -> list[dict[str, Any]]:
        allocations = list(self.discount_allocations.all())
        source_order = {
            InvoiceDiscountSource.LINE: 0,
            InvoiceDiscountSource.INVOICE: 1,
        }
        return aggregate_allocations(
            allocations,
            key=lambda allocation: allocation.coupon_id,
            build=lambda allocation: {
                "coupon_id": allocation.coupon_id,
                "name": allocation.coupon.name,
                "amount": allocation.amount,
            },
            order=lambda allocation: (source_order[allocation.source], getattr(allocation, "position", 0)),
        )

    @property
    def taxes(self) -> list[dict[str, Any]]:
        allocations = [
            allocation for allocation in self.tax_allocations.all() if allocation.source == InvoiceTaxSource.INVOICE
        ]
        return aggregate_allocations(
            allocations,
            key=lambda allocation: allocation.tax_rate_id,
            build=lambda allocation: {
                "tax_rate_id": allocation.tax_rate_id,
                "name": allocation.tax_rate.name,
                "percentage": allocation.tax_rate.percentage,
                "amount": allocation.amount,
            },
            order=lambda allocation: (getattr(allocation, "position", 0)),
        )

    @property
    def total_taxes(self) -> list[dict[str, Any]]:
        allocations = list(self.tax_allocations.all())
        source_order = {
            InvoiceTaxSource.LINE: 0,
            InvoiceTaxSource.SHIPPING: 1,
            InvoiceTaxSource.INVOICE: 2,
        }
        return aggregate_allocations(
            allocations,
            key=lambda allocation: allocation.tax_rate_id,
            build=lambda allocation: {
                "tax_rate_id": allocation.tax_rate_id,
                "name": allocation.tax_rate.name,
                "percentage": allocation.tax_rate.percentage,
                "amount": allocation.amount,
            },
            order=lambda allocation: (source_order[allocation.source], getattr(allocation, "position", 0)),
        )

    @property
    def has_line_taxes(self) -> bool:
        return any(allocation.source == InvoiceTaxSource.LINE for allocation in self.tax_allocations.all())

    def calculate_outstanding_amount(self) -> Money:
        return max(
            self.total_amount - self.total_paid_amount - self.total_credit_amount,
            zero(self.currency),
        )

    def recalculate(self) -> None:  # noqa: C901
        # Cleanup existing calculations
        self.discount_allocations.all().delete()
        self.tax_allocations.all().delete()

        lines = list(self.lines.select_related("price").all())
        invoice_tax_rates = list(self.tax_rates.order_by("invoice_tax_rates__position"))

        # Calculate base

        for line in lines:
            line.amount = line.price.calculate_amount(line.quantity) if line.price else line.unit_amount * line.quantity
            line_tax_rates = list(line.tax_rates.order_by("invoice_line_tax_rates__position"))
            tax_rates = line_tax_rates if line_tax_rates else invoice_tax_rates
            line.total_tax_rate = sum((tax_rate.percentage for tax_rate in tax_rates), Decimal(0))
            line.unit_excluding_tax_amount = line.unit_amount / line.tax_multiplier
            line.subtotal_amount = line.amount
            line.total_taxable_amount = line.amount
            line.total_discount_amount = zero(self.currency)
            line.total_tax_amount = zero(self.currency)

        # Calculate line discounts

        discountable_lines = []
        for line in lines:
            coupons = list(line.coupons.order_by("invoice_line_coupons__position"))

            if coupons:
                # Calculate discounts for line-level coupons
                for coupon in coupons:
                    discount_amount = coupon.calculate_amount(line.subtotal_amount)

                    if discount_amount.amount <= 0:
                        continue

                    line.subtotal_amount -= discount_amount
                    line.total_taxable_amount -= discount_amount
                    line.total_discount_amount += discount_amount
                    line.add_discount_allocation(discount_amount, coupon, InvoiceDiscountSource.LINE)
            else:
                # Accumulate invoice-level discountable lines for later discount calculation
                discountable_lines.append(line)

        # Calculate invoice discounts

        total_taxable_amount = sum(
            (line.total_taxable_amount for line in discountable_lines),
            start=zero(self.currency),
        )

        for coupon in list(self.coupons.order_by("invoice_coupons__position")):
            if total_taxable_amount.amount <= 0 or not discountable_lines:
                break

            discount_amount = coupon.calculate_amount(total_taxable_amount)
            if discount_amount.amount <= 0:
                continue

            bases = [line.total_taxable_amount for line in discountable_lines]
            discount_shares = allocate_proportionally(discount_amount, bases=bases)

            for line, share_amount in zip(discountable_lines, discount_shares, strict=False):
                share_amount = min(share_amount, line.total_taxable_amount)
                if share_amount.amount <= 0:
                    continue

                total_taxable_amount -= share_amount
                line.total_taxable_amount -= share_amount
                line.total_discount_amount += share_amount
                line.add_discount_allocation(share_amount, coupon, InvoiceDiscountSource.INVOICE)

        # Calculate taxes

        for line in lines:
            line_tax_rates = list(line.tax_rates.order_by("invoice_line_tax_rates__position"))
            tax_rates = line_tax_rates if line_tax_rates else invoice_tax_rates
            line.total_excluding_tax_amount = line.total_taxable_amount / line.tax_multiplier

            source = InvoiceTaxSource.LINE if line_tax_rates else InvoiceTaxSource.INVOICE
            tax_amounts = calculate_tax_amounts(
                base_amount=line.total_excluding_tax_amount,
                taxable_amount=line.total_taxable_amount,
                tax_multiplier=line.tax_multiplier,
                tax_rates=tax_rates,
            )

            line.total_tax_amount = zero(self.currency)
            for tax_rate, tax_amount in zip(tax_rates, tax_amounts, strict=False):
                if tax_amount.amount <= 0:
                    continue

                line.total_tax_amount += tax_amount
                line.add_tax_allocations(tax_amount, tax_rate, source)

            line.total_amount = line.total_excluding_tax_amount + line.total_tax_amount
            line.outstanding_amount = line.total_amount
            line.outstanding_quantity = line.quantity

        # Persist line calculations

        InvoiceLine.objects.bulk_update(
            lines,
            fields=[
                "unit_amount",
                "unit_excluding_tax_amount",
                "amount",
                "subtotal_amount",
                "total_discount_amount",
                "total_taxable_amount",
                "total_excluding_tax_amount",
                "total_tax_amount",
                "total_tax_rate",
                "total_amount",
                "outstanding_amount",
                "outstanding_quantity",
            ],
        )

        # Calculate total

        subtotal_amount = sum([line.subtotal_amount for line in lines], zero(self.currency))
        total_discount_amount = sum([line.total_discount_amount for line in lines], zero(self.currency))
        total_excluding_tax_amount = sum([line.total_excluding_tax_amount for line in lines], zero(self.currency))
        total_tax_amount = sum([line.total_tax_amount for line in lines], zero(self.currency))
        total_amount = total_excluding_tax_amount + total_tax_amount

        # Calculate shipping

        shipping_amount = zero(self.currency)
        if self.shipping:
            self.shipping.recalculate()
            shipping_amount = self.shipping.amount
            total_excluding_tax_amount += self.shipping.total_excluding_tax_amount
            total_tax_amount += self.shipping.total_tax_amount
            total_amount += self.shipping.total_amount

        self.subtotal_amount = subtotal_amount
        self.total_discount_amount = total_discount_amount
        self.total_excluding_tax_amount = total_excluding_tax_amount
        self.shipping_amount = shipping_amount
        self.total_tax_amount = total_tax_amount
        self.total_amount = total_amount
        self.outstanding_amount = self.calculate_outstanding_amount()
        self.save(
            update_fields=[
                "subtotal_amount",
                "total_discount_amount",
                "total_excluding_tax_amount",
                "shipping_amount",
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
        self.total_credit_amount = total_credit_amount
        self.outstanding_amount = self.calculate_outstanding_amount()
        self.save(update_fields=["total_credit_amount", "outstanding_amount", "updated_at"])

    def recalculate_paid(self) -> None:
        total_paid_amount = self.payments.succeeded().aggregate(
            total=Coalesce(Sum("amount"), Value(0), output_field=DecimalField(max_digits=19, decimal_places=2))
        )["total"]

        self.total_paid_amount = Money(total_paid_amount or 0, self.currency)
        self.outstanding_amount = self.calculate_outstanding_amount()
        self.save()

        if self.outstanding_amount.amount == 0:
            self.mark_paid()

    def set_coupons(self, coupons: Iterable[Coupon]) -> None:
        self.coupons.clear()
        self.coupons.through.objects.bulk_create(
            InvoiceCoupon(invoice=self, coupon=coupon, position=idx) for idx, coupon in enumerate(coupons)
        )

    def set_tax_rates(self, tax_rates: Iterable[TaxRate]) -> None:
        self.tax_rates.clear()
        self.tax_rates.through.objects.bulk_create(
            InvoiceTaxRate(invoice=self, tax_rate=tax_rate, position=idx) for idx, tax_rate in enumerate(tax_rates)
        )

    def add_shipping(self, shipping_rate: ShippingRate, tax_rates: list[TaxRate]) -> InvoiceShipping:
        shipping = InvoiceShipping.objects.create(
            currency=self.currency,
            amount=shipping_rate.amount,
            total_excluding_tax_amount=zero(self.currency),
            total_tax_amount=zero(self.currency),
            total_tax_rate=Decimal(0),
            total_amount=zero(self.currency),
            shipping_rate=shipping_rate,
        )
        self.shipping = shipping
        self.save(update_fields=["shipping_id"])

        shipping.set_tax_rates(tax_rates)

        return shipping

    def finalize(self) -> None:
        self.status = InvoiceStatus.OPEN
        self.opened_at = timezone.now()
        self.issue_date = self.issue_date or timezone.now().date()
        self.due_date = self.due_date or timezone.now().date() + relativedelta(days=self.net_payment_term)
        self.invoice_customer = InvoiceCustomer.objects.from_customer(self.customer)
        self.invoice_account = InvoiceAccount.objects.from_account(self.account)

        if self.shipping:
            self.shipping.name = self.customer.shipping_name
            self.shipping.phone = self.customer.shipping_phone
            self.shipping.address = Address.objects.from_address(self.customer.shipping_address)
            self.shipping.save(update_fields=["name", "phone", "address"])

        if self.number is None and self.numbering_system is not None:
            self.number = self.generate_number()

        self.save()

        if self.previous_revision and self.previous_revision.status == InvoiceStatus.OPEN:
            self.previous_revision.void()

        self.head.current = self
        self.head.save()

        if not (self.lines.exists() and self.outstanding_amount.amount > 0):
            self.mark_paid()
        elif self.payment_provider and self.payment_connection_id:
            Payment.objects.checkout_invoice(invoice=self)

    def void(self) -> None:
        self.status = InvoiceStatus.VOIDED
        self.voided_at = timezone.now()
        self.save()

    def mark_paid(self, timestamp: datetime | None = None) -> None:
        self.status = InvoiceStatus.PAID
        self.paid_at = timestamp or timezone.now()
        self.outstanding_amount = zero(self.currency)
        self.save()

    # TODO: fix typing
    def update(
        self,
        customer: Customer,
        currency: str,
        net_payment_term: int,
        number: str | None = None,
        numbering_system: NumberingSystem | None = None,
        issue_date: date | None = None,
        due_date: date | None = None,
        metadata: Mapping[str, Any] | None = None,
        payment_provider: PaymentProvider | None = None,
        payment_connection_id: uuid.UUID | None = None,
        delivery_method: InvoiceDeliveryMethod | None = None,
        recipients: list[str] | None = None,
        tax_behavior: InvoiceTaxBehavior | None = None,
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
        self.due_date = due_date
        self.net_payment_term = net_payment_term
        self.metadata = dict(metadata or self.metadata)
        self.payment_provider = payment_provider
        self.payment_connection_id = payment_connection_id
        self.customer = customer
        self.delivery_method = delivery_method
        self.recipients = recipients
        self.tax_behavior = tax_behavior or self.tax_behavior

        if currency != original_currency:
            self.lines.all().delete()

        self.save()


class InvoiceDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey("Invoice", on_delete=models.CASCADE, related_name="documents")
    audience = ArrayField(
        models.CharField(max_length=20, choices=InvoiceDocumentAudience.choices),
        default=list,
    )
    language = models.CharField(max_length=10, choices=settings.LANGUAGES)
    footer = models.CharField(max_length=600, null=True, blank=True)
    memo = models.CharField(max_length=600, null=True, blank=True)
    custom_fields = models.JSONField(default=dict)
    file = models.OneToOneField(
        "files.File",
        on_delete=models.SET_NULL,
        null=True,
        related_name="invoice_document_pdf",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = InvoiceDocumentManager()

    def update(
        self,
        language: str,
        audience: list[InvoiceDocumentAudience],
        footer: str | None,
        memo: str | None,
        custom_fields: dict[str, Any],
    ) -> None:
        self.language = language
        self.audience = audience
        self.footer = footer
        self.memo = memo
        self.custom_fields = custom_fields
        self.save()

    class Meta:
        indexes = [
            models.Index(fields=["invoice_id"]),
        ]


class InvoiceLine(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    description = models.CharField(max_length=255)
    quantity = models.BigIntegerField()
    currency = models.CharField(max_length=3, choices=djmoney_settings.CURRENCY_CHOICES)
    unit_amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    unit_excluding_tax_amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    subtotal_amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    total_discount_amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    total_taxable_amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    total_excluding_tax_amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    total_tax_amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    total_tax_rate = models.DecimalField(max_digits=5, decimal_places=2)
    total_amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    total_credit_amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    credit_quantity = models.BigIntegerField(default=0)
    outstanding_amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    outstanding_quantity = models.BigIntegerField(default=0)
    invoice = models.ForeignKey("Invoice", on_delete=models.CASCADE, related_name="lines")
    coupons = models.ManyToManyField("coupons.Coupon", through="InvoiceLineCoupon", related_name="+")
    tax_rates = models.ManyToManyField("tax_rates.TaxRate", through="InvoiceLineTaxRate", related_name="+")
    price = models.ForeignKey("prices.Price", on_delete=models.PROTECT, related_name="invoice_lines", null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = InvoiceLineManager.from_queryset(InvoiceLineQuerySet)()

    class Meta:
        ordering = ["created_at"]

    @property
    def tax_multiplier(self) -> Decimal:
        if self.invoice.effective_tax_behavior == InvoiceTaxBehavior.INCLUSIVE and self.total_tax_rate > 0:
            return Decimal(1) + (self.total_tax_rate / Decimal(100))
        return Decimal(1)

    def set_coupons(self, coupons: Iterable[Coupon]) -> None:
        self.coupons.clear()
        self.coupons.through.objects.bulk_create(
            InvoiceLineCoupon(invoice_line=self, coupon=coupon, position=idx) for idx, coupon in enumerate(coupons)
        )

    def set_tax_rates(self, tax_rates: Iterable[TaxRate]) -> None:
        self.tax_rates.clear()
        self.tax_rates.through.objects.bulk_create(
            InvoiceLineTaxRate(invoice_line=self, tax_rate=tax_rate, position=idx)
            for idx, tax_rate in enumerate(tax_rates)
        )

    def add_discount_allocation(
        self, amount: Money, coupon: Coupon, source: InvoiceDiscountSource
    ) -> InvoiceDiscountAllocation:
        return self.discount_allocations.create(
            invoice=self.invoice,
            invoice_line=self,
            coupon=coupon,
            source=source,
            currency=self.currency,
            amount=amount,
        )

    def add_tax_allocations(self, amount: Money, tax_rate: TaxRate, source: InvoiceTaxSource) -> InvoiceTaxAllocation:
        return self.tax_allocations.create(
            invoice=self.invoice,
            invoice_line=self,
            tax_rate=tax_rate,
            source=source,
            currency=self.currency,
            amount=amount,
        )

    @property
    def discounts(self) -> list[dict[str, Any]]:
        allocations = [
            allocation
            for allocation in self.discount_allocations.all()
            if allocation.source == InvoiceDiscountSource.LINE
        ]
        return aggregate_allocations(
            allocations,
            key=lambda allocation: allocation.coupon_id,
            build=lambda allocation: {
                "coupon_id": allocation.coupon_id,
                "name": allocation.coupon.name,
                "amount": allocation.amount,
            },
            order=lambda allocation: (getattr(allocation, "position", 0)),
        )

    @property
    def total_discounts(self) -> list[dict[str, Any]]:
        allocations = list(self.discount_allocations.all())
        source_order = {
            InvoiceDiscountSource.LINE: 0,
            InvoiceDiscountSource.INVOICE: 1,
        }
        return aggregate_allocations(
            allocations,
            key=lambda allocation: allocation.coupon_id,
            build=lambda allocation: {
                "coupon_id": allocation.coupon_id,
                "name": allocation.coupon.name,
                "amount": allocation.amount,
            },
            order=lambda allocation: (source_order[allocation.source], getattr(allocation, "position", 0)),
        )

    @property
    def taxes(self) -> list[dict[str, Any]]:
        allocations = [
            allocation for allocation in self.tax_allocations.all() if allocation.source == InvoiceTaxSource.LINE
        ]
        return aggregate_allocations(
            allocations,
            key=lambda allocation: allocation.tax_rate_id,
            build=lambda allocation: {
                "tax_rate_id": allocation.tax_rate_id,
                "name": allocation.tax_rate.name,
                "percentage": allocation.tax_rate.percentage,
                "amount": allocation.amount,
            },
            order=lambda allocation: (getattr(allocation, "position", 0)),
        )

    @property
    def total_taxes(self) -> list[dict[str, Any]]:
        allocations = list(self.tax_allocations.all())
        source_order = {
            InvoiceTaxSource.LINE: 0,
            InvoiceTaxSource.INVOICE: 1,
        }
        return aggregate_allocations(
            allocations,
            key=lambda allocation: allocation.tax_rate_id,
            build=lambda allocation: {
                "tax_rate_id": allocation.tax_rate_id,
                "name": allocation.tax_rate.name,
                "percentage": allocation.tax_rate.percentage,
                "amount": allocation.amount,
            },
            order=lambda allocation: (
                source_order[allocation.source],
                getattr(allocation, "position", 0),
                allocation.tax_rate_id,
            ),
        )

    def apply_credit(self, amount: Money, quantity: int) -> None:
        self.total_credit_amount = amount
        self.credit_quantity = quantity
        self.outstanding_amount = max(self.total_amount - self.total_credit_amount, zero(self.currency))
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


class InvoiceShipping(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, null=True)
    phone = models.CharField(max_length=255, null=True)
    address = models.OneToOneField(
        "addresses.Address",
        on_delete=models.SET_NULL,
        null=True,
        related_name="invoice_shipping_address",
    )
    currency = models.CharField(max_length=3, choices=djmoney_settings.CURRENCY_CHOICES)
    amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    total_excluding_tax_amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    total_tax_amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    total_tax_rate = models.DecimalField(max_digits=5, decimal_places=2)
    total_amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    created_at = models.DateTimeField(auto_now_add=True)
    shipping_rate = models.ForeignKey("shipping_rates.ShippingRate", on_delete=models.PROTECT)
    tax_rates = models.ManyToManyField("tax_rates.TaxRate", through="InvoiceShippingTaxRate", related_name="+")

    @property
    def effective_name(self) -> str | None:
        return self.invoice.customer.shipping_name if self.invoice.is_draft else self.name

    @property
    def effective_phone(self) -> str | None:
        return self.invoice.customer.shipping_phone if self.invoice.is_draft else self.phone

    @property
    def effective_address(self) -> Address | None:
        return self.invoice.customer.shipping_address if self.invoice.is_draft else self.address

    @property
    def tax_multiplier(self) -> Decimal:
        if self.invoice.effective_tax_behavior == InvoiceTaxBehavior.INCLUSIVE and self.total_tax_rate > 0:
            return Decimal(1) + (self.total_tax_rate / Decimal(100))
        return Decimal(1)

    @property
    def total_taxes(self) -> list[dict[str, Any]]:
        allocations = [
            allocation for allocation in self.tax_allocations.all() if allocation.source == InvoiceTaxSource.SHIPPING
        ]
        return aggregate_allocations(
            allocations,
            key=lambda allocation: allocation.tax_rate_id,
            build=lambda allocation: {
                "tax_rate_id": allocation.tax_rate_id,
                "name": allocation.tax_rate.name,
                "percentage": allocation.tax_rate.percentage,
                "amount": allocation.amount,
            },
            order=lambda allocation: (getattr(allocation, "position", 0)),
        )

    def set_tax_rates(self, tax_rates: Iterable[TaxRate]) -> None:
        self.tax_rates.clear()
        self.tax_rates.through.objects.bulk_create(
            InvoiceShippingTaxRate(invoice_shipping=self, tax_rate=tax_rate, position=idx)
            for idx, tax_rate in enumerate(tax_rates)
        )

    def add_tax_allocation(self, amount: Money, tax_rate: TaxRate) -> InvoiceTaxAllocation:
        return self.tax_allocations.create(
            invoice=self.invoice,
            invoice_shipping=self,
            tax_rate=tax_rate,
            source=InvoiceTaxSource.SHIPPING,
            currency=self.currency,
            amount=amount,
        )

    def recalculate(self) -> None:
        tax_rates = list(self.tax_rates.order_by("invoice_shipping_tax_rates__position"))
        self.total_tax_rate = sum((tax_rate.percentage for tax_rate in tax_rates), Decimal(0))
        self.total_excluding_tax_amount = self.amount / self.tax_multiplier
        self.total_tax_amount = zero(self.currency)

        tax_amounts = calculate_tax_amounts(
            base_amount=self.total_excluding_tax_amount,
            taxable_amount=self.amount,
            tax_multiplier=self.tax_multiplier,
            tax_rates=tax_rates,
        )

        for tax_rate, tax_amount in zip(tax_rates, tax_amounts, strict=False):
            if tax_amount.amount <= 0:
                continue

            self.total_tax_amount += tax_amount
            self.add_tax_allocation(tax_amount, tax_rate)

        self.total_amount = self.total_excluding_tax_amount + self.total_tax_amount
        self.save(
            update_fields=[
                "total_excluding_tax_amount",
                "total_tax_rate",
                "total_tax_amount",
                "total_amount",
            ]
        )


class InvoiceCoupon(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey("Invoice", on_delete=models.CASCADE, related_name="invoice_coupons")
    coupon = models.ForeignKey("coupons.Coupon", on_delete=models.PROTECT, related_name="invoice_coupons")
    position = models.PositiveIntegerField()

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(fields=["invoice", "coupon"], name="unique_invoice_coupon_link"),
            models.UniqueConstraint(fields=["invoice", "position"], name="unique_invoice_coupon_position"),
        ]


class InvoiceLineCoupon(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice_line = models.ForeignKey("InvoiceLine", on_delete=models.CASCADE, related_name="invoice_line_coupons")
    coupon = models.ForeignKey("coupons.Coupon", on_delete=models.PROTECT, related_name="invoice_line_coupons")
    position = models.PositiveIntegerField()

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(fields=["invoice_line", "coupon"], name="unique_invoice_line_coupon_link"),
            models.UniqueConstraint(fields=["invoice_line", "position"], name="unique_invoice_line_coupon_position"),
        ]


class InvoiceTaxRate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey("Invoice", on_delete=models.CASCADE, related_name="invoice_tax_rates")
    tax_rate = models.ForeignKey("tax_rates.TaxRate", on_delete=models.PROTECT, related_name="invoice_tax_rates")
    position = models.PositiveIntegerField()

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(fields=["invoice", "tax_rate"], name="unique_invoice_tax_rate_link"),
            models.UniqueConstraint(fields=["invoice", "position"], name="unique_invoice_tax_rate_position"),
        ]


class InvoiceLineTaxRate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice_line = models.ForeignKey("InvoiceLine", on_delete=models.CASCADE, related_name="invoice_line_tax_rates")
    tax_rate = models.ForeignKey("tax_rates.TaxRate", on_delete=models.PROTECT, related_name="invoice_line_tax_rates")
    position = models.PositiveIntegerField()

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(fields=["invoice_line", "tax_rate"], name="unique_invoice_line_tax_rate_link"),
            models.UniqueConstraint(fields=["invoice_line", "position"], name="unique_invoice_line_tax_rate_position"),
        ]


class InvoiceShippingTaxRate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice_shipping = models.ForeignKey(
        "InvoiceShipping", on_delete=models.CASCADE, related_name="invoice_shipping_tax_rates"
    )
    tax_rate = models.ForeignKey(
        "tax_rates.TaxRate", on_delete=models.PROTECT, related_name="invoice_shipping_tax_rates"
    )
    position = models.PositiveIntegerField()

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(
                fields=["invoice_shipping", "tax_rate"],
                name="unique_invoice_shipping_tax_rate_link",
            ),
            models.UniqueConstraint(
                fields=["invoice_shipping", "position"],
                name="unique_invoice_shipping_tax_rate_position",
            ),
        ]


class InvoiceDiscountAllocation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey("Invoice", on_delete=models.CASCADE, related_name="discount_allocations")
    invoice_line = models.ForeignKey("InvoiceLine", on_delete=models.CASCADE, related_name="discount_allocations")
    coupon = models.ForeignKey("coupons.Coupon", on_delete=models.PROTECT, related_name="+")
    source = models.CharField(max_length=20, choices=InvoiceDiscountSource.choices)
    currency = models.CharField(max_length=3, choices=djmoney_settings.CURRENCY_CHOICES)
    amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    created_at = models.DateTimeField(auto_now_add=True)

    objects = InvoiceDiscountAllocationQuerySet.as_manager()

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["invoice_id", "source"]),
            models.Index(fields=["invoice_line_id", "source"]),
            models.Index(fields=["invoice_id", "coupon_id"]),
            models.Index(fields=["invoice_line_id", "coupon_id"]),
        ]
        constraints = [
            models.CheckConstraint(
                name="discount_allocation_positive_amount",
                condition=Q(amount__gt=0),
            ),
        ]


class InvoiceTaxAllocation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey("Invoice", on_delete=models.CASCADE, related_name="tax_allocations")
    invoice_line = models.ForeignKey(
        "InvoiceLine",
        on_delete=models.CASCADE,
        related_name="tax_allocations",
        null=True,
    )
    invoice_shipping = models.ForeignKey(
        "InvoiceShipping",
        on_delete=models.CASCADE,
        related_name="tax_allocations",
        null=True,
    )
    tax_rate = models.ForeignKey("tax_rates.TaxRate", on_delete=models.PROTECT, related_name="+")
    source = models.CharField(max_length=20, choices=InvoiceTaxSource.choices)
    currency = models.CharField(max_length=3, choices=djmoney_settings.CURRENCY_CHOICES)
    amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    created_at = models.DateTimeField(auto_now_add=True)

    objects = InvoiceTaxAllocationQuerySet.as_manager()

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["invoice_id", "source"]),
            models.Index(fields=["invoice_id", "tax_rate_id"]),
            models.Index(fields=["invoice_line_id", "tax_rate_id"]),
            models.Index(fields=["invoice_shipping_id", "tax_rate_id"]),
        ]
        constraints = [
            # exactly one target: line XOR shipping
            models.CheckConstraint(
                name="tax_allocation_exactly_one_target",
                condition=(
                    (Q(invoice_line__isnull=False) & Q(invoice_shipping__isnull=True))
                    | (Q(invoice_line__isnull=True) & Q(invoice_shipping__isnull=False))
                ),
            ),
            models.CheckConstraint(
                name="tax_allocation_positive_amount",
                condition=Q(amount__gt=0),
            ),
        ]
