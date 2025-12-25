import pytest
from drf_standardized_errors.types import ErrorType

from tests.factories import TaxRateFactory

pytestmark = pytest.mark.django_db


def test_unarchive_tax_rate(api_client, user, account):
    tax = TaxRateFactory(account=account, is_active=False)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/tax-rates/{tax.id}/unarchive")

    assert response.status_code == 200
    assert response.data["is_active"] is True


def test_unarchive_tax_rate_requires_account(api_client, user):
    tax = TaxRateFactory(is_active=False)

    api_client.force_login(user)
    response = api_client.post(f"/api/v1/tax-rates/{tax.id}/unarchive")

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


def test_unarchive_tax_rate_requires_authentication(api_client, account):
    tax = TaxRateFactory(account=account, is_active=False)

    response = api_client.post(f"/api/v1/tax-rates/{tax.id}/unarchive")

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


def test_unarchive_tax_rate_rejects_foreign_account(api_client, user, account):
    other = TaxRateFactory(is_active=False)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/tax-rates/{other.id}/unarchive")

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
