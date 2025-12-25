import uuid
from datetime import date

import pytest
from freezegun import freeze_time

from apps.quotes.enums import QuoteDeliveryMethod, QuoteStatus
from tests.factories import CustomerFactory, QuoteFactory

pytestmark = pytest.mark.django_db


@freeze_time("2025-06-01T10:00:00Z")
def test_cancel_quote(api_client, user, account):
    customer = CustomerFactory(account=account)
    quote = QuoteFactory(
        account=account,
        customer=customer,
        status=QuoteStatus.OPEN,
        number="QT-2025-5001",
        currency="USD",
        issue_date=date(2025, 6, 1),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/quotes/{quote.id}/cancel")

    assert response.status_code == 200
    assert response.data == {
        "id": str(quote.id),
        "status": QuoteStatus.CANCELED,
        "number": "QT-2025-5001",
        "numbering_system_id": None,
        "currency": "USD",
        "issue_date": "2025-06-01",
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
        "created_at": "2025-06-01T10:00:00Z",
        "updated_at": "2025-06-01T10:00:00Z",
        "opened_at": None,
        "accepted_at": None,
        "canceled_at": "2025-06-01T10:00:00Z",
        "pdf_id": None,
        "invoice_id": None,
        "lines": [],
        "discounts": [],
        "taxes": [],
    }


def test_cancel_quote_not_found(api_client, user, account):
    quote_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/quotes/{quote_id}/cancel")

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


def test_cancel_accepted_quote(api_client, user, account):
    quote = QuoteFactory(account=account, number="QT-3001", status=QuoteStatus.ACCEPTED)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/quotes/{quote.id}/cancel")

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Accepted quotes cannot be canceled",
            }
        ],
    }


def test_cancel_quote_already_canceled(api_client, user, account):
    quote = QuoteFactory(account=account, number="QT-4001", status=QuoteStatus.CANCELED)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/quotes/{quote.id}/cancel")

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Quote is already canceled",
            }
        ],
    }


def test_cancel_quote_requires_authentication(api_client):
    quote_id = uuid.uuid4()

    response = api_client.post(f"/api/v1/quotes/{quote_id}/cancel")

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


def test_cancel_quote_requires_account(api_client, user):
    quote_id = uuid.uuid4()

    api_client.force_login(user)
    response = api_client.post(f"/api/v1/quotes/{quote_id}/cancel")

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
