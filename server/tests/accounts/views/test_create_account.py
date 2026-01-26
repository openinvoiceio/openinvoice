from unittest.mock import ANY

import pytest

from apps.accounts.session import ACTIVE_ACCOUNT_SESSION_KEY
from apps.numbering_systems.choices import NumberingSystemAppliesTo, NumberingSystemResetInterval
from apps.numbering_systems.models import NumberingSystem
from common.choices import LimitCode

pytestmark = pytest.mark.django_db


def test_create_account(api_client, user, settings):
    api_client.force_login(user)
    assert ACTIVE_ACCOUNT_SESSION_KEY not in api_client.session
    response = api_client.post(
        "/api/v1/accounts",
        data={
            "name": "Test Account",
            "email": "test@example.com",
            "country": "PL",
        },
    )

    assert response.status_code == 201
    assert ACTIVE_ACCOUNT_SESSION_KEY in api_client.session
    assert response.data == {
        "id": ANY,
        "name": "Test Account",
        "legal_name": None,
        "legal_number": None,
        "email": "test@example.com",
        "phone": None,
        "address": {
            "country": None,
            "line1": None,
            "line2": None,
            "locality": None,
            "postal_code": None,
            "state": None,
        },
        "country": "PL",
        "default_currency": "PLN",
        "invoice_footer": None,
        "invoice_numbering_system_id": ANY,
        "credit_note_numbering_system_id": ANY,
        "net_payment_term": 7,
        "metadata": {},
        "subscription": None,
        "logo_id": None,
        "logo_url": None,
        "tax_ids": [],
        "created_at": ANY,
        "updated_at": ANY,
    }
    numbering_system = NumberingSystem.objects.get(id=response.data.get("invoice_numbering_system_id"))
    assert numbering_system.template == "INV-{nnnn}"
    assert numbering_system.description == "Default"
    assert numbering_system.reset_interval == NumberingSystemResetInterval.NEVER
    assert numbering_system.applies_to == NumberingSystemAppliesTo.INVOICE

    credit_note_numbering_system = NumberingSystem.objects.get(id=response.data.get("credit_note_numbering_system_id"))
    assert credit_note_numbering_system.description == settings.ACCOUNT_CREDIT_NOTE_NUMBERING_SYSTEM_DESCRIPTION
    assert credit_note_numbering_system.reset_interval == NumberingSystemResetInterval.NEVER
    assert credit_note_numbering_system.applies_to == NumberingSystemAppliesTo.CREDIT_NOTE


def test_create_account_requires_authentication(api_client):
    response = api_client.post(
        "/api/v1/accounts",
        data={"name": "Test", "email": "test@example.com", "country": "PL"},
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


def test_create_account_limit_exceeded(api_client, user, settings):
    settings.DEFAULT_PLAN = "test"
    settings.PLANS = {"test": {"limits": {LimitCode.MAX_ACCOUNTS: 0}}}

    api_client.force_login(user)
    response = api_client.post(
        "/api/v1/accounts",
        data={"name": "Test", "email": "test@example.com", "country": "PL"},
    )

    assert response.status_code == 403
    assert response.data == {
        "type": "client_error",
        "errors": [
            {
                "attr": None,
                "code": "limit_exceeded",
                "detail": "Limit has been exceeded for your account.",
            }
        ],
    }
