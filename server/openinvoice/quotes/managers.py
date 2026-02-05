from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.db import models
from djmoney.money import Money

from openinvoice.accounts.models import Account
from openinvoice.addresses.models import Address
from openinvoice.core.calculations import zero
from openinvoice.customers.models import Customer
from openinvoice.numbering_systems.models import NumberingSystem
from openinvoice.prices.models import Price

from .choices import QuoteDeliveryMethod, QuoteStatus


class QuoteManager(models.Manager):
    def create_draft(
        self,
        account: Account,
        customer: Customer,
        number: str | None = None,
        numbering_system: NumberingSystem | None = None,
        currency: str | None = None,
        issue_date: date | None = None,
        metadata: dict | None = None,
        custom_fields: dict | None = None,
        footer: str | None = None,
        delivery_method: QuoteDeliveryMethod | None = None,
        recipients: list[str] | None = None,
    ):
        currency = currency or customer.currency or account.default_currency
        resolved_numbering_system = None

        if number is None:
            resolved_numbering_system = numbering_system
        # TODO: add default quote numbering system for customer and account
        #     resolved_numbering_system = (
        #         numbering_system or customer.invoice_numbering_system or account.invoice_numbering_system
        #     )

        default_recipients = [customer.email] if customer.email else []

        quote = self.create(
            account=account,
            customer=customer,
            number=number,
            numbering_system=resolved_numbering_system,
            currency=currency,
            status=QuoteStatus.DRAFT,
            issue_date=issue_date,
            metadata=metadata or {},
            custom_fields=custom_fields or {},
            footer=footer or account.invoice_footer,
            subtotal_amount=zero(currency),
            total_discount_amount=zero(currency),
            total_amount_excluding_tax=zero(currency),
            total_tax_amount=zero(currency),
            total_amount=zero(currency),
            delivery_method=delivery_method or QuoteDeliveryMethod.MANUAL,
            recipients=recipients or default_recipients,
        )

        for tax_rate in customer.tax_rates.active():
            quote.add_tax(tax_rate)

        return quote


class QuoteLineManager(models.Manager):
    def create_line(
        self,
        quote,
        description: str,
        quantity: int,
        unit_amount: Money | None = None,
        price: Price | None = None,
    ):
        currency = quote.currency
        unit_amount = price.calculate_unit_amount(quantity) if price else unit_amount

        quote_line = self.create(
            quote=quote,
            description=description,
            quantity=quantity,
            price=price,
            unit_amount=unit_amount,
            currency=currency,
            total_tax_rate=Decimal("0"),
            amount=zero(currency),
            total_discount_amount=zero(currency),
            total_amount_excluding_tax=zero(currency),
            total_tax_amount=zero(currency),
            total_amount=zero(currency),
        )

        quote_line.recalculate()

        return quote_line


class QuoteCustomerManager(models.Manager):
    def from_customer(self, customer: Customer):
        quote_customer = self.model.objects.create(
            customer=customer,
            name=customer.name,
            legal_name=customer.legal_name,
            legal_number=customer.legal_number,
            email=customer.email,
            phone=customer.phone,
            description=customer.description,
            address=Address.objects.from_address(customer.address),
            logo=customer.logo.clone() if customer.logo else None,
        )
        quote_customer.tax_ids.set(customer.tax_ids.clone())
        return quote_customer


class QuoteAccountManager(models.Manager):
    def from_account(self, account: Account):
        quote_account = self.model.objects.create(
            account=account,
            name=account.name,
            legal_name=account.legal_name,
            legal_number=account.legal_number,
            email=account.email,
            phone=account.phone,
            address=Address.objects.from_address(account.address),
            logo=account.logo.clone() if account.logo else None,
        )
        quote_account.tax_ids.set(account.tax_ids.clone())
        return quote_account
