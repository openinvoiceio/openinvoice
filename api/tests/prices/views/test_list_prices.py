from datetime import timedelta
from unittest.mock import ANY

import pytest
from django.utils import timezone

from apps.prices.choices import PriceModel, PriceStatus
from apps.prices.models import Price
from tests.factories import PriceFactory

pytestmark = pytest.mark.django_db


def test_list_prices(api_client, user, account):
    first_price = PriceFactory(account=account)
    second_price = PriceFactory(account=account)
    PriceFactory()  # other account

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/prices")

    assert response.status_code == 200
    assert response.data == {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": str(price.id),
                "account_id": str(account.id),
                "product": {
                    "id": str(price.product.id),
                    "name": price.product.name,
                    "description": "Test product",
                    "status": "active",
                    "default_price_id": None,
                    "metadata": {},
                    "created_at": ANY,
                    "updated_at": ANY,
                    "archived_at": None,
                },
                "currency": "PLN",
                "amount": "10.00",
                "model": PriceModel.FLAT,
                "status": "active",
                "metadata": {},
                "code": None,
                "created_at": ANY,
                "updated_at": ANY,
                "archived_at": None,
                "tiers": [],
            }
            for price in [second_price, first_price]
        ],
    }


def test_list_prices_rejects_foreign_account(api_client, user, account):
    owned_price = PriceFactory(account=account)
    PriceFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/prices")

    assert response.status_code == 200
    assert [item["id"] for item in response.data["results"]] == [str(owned_price.id)]


def test_list_prices_requires_authentication(api_client):
    response = api_client.get("/api/v1/prices")

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


def test_list_prices_filter_by_currency(api_client, user, account):
    usd = PriceFactory(account=account, currency="USD")
    PriceFactory(account=account, currency="EUR")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/prices", {"currency": "USD"})

    assert response.status_code == 200
    assert [r["id"] for r in response.data["results"]] == [str(usd.id)]


def test_list_prices_filter_status(api_client, user, account):
    PriceFactory(account=account, status=PriceStatus.ACTIVE)
    archived = PriceFactory(account=account, status=PriceStatus.ARCHIVED)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/prices", {"status": "archived"})

    assert response.status_code == 200
    assert [r["id"] for r in response.data["results"]] == [str(archived.id)]


def test_list_prices_filter_by_product_id(api_client, user, account):
    matching = PriceFactory(account=account)
    PriceFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/prices", {"product_id": str(matching.product_id)})

    assert response.status_code == 200
    assert [r["id"] for r in response.data["results"]] == [str(matching.id)]


def test_list_prices_filter_created_at_after(api_client, user, account):
    base = timezone.now()
    older = PriceFactory(account=account)
    Price.objects.filter(id=older.id).update(created_at=base - timedelta(days=1))
    newer = PriceFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/prices", {"created_at_after": (base - timedelta(hours=12)).isoformat()})

    assert response.status_code == 200
    assert [r["id"] for r in response.data["results"]] == [str(newer.id)]


def test_list_prices_filter_created_at_before(api_client, user, account):
    base = timezone.now()
    older = PriceFactory(account=account)
    Price.objects.filter(id=older.id).update(created_at=base - timedelta(days=1))
    PriceFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/prices", {"created_at_before": base.isoformat()})

    assert response.status_code == 200
    assert [r["id"] for r in response.data["results"]] == [str(older.id)]


def test_list_prices_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.get("/api/v1/prices")

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
