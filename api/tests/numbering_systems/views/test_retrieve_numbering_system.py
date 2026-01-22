import uuid
from unittest.mock import ANY

import pytest
from drf_standardized_errors.types import ErrorType

from tests.factories import (
    NumberingSystemFactory,
)

pytestmark = pytest.mark.django_db


def test_retrieve_numbering_system(api_client, user, subscribed_account):
    numbering_system = NumberingSystemFactory(account=subscribed_account)

    api_client.force_login(user)
    api_client.force_account(subscribed_account)
    response = api_client.get(f"/api/v1/numbering-systems/{numbering_system.id}")

    assert response.status_code == 200
    assert response.data == {
        "id": str(numbering_system.id),
        "template": numbering_system.template,
        "description": numbering_system.description,
        "applies_to": numbering_system.applies_to,
        "reset_interval": numbering_system.reset_interval,
        "status": numbering_system.status,
        "created_at": ANY,
        "updated_at": ANY,
        "archived_at": numbering_system.archived_at,
    }


def test_retrieve_numbering_system_not_found(api_client, user, subscribed_account):
    api_client.force_login(user)
    api_client.force_account(subscribed_account)
    response = api_client.get(f"/api/v1/numbering-systems/{uuid.uuid4()}")

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


def test_retrieve_numbering_system_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.get(f"/api/v1/numbering-systems/{uuid.uuid4()}")

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


def test_retrieve_numbering_system_requires_authentication(api_client, subscribed_account):
    numbering_system = NumberingSystemFactory(account=subscribed_account)

    response = api_client.get(f"/api/v1/numbering-systems/{numbering_system.id}")

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
