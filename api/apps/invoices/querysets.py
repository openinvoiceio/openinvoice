from __future__ import annotations

from uuid import UUID

from django.db import models
from django.db.models import F, IntegerField, Value
from django_cte import CTE, with_cte

from apps.invoices.choices import InvoiceDiscountSource, InvoiceTaxSource


class InvoiceQuerySet(models.QuerySet):
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
    def line_discounts(self):
        return (
            self.values("currency", "coupon_id", "coupon__name")
            .filter(source=InvoiceDiscountSource.LINE)
            .annotate(amount=models.Sum("amount"))
            .order_by("currency", "coupon_id")
        )

    def invoice_discounts(self):
        return (
            self.values("currency", "coupon_id", "coupon__name")
            .filter(source=InvoiceDiscountSource.INVOICE)
            .annotate(amount=models.Sum("amount"))
            .order_by("currency", "coupon_id")
        )

    # TODO: add total_discounts too


class InvoiceTaxAllocationQuerySet(models.QuerySet):
    def line_taxes(self):
        return (
            self.values("currency", "tax_rate_id", "tax_rate__name", "tax_rate__percentage")
            .filter(source=InvoiceTaxSource.LINE)
            .annotate(amount=models.Sum("amount"))
            .order_by("currency", "tax_rate_id")
        )

    def invoice_taxes(self):
        return (
            self.values("currency", "tax_rate_id", "tax_rate__name", "tax_rate__percentage")
            .filter(source=InvoiceTaxSource.INVOICE)
            .annotate(amount=models.Sum("amount"))
            .order_by("currency", "tax_rate_id")
        )

    def total_taxes(self):
        return (
            self.values("currency", "tax_rate_id", "tax_rate__name", "tax_rate__percentage")
            .annotate(amount=models.Sum("amount"))
            .order_by("currency", "tax_rate_id")
        )
