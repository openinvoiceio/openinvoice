from decimal import Decimal

from django.apps import apps
from django.db import models
from django.db.models import Prefetch
from djmoney.money import Money

from common.calculations import zero


class QuoteQuerySet(models.QuerySet):
    def for_recalculation(self):
        QuoteLine = apps.get_model("quotes.QuoteLine")  # noqa: N806
        QuoteDiscount = apps.get_model("quotes.QuoteDiscount")  # noqa: N806

        return self.prefetch_related(
            Prefetch(
                "lines",
                queryset=QuoteLine.objects.order_by("created_at").prefetch_related(
                    Prefetch("discounts", queryset=QuoteDiscount.objects.select_related("coupon")),
                    "taxes",
                ),
            ),
            Prefetch("discounts", queryset=QuoteDiscount.objects.select_related("coupon")),
            "taxes",
        )


class QuoteDiscountQuerySet(models.QuerySet):
    def for_quote(self):
        return self.filter(quote_line__isnull=True)

    def for_lines(self):
        return self.filter(quote_line__isnull=False)

    def breakdown(self):
        return (
            self.values("coupon_id", "currency", name=models.F("coupon__name"))
            .annotate(amount=models.Sum("amount"))
            .order_by("name", "currency", "coupon_id")
        )

    def recalculate(self, base: Money):
        taxable = base
        currency = base.currency
        total = zero(currency)
        updated = []

        for discount in self:
            discount.amount = discount.recalculate(taxable)
            updated.append(discount)
            total += discount.amount
            taxable = max(taxable - discount.amount, zero(currency))

        if updated:
            self.model.objects.bulk_update(updated, ["amount"])

        return total, taxable


class QuoteTaxQuerySet(models.QuerySet):
    def for_quote(self):
        return self.filter(quote_line__isnull=True)

    def for_lines(self):
        return self.filter(quote_line__isnull=False)

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
            tax.amount = tax.recalculate(taxable)
            updated.append(tax)
            total += tax.amount
            rate_total += Decimal(tax.rate)

        if updated:
            self.model.objects.bulk_update(updated, ["amount"])

        return total, rate_total
