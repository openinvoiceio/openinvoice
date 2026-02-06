import uuid
from unittest.mock import ANY

import pytest
from freezegun import freeze_time

from openinvoice.core.choices import FeatureCode, LimitCode
from openinvoice.quotes.choices import QuoteDeliveryMethod
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
        },
    )

    assert response.status_code == 201
    assert response.data == {
        "id": ANY,
        "status": "draft",
        "number": "QT-0007",
        "numbering_system_id": None,
        "currency": customer.default_billing_profile.currency,
        "issue_date": "2025-02-01",
        "billing_profile": {
            "id": str(customer.default_billing_profile.id),
            "legal_name": customer.default_billing_profile.legal_name,
            "legal_number": customer.default_billing_profile.legal_number,
            "email": customer.default_billing_profile.email,
            "phone": customer.default_billing_profile.phone,
            "address": {
                "line1": customer.default_billing_profile.address.line1,
                "line2": customer.default_billing_profile.address.line2,
                "locality": customer.default_billing_profile.address.locality,
                "state": customer.default_billing_profile.address.state,
                "postal_code": customer.default_billing_profile.address.postal_code,
                "country": str(customer.default_billing_profile.address.country),
            },
            "currency": customer.default_billing_profile.currency,
            "language": customer.default_billing_profile.language,
            "net_payment_term": customer.default_billing_profile.net_payment_term,
            "invoice_numbering_system_id": customer.default_billing_profile.invoice_numbering_system_id,
            "credit_note_numbering_system_id": customer.default_billing_profile.credit_note_numbering_system_id,
            "tax_rates": [],
            "tax_ids": [],
            "created_at": ANY,
            "updated_at": ANY,
        },
        "business_profile": {
            "id": str(account.default_business_profile.id),
            "legal_name": account.default_business_profile.legal_name,
            "legal_number": account.default_business_profile.legal_number,
            "email": account.default_business_profile.email,
            "phone": account.default_business_profile.phone,
            "address": {
                "line1": account.default_business_profile.address.line1,
                "line2": account.default_business_profile.address.line2,
                "locality": account.default_business_profile.address.locality,
                "state": account.default_business_profile.address.state,
                "postal_code": account.default_business_profile.address.postal_code,
                "country": str(account.default_business_profile.address.country),
            },
            "tax_ids": [],
            "created_at": ANY,
            "updated_at": ANY,
        },
        "metadata": {"channel": "partner"},
        "custom_fields": {"po_number": "PO-9001"},
        "footer": "Thank you for your business",
        "delivery_method": QuoteDeliveryMethod.MANUAL,
        "recipients": [customer.default_billing_profile.email],
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
