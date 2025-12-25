from datetime import UTC, datetime
from typing import TYPE_CHECKING

import stripe
import structlog
from djmoney.money import Money
from stripe import StripeError

from apps.integrations.models import StripeConnection
from apps.payments.enums import PaymentStatus
from apps.payments.exceptions import PaymentCheckoutError
from apps.payments.models import Payment

from .base import PaymentBackend

if TYPE_CHECKING:
    from apps.invoices.models import Invoice

DEFAULT_SUCCESS_URL = "https://stripe.com"
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

logger = structlog.get_logger(__name__)


def convert_amount(amount: Money) -> int:
    currency = str(amount.currency).lower()
    factor = 1 if currency in ZERO_DECIMAL_CURRENCIES else 100
    return int((amount.amount * factor).to_integral_value())


class StripeBackend(PaymentBackend):
    def __init__(self, connection: StripeConnection) -> None:
        self.connection = connection

    def checkout(self, *, invoice: "Invoice", payment: Payment) -> tuple[str, str | None]:
        try:
            session = stripe.checkout.Session.create(
                mode="payment",
                stripe_account=self.connection.connected_account_id,
                customer_email=invoice.customer.email,
                client_reference_id=str(payment.id),
                success_url=self.connection.redirect_url or DEFAULT_SUCCESS_URL,
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

    @classmethod
    def process_event(cls, event: stripe.Event) -> None:
        match event.get("type"):
            case "checkout.session.completed" | "checkout.session.async_payment_succeeded":
                session = event["data"]["object"]
                payment_id = session.get("client_reference_id")

                try:
                    payment = Payment.objects.get(id=payment_id)
                except Payment.DoesNotExist:
                    return

                payment.status = PaymentStatus.SUCCEEDED
                payment.message = None
                payment.extra_data = event
                payment.received_at = datetime.fromtimestamp(session.get("created"), tz=UTC)  # TODO: pick better field
                payment.save(update_fields=["received_at", "extra_data", "status", "message"])

                for invoice in payment.invoices.all():
                    invoice.recalculate_paid()

                logger.info(
                    "Stripe payment succeeded",
                    payment_id=str(payment.id),
                    transaction_id=payment.transaction_id,
                )

            case "checkout.session.async_payment_failed":
                session = event["data"]["object"]
                payment_id = session.get("client_reference_id")

                try:
                    payment = Payment.objects.get(id=payment_id)
                except Payment.DoesNotExist:
                    return

                payment.status = PaymentStatus.FAILED
                payment.message = (
                    session.get("last_payment_error", {}).get("message") or session.get("status") or "payment_failed"
                )
                payment.extra_data = event
                payment.received_at = datetime.fromtimestamp(session.get("created"), tz=UTC)  # TODO: pick better field
                payment.save(update_fields=["received_at", "extra_data", "status", "message"])

                logger.info(
                    "Stripe payment failed",
                    payment_id=str(payment.id),
                    transaction_id=payment.transaction_id,
                    error=payment.message,
                )

            case "checkout.session.expired":
                session = event["data"]["object"]
                payment_id = session.get("client_reference_id")

                try:
                    payment = Payment.objects.get(id=payment_id)
                except Payment.DoesNotExist:
                    return

                payment.extra_data = event
                payment.status = PaymentStatus.REJECTED
                payment.message = session.get("message") or "expired"
                payment.save(update_fields=["received_at", "extra_data", "status", "message"])

                logger.warning(
                    "Stripe payment expired",
                    payment_id=str(payment.id),
                    transaction_id=payment.transaction_id,
                )

            case _:
                logger.info("Stripe event ignored", event_type=event.get("type"))
                return
