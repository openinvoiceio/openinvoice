import uuid
from unittest.mock import ANY

import pytest

from openinvoice.numbering_systems.choices import NumberingSystemResetInterval, NumberingSystemStatus
from tests.factories import (
    InvoiceFactory,
    NumberingSystemFactory,
)

pytestmark = pytest.mark.django_db


def test_update_numbering_system(api_client, user, subscribed_account):
    numbering_system = NumberingSystemFactory(account=subscribed_account)

    api_client.force_login(user)
    api_client.force_account(subscribed_account)
    response = api_client.put(
        f"/api/v1/numbering-systems/{numbering_system.id}",
        data={
            "template": "NEW-{yyyy}-{n}",
            "description": "Updated",
            "reset_interval": NumberingSystemResetInterval.MONTHLY,
        },
    )

    assert response.status_code == 200
    assert response.data == {
        "id": str(numbering_system.id),
        "template": "NEW-{yyyy}-{n}",
        "description": "Updated",
        "applies_to": numbering_system.applies_to,
        "reset_interval": NumberingSystemResetInterval.MONTHLY,
        "status": numbering_system.status,
        "created_at": ANY,
        "updated_at": ANY,
        "archived_at": numbering_system.archived_at,
    }


def test_update_numbering_system_with_invoices(api_client, user, subscribed_account):
    numbering_system = NumberingSystemFactory(
        account=subscribed_account,
        template="INV-{n}",
        reset_interval=NumberingSystemResetInterval.NEVER,
        description="Old",
    )
    InvoiceFactory(account=subscribed_account, numbering_system=numbering_system)

    api_client.force_login(user)
    api_client.force_account(subscribed_account)
    response = api_client.put(
        f"/api/v1/numbering-systems/{numbering_system.id}",
        data={
            "template": "NEW-{yyyy}-{n}",
            "description": "New",
            "reset_interval": NumberingSystemResetInterval.YEARLY,
        },
    )

    assert response.status_code == 200
    assert response.data == {
        "id": str(numbering_system.id),
        "template": "INV-{n}",
        "description": "New",
        "applies_to": numbering_system.applies_to,
        "reset_interval": NumberingSystemResetInterval.NEVER,
        "status": numbering_system.status,
        "created_at": ANY,
        "updated_at": ANY,
        "archived_at": numbering_system.archived_at,
    }


def test_update_numbering_system_archived(api_client, user, subscribed_account):
    numbering_system = NumberingSystemFactory(
        account=subscribed_account,
        status=NumberingSystemStatus.ARCHIVED,
    )

    api_client.force_login(user)
    api_client.force_account(subscribed_account)
    response = api_client.put(
        f"/api/v1/numbering-systems/{numbering_system.id}",
        data={
            "template": "NEW-{yyyy}-{n}",
            "description": "Updated",
            "reset_interval": NumberingSystemResetInterval.MONTHLY,
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Cannot update once archived.",
            }
        ],
    }


def test_update_numbering_system_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.put(
        f"/api/v1/numbering-systems/{uuid.uuid4()}",
        data={
            "template": "INV-{n}",
            "description": "Test",
            "reset_interval": NumberingSystemResetInterval.NEVER,
        },
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


def test_update_numbering_system_requires_authentication(api_client, subscribed_account):
    numbering_system = NumberingSystemFactory(account=subscribed_account)

    response = api_client.put(
        f"/api/v1/numbering-systems/{numbering_system.id}",
        data={
            "template": "INV-{n}",
            "description": "Test",
            "reset_interval": NumberingSystemResetInterval.NEVER,
        },
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
