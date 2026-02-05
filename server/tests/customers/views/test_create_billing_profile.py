from unittest.mock import ANY

import pytest

from tests.factories import CustomerFactory, TaxRateFactory

pytestmark = pytest.mark.django_db


def test_create_billing_profile_with_tax_rates(api_client, user, account):
    tax_rate = TaxRateFactory(account=account)
    customer = CustomerFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/billing-profiles",
        {
            "customer_id": str(customer.id),
            "name": "Billing",
            "currency": "USD",
            "tax_rates": [str(tax_rate.id)],
        },
    )

    assert response.status_code == 201
    assert response.data == {
        "id": ANY,
        "name": "Billing",
        "legal_name": None,
        "legal_number": None,
        "email": None,
        "phone": None,
        "address": {
            "line1": None,
            "line2": None,
            "locality": None,
            "state": None,
            "postal_code": None,
            "country": None,
        },
        "currency": "USD",
        "language": None,
        "net_payment_term": None,
        "invoice_numbering_system_id": None,
        "credit_note_numbering_system_id": None,
        "tax_rates": [
            {
                "id": str(tax_rate.id),
                "account_id": str(tax_rate.account_id),
                "name": tax_rate.name,
                "description": tax_rate.description,
                "percentage": f"{tax_rate.percentage:.2f}",
                "country": str(tax_rate.country) if tax_rate.country else None,
                "status": tax_rate.status,
                "created_at": ANY,
                "updated_at": ANY,
                "archived_at": tax_rate.archived_at,
            }
        ],
        "tax_ids": [],
        "created_at": ANY,
        "updated_at": ANY,
    }
