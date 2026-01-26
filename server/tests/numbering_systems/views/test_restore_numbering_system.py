import uuid

import pytest

from apps.numbering_systems.choices import NumberingSystemStatus
from tests.factories import NumberingSystemFactory

pytestmark = pytest.mark.django_db


def test_restore_numbering_system(api_client, user, subscribed_account):
    numbering_system = NumberingSystemFactory(account=subscribed_account, status=NumberingSystemStatus.ARCHIVED)

    api_client.force_login(user)
    api_client.force_account(subscribed_account)
    response = api_client.post(f"/api/v1/numbering-systems/{numbering_system.id}/restore")

    assert response.status_code == 200
    assert response.data["status"] == "active"
    assert response.data["archived_at"] is None


def test_restore_numbering_system_already_active(api_client, user, subscribed_account):
    numbering_system = NumberingSystemFactory(account=subscribed_account, status=NumberingSystemStatus.ACTIVE)

    api_client.force_login(user)
    api_client.force_account(subscribed_account)
    response = api_client.post(f"/api/v1/numbering-systems/{numbering_system.id}/restore")

    assert response.status_code == 200
    assert response.data["status"] == "active"


def test_restore_numbering_system_requires_account(api_client, user):
    numbering_system_id = uuid.uuid4()

    api_client.force_login(user)
    response = api_client.post(f"/api/v1/numbering-systems/{numbering_system_id}/restore")

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


def test_restore_numbering_system_requires_authentication(api_client):
    numbering_system_id = uuid.uuid4()

    response = api_client.post(f"/api/v1/numbering-systems/{numbering_system_id}/restore")

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


def test_restore_numbering_system_rejects_foreign_account(api_client, user, account):
    numbering_system = NumberingSystemFactory(status=NumberingSystemStatus.ARCHIVED)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/numbering-systems/{numbering_system.id}/restore")

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
