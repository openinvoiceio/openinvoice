from unittest.mock import ANY

import pytest
from drf_standardized_errors.types import ErrorType

from apps.integrations.enums import IntegrationType
from tests.factories import StripeConnectionFactory

pytestmark = pytest.mark.django_db


def test_list_integrations_connections(api_client, user, account):
    connection = StripeConnectionFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/integrations")

    assert response.status_code == 200
    assert response.data == [
        {
            "id": str(connection.id),
            "type": IntegrationType.STRIPE,
            "created_at": ANY,
        }
    ]


def test_list_integrations_connections_rejects_foreign_account(api_client, user, account):
    StripeConnectionFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/integrations")

    assert response.status_code == 200
    assert response.data == []


def test_list_integrations_requires_authentication(api_client):
    response = api_client.get("/api/v1/integrations")

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


def test_list_integrations_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.get("/api/v1/integrations")

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
