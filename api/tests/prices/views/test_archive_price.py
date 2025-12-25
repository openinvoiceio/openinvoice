import uuid
from unittest.mock import ANY

import pytest
from django.utils import timezone
from drf_standardized_errors.types import ErrorType

from apps.prices.enums import PriceModel
from tests.factories import PriceFactory

pytestmark = pytest.mark.django_db


def test_archive_price(api_client, user, account):
    price = PriceFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/prices/{price.id}/archive")

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
        "currency": "PLN",
        "amount": "10.00",
        "model": PriceModel.FLAT,
        "is_active": False,
        "metadata": {},
        "is_used": False,
        "code": None,
        "created_at": ANY,
        "updated_at": ANY,
        "archived_at": ANY,
        "tiers": [],
    }


def test_archive_price_already_archived(api_client, user, account):
    price = PriceFactory(account=account, is_active=False, archived_at=timezone.now())

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/prices/{price.id}/archive")

    assert response.status_code == 200
    assert response.data["is_active"] is False


def test_archive_price_rejects_foreign_account(api_client, user, account):
    other_price = PriceFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/prices/{other_price.id}/archive")

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


def test_archive_price_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.post(f"/api/v1/prices/{uuid.uuid4()}/archive")

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


def test_archive_price_requires_authentication(api_client, account):
    price = PriceFactory(account=account)

    response = api_client.post(f"/api/v1/prices/{price.id}/archive")

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
