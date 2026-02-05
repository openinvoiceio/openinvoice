import uuid
from datetime import date
from unittest.mock import ANY

import pytest
from freezegun import freeze_time

from openinvoice.quotes.choices import QuoteStatus
from tests.factories import CustomerFactory, QuoteFactory

pytestmark = pytest.mark.django_db


@freeze_time("2025-02-01T09:00:00Z")
def test_retrieve_quote(api_client, user, account):
    customer = CustomerFactory(account=account)
    quote = QuoteFactory(
        account=account,
        customer=customer,
        number="QT-2025-2001",
        currency="EUR",
        issue_date=date(2025, 2, 1),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/quotes/{quote.id}")

    assert response.status_code == 200
    assert response.data == {
        "id": str(quote.id),
        "status": QuoteStatus.DRAFT,
        "number": "QT-2025-2001",
        "numbering_system_id": None,
        "currency": "EUR",
        "issue_date": "2025-02-01",
        "billing_profile": {
            "id": str(customer.default_billing_profile.id),
            "name": customer.default_billing_profile.name,
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
            "name": account.default_business_profile.name,
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
        "metadata": {},
        "custom_fields": {},
        "footer": None,
        "delivery_method": quote.delivery_method,
        "recipients": quote.recipients,
        "subtotal_amount": "0.00",
        "total_discount_amount": "0.00",
        "total_amount_excluding_tax": "0.00",
        "total_tax_amount": "0.00",
        "total_amount": "0.00",
        "created_at": "2025-02-01T09:00:00Z",
        "updated_at": "2025-02-01T09:00:00Z",
        "opened_at": None,
        "accepted_at": None,
        "canceled_at": None,
        "pdf_id": None,
        "invoice_id": None,
        "lines": [],
        "discounts": [],
        "taxes": [],
    }


def test_retrieve_quote_not_found(api_client, user, account):
    quote_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/quotes/{quote_id}")

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


def test_retrieve_quote_requires_authentication(api_client, account):
    quote = QuoteFactory(account=account)

    response = api_client.get(f"/api/v1/quotes/{quote.id}")

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


def test_retrieve_quote_requires_account(api_client, user):
    quote = QuoteFactory()

    api_client.force_login(user)
    response = api_client.get(f"/api/v1/quotes/{quote.id}")

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
