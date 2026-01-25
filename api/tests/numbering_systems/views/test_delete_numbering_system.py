import uuid

import pytest

from tests.factories import (
    InvoiceFactory,
    NumberingSystemFactory,
)

pytestmark = pytest.mark.django_db


def test_delete_numbering_system(api_client, user, subscribed_account):
    numbering_system = NumberingSystemFactory(account=subscribed_account)

    api_client.force_login(user)
    api_client.force_account(subscribed_account)
    response = api_client.delete(f"/api/v1/numbering-systems/{numbering_system.id}")

    assert response.status_code == 204


def test_delete_numbering_system_with_invoices(api_client, user, subscribed_account):
    numbering_system = NumberingSystemFactory(account=subscribed_account)
    InvoiceFactory(account=subscribed_account, numbering_system=numbering_system)

    api_client.force_login(user)
    api_client.force_account(subscribed_account)
    response = api_client.delete(f"/api/v1/numbering-systems/{numbering_system.id}")

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Cannot delete numbering system with associated documents",
            }
        ],
    }


def test_delete_numbering_system_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.delete(f"/api/v1/numbering-systems/{uuid.uuid4()}")

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


def test_delete_numbering_system_requires_authentication(api_client, subscribed_account):
    numbering_system = NumberingSystemFactory(account=subscribed_account)

    response = api_client.delete(f"/api/v1/numbering-systems/{numbering_system.id}")

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
