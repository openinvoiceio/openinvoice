from __future__ import annotations

from decimal import Decimal

from django.db import models
from django.db.models import Prefetch
from djmoney.money import Money

from common.calculations import zero


class InvoiceQuerySet(models.QuerySet):
    def for_recalculation(self) -> InvoiceQuerySet:
        InvoiceLine = self.model._meta.get_field("lines").related_model  # noqa: SLF001, N806
        InvoiceDiscount = self.model._meta.get_field("discounts").related_model  # noqa: SLF001, N806

        return self.prefetch_related(
            Prefetch(
                "lines",
                queryset=InvoiceLine.objects.order_by("created_at").prefetch_related(
                    Prefetch("discounts", queryset=InvoiceDiscount.objects.select_related("coupon")),
                    "taxes",
                ),
            ),
            Prefetch("discounts", queryset=InvoiceDiscount.objects.select_related("coupon")),
            "taxes",
        )

    def for_pdf(self) -> InvoiceQuerySet:
        InvoiceLine = self.model._meta.get_field("lines").related_model  # noqa: SLF001, N806

        return self.select_related(
            "account_on_invoice__logo",
            "account__logo",
            "account_on_invoice__address",
            "account__address",
            "customer_on_invoice__billing_address",
            "customer_on_invoice__shipping_address",
            "customer_on_invoice__logo",
            "customer__billing_address",
            "customer__shipping_address",
            "customer__logo",
            "previous_revision",
            "latest_revision",
        ).prefetch_related(
            Prefetch(
                "lines",
                queryset=InvoiceLine.objects.order_by("created_at").prefetch_related("discounts", "taxes"),
            ),
            "discounts",
            "taxes",
            "account_on_invoice__tax_ids",
            "customer_on_invoice__tax_ids",
        )


class InvoiceLineQuerySet(models.QuerySet):
    """Custom queryset for invoice lines."""


class InvoiceDiscountQuerySet(models.QuerySet):
    def for_invoice(self):
        return self.filter(invoice_line__isnull=True)

    def for_lines(self):
        return self.filter(invoice_line__isnull=False)

    def breakdown(self):
        return (
            self.values("coupon_id", "currency", name=models.F("coupon__name"))
            .annotate(amount=models.Sum("amount"))
            .order_by("name", "currency", "coupon_id")
        )


class InvoiceTaxQuerySet(models.QuerySet):
    def for_invoice(self):
        return self.filter(invoice_line__isnull=True)

    def for_lines(self):
        return self.filter(invoice_line__isnull=False)

    def has_lines(self):
        return self.for_lines().exists()

    def breakdown(self):
        return (
            self.values("name", "currency", "rate")
            .annotate(amount=models.Sum("amount"))
            .order_by("name", "currency", "rate")
        )

    def recalculate(self, taxable: Money):
        currency = taxable.currency
        total = zero(currency)
        rate_total = Decimal("0")
        updated = []

        for tax in self:
            tax.amount = self.model.calculate_amount(taxable, tax.rate)
            updated.append(tax)
            total += tax.amount
            rate_total += Decimal(tax.rate)

        if updated:
            self.model.objects.bulk_update(updated, ["amount"])

        return total, rate_total
