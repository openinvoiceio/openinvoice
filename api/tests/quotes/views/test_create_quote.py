import uuid
from unittest.mock import ANY

import pytest
from freezegun import freeze_time

from apps.quotes.choices import QuoteDeliveryMethod
from common.choices import FeatureCode, LimitCode
from tests.factories import CustomerFactory

pytestmark = pytest.mark.django_db


@freeze_time("2025-01-05T15:45:30Z")
def test_create_quote(api_client, user, account):
    customer = CustomerFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/quotes",
        {
            "customer_id": str(customer.id),
            "issue_date": "2025-02-01",
            "number": "QT-0007",
            "metadata": {"channel": "partner"},
            "custom_fields": {"po_number": "PO-9001"},
            "footer": "Thank you for your business",
            "description": "Quarterly consulting retainer",
        },
    )

    assert response.status_code == 201
    assert response.data == {
        "id": ANY,
        "status": "draft",
        "number": "QT-0007",
        "numbering_system_id": None,
        "currency": customer.currency,
        "issue_date": "2025-02-01",
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
        "metadata": {"channel": "partner"},
        "custom_fields": {"po_number": "PO-9001"},
        "footer": "Thank you for your business",
        "description": "Quarterly consulting retainer",
        "delivery_method": QuoteDeliveryMethod.MANUAL,
        "recipients": [customer.email],
        "subtotal_amount": "0.00",
        "total_discount_amount": "0.00",
        "total_amount_excluding_tax": "0.00",
        "total_tax_amount": "0.00",
        "total_amount": "0.00",
        "created_at": "2025-01-05T15:45:30Z",
        "updated_at": "2025-01-05T15:45:30Z",
        "opened_at": None,
        "accepted_at": None,
        "canceled_at": None,
        "pdf_id": None,
        "invoice_id": None,
        "lines": [],
        "discounts": [],
        "taxes": [],
    }


def test_create_quote_with_automatic_delivery_and_without_entitlement(api_client, user, account, settings):
    settings.DEFAULT_PLAN = "test"
    settings.PLANS = {"test": {"features": {FeatureCode.AUTOMATIC_QUOTE_DELIVERY: False}}}
    customer = CustomerFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/quotes",
        {
            "customer_id": str(customer.id),
            "delivery_method": QuoteDeliveryMethod.AUTOMATIC,
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "delivery_method",
                "code": "invalid",
                "detail": "Automatic delivery is forbidden for your account.",
            }
        ],
    }


def test_create_quote_invalid_customer(api_client, user, account):
    customer_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post("/api/v1/quotes", {"customer_id": str(customer_id)})

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "customer_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{customer_id}" - object does not exist.',
            }
        ],
    }


def test_create_quote_invalid_numbering_system(api_client, user, account):
    customer = CustomerFactory(account=account)
    numbering_system_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/quotes",
        {
            "customer_id": str(customer.id),
            "numbering_system_id": str(numbering_system_id),
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "numbering_system_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{numbering_system_id}" - object does not exist.',
            }
        ],
    }


def test_create_quote_requires_account(api_client, user):
    customer = CustomerFactory()

    api_client.force_login(user)
    response = api_client.post("/api/v1/quotes", {"customer_id": str(customer.id)})

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


def test_create_quote_requires_authentication(api_client, account):
    customer = CustomerFactory(account=account)

    response = api_client.post("/api/v1/quotes", {"customer_id": customer.id})

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


def test_create_quote_limit_exceeded(api_client, user, account, settings):
    settings.DEFAULT_PLAN = "test"
    settings.PLANS = {"test": {"limits": {LimitCode.MAX_QUOTES_PER_MONTH: 0}}}
    customer = CustomerFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/quotes",
        {
            "customer_id": str(customer.id),
        },
    )

    assert response.status_code == 403
    assert response.data == {
        "type": "client_error",
        "errors": [
            {
                "attr": None,
                "code": "limit_exceeded",
                "detail": "Limit has been exceeded for your account.",
            }
        ],
    }
