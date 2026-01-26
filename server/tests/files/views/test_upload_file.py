from unittest.mock import ANY

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from openinvoice.files.choices import FilePurpose

pytestmark = pytest.mark.django_db


def test_upload_profile_avatar(api_client, user, account):
    uploaded = SimpleUploadedFile("avatar.png", b"avatar", content_type="image/png")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/files",
        {"file": uploaded, "purpose": FilePurpose.PROFILE_AVATAR},
        format="multipart",
    )

    assert response.status_code == 201
    assert response.data == {
        "id": ANY,
        "account_id": None,
        "purpose": FilePurpose.PROFILE_AVATAR,
        "url": ANY,
        "filename": "avatar.png",
        "size": uploaded.size,
        "content_type": "image/png",
        "created_at": ANY,
    }


def test_upload_account_logo(api_client, user, account):
    uploaded = SimpleUploadedFile("logo.png", b"logo", content_type="image/png")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/files",
        {"file": uploaded, "purpose": FilePurpose.ACCOUNT_LOGO},
        format="multipart",
    )

    assert response.status_code == 201
    assert response.data == {
        "id": ANY,
        "account_id": str(account.id),
        "purpose": FilePurpose.ACCOUNT_LOGO,
        "url": ANY,
        "filename": "logo.png",
        "size": uploaded.size,
        "content_type": "image/png",
        "created_at": ANY,
    }


def test_upload_file_requires_account(api_client, user):
    uploaded = SimpleUploadedFile("logo.png", b"logo", content_type="image/png")

    api_client.force_login(user)
    response = api_client.post(
        "/api/v1/files",
        {"file": uploaded, "purpose": FilePurpose.ACCOUNT_LOGO},
        format="multipart",
    )

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


def test_upload_file_requires_authentication(api_client):
    uploaded = SimpleUploadedFile("logo.png", b"logo", content_type="image/png")

    response = api_client.post(
        "/api/v1/files",
        {"file": uploaded, "purpose": FilePurpose.ACCOUNT_LOGO},
        format="multipart",
    )

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
