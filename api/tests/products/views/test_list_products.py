from datetime import timedelta
from unittest.mock import ANY

import pytest
from django.utils import timezone
from drf_standardized_errors.types import ErrorType

from apps.prices.choices import PriceStatus
from apps.products.choices import ProductStatus
from apps.products.models import Product
from tests.factories import PriceFactory, ProductFactory

pytestmark = pytest.mark.django_db


def test_list_products(api_client, user, account):
    first_product = ProductFactory(account=account, name="P1")
    second_product = ProductFactory(account=account, name="P2")
    ProductFactory()  # other account

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/products")

    assert response.status_code == 200
    assert response.data == {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": str(product.id),
                "account_id": str(account.id),
                "name": product.name,
                "description": "Test product",
                "status": "active",
                "url": None,
                "image_url": None,
                "image_id": None,
                "default_price": None,
                "prices_count": 0,
                "metadata": {},
                "created_at": ANY,
                "updated_at": ANY,
                "archived_at": None,
            }
            for product in [second_product, first_product]
        ],
    }


def test_list_products_requires_authentication(api_client):
    response = api_client.get("/api/v1/products")

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


def test_list_products_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.get("/api/v1/products")

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


def test_list_products_filter_by_price_currency(api_client, user, account):
    usd_product = ProductFactory(account=account, name="USD")
    PriceFactory(account=account, product=usd_product, currency="USD")
    eur_product = ProductFactory(account=account, name="EUR")
    PriceFactory(account=account, product=eur_product, currency="EUR")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/products", {"price_currency": "USD"})

    assert response.status_code == 200
    assert [r["id"] for r in response.data["results"]] == [str(usd_product.id)]


def test_list_products_filter_has_active_prices(api_client, user, account):
    active_product = ProductFactory(account=account, name="Active")
    PriceFactory(account=account, product=active_product, status=PriceStatus.ACTIVE)
    inactive_product = ProductFactory(account=account, name="Inactive")
    PriceFactory(account=account, product=inactive_product, status=PriceStatus.ARCHIVED)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/products", {"has_active_prices": "true"})

    assert response.status_code == 200
    assert [r["id"] for r in response.data["results"]] == [str(active_product.id)]


def test_list_products_filter_status(api_client, user, account):
    ProductFactory(account=account, status=ProductStatus.ACTIVE)
    archived = ProductFactory(account=account, status=ProductStatus.ARCHIVED, archived_at=timezone.now())

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/products", {"status": "archived"})

    assert response.status_code == 200
    assert [r["id"] for r in response.data["results"]] == [str(archived.id)]


def test_list_products_filter_created_at_after(api_client, user, account):
    base = timezone.now()
    older = ProductFactory(account=account)
    Product.objects.filter(id=older.id).update(created_at=base - timedelta(days=1))
    newer = ProductFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/products", {"created_at_after": (base - timedelta(hours=12)).isoformat()})

    assert response.status_code == 200
    assert [r["id"] for r in response.data["results"]] == [str(newer.id)]


def test_list_products_filter_created_at_before(api_client, user, account):
    base = timezone.now()
    older = ProductFactory(account=account)
    Product.objects.filter(id=older.id).update(created_at=base - timedelta(days=1))
    ProductFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/products", {"created_at_before": base.isoformat()})

    assert response.status_code == 200
    assert [r["id"] for r in response.data["results"]] == [str(older.id)]


def test_list_products_search_by_name(api_client, user, account):
    ProductFactory(account=account, name="Alpha")
    ProductFactory(account=account, name="Beta")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/products", {"search": "Alpha"})

    assert response.status_code == 200
    assert [r["name"] for r in response.data["results"]] == ["Alpha"]


def test_list_products_search_by_description(api_client, user, account):
    ProductFactory(account=account, description="desc1")
    ProductFactory(account=account, description="desc2")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/products", {"search": "desc1"})

    assert response.status_code == 200
    assert [r["description"] for r in response.data["results"]] == ["desc1"]


def test_list_products_order_by_created_at(api_client, user, account):
    older = ProductFactory(account=account, name="Older")
    newer = ProductFactory(account=account, name="Newer")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/products", {"ordering": "created_at"})

    assert [r["id"] for r in response.data["results"]] == [
        str(older.id),
        str(newer.id),
    ]


def test_list_products_rejects_foreign_account(api_client, user, account):
    owned = ProductFactory(account=account)
    ProductFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/products")

    assert response.status_code == 200
    assert [r["id"] for r in response.data["results"]] == [str(owned.id)]


def test_list_products_order_by_created_at_desc(api_client, user, account):
    older = ProductFactory(account=account, name="Older")
    newer = ProductFactory(account=account, name="Newer")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/products", {"ordering": "-created_at"})

    assert [r["id"] for r in response.data["results"]] == [
        str(newer.id),
        str(older.id),
    ]
