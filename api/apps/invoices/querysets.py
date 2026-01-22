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
