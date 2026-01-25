import uuid

import pytest

from tests.factories import CustomerFactory, TaxRateFactory

pytestmark = pytest.mark.django_db


def test_remove_customer_tax_rate(api_client, user, account):
    tax_rate = TaxRateFactory(account=account)
    customer = CustomerFactory(account=account)
    customer.tax_rates.add(tax_rate)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/customers/{customer.id}/tax-rates/{tax_rate.id}")

    assert response.status_code == 204


def test_remove_customer_tax_rate_tax_rate_not_found(api_client, user, account):
    customer = CustomerFactory(account=account)
    tax_rate_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/customers/{customer.id}/tax-rates/{tax_rate_id}")

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


def test_remove_customer_tax_rate_customer_not_found(api_client, user, account):
    tax_rate = TaxRateFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/customers/{uuid.uuid4()}/tax-rates/{tax_rate.id}")

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


def test_remove_customer_tax_rate_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.delete(f"/api/v1/customers/{uuid.uuid4()}/tax-rates/{uuid.uuid4()}")

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


def test_remove_customer_tax_rate_requires_authentication(api_client, account):
    tax_rate = TaxRateFactory(account=account)
    customer = CustomerFactory(account=account)
    customer.tax_rates.add(tax_rate)

    response = api_client.delete(f"/api/v1/customers/{customer.id}/tax-rates/{tax_rate.id}")

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
