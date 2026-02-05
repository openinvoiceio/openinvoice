from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.db import models
from djmoney.money import Money

from openinvoice.accounts.models import Account, BusinessProfile
from openinvoice.core.calculations import zero
from openinvoice.customers.models import BillingProfile, Customer
from openinvoice.numbering_systems.models import NumberingSystem
from openinvoice.prices.models import Price

from .choices import QuoteDeliveryMethod, QuoteStatus


class QuoteManager(models.Manager):
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
        metadata: dict | None = None,
        custom_fields: dict | None = None,
        footer: str | None = None,
        delivery_method: QuoteDeliveryMethod | None = None,
        recipients: list[str] | None = None,
    ):
        billing_profile = billing_profile or customer.default_billing_profile
        business_profile = business_profile or account.default_business_profile
        currency = currency or billing_profile.currency or account.default_currency
        resolved_numbering_system = None

        if number is None:
            resolved_numbering_system = numbering_system
        # TODO: add default quote numbering system for customer and account
        #     resolved_numbering_system = (
        #         numbering_system or customer.invoice_numbering_system or account.invoice_numbering_system
        #     )

        default_recipients = [billing_profile.email] if billing_profile.email else []

        quote = self.create(
            account=account,
            customer=customer,
            billing_profile=billing_profile,
            business_profile=business_profile,
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

        for tax_rate in billing_profile.tax_rates.active():
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
