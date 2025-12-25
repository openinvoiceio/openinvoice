import uuid
from unittest.mock import ANY

import pytest
from django.conf import settings
from drf_standardized_errors.types import ErrorType

from tests.factories import CustomerFactory, TaxRateFactory

pytestmark = pytest.mark.django_db


def test_assign_customer_tax_rate(api_client, user, account):
    tax_rate = TaxRateFactory(account=account)
    customer = CustomerFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/customers/{customer.id}/tax-rates",
        {"tax_rate_id": str(tax_rate.id)},
    )

    customer.refresh_from_db()

    assert response.status_code == 200
    assert response.data == {
        "id": str(customer.id),
        "account_id": str(customer.account_id),
        "name": customer.name,
        "legal_name": customer.legal_name,
        "legal_number": customer.legal_number,
        "email": customer.email,
        "phone": customer.phone,
        "currency": customer.currency,
        "net_payment_term": customer.net_payment_term,
        "invoice_numbering_system_id": None,
        "credit_note_numbering_system_id": None,
        "description": customer.description,
        "metadata": customer.metadata,
        "billing_address": {
            "country": customer.billing_address.country,
            "line1": customer.billing_address.line1,
            "line2": customer.billing_address.line2,
            "locality": customer.billing_address.locality,
            "postal_code": customer.billing_address.postal_code,
            "state": customer.billing_address.state,
        },
        "shipping_address": {
            "country": customer.shipping_address.country,
            "line1": customer.shipping_address.line1,
            "line2": customer.shipping_address.line2,
            "locality": customer.shipping_address.locality,
            "postal_code": customer.shipping_address.postal_code,
            "state": customer.shipping_address.state,
        },
        "tax_rates": [
            {
                "id": str(tax_rate.id),
                "account_id": str(tax_rate.account_id),
                "name": tax_rate.name,
                "description": tax_rate.description,
                "percentage": str(tax_rate.percentage),
                "country": tax_rate.country,
                "is_active": tax_rate.is_active,
                "created_at": ANY,
                "updated_at": ANY,
            }
        ],
        "tax_ids": [],
        "logo_id": None,
        "logo_url": None,
        "created_at": ANY,
        "updated_at": ANY,
    }


def test_assign_customer_tax_rate_duplicate(api_client, user, account):
    tax_rate = TaxRateFactory(account=account)
    customer = CustomerFactory(account=account)
    customer.tax_rates.add(tax_rate)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/customers/{customer.id}/tax-rates",
        {"tax_rate_id": str(tax_rate.id)},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Tax rate already assigned",
            }
        ],
    }


def test_assign_customer_tax_rate_limit(api_client, user, account):
    limit = settings.CUSTOMER_TAX_RATES_LIMIT
    tax_rates = [TaxRateFactory(account=account) for _ in range(limit + 1)]
    customer = CustomerFactory(account=account)
    customer.tax_rates.add(*tax_rates[:limit])

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/customers/{customer.id}/tax-rates",
        {"tax_rate_id": str(tax_rates[limit].id)},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": f"At most {settings.CUSTOMER_TAX_RATES_LIMIT} tax rates are allowed",
            }
        ],
    }


def test_assign_customer_tax_rate_tax_rate_not_found(api_client, user, account):
    customer = CustomerFactory(account=account)
    tax_rate_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/customers/{customer.id}/tax-rates",
        {"tax_rate_id": str(tax_rate_id)},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "tax_rate_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{tax_rate_id}" - object does not exist.',
            }
        ],
    }


def test_assign_customer_tax_rate_customer_not_found(api_client, user, account):
    tax_rate = TaxRateFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/customers/{uuid.uuid4()}/tax-rates",
        {"tax_rate_id": str(tax_rate.id)},
    )

    assert response.status_code == 404
    assert response.data == {
        "type": ErrorType.CLIENT_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "not_found",
                "detail": "Not found.",
            }
        ],
    }


def test_assign_customer_tax_rate_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.post(
        f"/api/v1/customers/{uuid.uuid4()}/tax-rates",
        {"tax_rate_id": str(uuid.uuid4())},
    )

    assert response.status_code == 403
    assert response.data == {
        "type": ErrorType.CLIENT_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "permission_denied",
                "detail": "You do not have permission to perform this action.",
            }
        ],
    }


def test_assign_customer_tax_rate_requires_authentication(api_client, account):
    customer = CustomerFactory(account=account)
    tax_rate = TaxRateFactory(account=account)

    response = api_client.post(
        f"/api/v1/customers/{customer.id}/tax-rates",
        {"tax_rate_id": str(tax_rate.id)},
    )

    assert response.status_code == 403
    assert response.data == {
        "type": ErrorType.CLIENT_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "not_authenticated",
                "detail": "Authentication credentials were not provided.",
            }
        ],
    }
