import uuid
from unittest.mock import ANY

import pytest
from drf_standardized_errors.types import ErrorType

from apps.files.enums import FilePurpose
from tests.factories import FileFactory

pytestmark = pytest.mark.django_db


def test_retrieve_file(api_client, user, account):
    file = FileFactory(
        account=account,
        uploader=user,
        purpose=FilePurpose.ACCOUNT_LOGO,
        filename="logo.png",
        content_type="image/png",
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/files/{file.id}")

    assert response.status_code == 200
    assert response.data == {
        "id": str(file.id),
        "account_id": str(account.id),
        "purpose": file.purpose,
        "url": ANY,
        "filename": file.filename,
        "size": file.data.size,
        "content_type": file.content_type,
        "created_at": ANY,
    }


def test_retrieve_file_not_found(api_client, user, account):
    file_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/files/{file_id}")

    assert response.status_code == 404
    assert response.data == {
        "type": ErrorType.CLIENT_ERROR,
        "errors": [{"attr": None, "code": "not_found", "detail": "Not found."}],
    }


def test_retrieve_file_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.get(f"/api/v1/files/{uuid.uuid4()}")

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


def test_retrieve_file_requires_authentication(api_client, account):
    file = FileFactory(account=account)

    response = api_client.get(f"/api/v1/files/{file.id}")

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
