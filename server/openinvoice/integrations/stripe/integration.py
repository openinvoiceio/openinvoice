from typing import TYPE_CHECKING
from uuid import UUID

import stripe
import structlog
from djmoney.money import Money
from stripe import StripeError

from openinvoice.integrations.base import PaymentProviderIntegration
from openinvoice.integrations.exceptions import IntegrationConnectionError, IntegrationError

from .models import StripeConnection

if TYPE_CHECKING:
    from openinvoice.invoices.models import Invoice

logger = structlog.get_logger(__name__)

ZERO_DECIMAL_CURRENCIES = {
    "bif",
    "clp",
    "djf",
    "gnf",
    "jpy",
    "kmf",
    "krw",
    "mga",
    "pyg",
    "rwf",
    "ugx",
    "vnd",
    "vuv",
    "xaf",
    "xpf",
    "xof",
}


def convert_amount(amount: Money) -> int:
    currency = str(amount.currency).lower()
    factor = 1 if currency in ZERO_DECIMAL_CURRENCIES else 100
    return int((amount.amount * factor).to_integral_value())


class StripeIntegration(PaymentProviderIntegration):
    name = "Stripe"
    slug = "stripe"
    description = "Stripe Payment Integration"
    default_success_url = "https://stripe.com"

    def is_enabled(self, account_id: UUID) -> bool:
        return StripeConnection.objects.filter(account_id=account_id).exists()

    def checkout(self, invoice: "Invoice", payment_id: UUID) -> tuple[str, str | None]:
        try:
            connection = StripeConnection.objects.for_account(invoice.account).get(id=invoice.payment_connection_id)
        except StripeConnection.DoesNotExist as e:
            raise IntegrationConnectionError from e

        client = stripe.StripeClient(api_key=connection.api_key)
        try:
            session = client.checkout.sessions.create(
                mode="payment",
                customer_email=invoice.customer.email,
                client_reference_id=str(payment_id),
                success_url=connection.redirect_url or self.default_success_url,
                invoice_creation={"enabled": False},
                line_items=[
                    {
                        "price_data": {
                            "currency": line.currency.lower(),
                            "product_data": {"name": line.description},
                            "unit_amount": convert_amount(line.unit_amount),
                        },
                        "quantity": line.quantity,
                    }
                    for line in invoice.lines.all()
                ],
            )
        except StripeError as e:
            raise IntegrationError from e

        return session.id, getattr(session, "url", None)
