from typing import TYPE_CHECKING
from uuid import UUID

import stripe
import structlog
from djmoney.money import Money
from stripe import StripeError

from apps.payments.backend import PaymentBackend
from apps.payments.exceptions import PaymentBackendNotFoundError, PaymentCheckoutError
from apps.payments.models import Payment

from .models import StripeConnection

if TYPE_CHECKING:
    from apps.invoices.models import Invoice

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


class StripePaymentBackend(PaymentBackend):
    default_success_url = "https://stripe.com"

    def __init__(self, connection: StripeConnection) -> None:
        self.connection = connection
        self.client = stripe.StripeClient(api_key=connection.api_key)

    @classmethod
    def from_account(cls, account_id: UUID, connection_id: UUID) -> "StripePaymentBackend":
        try:
            connection = StripeConnection.objects.get(account_id=account_id, id=connection_id)
        except StripeConnection.DoesNotExist as e:
            raise PaymentBackendNotFoundError from e
        return cls(connection)

    def checkout(self, invoice: "Invoice", payment: Payment) -> tuple[str, str | None]:
        try:
            session = self.client.checkout.Session.create(
                mode="payment",
                customer_email=invoice.customer.email,
                client_reference_id=str(payment.id),
                success_url=self.connection.redirect_url or self.default_success_url,
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
            raise PaymentCheckoutError from e

        return session.id, getattr(session, "url", None)
