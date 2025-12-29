from unittest.mock import ANY

import pytest
from drf_standardized_errors.types import ErrorType

from tests.factories import StripeConnectionFactory

pytestmark = pytest.mark.django_db


def test_list_stripe_connections(api_client, user, account):
    connection_1 = StripeConnectionFactory(account=account, name="My Stripe Connection", code="test_code")
    connection_2 = StripeConnectionFactory(account=account, name="Another Stripe Connection", code="another_code")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/integrations/stripe/connections")

    assert response.status_code == 200
    assert response.data == {
        "next": None,
        "previous": None,
        "count": 2,
        "results": [
            {
                "id": str(connection_1.id),
                "name": "My Stripe Connection",
                "code": "test_code",
                "redirect_url": None,
                "created_at": ANY,
                "updated_at": ANY,
            },
            {
                "id": str(connection_2.id),
                "name": "Another Stripe Connection",
                "code": "another_code",
                "redirect_url": None,
                "created_at": ANY,
                "updated_at": ANY,
            },
        ],
    }


def test_list_stripe_connections_rejects_foreign_account(api_client, user, account):
    connection = StripeConnectionFactory(account=account)
    StripeConnectionFactory(name="Other Account Connection")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/integrations/stripe/connections")

    assert response.status_code == 200
    assert response.data == {
        "next": None,
        "previous": None,
        "count": 1,
        "results": [
            {
                "id": str(connection.id),
                "name": connection.name,
                "code": connection.code,
                "redirect_url": None,
                "created_at": ANY,
                "updated_at": ANY,
            }
        ],
    }


def test_list_stripe_connections_requires_authentication(api_client):
    response = api_client.get("/api/v1/integrations/stripe/connections")

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


def test_list_stripe_connections_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.get("/api/v1/integrations/stripe/connections")

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
