import uuid
from unittest.mock import ANY

import pytest

from apps.files.choices import FilePurpose
from tests.factories import FileFactory

pytestmark = pytest.mark.django_db


def test_update_profile(api_client, user):
    avatar = FileFactory(purpose=FilePurpose.PROFILE_AVATAR, uploader=user)

    api_client.force_login(user)
    response = api_client.put(
        "/api/v1/profile",
        data={"name": "Bob", "avatar_id": str(avatar.id)},
    )

    assert response.status_code == 200
    assert response.data == {
        "id": user.id,
        "name": "Bob",
        "email": user.email,
        "avatar_url": ANY,
        "avatar_id": str(avatar.id),
        "active_account_id": None,
        "joined_at": ANY,
        "has_usable_password": True,
    }
    user.refresh_from_db()
    assert user.name == "Bob"
    assert user.avatar_id == avatar.id


def test_update_profile_without_avatar_removes_existing(api_client, user):
    avatar = FileFactory(purpose=FilePurpose.PROFILE_AVATAR, uploader=user)
    user.avatar = avatar
    user.save()

    api_client.force_login(user)
    response = api_client.put(
        "/api/v1/profile",
        data={"name": "Charlie"},
    )

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.name == "Charlie"
    assert user.avatar_id is None
    assert response.data["avatar_id"] is None


def test_update_profile_clear_name_and_avatar(api_client, user):
    avatar = FileFactory(purpose=FilePurpose.PROFILE_AVATAR, uploader=user)
    user.avatar = avatar
    user.save()

    api_client.force_login(user)
    response = api_client.put(
        "/api/v1/profile",
        data={"name": None, "avatar_id": None},
    )

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.name is None
    assert user.avatar_id is None


def test_update_profile_requires_authentication(api_client):
    response = api_client.put("/api/v1/profile", data={"name": "Bob"})

    assert response.status_code == 403
    assert response.data == {
        "type": "client_error",
        "errors": [
            {"attr": None, "code": "not_authenticated", "detail": "Authentication credentials were not provided."}
        ],
    }


def test_update_profile_invalid_avatar(api_client, user):
    avatar_id = uuid.uuid4()

    api_client.force_login(user)
    response = api_client.put(
        "/api/v1/profile",
        data={"name": "Bob", "avatar_id": str(avatar_id)},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "avatar_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{avatar_id}" - object does not exist.',
            }
        ],
    }
