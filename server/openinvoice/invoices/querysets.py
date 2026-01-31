from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from django.apps import apps
from django.db import models
from django.db.models import Case, F, IntegerField, OuterRef, Prefetch, Subquery, Value, When
from django_cte import CTE, with_cte

if TYPE_CHECKING:
    from openinvoice.accounts.models import Account

from .choices import InvoiceDiscountSource, InvoiceTaxSource


class InvoiceQuerySet(models.QuerySet):
    def for_account(self, account: Account):
        return self.filter(account=account)

    def eager_load(self):
        InvoiceLine = apps.get_model("invoices.InvoiceLine")  # noqa: N806
        Coupon = apps.get_model("coupons.Coupon")  # noqa: N806
        TaxRate = apps.get_model("tax_rates.TaxRate")  # noqa: N806
        InvoiceDiscountAllocation = apps.get_model("invoices.InvoiceDiscountAllocation")  # noqa: N806
        InvoiceTaxAllocation = apps.get_model("invoices.InvoiceTaxAllocation")  # noqa: N806
        InvoiceDocument = apps.get_model("invoices.InvoiceDocument")  # noqa: N806

        return self.select_related(
            "account",
            "account__address",
            "invoice_account",
            "invoice_account__address",
            "customer",
            "customer__address",
            "invoice_customer",
            "invoice_customer__address",
            "numbering_system",
            "previous_revision",
            "shipping",
            "shipping__address",
            "shipping__shipping_rate",
        ).prefetch_related(
            Prefetch("lines", queryset=InvoiceLine.objects.eager_load().order_by("created_at")),
            Prefetch("coupons", queryset=Coupon.objects.order_by("invoice_coupons__position")),
            Prefetch("tax_rates", queryset=TaxRate.objects.order_by("invoice_tax_rates__position")),
            Prefetch("lines__coupons", queryset=Coupon.objects.order_by("invoice_line_coupons__position")),
            Prefetch("lines__tax_rates", queryset=TaxRate.objects.order_by("invoice_line_tax_rates__position")),
            Prefetch("shipping__tax_rates", queryset=TaxRate.objects.order_by("invoice_shipping_tax_rates__position")),
            Prefetch("discount_allocations", queryset=InvoiceDiscountAllocation.objects.annotate_position()),
            Prefetch("lines__discount_allocations", queryset=InvoiceDiscountAllocation.objects.annotate_position()),
            Prefetch("tax_allocations", queryset=InvoiceTaxAllocation.objects.annotate_position()),
            Prefetch("lines__tax_allocations", queryset=InvoiceTaxAllocation.objects.annotate_position()),
            Prefetch("shipping__tax_allocations", queryset=InvoiceTaxAllocation.objects.annotate_position()),
            Prefetch("documents", queryset=InvoiceDocument.objects.select_related("file").order_by("created_at")),
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


class InvoiceLineQuerySet(models.QuerySet):
    def for_account(self, account: Account):
        return self.filter(invoice__account=account)

    def eager_load(self):
        Coupon = apps.get_model("coupons.Coupon")  # noqa: N806
        TaxRate = apps.get_model("tax_rates.TaxRate")  # noqa: N806
        InvoiceDiscountAllocation = apps.get_model("invoices.InvoiceDiscountAllocation")  # noqa: N806
        InvoiceTaxAllocation = apps.get_model("invoices.InvoiceTaxAllocation")  # noqa: N806

        return self.select_related("invoice", "price").prefetch_related(
            Prefetch("coupons", queryset=Coupon.objects.order_by("invoice_line_coupons__position")),
            Prefetch("tax_rates", queryset=TaxRate.objects.order_by("invoice_line_tax_rates__position")),
            Prefetch("invoice__coupons", queryset=Coupon.objects.order_by("invoice_coupons__position")),
            Prefetch("invoice__tax_rates", queryset=TaxRate.objects.order_by("invoice_tax_rates__position")),
            Prefetch("discount_allocations", queryset=InvoiceDiscountAllocation.objects.annotate_position()),
            Prefetch("tax_allocations", queryset=InvoiceTaxAllocation.objects.annotate_position()),
        )


class InvoiceDiscountAllocationQuerySet(models.QuerySet):
    def annotate_position(self):
        InvoiceLineCoupon = apps.get_model("invoices.InvoiceLineCoupon")  # noqa: N806
        InvoiceCoupon = apps.get_model("invoices.InvoiceCoupon")  # noqa: N806

        line_position = Subquery(
            InvoiceLineCoupon.objects.filter(
                invoice_line_id=OuterRef("invoice_line_id"),
                coupon_id=OuterRef("coupon_id"),
            )
            .values("position")
            .order_by("position")[:1]
        )
        invoice_position = Subquery(
            InvoiceCoupon.objects.filter(
                invoice_id=OuterRef("invoice_id"),
                coupon_id=OuterRef("coupon_id"),
            )
            .values("position")
            .order_by("position")[:1]
        )

        return self.select_related("coupon").annotate(
            position=Case(
                When(source=InvoiceDiscountSource.LINE, then=line_position),
                default=invoice_position,
                output_field=IntegerField(),
            )
        )


class InvoiceTaxAllocationQuerySet(models.QuerySet):
    def annotate_position(self):
        InvoiceLineTaxRate = apps.get_model("invoices.InvoiceLineTaxRate")  # noqa: N806
        InvoiceTaxRate = apps.get_model("invoices.InvoiceTaxRate")  # noqa: N806
        InvoiceShippingTaxRate = apps.get_model("invoices.InvoiceShippingTaxRate")  # noqa: N806

        line_position = Subquery(
            InvoiceLineTaxRate.objects.filter(
                invoice_line_id=OuterRef("invoice_line_id"),
                tax_rate_id=OuterRef("tax_rate_id"),
            )
            .values("position")
            .order_by("position")[:1]
        )
        shipping_position = Subquery(
            InvoiceShippingTaxRate.objects.filter(
                invoice_shipping_id=OuterRef("invoice_shipping_id"),
                tax_rate_id=OuterRef("tax_rate_id"),
            )
            .values("position")
            .order_by("position")[:1]
        )
        invoice_position = Subquery(
            InvoiceTaxRate.objects.filter(
                invoice_id=OuterRef("invoice_id"),
                tax_rate_id=OuterRef("tax_rate_id"),
            )
            .values("position")
            .order_by("position")[:1]
        )

        return self.select_related("tax_rate").annotate(
            position=Case(
                When(source=InvoiceTaxSource.LINE, then=line_position),
                When(source=InvoiceTaxSource.SHIPPING, then=shipping_position),
                default=invoice_position,
                output_field=IntegerField(),
            )
        )
