from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from uuid import UUID

from django.apps import apps
from django.conf import settings
from django.db import models
from djmoney.money import Money

from openinvoice.accounts.models import Account
from openinvoice.core.calculations import zero
from openinvoice.customers.models import BillingProfile, Customer
from openinvoice.integrations.choices import PaymentProvider
from openinvoice.numbering_systems.models import NumberingSystem
from openinvoice.prices.models import Price

from .choices import InvoiceDeliveryMethod, InvoiceDocumentAudience, InvoiceStatus, InvoiceTaxBehavior

if TYPE_CHECKING:
    from openinvoice.accounts.models import BusinessProfile

    from .models import Invoice


class InvoiceDocumentManager(models.Manager):
    def create_document(
        self,
        invoice: Invoice,
        language: str,
        audience: list[InvoiceDocumentAudience] | None = None,
        footer: str | None = None,
        memo: str | None = None,
        custom_fields: Mapping[str, Any] | None = None,
    ):
        return self.create(
            invoice=invoice,
            audience=audience or [InvoiceDocumentAudience.INTERNAL],
            language=language,
            footer=footer,
            memo=memo,
            custom_fields=custom_fields or {},
        )


class InvoiceManager(models.Manager):
    def create_draft(
        self,
        account: Account,
        customer: Customer,
        billing_profile: BillingProfile | None = None,
        business_profile: BusinessProfile | None = None,
        number: str | None = None,
        numbering_system: NumberingSystem | None = None,
        currency: str | None = None,
        issue_date: date | None = None,
        due_date: date | None = None,
        net_payment_term: int | None = None,
        metadata: Mapping[str, Any] | None = None,
        payment_provider: PaymentProvider | None = None,
        payment_connection_id: UUID | None = None,
        delivery_method: InvoiceDeliveryMethod | None = None,
        recipients: list[str] | None = None,
        tax_behavior: InvoiceTaxBehavior | None = None,
    ) -> Invoice:
        InvoiceHead = apps.get_model("invoices", "InvoiceHead")

        billing_profile = billing_profile or customer.default_billing_profile
        business_profile = business_profile or account.default_business_profile
        currency = currency or billing_profile.currency or account.default_currency
        resolved_numbering_system = None
        if number is None:
            resolved_numbering_system = (
                numbering_system or billing_profile.invoice_numbering_system or account.invoice_numbering_system
            )

        net_payment_term = net_payment_term or billing_profile.net_payment_term or account.net_payment_term
        default_recipients = [billing_profile.email] if billing_profile.email else []
        language = billing_profile.language or account.language or settings.LANGUAGE_CODE

        head = InvoiceHead.objects.create(root=None)
        invoice = self.create(
            head=head,
            account=account,
            customer=customer,
            billing_profile=billing_profile,
            business_profile=business_profile,
            number=number,
            numbering_system=resolved_numbering_system,
            currency=currency,
            status=InvoiceStatus.DRAFT,
            issue_date=issue_date,
            due_date=due_date,
            net_payment_term=net_payment_term,
            metadata=metadata or {},
            payment_provider=payment_provider,
            payment_connection_id=payment_connection_id,
            subtotal_amount=zero(currency),
            total_discount_amount=zero(currency),
            total_excluding_tax_amount=zero(currency),
            shipping_amount=zero(currency),
            total_tax_amount=zero(currency),
            total_amount=zero(currency),
            total_credit_amount=zero(currency),
            total_paid_amount=zero(currency),
            outstanding_amount=zero(currency),
            delivery_method=delivery_method or InvoiceDeliveryMethod.MANUAL,
            recipients=recipients or default_recipients,
            tax_behavior=tax_behavior or InvoiceTaxBehavior.AUTOMATIC,
        )

        head.root = invoice
        head.save(update_fields=["root"])

        invoice.set_tax_rates(billing_profile.tax_rates.active())

        invoice.documents.create_document(
            invoice=invoice,
            audience=[InvoiceDocumentAudience.CUSTOMER],
            language=language,
            footer=account.invoice_footer,
        )

        return invoice

    def create_revision(
        self,
        account: Account,
        previous_revision: Invoice,
        billing_profile: BillingProfile | None = None,
        business_profile: BusinessProfile | None = None,
        number: str | None = None,
        numbering_system: NumberingSystem | None = None,
        currency: str | None = None,
        issue_date: date | None = None,
        due_date: date | None = None,
        net_payment_term: int | None = None,
        metadata: Mapping[str, Any] | None = None,
        payment_provider: PaymentProvider | None = None,
        payment_connection_id: UUID | None = None,
        delivery_method: InvoiceDeliveryMethod | None = None,
        recipients: Iterable[str] | None = None,
        tax_behavior: InvoiceTaxBehavior | None = None,
    ) -> Invoice:
        InvoiceLine = apps.get_model("invoices", "InvoiceLine")
        currency = currency or previous_revision.currency
        billing_profile = billing_profile or previous_revision.customer.default_billing_profile
        business_profile = business_profile or account.default_business_profile
        resolved_numbering_system = None
        if number is None:
            resolved_numbering_system = (
                numbering_system
                or previous_revision.numbering_system
                or billing_profile.invoice_numbering_system
                or account.invoice_numbering_system
            )

        invoice = self.create(
            account=account,
            customer=previous_revision.customer,
            billing_profile=billing_profile,
            business_profile=business_profile,
            number=number,
            numbering_system=resolved_numbering_system,
            currency=currency,
            status=InvoiceStatus.DRAFT,
            issue_date=issue_date,
            due_date=due_date,
            net_payment_term=net_payment_term or previous_revision.net_payment_term,
            metadata=metadata or {},
            payment_provider=payment_provider or previous_revision.payment_provider,
            payment_connection_id=payment_connection_id or previous_revision.payment_connection_id,
            previous_revision=previous_revision,
            subtotal_amount=zero(currency),
            total_discount_amount=zero(currency),
            total_excluding_tax_amount=zero(currency),
            shipping_amount=zero(currency),
            total_tax_amount=zero(currency),
            total_amount=zero(currency),
            total_credit_amount=zero(currency),
            total_paid_amount=zero(currency),
            outstanding_amount=zero(currency),
            delivery_method=delivery_method or previous_revision.delivery_method,
            recipients=recipients or previous_revision.recipients,
            head=previous_revision.head,
            tax_behavior=tax_behavior or previous_revision.tax_behavior,
        )

        for line in previous_revision.lines.filter(currency=currency):
            new_line = InvoiceLine.objects.create_line(
                invoice=invoice,
                description=line.description,
                quantity=line.quantity,
                unit_amount=line.unit_amount,
                price=line.price,
            )
            new_line.set_coupons(line.coupons.active())
            new_line.set_tax_rates(line.tax_rates.active())

        if previous_revision.shipping is not None:
            invoice.add_shipping(
                shipping_rate=previous_revision.shipping.shipping_rate,
                tax_rates=previous_revision.shipping.tax_rates.active(),
            )

        invoice.set_coupons(previous_revision.coupons.active())
        invoice.set_tax_rates(previous_revision.tax_rates.active())

        for document in previous_revision.documents.all():
            invoice.documents.create_document(
                invoice=invoice,
                audience=document.audience,
                language=document.language,
                footer=document.footer,
                memo=document.memo,
                custom_fields=document.custom_fields,
            )

        return invoice

    def clone_invoice(self, invoice: Invoice) -> Invoice:
        InvoiceHead = apps.get_model("invoices", "InvoiceHead")
        head = InvoiceHead.objects.create(root=None)

        new_invoice = self.create(
            head=head,
            account=invoice.account,
            customer=invoice.customer,
            billing_profile=invoice.customer.default_billing_profile,
            business_profile=invoice.account.default_business_profile,
            number=None,
            numbering_system=invoice.numbering_system,
            currency=invoice.currency,
            status=InvoiceStatus.DRAFT,
            issue_date=None,
            due_date=None,
            net_payment_term=invoice.net_payment_term,
            metadata={},
            payment_provider=invoice.payment_provider,
            payment_connection_id=invoice.payment_connection_id,
            subtotal_amount=zero(invoice.currency),
            total_discount_amount=zero(invoice.currency),
            total_excluding_tax_amount=zero(invoice.currency),
            shipping_amount=zero(invoice.currency),
            total_tax_amount=zero(invoice.currency),
            total_amount=zero(invoice.currency),
            total_credit_amount=zero(invoice.currency),
            total_paid_amount=zero(invoice.currency),
            outstanding_amount=zero(invoice.currency),
            delivery_method=invoice.delivery_method,
            recipients=invoice.recipients,
            tax_behavior=invoice.tax_behavior,
        )

        head.root = new_invoice
        head.save(update_fields=["root"])

        for line in invoice.lines.all():
            new_line = new_invoice.lines.create(
                invoice=new_invoice,
                description=line.description,
                quantity=line.quantity,
                currency=invoice.currency,
                unit_amount=line.unit_amount,
                unit_excluding_tax_amount=zero(invoice.currency),
                price=line.price,
                total_tax_rate=Decimal(9),
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
            new_line.set_coupons(line.coupons.active())
            new_line.set_tax_rates(line.tax_rates.active())

        if invoice.shipping is not None:
            new_invoice.add_shipping(
                shipping_rate=invoice.shipping.shipping_rate,
                tax_rates=invoice.shipping.tax_rates.active(),
                shipping_profile=invoice.customer.default_shipping_profile,
            )

        new_invoice.set_coupons(invoice.coupons.active())
        new_invoice.set_tax_rates(invoice.tax_rates.active())

        for document in invoice.documents.all():
            new_invoice.documents.create_document(
                invoice=new_invoice,
                audience=document.audience,
                language=document.language,
                footer=document.footer,
                memo=document.memo,
                custom_fields=document.custom_fields,
            )

        return new_invoice


class InvoiceLineManager(models.Manager):
    def create_line(
        self,
        invoice,
        description: str,
        quantity: int,
        unit_amount: Money | None = None,
        price: Price | None = None,
    ):
        currency = invoice.currency
        unit_amount = price.calculate_unit_amount(quantity) if price else unit_amount

        return self.create(
            invoice=invoice,
            description=description,
            quantity=quantity,
            price=price,
            unit_amount=unit_amount,
            unit_excluding_tax_amount=unit_amount,
            currency=currency,
            amount=zero(currency),
            subtotal_amount=zero(currency),
            total_discount_amount=zero(currency),
            total_taxable_amount=zero(currency),
            total_excluding_tax_amount=zero(currency),
            total_tax_amount=zero(currency),
            total_tax_rate=Decimal(0),
            total_amount=zero(currency),
            total_credit_amount=zero(currency),
            credit_quantity=0,
            outstanding_amount=zero(currency),
            outstanding_quantity=quantity,
        )
