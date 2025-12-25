from datetime import date
from unittest.mock import ANY

import pytest
from freezegun import freeze_time

from apps.quotes.enums import QuoteStatus
from tests.factories import CustomerFactory, QuoteFactory

pytestmark = pytest.mark.django_db


@freeze_time("2025-01-15T10:00:00Z")
def test_list_quotes(api_client, user, account):
    customer = CustomerFactory(account=account)
    quote_1 = QuoteFactory(account=account, customer=customer, number="QT-2025-0001", currency="USD")
    quote_2 = QuoteFactory(
        account=account,
        customer=customer,
        number="QT-2025-0002",
        currency="USD",
        status=QuoteStatus.DRAFT,
        issue_date=date(2025, 1, 11),
        metadata={"channel": "direct"},
        custom_fields={"po_number": "PO-456"},
        footer="Warm regards",
        description="February retainer",
    )
    QuoteFactory()  # other account

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/quotes")

    assert response.status_code == 200
    assert response.data == {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": str(quote.id),
                "status": quote.status,
                "number": quote.number,
                "numbering_system_id": None,
                "currency": quote.currency,
                "issue_date": quote.issue_date.isoformat(),
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
                "metadata": quote.metadata,
                "custom_fields": quote.custom_fields,
                "footer": quote.footer,
                "description": quote.description,
                "delivery_method": quote.delivery_method,
                "recipients": quote.recipients,
                "subtotal_amount": "0.00",
                "total_discount_amount": "0.00",
                "total_amount_excluding_tax": "0.00",
                "total_tax_amount": "0.00",
                "total_amount": "0.00",
                "created_at": "2025-01-15T10:00:00Z",
                "updated_at": "2025-01-15T10:00:00Z",
                "opened_at": None,
                "accepted_at": None,
                "canceled_at": None,
                "pdf_id": ANY,
                "invoice_id": None,
                "lines": [],
                "discounts": [],
                "taxes": [],
            }
            for quote in [quote_1, quote_2]
        ],
    }


# TODO: add filtering, ordering, search tests


def test_list_quotes_requires_authentication(api_client):
    response = api_client.get("/api/v1/quotes")

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


def test_list_quotes_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.get("/api/v1/quotes")

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
