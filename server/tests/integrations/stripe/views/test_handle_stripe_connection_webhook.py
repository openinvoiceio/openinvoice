import json
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import patch

import pytest

from apps.integrations.choices import PaymentProvider
from apps.invoices.choices import InvoiceStatus
from apps.payments.choices import PaymentStatus
from tests.factories import (
    InvoiceFactory,
    PaymentFactory,
    StripeConnectionFactory,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def construct_event_mock():
    with patch("apps.integrations.stripe.views.stripe.Webhook.construct_event") as mock:
        yield mock


@pytest.mark.parametrize("event_type", ["checkout.session.completed", "checkout.session.async_payment_succeeded"])
def test_process_stripe_checkout_completed_webhook(api_client, account, construct_event_mock, event_type):
    connection = StripeConnectionFactory(account=account)
    invoice = InvoiceFactory(
        account=account,
        status=InvoiceStatus.OPEN,
        total_amount=Decimal("10.00"),
        outstanding_amount=Decimal("10.00"),
        payment_provider=PaymentProvider.STRIPE,
        payment_connection_id=connection.id,
    )
    payment = PaymentFactory(
        account=account,
        status=PaymentStatus.PENDING,
        amount=Decimal("10.00"),
        provider=PaymentProvider.STRIPE,
        connection_id=connection.id,
        transaction_id="cs_123",
    )
    payment.invoices.add(invoice)

    received_at = datetime.now(UTC)
    event = {
        "type": event_type,
        "data": {
            "object": {
                "client_reference_id": str(payment.id),
                "created": received_at.timestamp(),
            }
        },
    }

    construct_event_mock.side_effect = lambda **_: event

    response = api_client.post(
        f"/api/v1/integrations/stripe/connections/{connection.id}/webhook",
        data=json.dumps(event),
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE="t=1,v1=abc",
    )

    assert response.status_code == 200
    assert response.content == b""
    payment.refresh_from_db()
    assert payment.status == PaymentStatus.SUCCEEDED
    assert payment.message is None
    assert payment.extra_data == event
    assert payment.received_at == received_at
    invoice.refresh_from_db()
    assert invoice.status == InvoiceStatus.PAID
    assert invoice.outstanding_amount.amount == Decimal("0.00")


def test_process_stripe_checkout_completed_webhook_payment_not_found(api_client, account, construct_event_mock):
    connection = StripeConnectionFactory(account=account)

    received_at = datetime.now(UTC)
    event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "client_reference_id": str(uuid.uuid4()),
                "created": received_at.timestamp(),
            }
        },
    }

    construct_event_mock.side_effect = lambda **_: event

    response = api_client.post(
        f"/api/v1/integrations/stripe/connections/{connection.id}/webhook",
        data=json.dumps(event),
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE="t=1,v1=abc",
    )

    assert response.status_code == 400
    assert response.content == b""


def test_process_stripe_checkout_payment_failed_webhook(api_client, account, construct_event_mock):
    connection = StripeConnectionFactory(account=account)
    invoice = InvoiceFactory(
        account=account,
        status=InvoiceStatus.OPEN,
        total_amount=Decimal("10.00"),
        outstanding_amount=Decimal("10.00"),
        payment_provider=PaymentProvider.STRIPE,
        payment_connection_id=connection.id,
    )
    payment = PaymentFactory(
        account=account,
        status=PaymentStatus.PENDING,
        amount=Decimal("10.00"),
        provider=PaymentProvider.STRIPE,
        connection_id=connection.id,
        transaction_id="cs_123",
    )
    payment.invoices.add(invoice)

    received_at = datetime.now(UTC)
    event = {
        "type": "checkout.session.async_payment_failed",
        "data": {
            "object": {
                "client_reference_id": str(payment.id),
                "last_payment_error": {"message": "Card declined"},
                "created": received_at.timestamp(),
            }
        },
    }
    construct_event_mock.side_effect = lambda **_: event

    response = api_client.post(
        f"/api/v1/integrations/stripe/connections/{connection.id}/webhook",
        data=json.dumps(event),
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE="t=1,v1=abc",
    )

    assert response.status_code == 200
    payment.refresh_from_db()
    assert payment.status == PaymentStatus.FAILED
    assert payment.message == "Card declined"
    assert payment.extra_data == event
    assert payment.received_at == received_at
    invoice.refresh_from_db()
    assert invoice.status == InvoiceStatus.OPEN
    assert invoice.outstanding_amount.amount == Decimal("10.00")


def test_process_stripe_checkout_payment_failed_webhook_payment_not_found(api_client, account, construct_event_mock):
    connection = StripeConnectionFactory(account=account)

    received_at = datetime.now(UTC)
    event = {
        "type": "checkout.session.async_payment_failed",
        "data": {
            "object": {
                "client_reference_id": str(uuid.uuid4()),
                "last_payment_error": {"message": "Card declined"},
                "created": received_at.timestamp(),
            }
        },
    }
    construct_event_mock.side_effect = lambda **_: event

    response = api_client.post(
        f"/api/v1/integrations/stripe/connections/{connection.id}/webhook",
        data=json.dumps(event),
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE="t=1,v1=abc",
    )

    assert response.status_code == 400
    assert response.content == b""


def test_process_stripe_checkout_expired_webhook(api_client, account, construct_event_mock):
    connection = StripeConnectionFactory(account=account)
    invoice = InvoiceFactory(
        account=account,
        status=InvoiceStatus.OPEN,
        total_amount=Decimal("10.00"),
        outstanding_amount=Decimal("10.00"),
        payment_provider=PaymentProvider.STRIPE,
        payment_connection_id=connection.id,
    )
    payment = PaymentFactory(
        account=account,
        status=PaymentStatus.PENDING,
        amount=Decimal("10.00"),
        provider=PaymentProvider.STRIPE,
        connection_id=connection.id,
        transaction_id="cs_123",
    )
    payment.invoices.add(invoice)

    received_at = datetime.now(UTC)
    event = {
        "type": "checkout.session.expired",
        "data": {
            "object": {
                "client_reference_id": str(payment.id),
                "status": "expired",
                "created": received_at.timestamp(),
            }
        },
    }
    construct_event_mock.side_effect = lambda **_: event

    response = api_client.post(
        f"/api/v1/integrations/stripe/connections/{connection.id}/webhook",
        data=json.dumps(event),
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE="t=1,v1=abc",
    )

    assert response.status_code == 200
    payment.refresh_from_db()
    assert payment.status == PaymentStatus.REJECTED
    assert payment.message == "Checkout session expired"
    assert payment.extra_data == event
    invoice.refresh_from_db()
    assert invoice.status == InvoiceStatus.OPEN
    assert invoice.outstanding_amount.amount == Decimal("10.00")


def test_process_stripe_checkout_expired_webhook_payment_not_found(api_client, account, construct_event_mock):
    connection = StripeConnectionFactory(account=account)

    received_at = datetime.now(UTC)
    event = {
        "type": "checkout.session.expired",
        "data": {
            "object": {
                "client_reference_id": str(uuid.uuid4()),
                "status": "expired",
                "created": received_at.timestamp(),
            }
        },
    }
    construct_event_mock.side_effect = lambda **_: event

    response = api_client.post(
        f"/api/v1/integrations/stripe/connections/{connection.id}/webhook",
        data=json.dumps(event),
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE="t=1,v1=abc",
    )

    assert response.status_code == 400
    assert response.content == b""
