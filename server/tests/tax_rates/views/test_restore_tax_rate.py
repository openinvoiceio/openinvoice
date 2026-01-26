import pytest

from apps.tax_rates.choices import TaxRateStatus
from tests.factories import TaxRateFactory

pytestmark = pytest.mark.django_db


def test_restore_tax_rate(api_client, user, account):
    tax = TaxRateFactory(account=account, status=TaxRateStatus.ARCHIVED)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/tax-rates/{tax.id}/restore")

    assert response.status_code == 200
    assert response.data["status"] == "active"
    assert response.data["archived_at"] is None


def test_restore_tax_rate_requires_account(api_client, user):
    tax = TaxRateFactory(status=TaxRateStatus.ARCHIVED)

    api_client.force_login(user)
    response = api_client.post(f"/api/v1/tax-rates/{tax.id}/restore")

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


def test_restore_tax_rate_requires_authentication(api_client, account):
    tax = TaxRateFactory(account=account, status=TaxRateStatus.ARCHIVED)

    response = api_client.post(f"/api/v1/tax-rates/{tax.id}/restore")

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


def test_restore_tax_rate_rejects_foreign_account(api_client, user, account):
    other = TaxRateFactory(status=TaxRateStatus.ARCHIVED)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/tax-rates/{other.id}/restore")

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
