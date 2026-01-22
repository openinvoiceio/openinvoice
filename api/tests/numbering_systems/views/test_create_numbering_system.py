from unittest.mock import ANY

import pytest
from drf_standardized_errors.types import ErrorType

from apps.numbering_systems.choices import (
    NumberingSystemAppliesTo,
    NumberingSystemResetInterval,
    NumberingSystemStatus,
)
from common.choices import FeatureCode

pytestmark = pytest.mark.django_db


def test_create_numbering_system(api_client, user, subscribed_account):
    api_client.force_login(user)
    api_client.force_account(subscribed_account)
    response = api_client.post(
        "/api/v1/numbering-systems",
        data={
            "template": "INV-{yyyy}-{n}",
            "description": "Main",
            "applies_to": NumberingSystemAppliesTo.INVOICE,
            "reset_interval": NumberingSystemResetInterval.MONTHLY,
        },
    )

    assert response.status_code == 201
    assert response.data == {
        "id": ANY,
        "template": "INV-{yyyy}-{n}",
        "description": "Main",
        "applies_to": NumberingSystemAppliesTo.INVOICE,
        "reset_interval": NumberingSystemResetInterval.MONTHLY,
        "status": NumberingSystemStatus.ACTIVE,
        "archived_at": None,
        "created_at": ANY,
        "updated_at": ANY,
    }


def test_create_numbering_system_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.post(
        "/api/v1/numbering-systems",
        data={"template": "INV-{n}", "applies_to": NumberingSystemAppliesTo.INVOICE},
    )

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


def test_create_numbering_system_requires_authentication(api_client):
    response = api_client.post(
        "/api/v1/numbering-systems",
        data={
            "template": "INV-{yyyy}-{n}",
            "description": "Main",
            "applies_to": NumberingSystemAppliesTo.INVOICE,
            "reset_interval": NumberingSystemResetInterval.MONTHLY,
        },
    )

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


def test_create_numbering_system_invalid_template_unknown_placeholder(api_client, user, subscribed_account):
    api_client.force_login(user)
    api_client.force_account(subscribed_account)
    response = api_client.post(
        "/api/v1/numbering-systems",
        data={"template": "INV-{dd}-{n}", "applies_to": NumberingSystemAppliesTo.INVOICE},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "template",
                "code": "invalid",
                "detail": "Unknown placeholder(s): {dd}. Allowed: {yyyy}, {yy}, {q}, {mm}, {m}, and {n...} (1-9 n's).",
            }
        ],
    }


def test_create_numbering_system_invalid_template_unmatched_braces(api_client, user, subscribed_account):
    api_client.force_login(user)
    api_client.force_account(subscribed_account)
    response = api_client.post(
        "/api/v1/numbering-systems",
        data={"template": "INV-{n-{", "applies_to": NumberingSystemAppliesTo.INVOICE},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "template",
                "code": "invalid",
                "detail": "Unmatched or stray braces in format.",
            }
        ],
    }


def test_create_numbering_system_custom_forbidden(api_client, user, account, settings):
    settings.DEFAULT_PLAN = "test"
    settings.PLANS = {"test": {"features": {FeatureCode.CUSTOM_NUMBERING_SYSTEMS: False}}}

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/numbering-systems",
        data={"template": "INV-{n}", "applies_to": NumberingSystemAppliesTo.INVOICE},
    )

    assert response.status_code == 403
    assert response.data == {
        "type": ErrorType.CLIENT_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "feature_unavailable",
                "detail": "Feature is not available for your account.",
            }
        ],
    }
