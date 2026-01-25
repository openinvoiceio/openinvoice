import uuid
from unittest.mock import ANY

import pytest
from django.utils import timezone

from apps.prices.choices import PriceModel, PriceStatus
from tests.factories import PriceFactory

pytestmark = pytest.mark.django_db


def test_restore_price(api_client, user, account):
    price = PriceFactory(account=account, status=PriceStatus.ARCHIVED, archived_at=timezone.now())

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/prices/{price.id}/restore")

    assert response.status_code == 200
    assert response.data == {
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
        "is_used": False,
        "code": None,
        "created_at": ANY,
        "updated_at": ANY,
        "archived_at": None,
        "tiers": [],
    }


def test_restore_price_already_active(api_client, user, account):
    price = PriceFactory(account=account, status=PriceStatus.ACTIVE)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/prices/{price.id}/restore")

    assert response.status_code == 200
    assert response.data["status"] == "active"


def test_restore_price_rejects_foreign_account(api_client, user, account):
    other_price = PriceFactory(status=PriceStatus.ARCHIVED, archived_at=timezone.now())

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/prices/{other_price.id}/restore")

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


def test_restore_price_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.post(f"/api/v1/prices/{uuid.uuid4()}/restore")

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


def test_restore_price_requires_authentication(api_client, account):
    price = PriceFactory(account=account, status=PriceStatus.ARCHIVED, archived_at=timezone.now())

    response = api_client.post(f"/api/v1/prices/{price.id}/restore")

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
