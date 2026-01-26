import uuid
from unittest.mock import ANY

import pytest

from common.choices import FeatureCode
from tests.factories import (
    StripeConnectionFactory,
)

pytestmark = pytest.mark.django_db


def test_update_stripe_connection(api_client, user, account):
    connection = StripeConnectionFactory(account=account, name="Original name", redirect_url=None)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/integrations/stripe/connections/{connection.id}",
        data={
            "name": "Updated name",
            "redirect_url": "https://example.com/updated",
        },
    )

    assert response.status_code == 200
    assert response.data == {
        "id": str(connection.id),
        "name": "Updated name",
        "code": connection.code,
        "redirect_url": "https://example.com/updated",
        "created_at": ANY,
        "updated_at": ANY,
    }


def test_update_stripe_connection_not_found(api_client, user, account):
    connection_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/integrations/stripe/connections/{connection_id}",
        data={"name": "Updated"},
    )

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


def test_update_stripe_connection_requires_authentication(api_client, account):
    connection = StripeConnectionFactory(account=account)

    response = api_client.put(f"/api/v1/integrations/stripe/connections/{connection.id}", data={"name": "Connection"})

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


def test_update_stripe_connection_requires_account(api_client, user):
    connection_id = uuid.uuid4()

    api_client.force_login(user)
    response = api_client.put(f"/api/v1/integrations/stripe/connections/{connection_id}", data={"name": "Updated"})

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


def test_update_stripe_connection_rejects_foreign_account(api_client, user, account):
    connection = StripeConnectionFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/integrations/stripe/connections/{connection.id}",
        data={"redirect_url": "https://example.com/updated"},
    )

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


def test_update_stripe_connection_without_available_feature(api_client, user, account, settings):
    connection_id = uuid.uuid4()
    settings.DEFAULT_PLAN = "test"
    settings.PLANS = {"test": {"features": {FeatureCode.STRIPE_INTEGRATION: False}}}

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/integrations/stripe/connections/{connection_id}",
        data={"redirect_url": "https://example.com/updated"},
    )

    assert response.status_code == 403
    assert response.data == {
        "type": "client_error",
        "errors": [
            {
                "attr": None,
                "code": "feature_unavailable",
                "detail": "Feature is not available for your account.",
            }
        ],
    }
