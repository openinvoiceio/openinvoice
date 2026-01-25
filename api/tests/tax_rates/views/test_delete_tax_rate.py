import uuid

import pytest

from tests.factories import InvoiceFactory, InvoiceTaxRateFactory, TaxRateFactory

pytestmark = pytest.mark.django_db


def test_delete_tax_rate(api_client, user, account):
    tax_rate = TaxRateFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/tax-rates/{tax_rate.id}")

    assert response.status_code == 204


def test_delete_tax_rate_in_use(api_client, user, account):
    tax_rate = TaxRateFactory(account=account)
    invoice = InvoiceFactory(account=account)
    InvoiceTaxRateFactory(invoice=invoice, tax_rate=tax_rate)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/tax-rates/{tax_rate.id}")

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "This object cannot be deleted because it has related data.",
            }
        ],
    }


def test_delete_tax_rate_not_found(api_client, user, account):
    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/tax-rates/{uuid.uuid4()}")

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


def test_delete_tax_rate_requires_account(api_client, user):
    tax_rate = TaxRateFactory()

    api_client.force_login(user)
    response = api_client.delete(f"/api/v1/tax-rates/{tax_rate.id}")

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


def test_delete_tax_rate_requires_authentication(api_client, account):
    tax_rate = TaxRateFactory(account=account)

    response = api_client.delete(f"/api/v1/tax-rates/{tax_rate.id}")

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


def test_delete_tax_rate_rejects_foreign_account(api_client, user, account):
    tax_rate = TaxRateFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/tax-rates/{tax_rate.id}")

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
