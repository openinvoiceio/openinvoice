from datetime import UTC, datetime

import stripe
import structlog

from .models import StripeCustomer, StripeSubscription

logger = structlog.get_logger(__name__)


def handle_subscription_created_event(event: stripe.Event) -> StripeSubscription:
    stripe_customer = StripeCustomer.objects.get(customer_id=event.data.object["customer"])
    price_id = event.data.object["items"]["data"][0]["price"]["id"]

    subscription = StripeSubscription.objects.create(
        stripe_customer=stripe_customer,
        subscription_id=event.data.object["id"],
        price_id=price_id,
        product_name="",
        status=event.data.object["status"],
        started_at=datetime.fromtimestamp(event.data.object["current_period_start"], tz=UTC),
    )
    logger.info("Subscription created", data=event, subscription=subscription)
    return subscription


def handle_subscription_updated_event(event: stripe.Event) -> StripeSubscription:
    stripe_customer = StripeCustomer.objects.get(customer_id=event.data.object["customer"])
    price_id = event.data.object["items"]["data"][0]["price"]["id"]
    canceled_at = (
        datetime.fromtimestamp(event.data.object["canceled_at"], tz=UTC) if event.data.object["canceled_at"] else None
    )
    ended_at = datetime.fromtimestamp(event.data.object["ended_at"], tz=UTC) if event.data.object["ended_at"] else None

    subscription, _ = StripeSubscription.objects.update_or_create(
        subscription_id=event.data.object["id"],
        defaults={
            "stripe_customer": stripe_customer,
            "price_id": price_id,
            "status": event.data.object["status"],
            "canceled_at": canceled_at,
            "ended_at": ended_at,
        },
    )
    logger.info("Subscription updated", data=event, subscription=subscription)
    return subscription


def handle_subscription_deleted_event(event: stripe.Event) -> StripeSubscription:
    subscription = handle_subscription_updated_event(event)
    logger.info("Subscription deleted", data=event, subscription=subscription)
    return subscription
