import uuid
from datetime import date
from unittest.mock import ANY

import pytest
from freezegun import freeze_time

from apps.quotes.choices import QuoteDeliveryMethod, QuoteStatus
from tests.factories import CustomerFactory, QuoteFactory

pytestmark = pytest.mark.django_db


@freeze_time("2025-04-01T11:00:00Z")
def test_finalize_quote(api_client, user, account, pdf_generator):
    customer = CustomerFactory(account=account)
    quote = QuoteFactory(
        account=account,
        customer=customer,
        number="QT-2025-3001",
        currency="USD",
        issue_date=date(2025, 4, 1),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/quotes/{quote.id}/finalize")

    assert response.status_code == 200
    assert response.data == {
        "id": str(quote.id),
        "status": "open",
        "number": "QT-2025-3001",
        "numbering_system_id": None,
        "currency": "USD",
        "issue_date": "2025-04-01",
        "customer": {
            "id": str(customer.id),
            "name": customer.name,
            "legal_name": customer.legal_name,
            "legal_number": customer.legal_number,
            "email": customer.email,
            "phone": customer.phone,
            "description": customer.description,
            "billing_address": {
                "line1": customer.billing_address.line1,
                "line2": customer.billing_address.line2,
                "locality": customer.billing_address.locality,
                "state": customer.billing_address.state,
                "postal_code": customer.billing_address.postal_code,
                "country": customer.billing_address.country,
            },
            "shipping_address": {
                "line1": customer.shipping_address.line1,
                "line2": customer.shipping_address.line2,
                "locality": customer.shipping_address.locality,
                "state": customer.shipping_address.state,
                "postal_code": customer.shipping_address.postal_code,
                "country": customer.shipping_address.country,
            },
            "logo_id": None,
        },
        "account": {
            "id": str(account.id),
            "name": account.name,
            "legal_name": account.legal_name,
            "legal_number": account.legal_number,
            "email": account.email,
            "phone": account.phone,
            "address": {
                "line1": account.address.line1,
                "line2": account.address.line2,
                "locality": account.address.locality,
                "state": account.address.state,
                "postal_code": account.address.postal_code,
                "country": account.address.country,
            },
            "logo_id": None,
        },
        "metadata": {},
        "custom_fields": {},
        "footer": None,
        "description": None,
        "delivery_method": QuoteDeliveryMethod.MANUAL,
        "recipients": [],
        "subtotal_amount": "0.00",
        "total_discount_amount": "0.00",
        "total_amount_excluding_tax": "0.00",
        "total_tax_amount": "0.00",
        "total_amount": "0.00",
        "created_at": "2025-04-01T11:00:00Z",
        "updated_at": "2025-04-01T11:00:00Z",
        "opened_at": "2025-04-01T11:00:00Z",
        "accepted_at": None,
        "canceled_at": None,
        "pdf_id": ANY,
        "invoice_id": None,
        "lines": [],
        "discounts": [],
        "taxes": [],
    }
    assert len(pdf_generator.requests) == 1


def test_finalize_quote_with_automatic_delivery(api_client, user, account, pdf_generator, mailoutbox):
    customer = CustomerFactory(account=account)
    quote = QuoteFactory(
        account=account,
        customer=customer,
        number="QT-2025-3002",
        delivery_method=QuoteDeliveryMethod.AUTOMATIC,
        recipients=["test@example.com"],
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/quotes/{quote.id}/finalize")

    assert response.status_code == 200
    assert len(pdf_generator.requests) == 1
    assert len(mailoutbox) == 1
    email = mailoutbox[0]
    assert email.subject == f"Quote {quote.number} from {account.name}"
    assert email.to == ["test@example.com"]


def test_finalize_quote_with_no_recipients(api_client, user, account, pdf_generator, mailoutbox):
    customer = CustomerFactory(account=account)
    quote = QuoteFactory(
        account=account,
        customer=customer,
        number="QT-2025-300",
        delivery_method=QuoteDeliveryMethod.AUTOMATIC,
        recipients=[],
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/quotes/{quote.id}/finalize")

    assert response.status_code == 200
    assert len(pdf_generator.requests) == 1
    assert len(mailoutbox) == 0


def test_finalize_quote_not_found(api_client, user, account):
    quote_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/quotes/{quote_id}/finalize")

    assert response.status_code == 404
    assert response.data == {
        "type": "client_error",
        "errors": [
            {
                "attr": None,
                "code": "not_found",
                "detail": "Not found.",
            }
        ],
    }


@pytest.mark.parametrize("status", [QuoteStatus.OPEN, QuoteStatus.ACCEPTED, QuoteStatus.CANCELED])
def test_finalize_quote_requires_draft(api_client, user, account, status):
    quote = QuoteFactory(account=account, currency="USD", status=status, number="QT-4001")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/quotes/{quote.id}/finalize")

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Only draft quotes can be finalized",
            }
        ],
    }


def test_finalize_quote_without_number_or_numbering_system(api_client, user, account):
    quote = QuoteFactory(account=account, currency="USD", status=QuoteStatus.DRAFT, number=None, numbering_system=None)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/quotes/{quote.id}/finalize")

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Number or numbering system is required before finalizing a quote",
            }
        ],
    }


def test_finalize_quote_requires_authentication(api_client):
    quote_id = uuid.uuid4()

    response = api_client.post(f"/api/v1/quotes/{quote_id}/finalize")

    assert response.status_code == 403
    assert response.data == {
        "type": "client_error",
        "errors": [
            {
                "attr": None,
                "code": "not_authenticated",
                "detail": "Authentication credentials were not provided.",
            }
        ],
    }


def test_finalize_quote_requires_account(api_client, user):
    quote_id = uuid.uuid4()

    api_client.force_login(user)
    response = api_client.post(f"/api/v1/quotes/{quote_id}/finalize")

    assert response.status_code == 403
    assert response.data == {
        "type": "client_error",
        "errors": [
            {
                "attr": None,
                "code": "permission_denied",
                "detail": "You do not have permission to perform this action.",
            }
        ],
    }
