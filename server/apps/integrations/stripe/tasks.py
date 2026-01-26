from datetime import UTC, datetime

import stripe
import structlog

from apps.payments.models import Payment

logger = structlog.get_logger(__name__)


def handle_checkout_session_completed_event(event: stripe.Event) -> None:
    session_data = event["data"]["object"]
    created_at = datetime.fromtimestamp(session_data["created"], tz=UTC)
    payment = Payment.objects.get(id=session_data.get("client_reference_id"))
    payment.complete(extra_data=event, received_at=created_at)
    logger.info("Stripe payment succeeded", payment_id=str(payment.id))


def handle_checkout_async_payment_succeeded_event(event: stripe.Event) -> None:
    session_data = event["data"]["object"]
    created_at = datetime.fromtimestamp(session_data["created"], tz=UTC)
    payment = Payment.objects.get(id=session_data.get("client_reference_id"))
    payment.complete(extra_data=event, received_at=created_at)
    logger.info("Stripe payment succeeded", payment_id=str(payment.id))


def handle_checkout_async_payment_failed_event(event: stripe.Event) -> None:
    session_data = event["data"]["object"]
    created_at = datetime.fromtimestamp(session_data["created"], tz=UTC)
    payment = Payment.objects.get(id=session_data.get("client_reference_id"))
    message = (
        session_data.get("last_payment_error", {}).get("message") or session_data.get("status") or "payment_failed"
    )
    payment.fail(message=message, extra_data=event, received_at=created_at)
    logger.info("Stripe payment failed", payment_id=str(payment.id))


def handle_checkout_session_expired_event(event: stripe.Event) -> None:
    session_data = event["data"]["object"]
    created_at = datetime.fromtimestamp(session_data["created"], tz=UTC)
    payment = Payment.objects.get(id=session_data.get("client_reference_id"))
    message = session_data.get("message", "Checkout session expired")
    payment.reject(message=message, extra_data=event, received_at=created_at)
    logger.info("Stripe payment expired", payment_id=str(payment.id))
