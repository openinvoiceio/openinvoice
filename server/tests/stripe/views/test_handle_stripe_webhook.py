import pytest
import stripe

from apps.stripe.models import StripeSubscription
from tests.factories import StripeCustomerFactory, StripeSubscriptionFactory

pytestmark = pytest.mark.django_db


def test_stripe_webhook_subscription_created(api_client, mock_construct_event):
    assert not StripeSubscription.objects.filter(subscription_id="sub_123").exists()
    StripeCustomerFactory(customer_id="cus_123")
    event = stripe.Event.construct_from(
        {
            "id": "evt_123",
            "type": "customer.subscription.created",
            "data": {
                "object": {
                    "id": "sub_123",
                    "customer": "cus_123",
                    "items": {"data": [{"price": {"id": "price_123", "product": {"name": "Basic"}}}]},
                    "status": "active",
                    "current_period_start": 0,
                }
            },
        },
        key="sk_test_dummy",
    )
    mock_construct_event.return_value = event

    response = api_client.post(
        "/api/v1/stripe/webhook",
        data="{}",
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE="sig",
    )

    assert response.status_code == 200
    mock_construct_event.assert_called_once()
    assert StripeSubscription.objects.filter(subscription_id="sub_123").exists()


def test_stripe_webhook_subscription_updated(api_client, mock_construct_event):
    stripe_customer = StripeCustomerFactory(customer_id="cus_123")
    stripe_subscription = StripeSubscriptionFactory(
        subscription_id="sub_123", stripe_customer=stripe_customer, product_name="Basic", status="trialing"
    )
    event = stripe.Event.construct_from(
        {
            "id": "evt_123",
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "id": "sub_123",
                    "customer": "cus_123",
                    "items": {"data": [{"price": {"id": "price_123", "product": {"name": "Pro"}}}]},
                    "status": "active",
                    "current_period_start": 0,
                    "canceled_at": None,
                    "ended_at": None,
                }
            },
        },
        key="sk_test_dummy",
    )
    mock_construct_event.return_value = event

    response = api_client.post(
        "/api/v1/stripe/webhook",
        data="{}",
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE="sig",
    )

    assert response.status_code == 200
    stripe_subscription.refresh_from_db()
    assert stripe_subscription.price_id == "price_123"
    assert stripe_subscription.status == "active"
    assert stripe_subscription.canceled_at is None
    assert stripe_subscription.ended_at is None


def test_stripe_webhook_subscription_deleted(api_client, mock_construct_event):
    stripe_customer = StripeCustomerFactory(customer_id="cus_123")
    stripe_subscription = StripeSubscriptionFactory(
        subscription_id="sub_123",
        stripe_customer=stripe_customer,
        product_name="Pro",
        status="active",
    )
    event = stripe.Event.construct_from(
        {
            "id": "evt_123",
            "type": "customer.subscription.deleted",
            "data": {
                "object": {
                    "id": "sub_123",
                    "customer": "cus_123",
                    "items": {"data": [{"price": {"id": "price_123", "product": {"name": "Pro"}}}]},
                    "status": "canceled",
                    "canceled_at": 0,
                    "ended_at": 0,
                }
            },
        },
        key="sk_test_dummy",
    )
    mock_construct_event.return_value = event

    response = api_client.post(
        "/api/v1/stripe/webhook",
        data="{}",
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE="sig",
    )

    assert response.status_code == 200
    stripe_subscription.refresh_from_db()
    assert stripe_subscription.status == "canceled"


def test_stripe_webhook_unhandled_event(api_client, mock_construct_event):
    event = stripe.Event.construct_from(
        {
            "id": "evt_123",
            "type": "customer.subscription.unhandled_event",
            "data": {
                "object": {
                    "id": "sub_123",
                    "customer": "cus_123",
                    "items": {"data": [{"price": {"id": "price_123", "product": {"name": "Pro"}}}]},
                    "status": "active",
                    "current_period_start": 0,
                }
            },
        },
        key="sk_test_dummy",
    )
    mock_construct_event.return_value = event

    response = api_client.post(
        "/api/v1/stripe/webhook",
        data="{}",
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE="sig",
    )

    assert response.status_code == 200
    assert StripeSubscription.objects.count() == 0


def test_stripe_webhook_invalid_signature(api_client, mock_construct_event):
    mock_construct_event.side_effect = stripe.error.SignatureVerificationError("bad", "sig")

    response = api_client.post(
        "/api/v1/stripe/webhook",
        data="{}",
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE="sig",
    )

    assert response.status_code == 400
    assert response.data is None


def test_stripe_webhook_invalid_payload(api_client, mock_construct_event):
    mock_construct_event.side_effect = ValueError("bad")

    response = api_client.post(
        "/api/v1/stripe/webhook",
        data="{}",
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE="sig",
    )

    assert response.status_code == 400
    assert response.data is None
