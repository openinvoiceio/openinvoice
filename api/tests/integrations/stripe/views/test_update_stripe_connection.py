from unittest.mock import ANY

import pytest
from drf_standardized_errors.types import ErrorType

from tests.factories import (
    StripeConnectionFactory,
)

pytestmark = pytest.mark.django_db


def test_update_stripe_connection(api_client, user, subscribed_account):
    connection = StripeConnectionFactory(account=subscribed_account)

    api_client.force_login(user)
    api_client.force_account(subscribed_account)
    response = api_client.put(
        "/api/v1/integrations/stripe",
        data={
            "redirect_url": "https://example.com/updated",
        },
    )

    assert response.status_code == 200
    assert response.data == {
        "id": str(connection.id),
        "connected_account_id": connection.connected_account_id,
        "redirect_url": "https://example.com/updated",
        "created_at": ANY,
        "updated_at": ANY,
    }


def test_update_stripe_connection_requires_account(api_client, user, account):
    StripeConnectionFactory(account=account)

    api_client.force_login(user)
    response = api_client.put("/api/v1/integrations/stripe", data={"name": "Updated"})

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


def test_update_stripe_connection_requires_authentication(api_client, subscribed_account):
    StripeConnectionFactory(account=subscribed_account)

    response = api_client.put(
        "/api/v1/integrations/stripe",
        data={"redirect_url": "https://example.com/callback"},
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


def test_update_stripe_connection_rejects_foreign_account(api_client, user, subscribed_account):
    StripeConnectionFactory()

    api_client.force_login(user)
    api_client.force_account(subscribed_account)
    response = api_client.put(
        "/api/v1/integrations/stripe",
        data={"redirect_url": "https://example.com/updated"},
    )

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
