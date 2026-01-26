from unittest.mock import ANY

import pytest

from openinvoice.numbering_systems.choices import NumberingSystemAppliesTo
from tests.factories import (
    NumberingSystemFactory,
)

pytestmark = pytest.mark.django_db


def test_list_numbering_systems(api_client, user, subscribed_account):
    numbering_system_one = NumberingSystemFactory(account=subscribed_account, template="INV-{n}")
    numbering_system_two = NumberingSystemFactory(account=subscribed_account, template="ORD-{yyyy}-{n}")
    NumberingSystemFactory()  # another account

    api_client.force_login(user)
    api_client.force_account(subscribed_account)
    response = api_client.get("/api/v1/numbering-systems")

    assert response.status_code == 200
    assert response.data["count"] == 2
    assert response.data["results"] == [
        {
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
        for numbering_system in [numbering_system_two, numbering_system_one]
    ]


def test_list_numbering_systems_filtered_by_applies_to(api_client, user, subscribed_account):
    credit_note_system = NumberingSystemFactory(
        account=subscribed_account,
        applies_to=NumberingSystemAppliesTo.CREDIT_NOTE,
    )
    NumberingSystemFactory(account=subscribed_account, applies_to=NumberingSystemAppliesTo.INVOICE)

    api_client.force_login(user)
    api_client.force_account(subscribed_account)
    response = api_client.get("/api/v1/numbering-systems", {"applies_to": "credit_note"})

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == str(credit_note_system.id)


def test_list_numbering_systems_invalid_applies_to(api_client, user, subscribed_account):
    api_client.force_login(user)
    api_client.force_account(subscribed_account)
    response = api_client.get("/api/v1/numbering-systems", {"applies_to": "invalid"})

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "applies_to",
                "code": "invalid_choice",
                "detail": "Invalid document type",
            }
        ],
    }


def test_list_numbering_systems_requires_authentication(api_client):
    response = api_client.get("/api/v1/numbering-systems")

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


def test_list_numbering_systems_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.get("/api/v1/numbering-systems")

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
