import uuid
from unittest.mock import ANY

import pytest
from drf_standardized_errors.types import ErrorType

from tests.factories import StripeConnectionFactory

pytestmark = pytest.mark.django_db


def test_retrieve_stripe_connection(api_client, user, account):
    connection = StripeConnectionFactory(account=account, name="My Stripe Connection", code="test_code")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/integrations/stripe/connections/{connection.id}")

    assert response.status_code == 200
    assert response.data == {
        "id": str(connection.id),
        "name": "My Stripe Connection",
        "code": "test_code",
        "redirect_url": None,
        "created_at": ANY,
        "updated_at": ANY,
    }


def test_retrieve_stripe_connection_not_found(api_client, user, account):
    connection_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/integrations/stripe/connections/{connection_id}")

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


def test_retrieve_stripe_connection_requires_authentication(api_client):
    connection_id = uuid.uuid4()

    response = api_client.get(f"/api/v1/integrations/stripe/connections/{connection_id}")

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


def test_retrieve_stripe_connection_requires_account(api_client, user):
    connection_id = uuid.uuid4()

    api_client.force_login(user)
    response = api_client.get(f"/api/v1/integrations/stripe/connections/{connection_id}")

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


def test_retrieve_stripe_connection_rejects_foreign_account(api_client, user, account):
    connection = StripeConnectionFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/integrations/stripe/connections/{connection.id}")

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
