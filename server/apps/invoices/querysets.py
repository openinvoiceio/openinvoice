from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from django.apps import apps
from django.db import models
from django.db.models import F, IntegerField, Prefetch, Value
from django_cte import CTE, with_cte

from apps.invoices.choices import InvoiceDiscountSource, InvoiceTaxSource

if TYPE_CHECKING:
    from apps.accounts.models import Account


class InvoiceQuerySet(models.QuerySet):
    def for_account(self, account: Account):
        return self.filter(account=account)

    def eager_load(self):
        InvoiceLine = apps.get_model("invoices.InvoiceLine")  # noqa: N806
        Coupon = apps.get_model("coupons.Coupon")  # noqa: N806
        TaxRate = apps.get_model("tax_rates.TaxRate")  # noqa: N806

        return self.select_related(
            "account",
            "account__address",
            "account_on_invoice",
            "account_on_invoice__address",
            "customer",
            "customer__address",
            "customer_on_invoice",
            "customer_on_invoice__address",
            "numbering_system",
            "previous_revision",
            "shipping",
            "shipping__address",
            "shipping__shipping_rate",
        ).prefetch_related(
            Prefetch("lines", queryset=InvoiceLine.objects.select_related("price").order_by("created_at")),
            Prefetch("coupons", queryset=Coupon.objects.order_by("invoice_coupons__position")),
            Prefetch("tax_rates", queryset=TaxRate.objects.order_by("invoice_tax_rates__position")),
            Prefetch("lines__coupons", queryset=Coupon.objects.order_by("invoice_line_coupons__position")),
            Prefetch("lines__tax_rates", queryset=TaxRate.objects.order_by("invoice_line_tax_rates__position")),
            Prefetch("shipping__tax_rates", queryset=TaxRate.objects.order_by("invoice_shipping_tax_rates__position")),
        )

    def revisions(self, head_id: UUID):
        def make_cte(cte):
            anchor = (
                self.filter(head_id=head_id, id=F("head__root_id"))
                .annotate(depth=Value(0, output_field=IntegerField()))
                .values("id", "depth")
            )
            recursive = (
                cte.join(self, previous_revision_id=cte.col.id)
                .annotate(depth=cte.col.depth + Value(1))
                .values("id", "depth")
            )
            return anchor.union(recursive, all=True)

        cte = CTE.recursive(make_cte)
        return with_cte(
            cte,
            select=cte.join(self, id=cte.col.id).annotate(depth=cte.col.depth).order_by("-depth"),
        )


class InvoiceDiscountAllocationQuerySet(models.QuerySet):
    def from_invoice(self):
        return self.filter(source=InvoiceDiscountSource.INVOICE)

    def from_line(self):
        return self.filter(source=InvoiceDiscountSource.LINE)

    def aggregate_coupon(self):
        return (
            self.values("coupon_id", name=F("coupon__name")).annotate(amount=models.Sum("amount")).order_by("coupon_id")
        )


class InvoiceTaxAllocationQuerySet(models.QuerySet):
    def from_invoice(self):
        return self.filter(source=InvoiceTaxSource.INVOICE)

    def from_line(self):
        return self.filter(source=InvoiceTaxSource.LINE)

    def aggregate_tax_rate(self):
        return (
            self.values("tax_rate_id", name=F("tax_rate__name"), percentage=F("tax_rate__percentage"))
            .annotate(amount=models.Sum("amount"))
            .order_by("tax_rate_id")
        )
