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
from apps.integrations.enums import PaymentProvider
from apps.numbering_systems.models import NumberingSystem
from apps.prices.models import Price
from apps.taxes.models import TaxId
from common.calculations import zero

from .enums import InvoiceDeliveryMethod, InvoiceStatus
from .querysets import (
    InvoiceDiscountQuerySet,
    InvoiceLineQuerySet,
    InvoiceQuerySet,
    InvoiceTaxQuerySet,
)

if TYPE_CHECKING:
    from .models import Invoice, InvoiceAccount, InvoiceCustomer


class InvoiceCustomerManager(models.Manager["InvoiceCustomer"]):
    def from_customer(self, customer: Customer) -> InvoiceCustomer:
        invoice_customer = self.create(
            name=customer.name,
            legal_name=customer.legal_name,
            legal_number=customer.legal_number,
            email=customer.email,
            phone=customer.phone,
            description=customer.description,
            billing_address=Address.objects.from_address(customer.billing_address),
            shipping_address=Address.objects.from_address(customer.shipping_address),
            logo=customer.logo.clone() if customer.logo else None,
        )
        invoice_customer.tax_ids.set(TaxId.objects.from_customer(customer))

        return invoice_customer


class InvoiceAccountManager(models.Manager["InvoiceAccount"]):
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


class InvoiceManager(models.Manager.from_queryset(InvoiceQuerySet)):
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
    ) -> Invoice:
        currency = currency or customer.currency or account.default_currency
        resolved_numbering_system = None
        if number is None:
            resolved_numbering_system = (
                numbering_system or customer.invoice_numbering_system or account.invoice_numbering_system
            )

        net_payment_term = net_payment_term or customer.net_payment_term or account.net_payment_term
        default_recipients = [customer.email] if customer.email else []

        invoice = self.create(
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
            total_amount_excluding_tax=zero(currency),
            total_tax_amount=zero(currency),
            total_amount=zero(currency),
            total_credit_amount=zero(currency),
            total_paid_amount=zero(currency),
            outstanding_amount=zero(currency),
            delivery_method=delivery_method or InvoiceDeliveryMethod.MANUAL,
            recipients=recipients or default_recipients,
        )

        for tax_rate in customer.tax_rates.filter(is_active=True):
            invoice.add_tax(tax_rate)

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
    ) -> Invoice:
        InvoiceDiscount = apps.get_model("invoices", "InvoiceDiscount")
        InvoiceTax = apps.get_model("invoices", "InvoiceTax")

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
            total_amount_excluding_tax=zero(currency),
            total_tax_amount=zero(currency),
            total_amount=zero(currency),
            total_credit_amount=zero(currency),
            total_paid_amount=zero(currency),
            outstanding_amount=zero(currency),
            delivery_method=delivery_method or previous_revision.delivery_method,
            recipients=recipients or previous_revision.recipients,
        )

        for line in previous_revision.lines.filter(currency=currency):
            new_line = invoice.lines.create(
                invoice=invoice,
                description=line.description,
                quantity=line.quantity,
                currency=currency,
                unit_amount=line.unit_amount,
                price=line.price,
                total_tax_rate=line.total_tax_rate,
                amount=zero(line.currency),
                total_discount_amount=zero(line.currency),
                total_amount_excluding_tax=zero(line.currency),
                total_tax_amount=zero(line.currency),
                total_amount=zero(line.currency),
                total_credit_amount=zero(line.currency),
                credit_quantity=0,
                outstanding_amount=zero(line.currency),
                outstanding_quantity=line.quantity,
            )
            new_line.discounts.bulk_create(
                InvoiceDiscount(
                    invoice=invoice,
                    invoice_line=new_line,
                    coupon=discount.coupon,
                    currency=invoice.currency,
                    amount=zero(invoice.currency),
                )
                for discount in line.discounts.filter(coupon__is_active=True)
            )
            new_line.taxes.bulk_create(
                InvoiceTax(
                    invoice=invoice,
                    invoice_line=new_line,
                    tax_rate=tax.tax_rate,
                    name=tax.name,
                    description=tax.description,
                    rate=tax.rate,
                    currency=invoice.currency,
                    amount=zero(invoice.currency),
                )
                for tax in line.taxes.all()
            )
            new_line.recalculate()

        invoice.discounts.bulk_create(
            InvoiceDiscount(
                invoice=invoice,
                coupon=discount.coupon,
                currency=invoice.currency,
                amount=zero(invoice.currency),
            )
            for discount in previous_revision.discounts.for_invoice().filter(coupon__is_active=True)
        )
        invoice.taxes.bulk_create(
            InvoiceTax(
                invoice=invoice,
                tax_rate=tax.tax_rate,
                name=tax.name,
                description=tax.description,
                rate=tax.rate,
                currency=invoice.currency,
                amount=zero(invoice.currency),
            )
            for tax in previous_revision.taxes.for_invoice()
        )

        invoice.recalculate()

        return invoice

    def sync_latest_revision(self, latest: Invoice) -> None:
        """Point all revisions in the chain at the provided latest revision."""

        latest_id = latest.id
        previous_latest_id = latest.previous_revision_id

        if latest.latest_revision_id != latest_id:
            self.filter(id=latest_id).update(latest_revision=latest)
            latest.latest_revision = latest

        if previous_latest_id is None:
            return

        updated = self.filter(latest_revision_id=previous_latest_id).update(latest_revision=latest)
        if updated:
            previous_revision = getattr(latest, "previous_revision", None)
            if previous_revision is not None:
                previous_revision.latest_revision = latest


class InvoiceLineManager(models.Manager.from_queryset(InvoiceLineQuerySet)):
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
            currency=currency,
            total_tax_rate=Decimal(0),
            amount=zero(currency),
            total_discount_amount=zero(currency),
            total_amount_excluding_tax=zero(currency),
            total_tax_amount=zero(currency),
            total_amount=zero(currency),
            total_credit_amount=zero(currency),
            credit_quantity=0,
            outstanding_amount=zero(currency),
            outstanding_quantity=quantity,
        )

        invoice_line.recalculate()

        if price:
            price.mark_as_used()

        return invoice_line


class InvoiceDiscountManager(models.Manager.from_queryset(InvoiceDiscountQuerySet)): ...


class InvoiceTaxManager(models.Manager.from_queryset(InvoiceTaxQuerySet)): ...
