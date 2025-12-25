from unittest.mock import ANY

import pytest
from drf_standardized_errors.types import ErrorType

pytestmark = pytest.mark.django_db


def test_retrieve_profile(api_client, user, account):
    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/profile")

    assert response.status_code == 200
    assert response.data == {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "avatar_url": None,
        "avatar_id": None,
        "active_account_id": str(account.id),
        "joined_at": ANY,
        "has_usable_password": True,
    }


def test_retrieve_profile_without_active_account_uses_first(api_client, user, account):
    api_client.force_login(user)
    response = api_client.get("/api/v1/profile")

    assert response.status_code == 200
    assert response.data["active_account_id"] == str(account.id)


def test_retrieve_profile_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.get("/api/v1/profile")

    assert response.status_code == 200
    assert response.data["active_account_id"] is None


def test_retrieve_profile_name_fallback(api_client, user):
    user.name = None
    user.save()

    api_client.force_login(user)
    response = api_client.get("/api/v1/profile")

    assert response.status_code == 200
    assert response.data["name"] == user.email


def test_retrieve_profile_has_unusable_password(api_client, user):
    user.set_unusable_password()
    user.save()

    api_client.force_login(user)
    response = api_client.get("/api/v1/profile")

    assert response.status_code == 200
    assert response.data["has_usable_password"] is False


def test_retrieve_profile_requires_authentication(api_client):
    response = api_client.get("/api/v1/profile")

    assert response.status_code == 403
    assert response.data == {
        "type": ErrorType.CLIENT_ERROR,
        "errors": [
            {"attr": None, "code": "not_authenticated", "detail": "Authentication credentials were not provided."}
        ],
    }
