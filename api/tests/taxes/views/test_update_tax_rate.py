from unittest.mock import ANY

import pytest
from drf_standardized_errors.types import ErrorType

from tests.factories import TaxRateFactory

pytestmark = pytest.mark.django_db


def test_update_tax_rate(api_client, user, account):
    tax = TaxRateFactory(account=account, name="Old")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/tax-rates/{tax.id}",
        {"name": "New", "description": None, "percentage": "15.00", "country": "DE"},
    )

    assert response.status_code == 200
    assert response.data == {
        "id": str(tax.id),
        "account_id": str(account.id),
        "name": "New",
        "description": None,
        "percentage": "10.00",  # percentage is immutable
        "country": "DE",
        "status": "active",
        "created_at": ANY,
        "updated_at": ANY,
        "archived_at": None,
    }


def test_update_tax_rate_requires_account(api_client, user):
    tax = TaxRateFactory()

    api_client.force_login(user)
    response = api_client.put(
        f"/api/v1/tax-rates/{tax.id}",
        {"name": "New", "description": None, "percentage": "15.00", "country": "DE"},
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


def test_update_tax_rate_requires_authentication(api_client, account):
    tax = TaxRateFactory(account=account)

    response = api_client.put(
        f"/api/v1/tax-rates/{tax.id}",
        {"name": "New", "description": None, "percentage": "15.00", "country": "DE"},
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


def test_update_tax_rate_rejects_foreign_account(api_client, user, account):
    other = TaxRateFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/tax-rates/{other.id}",
        {"name": "New", "description": None, "percentage": "15.00", "country": "DE"},
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
