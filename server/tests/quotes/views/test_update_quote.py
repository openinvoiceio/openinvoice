import uuid
from datetime import date
from unittest.mock import ANY

import pytest
from freezegun import freeze_time

from openinvoice.core.choices import FeatureCode
from openinvoice.quotes.choices import QuoteDeliveryMethod, QuoteStatus
from tests.factories import CustomerFactory, QuoteFactory

pytestmark = pytest.mark.django_db


@freeze_time("2025-03-01T09:00:00Z")
def test_update_quote(api_client, user, account):
    customer = CustomerFactory(account=account)
    quote = QuoteFactory(
        account=account,
        customer=customer,
        number="QT-2025-9001",
        currency="USD",
        issue_date=date(2025, 3, 1),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/quotes/{quote.id}",
        {
            "issue_date": "2025-03-05",
            "number": "QT-2025-9002",
            "currency": "USD",
            "metadata": {"stage": "final"},
            "custom_fields": {"reference": "REF-2"},
            "footer": "Updated footer",
        },
    )

    assert response.status_code == 200
    assert response.data == {
        "id": str(quote.id),
        "status": "draft",
        "number": "QT-2025-9002",
        "numbering_system_id": None,
        "currency": "USD",
        "issue_date": "2025-03-05",
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
        "metadata": {"stage": "final"},
        "custom_fields": {"reference": "REF-2"},
        "footer": "Updated footer",
        "delivery_method": QuoteDeliveryMethod.MANUAL,
        "recipients": [],
        "subtotal_amount": "0.00",
        "total_discount_amount": "0.00",
        "total_amount_excluding_tax": "0.00",
        "total_tax_amount": "0.00",
        "total_amount": "0.00",
        "created_at": "2025-03-01T09:00:00Z",
        "updated_at": "2025-03-01T09:00:00Z",
        "opened_at": None,
        "accepted_at": None,
        "canceled_at": None,
        "pdf_id": None,
        "invoice_id": None,
        "lines": [],
        "discounts": [],
        "taxes": [],
    }


@pytest.mark.parametrize("status", [QuoteStatus.OPEN, QuoteStatus.ACCEPTED, QuoteStatus.CANCELED])
def test_update_quote_requires_draft_status(api_client, user, account, status):
    customer = CustomerFactory(account=account)
    quote = QuoteFactory(
        account=account,
        customer=customer,
        status=status,
        number="QT-2025-9001",
        currency="USD",
        issue_date=date(2025, 3, 1),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/quotes/{quote.id}",
        {
            "issue_date": "2025-03-05",
            "number": "QT-2025-9002",
            "currency": "USD",
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Only draft quotes can be updated",
            }
        ],
    }


def test_update_quote_not_found(api_client, user, account):
    quote_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/quotes/{quote_id}",
        {
            "issue_date": "2025-03-05",
            "number": "QT-2025-9002",
            "currency": "USD",
        },
    )

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


def test_update_quote_with_automatic_delivery_and_without_entitlement(api_client, user, account, settings):
    settings.DEFAULT_PLAN = "test"
    settings.PLANS = {"test": {"features": {FeatureCode.AUTOMATIC_QUOTE_DELIVERY: False}}}
    customer = CustomerFactory(account=account)
    quote = QuoteFactory(
        account=account,
        customer=customer,
        number="QT-2025-9001",
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/quotes/{quote.id}",
        {"delivery_method": QuoteDeliveryMethod.AUTOMATIC},
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


def test_update_quote_invalid_customer(api_client, user, account):
    quote = QuoteFactory(
        account=account,
        number="QT-2025-9001",
        currency="USD",
        issue_date=date(2025, 3, 1),
    )
    customer_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/quotes/{quote.id}",
        {
            "issue_date": "2025-03-05",
            "number": "QT-2025-9002",
            "currency": "USD",
            "customer_id": str(customer_id),
        },
    )

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


def test_update_quote_invalid_numbering_system(api_client, user, account):
    customer = CustomerFactory(account=account)
    quote = QuoteFactory(
        account=account,
        customer=customer,
        number="QT-2025-9001",
        currency="USD",
        issue_date=date(2025, 3, 1),
    )
    numbering_system_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/quotes/{quote.id}",
        {
            "issue_date": "2025-03-05",
            "number": "QT-2025-9002",
            "currency": "USD",
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


def test_update_quote_requires_authentication(api_client):
    quote_id = uuid.uuid4()

    response = api_client.put(
        f"/api/v1/quotes/{quote_id}",
        {
            "issue_date": "2025-03-05",
            "number": "QT-2025-9002",
            "currency": "USD",
        },
    )

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


def test_update_quote_requires_account(api_client, user):
    quote_id = uuid.uuid4()

    api_client.force_login(user)
    response = api_client.put(
        f"/api/v1/quotes/{quote_id}",
        {
            "issue_date": "2025-03-05",
            "number": "QT-2025-9002",
            "currency": "USD",
        },
    )

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
