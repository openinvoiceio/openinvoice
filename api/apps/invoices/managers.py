from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from uuid import UUID

from django.apps import apps
from django.db import models
from djmoney.money import Money

from apps.accounts.models import Account
from apps.addresses.models import Address
from apps.customers.models import Customer
from apps.integrations.choices import PaymentProvider
from apps.numbering_systems.models import NumberingSystem
from apps.prices.models import Price
from apps.tax_ids.models import TaxId
from common.calculations import zero

from .choices import InvoiceDeliveryMethod, InvoiceStatus, InvoiceTaxBehavior

if TYPE_CHECKING:
    from .models import Invoice, InvoiceAccount, InvoiceCustomer


class InvoiceCustomerManager(models.Manager):
    def from_customer(self, customer: Customer) -> InvoiceCustomer:
        invoice_customer = self.create(
            name=customer.name,
            legal_name=customer.legal_name,
            legal_number=customer.legal_number,
            email=customer.email,
            phone=customer.phone,
            description=customer.description,
            address=Address.objects.from_address(customer.address),
            logo=customer.logo.clone() if customer.logo else None,
        )
        invoice_customer.tax_ids.set(TaxId.objects.from_customer(customer))

        return invoice_customer


class InvoiceAccountManager(models.Manager):
    def from_account(self, account: Account) -> InvoiceAccount:
        invoice_account = self.create(
            name=account.name,
            legal_name=account.legal_name,
            legal_number=account.legal_number,
            email=account.email,
            phone=account.phone,
            address=Address.objects.from_address(account.address),
            logo=account.logo.clone() if account.logo else None,
        )
        invoice_account.tax_ids.set(TaxId.objects.from_account(account))

        return invoice_account


class InvoiceManager(models.Manager):
    def create_draft(
        self,
        account: Account,
        customer: Customer,
        number: str | None = None,
        numbering_system: NumberingSystem | None = None,
        currency: str | None = None,
        issue_date: date | None = None,
        sell_date: date | None = None,
        due_date: date | None = None,
        net_payment_term: int | None = None,
        metadata: Mapping[str, Any] | None = None,
        custom_fields: Mapping[str, Any] | None = None,
        footer: str | None = None,
        description: str | None = None,
        payment_provider: PaymentProvider | None = None,
        payment_connection_id: UUID | None = None,
        delivery_method: InvoiceDeliveryMethod | None = None,
        recipients: list[str] | None = None,
        tax_behavior: InvoiceTaxBehavior | None = None,
    ) -> Invoice:
        InvoiceHead = apps.get_model("invoices", "InvoiceHead")

        currency = currency or customer.currency or account.default_currency
        resolved_numbering_system = None
        if number is None:
            resolved_numbering_system = (
                numbering_system or customer.invoice_numbering_system or account.invoice_numbering_system
            )

        net_payment_term = net_payment_term or customer.net_payment_term or account.net_payment_term
        default_recipients = [customer.email] if customer.email else []
        head = InvoiceHead.objects.create(root=None)

        invoice = self.create(
            head=head,
            account=account,
            customer=customer,
            number=number,
            numbering_system=resolved_numbering_system,
            currency=currency,
            status=InvoiceStatus.DRAFT,
            issue_date=issue_date,
            sell_date=sell_date,
            due_date=due_date,
            net_payment_term=net_payment_term,
            metadata=metadata or {},
            custom_fields=custom_fields or {},
            footer=footer or account.invoice_footer,
            description=description,
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

        invoice.set_tax_rates(customer.tax_rates.active())

        return invoice

    def create_revision(
        self,
        account: Account,
        previous_revision: Invoice,
        number: str | None = None,
        numbering_system: NumberingSystem | None = None,
        currency: str | None = None,
        issue_date: date | None = None,
        sell_date: date | None = None,
        due_date: date | None = None,
        net_payment_term: int | None = None,
        metadata: Mapping[str, Any] | None = None,
        custom_fields: Mapping[str, Any] | None = None,
        footer: str | None = None,
        description: str | None = None,
        payment_provider: PaymentProvider | None = None,
        payment_connection_id: UUID | None = None,
        delivery_method: InvoiceDeliveryMethod | None = None,
        recipients: Iterable[str] | None = None,
        tax_behavior: InvoiceTaxBehavior | None = None,
    ) -> Invoice:
        currency = currency or previous_revision.currency

        resolved_numbering_system = None
        if number is None:
            resolved_numbering_system = (
                numbering_system
                or previous_revision.numbering_system
                or previous_revision.customer.invoice_numbering_system
                or account.invoice_numbering_system
            )

        invoice = self.create(
            account=account,
            customer=previous_revision.customer,
            number=number,
            numbering_system=resolved_numbering_system,
            currency=currency,
            status=InvoiceStatus.DRAFT,
            issue_date=issue_date,
            sell_date=sell_date,
            due_date=due_date,
            net_payment_term=net_payment_term or previous_revision.net_payment_term,
            metadata=metadata or {},
            custom_fields=custom_fields or previous_revision.custom_fields,
            footer=footer or previous_revision.footer,
            description=description or previous_revision.description,
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
            new_line = invoice.lines.create(
                invoice=invoice,
                description=line.description,
                quantity=line.quantity,
                currency=currency,
                unit_amount=line.unit_amount,
                unit_excluding_tax_amount=line.unit_excluding_tax_amount,
                price=line.price,
                total_tax_rate=line.total_tax_rate,
                amount=zero(line.currency),
                subtotal_amount=zero(line.currency),
                total_discount_amount=zero(line.currency),
                total_taxable_amount=zero(line.currency),
                total_excluding_tax_amount=zero(line.currency),
                total_tax_amount=zero(line.currency),
                total_amount=zero(line.currency),
                total_credit_amount=zero(line.currency),
                credit_quantity=0,
                outstanding_amount=zero(line.currency),
                outstanding_quantity=line.quantity,
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

        return invoice

    def clone_invoice(self, invoice: Invoice) -> Invoice:
        InvoiceHead = apps.get_model("invoices", "InvoiceHead")
        head = InvoiceHead.objects.create(root=None)

        new_invoice = self.create(
            head=head,
            account=invoice.account,
            customer=invoice.customer,
            number=None,
            numbering_system=invoice.numbering_system,
            currency=invoice.currency,
            status=InvoiceStatus.DRAFT,
            issue_date=None,
            sell_date=None,
            due_date=None,
            net_payment_term=invoice.net_payment_term,
            metadata={},
            custom_fields=invoice.custom_fields,
            footer=invoice.footer,
            description=invoice.description,
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
            )

        new_invoice.set_coupons(invoice.coupons.active())
        new_invoice.set_tax_rates(invoice.tax_rates.active())

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

        invoice_line = self.create(
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

        if price:
            price.mark_as_used()

        return invoice_line
