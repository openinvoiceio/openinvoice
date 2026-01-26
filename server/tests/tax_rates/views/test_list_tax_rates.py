from datetime import timedelta

import pytest
from django.utils import timezone

from apps.tax_rates.choices import TaxRateStatus
from apps.tax_rates.models import TaxRate
from tests.factories import TaxRateFactory

pytestmark = pytest.mark.django_db


def test_list_tax_rates(api_client, user, account):
    first = TaxRateFactory(account=account, name="A")
    second = TaxRateFactory(account=account, name="B")
    TaxRateFactory()  # other account

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/tax-rates")

    assert response.status_code == 200
    assert [r["id"] for r in response.data["results"]] == [str(second.id), str(first.id)]


def test_list_tax_rates_filter_by_status(api_client, user, account):
    TaxRateFactory(account=account, status=TaxRateStatus.ACTIVE)
    archived = TaxRateFactory(account=account, status=TaxRateStatus.ARCHIVED)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/tax-rates", {"status": "archived"})

    assert response.status_code == 200
    assert [r["id"] for r in response.data["results"]] == [str(archived.id)]


def test_list_tax_rates_filter_created_at_after(api_client, user, account):
    base = timezone.now()
    older = TaxRateFactory(account=account)
    TaxRate.objects.filter(id=older.id).update(created_at=base - timedelta(days=1))
    newer = TaxRateFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/tax-rates", {"created_at_after": (base - timedelta(hours=12)).isoformat()})

    assert response.status_code == 200
    assert [r["id"] for r in response.data["results"]] == [str(newer.id)]


def test_list_tax_rates_filter_created_at_before(api_client, user, account):
    base = timezone.now()
    older = TaxRateFactory(account=account)
    TaxRate.objects.filter(id=older.id).update(created_at=base - timedelta(days=1))
    TaxRateFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/tax-rates", {"created_at_before": base.isoformat()})

    assert response.status_code == 200
    assert [r["id"] for r in response.data["results"]] == [str(older.id)]


def test_list_tax_rates_rejects_foreign_account(api_client, user, account):
    owned = TaxRateFactory(account=account)
    TaxRateFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/tax-rates")

    assert response.status_code == 200
    assert [item["id"] for item in response.data["results"]] == [str(owned.id)]


def test_list_tax_rates_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.get("/api/v1/tax-rates")

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


def test_list_tax_rates_requires_authentication(api_client, account):
    TaxRateFactory(account=account)

    response = api_client.get("/api/v1/tax-rates")

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
