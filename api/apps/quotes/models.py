from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from django.contrib.postgres.fields import ArrayField
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import models
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.functional import cached_property
from djmoney import settings as djmoney_settings
from djmoney.models.fields import MoneyField
from djmoney.money import Money

from apps.coupons.models import Coupon
from apps.customers.models import Customer
from apps.files.choices import FilePurpose
from apps.files.models import File
from apps.invoices.models import Invoice
from apps.numbering_systems.models import NumberingSystem
from apps.prices.models import Price
from apps.tax_rates.models import TaxRate
from common.calculations import calculate_percentage_amount, zero
from common.pdf import generate_pdf

from .choices import QuoteDeliveryMethod, QuoteStatus
from .managers import (
    QuoteAccountManager,
    QuoteCustomerManager,
    QuoteLineManager,
    QuoteManager,
)
from .querysets import QuoteDiscountQuerySet, QuoteQuerySet, QuoteTaxQuerySet


class QuoteCustomer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey("customers.Customer", on_delete=models.PROTECT, related_name="quotes_customers")
    name = models.CharField(max_length=255)
    legal_name = models.CharField(max_length=255, null=True)
    legal_number = models.CharField(max_length=255, null=True)
    email = models.CharField(max_length=255, null=True)
    phone = models.CharField(max_length=255, null=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    address = models.OneToOneField(
        "addresses.Address",
        on_delete=models.PROTECT,
        related_name="quote_customer_address",
    )
    logo = models.ForeignKey(
        "files.File",
        on_delete=models.SET_NULL,
        null=True,
        related_name="quote_customer_logo",
    )
    tax_ids = models.ManyToManyField("tax_ids.TaxId", related_name="quote_customers")

    objects = QuoteCustomerManager()


class QuoteAccount(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey("accounts.Account", on_delete=models.PROTECT, related_name="quotes_accounts")
    name = models.CharField(max_length=255)
    legal_name = models.CharField(max_length=255, null=True)
    legal_number = models.CharField(max_length=255, null=True)
    email = models.CharField(max_length=255, null=True)
    phone = models.CharField(max_length=255, null=True)
    address = models.OneToOneField(
        "addresses.Address",
        on_delete=models.PROTECT,
        related_name="quote_account_address",
    )
    logo = models.ForeignKey(
        "files.File",
        on_delete=models.SET_NULL,
        null=True,
        related_name="quote_account_logo",
    )
    tax_ids = models.ManyToManyField("tax_ids.TaxId", related_name="quote_accounts")

    objects = QuoteAccountManager()


class Quote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    number = models.CharField(max_length=255, null=True)
    numbering_system = models.ForeignKey(
        "numbering_systems.NumberingSystem",
        on_delete=models.PROTECT,
        related_name="quotes",
        null=True,
    )
    currency = models.CharField(max_length=3, choices=djmoney_settings.CURRENCY_CHOICES)
    status = models.CharField(max_length=50, choices=QuoteStatus.choices)
    issue_date = models.DateField(null=True)
    account = models.ForeignKey("accounts.Account", on_delete=models.PROTECT, related_name="quotes")
    customer = models.ForeignKey("customers.Customer", on_delete=models.PROTECT, related_name="quotes")
    footer = models.CharField(max_length=500, null=True, blank=True)
    description = models.CharField(max_length=500, null=True, blank=True)
    subtotal_amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    total_discount_amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    total_amount_excluding_tax = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    total_tax_amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    total_amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    metadata = models.JSONField(default=dict)
    custom_fields = models.JSONField(default=dict)
    delivery_method = models.CharField(
        max_length=20,
        choices=QuoteDeliveryMethod.choices,
        default=QuoteDeliveryMethod.MANUAL,
    )
    recipients = ArrayField(
        base_field=models.EmailField(max_length=254),
        default=list,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    opened_at = models.DateTimeField(null=True)
    accepted_at = models.DateTimeField(null=True)
    canceled_at = models.DateTimeField(null=True)
    pdf = models.OneToOneField("files.File", on_delete=models.SET_NULL, null=True, related_name="quotes_pdf")
    customer_on_quote = models.OneToOneField(
        "QuoteCustomer",
        on_delete=models.PROTECT,
        related_name="quote",
        null=True,
    )
    account_on_quote = models.OneToOneField(
        "QuoteAccount",
        on_delete=models.PROTECT,
        related_name="quote",
        null=True,
    )
    invoice = models.OneToOneField(
        "invoices.Invoice",
        on_delete=models.SET_NULL,
        related_name="quote",
        null=True,
    )

    objects = QuoteManager.from_queryset(QuoteQuerySet)()

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                name="quote_number_required_if_not_draft",
                condition=Q(status__in=[QuoteStatus.DRAFT, QuoteStatus.CANCELED])
                | (Q(number__isnull=False) & ~Q(number="")),
            )
        ]

    @property
    def effective_customer(self):
        if self.customer_on_quote_id:
            return self.customer_on_quote
        return self.customer

    @property
    def effective_account(self):
        if self.account_on_quote_id:
            return self.account_on_quote
        return self.account

    @cached_property
    def effective_number(self) -> str | None:
        if self.number is not None:
            return self.number
        return self.generate_number()

    def generate_number(self) -> str | None:
        if self.numbering_system is None:
            return None

        timestamp = timezone.now()
        start_at, end_at = self.numbering_system.calculate_bounds(effective_at=timestamp)

        query = Q(numbering_system=self.numbering_system) & ~Q(status=QuoteStatus.DRAFT)
        if start_at:
            query &= Q(opened_at__gte=start_at)
        if end_at:
            query &= Q(opened_at__lt=end_at)

        issued_count = Quote.objects.filter(query).count()

        draft_offset = 0
        if self.status == QuoteStatus.DRAFT:
            draft_query = Q(numbering_system=self.numbering_system, status=QuoteStatus.DRAFT)
            if start_at:
                draft_query &= Q(created_at__gte=start_at)
            if end_at:
                draft_query &= Q(created_at__lt=end_at)

            drafts = Quote.objects.filter(draft_query)
            earlier_condition = Q(created_at__lt=self.created_at) | (Q(created_at=self.created_at) & Q(pk__lt=self.pk))
            draft_offset = drafts.filter(earlier_condition).count()

        return self.numbering_system.render_number(count=issued_count + draft_offset, effective_at=timestamp)

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

        quote_discount_amount, total_amount_excluding_tax = self.discounts.for_quote().recalculate(
            total_line_amount_excluding_tax
        )

        taxed_line_amount_excluding_tax_after_discounts = self._distribute_discount_to_taxed_lines(
            total_line_amount_excluding_tax,
            taxed_line_amount_excluding_tax,
            quote_discount_amount,
        )

        quote_taxable_amount = max(
            total_amount_excluding_tax - taxed_line_amount_excluding_tax_after_discounts,
            zero(self.currency),
        )

        quote_tax_amount, _ = self.taxes.for_quote().recalculate(quote_taxable_amount)

        total_discount_amount = total_line_discount_amount + quote_discount_amount
        total_tax_amount = total_line_tax_amount + quote_tax_amount
        total_amount = total_amount_excluding_tax + total_tax_amount

        self.subtotal_amount = subtotal
        self.total_discount_amount = total_discount_amount
        self.total_amount_excluding_tax = total_amount_excluding_tax
        self.total_tax_amount = total_tax_amount
        self.total_amount = total_amount
        self.save(
            update_fields=[
                "subtotal_amount",
                "total_discount_amount",
                "total_amount_excluding_tax",
                "total_tax_amount",
                "total_amount",
                "updated_at",
            ]
        )

    def _distribute_discount_to_taxed_lines(
        self,
        total_line_amount_excluding_tax: Money,
        taxed_line_amount_excluding_tax: Money,
        discount_amount: Money,
    ) -> Money:
        # TODO: verify if this is correct, on invoices too
        if taxed_line_amount_excluding_tax == zero(self.currency):
            return zero(self.currency)

        if total_line_amount_excluding_tax == zero(self.currency):
            return zero(self.currency)

        ratio = taxed_line_amount_excluding_tax / total_line_amount_excluding_tax
        return discount_amount * ratio

    def add_tax(self, tax_rate: TaxRate):
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

    def add_discount(self, coupon: Coupon):
        discount = self.discounts.create(
            coupon=coupon,
            currency=self.currency,
            amount=zero(self.currency),
        )
        self.recalculate()
        discount.refresh_from_db()
        return discount

    def finalize(self):
        if not self.number:
            self.number = self.generate_number()

        self.customer_on_quote = QuoteCustomer.objects.from_customer(self.customer)
        self.account_on_quote = QuoteAccount.objects.from_account(self.account)

        self.status = QuoteStatus.OPEN
        self.opened_at = timezone.now()
        self.save()

        self.generate_pdf()

    def cancel(self):
        if self.status in {QuoteStatus.CANCELED, QuoteStatus.ACCEPTED}:
            return

        self.status = QuoteStatus.CANCELED
        self.canceled_at = timezone.now()
        self.save(update_fields=["status", "canceled_at", "updated_at"])

    def accept(self) -> Invoice:
        invoice = Invoice.objects.create_draft(
            account=self.account,
            customer=self.customer,
            number=None,
            numbering_system=self.numbering_system,
            currency=self.currency,
            issue_date=self.issue_date or timezone.now().date(),  # TODO: verify this
            sell_date=None,
            due_date=None,
            net_payment_term=None,
            custom_fields=self.custom_fields,
            footer=self.footer,
            # TODO: verify this, we probably want to differ quote and invoice copy descriptions
            # description=self.description,
        )

        for line in self.lines.all():
            # TODO: use InvoiceLine.create_line?
            new_line = invoice.lines.create(
                description=line.description,
                quantity=line.quantity,
                currency=invoice.currency,
                unit_amount=line.unit_amount,
                unit_excluding_tax_amount=zero(self.currency),
                price=line.price,
                total_tax_rate=line.total_tax_rate,
                amount=zero(invoice.currency),
                subtotal_amount=zero(invoice.currency),
                total_discount_amount=zero(invoice.currency),
                total_taxable_amount=zero(invoice.currency),
                total_excluding_tax_amount=zero(invoice.currency),
                total_tax_amount=zero(invoice.currency),
                total_amount=zero(invoice.currency),
                total_credit_amount=zero(invoice.currency),
                credit_quantity=0,
                outstanding_amount=zero(invoice.currency),
                outstanding_quantity=line.quantity,
            )
            # TODO: change it later
            new_line.set_coupons([discount.coupon for discount in line.discounts.all()])
            new_line.set_tax_rates([tax.tax_rate for tax in line.taxes.filter(tax_rate__isnull=False).all()])

        invoice.set_coupons([discount.coupon for discount in self.discounts.for_quote()])
        invoice.set_tax_rates([tax.tax_rate for tax in self.taxes.for_quote().filter(tax_rate__isnull=False).all()])
        self.invoice = invoice
        self.status = QuoteStatus.ACCEPTED
        self.accepted_at = timezone.now()
        self.save()

        return invoice

    def update(
        self,
        customer: Customer,
        number: str | None,
        numbering_system: NumberingSystem | None,
        currency: str,
        issue_date: date | None,
        metadata: dict,
        custom_fields: dict,
        footer: str | None,
        description: str | None,
        delivery_method: QuoteDeliveryMethod,
        recipients: list[str],
    ) -> None:
        resolved_numbering_system: NumberingSystem | None = None
        if number is None:
            resolved_numbering_system = (
                numbering_system or customer.invoice_numbering_system or self.account.invoice_numbering_system
            )

        # TODO: remove lines if customer is changed?

        self.customer = customer
        self.number = number
        self.numbering_system = resolved_numbering_system
        self.currency = currency
        self.issue_date = issue_date
        self.metadata = metadata
        self.custom_fields = custom_fields
        self.footer = footer
        self.description = description
        self.delivery_method = delivery_method
        self.recipients = recipients
        self.save()

    def generate_pdf(self) -> File:
        quote = (
            Quote.objects.filter(pk=self.pk)
            .select_related(
                "account__logo",
                "account__address",
                "customer",
                "customer__address",
                "customer__shipping__address",
                "customer__logo",
                "customer_on_quote__address",
                "customer_on_quote__logo",
                "account_on_quote__address",
                "account_on_quote__logo",
            )
            .prefetch_related(
                "lines__discounts",
                "lines__taxes",
                "discounts",
                "taxes",
                "account__tax_ids",
                "customer_on_quote__tax_ids",
                "account_on_quote__tax_ids",
            )
            .get()
        )

        html = render_to_string("quotes/pdf/classic.html", {"quote": quote})
        pdf_content = generate_pdf(html)
        filename = f"{quote.id}.pdf"
        upload = SimpleUploadedFile(filename, pdf_content, content_type="application/pdf")
        file = File.objects.upload_for_account(
            account=self.account,
            purpose=FilePurpose.QUOTE_PDF,
            filename=filename,
            data=upload,
            content_type="application/pdf",
        )
        self.pdf = file
        self.save(update_fields=["pdf", "updated_at"])
        return file


class QuoteLine(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    description = models.CharField(max_length=255)
    quantity = models.BigIntegerField()
    currency = models.CharField(max_length=3, choices=djmoney_settings.CURRENCY_CHOICES)
    unit_amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    total_amount_excluding_tax = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    total_amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    total_discount_amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    total_tax_amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    total_tax_rate = models.DecimalField(max_digits=5, decimal_places=2)
    quote = models.ForeignKey("Quote", on_delete=models.CASCADE, related_name="lines")
    price = models.ForeignKey("prices.Price", on_delete=models.PROTECT, related_name="quote_lines", null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = QuoteLineManager()

    class Meta:
        ordering = ["created_at"]

    def recalculate(self) -> None:
        if self.price:
            amount = self.price.calculate_amount(self.quantity)
            self.unit_amount = self.price.calculate_unit_amount(self.quantity)
        else:
            amount = self.unit_amount * self.quantity

        total_discount_amount, total_amount_excluding_tax = (
            self.discounts.select_related("coupon").for_lines().recalculate(amount)
        )

        total_tax_amount, total_tax_rate = self.taxes.for_lines().recalculate(total_amount_excluding_tax)

        self.amount = amount
        self.total_discount_amount = total_discount_amount
        self.total_amount_excluding_tax = total_amount_excluding_tax
        self.total_tax_amount = total_tax_amount
        self.total_tax_rate = total_tax_rate
        self.total_amount = total_amount_excluding_tax + total_tax_amount
        self.save(
            update_fields=[
                "unit_amount",
                "amount",
                "total_discount_amount",
                "total_amount_excluding_tax",
                "total_tax_amount",
                "total_tax_rate",
                "total_amount",
            ]
        )

        self.quote.recalculate()

    def add_tax(self, tax_rate: TaxRate):
        tax = self.taxes.create(
            quote=self.quote,
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

    def add_discount(self, coupon: Coupon):
        discount = self.discounts.create(
            quote=self.quote,
            coupon=coupon,
            currency=self.currency,
            amount=zero(self.currency),
        )
        self.recalculate()
        discount.refresh_from_db()
        return discount

    def update(
        self,
        description: str,
        quantity: int,
        unit_amount: Money | None,
        price: Price | None,
    ) -> None:
        self.description = description
        self.quantity = quantity
        self.unit_amount = price.calculate_unit_amount(quantity) if price else unit_amount
        self.price = price
        self.save(update_fields=["description", "quantity", "unit_amount", "price"])
        self.recalculate()


class QuoteDiscount(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quote = models.ForeignKey("Quote", on_delete=models.CASCADE, related_name="discounts")
    quote_line = models.ForeignKey(
        "QuoteLine",
        on_delete=models.CASCADE,
        related_name="discounts",
        null=True,
    )
    coupon = models.ForeignKey("coupons.Coupon", on_delete=models.PROTECT, related_name="quote_discounts")
    currency = models.CharField(max_length=3, choices=djmoney_settings.CURRENCY_CHOICES)
    amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    created_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager.from_queryset(QuoteDiscountQuerySet)()

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["quote_line", "coupon"],
                condition=models.Q(quote_line__isnull=False),
                name="unique_quote_line_coupon",
            ),
            models.UniqueConstraint(
                fields=["quote", "coupon"],
                condition=models.Q(quote_line__isnull=True),
                name="unique_quote_coupon",
            ),
        ]

    def recalculate(self, base: Money) -> Money:
        coupon = self.coupon

        if coupon.amount is not None:
            if coupon.amount <= zero(base.currency):
                return zero(base.currency)
            return min(coupon.amount, base)

        if coupon.percentage is not None:
            percentage_amount = calculate_percentage_amount(base, coupon.percentage)
            return min(percentage_amount, base)

        return zero(base.currency)


class QuoteTax(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quote = models.ForeignKey("Quote", on_delete=models.CASCADE, related_name="taxes")
    quote_line = models.ForeignKey(
        "QuoteLine",
        on_delete=models.CASCADE,
        related_name="taxes",
        null=True,
    )
    tax_rate = models.ForeignKey("tax_rates.TaxRate", on_delete=models.PROTECT, related_name="quote_taxes", null=True)
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, null=True)
    rate = models.DecimalField(max_digits=5, decimal_places=2)
    currency = models.CharField(max_length=3, choices=djmoney_settings.CURRENCY_CHOICES)
    amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    created_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager.from_queryset(QuoteTaxQuerySet)()

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["quote_line", "tax_rate"],
                condition=models.Q(quote_line__isnull=False, tax_rate__isnull=False),
                name="unique_quote_line_tax_rate",
            ),
            models.UniqueConstraint(
                fields=["quote", "tax_rate"],
                condition=models.Q(quote_line__isnull=True, tax_rate__isnull=False),
                name="unique_quote_tax_rate",
            ),
        ]

    def recalculate(self, base: Money) -> Money:
        percentage = self.rate if isinstance(self.rate, Decimal) else Decimal(self.rate)

        if percentage <= 0:
            return zero(base.currency)

        return calculate_percentage_amount(base, percentage)
