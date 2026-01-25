from unittest.mock import ANY

import pytest

from apps.files.choices import FilePurpose
from tests.factories import FileFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_list_files(api_client, user, account):
    file_account = FileFactory(
        account=account,
        uploader=user,
        purpose=FilePurpose.ACCOUNT_LOGO,
        filename="logo.png",
        content_type="image/png",
    )
    file_user = FileFactory(
        uploader=user,
        purpose=FilePurpose.PROFILE_AVATAR,
        filename="avatar.png",
        content_type="image/png",
    )
    FileFactory(
        uploader=UserFactory(email="other@example.com", username="other@example.com")
    )  # other file not accessible

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/files")

    assert response.status_code == 200
    assert response.data["count"] == 2
    assert response.data["results"] == [
        {
            "id": str(f.id),
            "account_id": str(f.account_id) if f.account_id else None,
            "purpose": f.purpose,
            "url": ANY,
            "filename": f.filename,
            "size": f.data.size,
            "content_type": f.content_type,
            "created_at": ANY,
        }
        for f in [file_user, file_account]
    ]


def test_list_files_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.get("/api/v1/files")

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


def test_list_files_requires_authentication(api_client, account):
    FileFactory(account=account)

    response = api_client.get("/api/v1/files")

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
