from __future__ import annotations

from uuid import UUID

from django.db import models
from django.db.models import F, IntegerField, Prefetch, Value
from django_cte import CTE, with_cte


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

    def revisions(self, head_id: UUID) -> InvoiceQuerySet:
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
        return self.filter(invoice_line__isnull=True, invoice_shipping__isnull=True)

    def for_lines(self):
        return self.filter(invoice_line__isnull=False)

    def for_shipping(self):
        return self.filter(invoice_shipping__isnull=False)

    def has_lines(self):
        return self.for_lines().exists()

    def breakdown(self):
        return (
            self.values("name", "currency", "rate")
            .annotate(amount=models.Sum("amount"))
            .order_by("name", "currency", "rate")
        )
