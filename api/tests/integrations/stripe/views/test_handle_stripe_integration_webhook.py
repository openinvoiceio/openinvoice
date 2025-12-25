import json
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from apps.integrations.enums import PaymentProvider
from apps.invoices.enums import InvoiceStatus
from apps.payments.enums import PaymentStatus
from tests.factories import (
    InvoiceFactory,
    PaymentFactory,
    StripeConnectionFactory,
)

pytestmark = pytest.mark.django_db


def test_process_stripe_checkout_completed_webhook(api_client, account, monkeypatch):
    StripeConnectionFactory(account=account)
    invoice = InvoiceFactory(account=account, status=InvoiceStatus.OPEN, total_amount=Decimal("10.00"))
    payment = PaymentFactory(
        account=account,
        status=PaymentStatus.PENDING,
        amount=Decimal("10.00"),
    )
    payment.provider_provider = PaymentProvider.STRIPE
    payment.transaction_id = "cs_123"
    payment.save()
    payment.invoices.add(invoice)

    session_created = 1_700_000_000
    event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "client_reference_id": str(payment.id),
                "created": session_created,
            }
        },
    }

    def fake_construct_event(**_):
        return event

    monkeypatch.setattr("apps.integrations.stripe.views.stripe.Webhook.construct_event", fake_construct_event)

    response = api_client.post(
        "/api/v1/integrations/stripe/webhook",
        data=json.dumps(event),
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE="t=1,v1=abc",
    )

    assert response.status_code == 200
    payment.refresh_from_db()
    invoice.refresh_from_db()
    assert payment.status == PaymentStatus.SUCCEEDED
    assert payment.message is None
    assert invoice.status == InvoiceStatus.PAID
    assert payment.received_at == datetime.fromtimestamp(session_created, tz=UTC)


def test_process_stripe_checkout_expired_webhook(api_client, account, monkeypatch):
    StripeConnectionFactory(account=account)
    invoice = InvoiceFactory(account=account, status=InvoiceStatus.OPEN, total_amount=Decimal("10.00"))
    payment = PaymentFactory(
        account=account,
        status=PaymentStatus.PENDING,
        amount=Decimal("10.00"),
    )
    payment.provider_provider = PaymentProvider.STRIPE
    payment.transaction_id = "cs_123"
    payment.save()
    payment.invoices.add(invoice)

    event = {
        "type": "checkout.session.expired",
        "data": {
            "object": {
                "client_reference_id": str(payment.id),
                "status": "expired",
                "created": 1_700_000_000,
            }
        },
    }

    def fake_construct_event(**_):
        return event

    monkeypatch.setattr("apps.integrations.stripe.views.stripe.Webhook.construct_event", fake_construct_event)

    response = api_client.post(
        "/api/v1/integrations/stripe/webhook",
        data=json.dumps(event),
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE="t=1,v1=abc",
    )

    assert response.status_code == 200
    payment.refresh_from_db()
    invoice.refresh_from_db()
    assert payment.status == PaymentStatus.REJECTED
    assert payment.message == "expired"
    assert invoice.status == InvoiceStatus.OPEN
