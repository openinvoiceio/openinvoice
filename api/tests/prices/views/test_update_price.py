import uuid
from unittest.mock import ANY

import pytest
from django.utils import timezone
from djmoney.money import Money
from drf_standardized_errors.types import ErrorType

from apps.prices.choices import PriceModel
from tests.factories import PriceFactory, ProductFactory

pytestmark = pytest.mark.django_db


def test_update_flat_price(api_client, user, account):
    price = PriceFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/prices/{price.id}",
        data={
            "currency": "USD",
            "amount": "20.00",
            "metadata": {},
            "code": None,
        },
    )

    assert response.status_code == 200
    assert response.data == {
        "id": str(price.id),
        "account_id": str(account.id),
        "product": {
            "id": str(price.product.id),
            "name": price.product.name,
            "description": "Test product",
            "is_active": True,
            "default_price_id": None,
            "metadata": {},
            "created_at": ANY,
            "updated_at": ANY,
        },
        "currency": "USD",
        "amount": "20.00",
        "model": PriceModel.FLAT,
        "is_active": True,
        "metadata": {},
        "is_used": False,
        "code": None,
        "created_at": ANY,
        "updated_at": ANY,
        "archived_at": None,
        "tiers": [],
    }


def test_update_volume_price(api_client, user, account):
    currency = account.default_currency
    product = ProductFactory(account=account)
    price = PriceFactory(account=account, amount=0, product=product, currency=currency, model=PriceModel.VOLUME)
    price.add_tier(unit_amount=Money(8, currency), from_value=1, to_value=10)
    price.add_tier(unit_amount=Money(10, currency), from_value=11, to_value=None)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/prices/{price.id}",
        data={
            "tiers": [
                {"unit_amount": "9.00", "from_value": 1, "to_value": 5},
                {"unit_amount": "7.00", "from_value": 6, "to_value": 20},
                {"unit_amount": "5.00", "from_value": 21, "to_value": 50},
            ],
        },
    )

    assert response.status_code == 200
    assert response.data == {
        "id": str(price.id),
        "account_id": str(account.id),
        "product": {
            "id": str(price.product.id),
            "name": product.name,
            "description": "Test product",
            "is_active": True,
            "default_price_id": None,
            "metadata": {},
            "created_at": ANY,
            "updated_at": ANY,
        },
        "currency": currency,
        "amount": "0.00",
        "model": PriceModel.VOLUME,
        "is_active": True,
        "metadata": {},
        "is_used": False,
        "code": None,
        "created_at": ANY,
        "updated_at": ANY,
        "archived_at": None,
        "tiers": [
            {"unit_amount": "9.00", "from_value": 1, "to_value": 5},
            {"unit_amount": "7.00", "from_value": 6, "to_value": 20},
            {"unit_amount": "5.00", "from_value": 21, "to_value": 50},
        ],
    }
    assert price.tiers.count() == 3


def test_update_graduated_price(api_client, user, account):
    currency = account.default_currency
    product = ProductFactory(account=account)
    price = PriceFactory(account=account, amount=0, product=product, currency=currency, model=PriceModel.GRADUATED)
    price.add_tier(unit_amount=Money(5, currency), from_value=1, to_value=5)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/prices/{price.id}",
        data={
            "tiers": [
                {"unit_amount": "6.00", "from_value": 1, "to_value": 10},
                {"unit_amount": "4.00", "from_value": 11, "to_value": None},
            ],
        },
    )

    assert response.status_code == 200
    assert response.data == {
        "id": str(price.id),
        "account_id": str(account.id),
        "product": {
            "id": str(price.product.id),
            "name": product.name,
            "description": "Test product",
            "is_active": True,
            "default_price_id": None,
            "metadata": {},
            "created_at": ANY,
            "updated_at": ANY,
        },
        "currency": currency,
        "amount": "0.00",
        "model": PriceModel.GRADUATED,
        "is_active": True,
        "metadata": {},
        "is_used": False,
        "code": None,
        "created_at": ANY,
        "updated_at": ANY,
        "archived_at": None,
        "tiers": [
            {"unit_amount": "6.00", "from_value": 1, "to_value": 10},
            {"unit_amount": "4.00", "from_value": 11, "to_value": None},
        ],
    }
    assert price.tiers.count() == 2


def test_update_price_remove_tiers(api_client, user, account):
    currency = account.default_currency
    product = ProductFactory(account=account)
    price = PriceFactory(account=account, amount=0, product=product, currency=currency, model=PriceModel.VOLUME)
    price.add_tier(unit_amount=Money(8, currency), from_value=1, to_value=10)
    price.add_tier(unit_amount=Money(10, currency), from_value=11, to_value=None)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/prices/{price.id}",
        data={
            "amount": "15.00",
            "tiers": [],
        },
    )

    assert response.status_code == 200
    assert response.data["tiers"] == []
    assert response.data["amount"] == "15.00"
    price.refresh_from_db()
    assert price.tiers.count() == 0
    assert price.amount == Money("15.00", currency)


def test_update_price_non_continuous_tiers(api_client, user, account):
    currency = account.default_currency
    product = ProductFactory(account=account)
    price = PriceFactory(account=account, amount=0, product=product, currency=currency, model=PriceModel.VOLUME)
    price.add_tier(unit_amount=Money(8, currency), from_value=1, to_value=10)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/prices/{price.id}",
        data={
            "tiers": [
                {"unit_amount": "9.00", "from_value": 12, "to_value": 20},
                {"unit_amount": "9.00", "from_value": 12, "to_value": 20},
            ],
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "tiers",
                "code": "invalid",
                "detail": "Tiers must be continuous without gaps",
            }
        ],
    }


def test_update_price_invalid_tier_range(api_client, user, account):
    currency = account.default_currency
    product = ProductFactory(account=account)
    price = PriceFactory(account=account, amount=0, product=product, currency=currency, model=PriceModel.VOLUME)
    price.add_tier(unit_amount=Money(8, currency), from_value=1, to_value=10)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/prices/{price.id}",
        data={
            "tiers": [
                {"unit_amount": "9.00", "from_value": 10, "to_value": 5},
            ],
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "tiers.0.to_value",
                "code": "invalid",
                "detail": "Upper bound must be greater than or equal to lower bound.",
            }
        ],
    }


def test_update_price_rejects_foreign_account(api_client, user, account):
    other_price = PriceFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/prices/{other_price.id}",
        data={"currency": "USD", "amount": "20.00", "metadata": {}, "code": None},
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


def test_update_price_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.put(
        f"/api/v1/prices/{uuid.uuid4()}",
        data={"currency": "USD", "amount": "20.00", "metadata": {}, "code": None},
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


def test_update_price_archived(api_client, user, account):
    price = PriceFactory(account=account, is_active=False, archived_at=timezone.now())

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/prices/{price.id}",
        data={"currency": "USD", "amount": "20.00", "metadata": {}, "code": None},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Archived prices cannot be updated",
            }
        ],
    }


def test_update_price_requires_authentication(api_client, account):
    price = PriceFactory(account=account)

    response = api_client.put(
        f"/api/v1/prices/{price.id}",
        data={"currency": price.currency, "amount": "20.00", "metadata": {}, "code": None},
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
