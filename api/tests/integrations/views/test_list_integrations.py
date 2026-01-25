import pytest

from tests.factories import StripeConnectionFactory

pytestmark = pytest.mark.django_db


def test_list_integrations(api_client, user, account):
    StripeConnectionFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/integrations")

    assert response.status_code == 200
    assert response.data == [
        {
            "name": "Stripe",
            "slug": "stripe",
            "description": "Stripe Payment Integration",
            "is_enabled": True,
        }
    ]


def test_list_disabled_integrations(api_client, user, account):
    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/integrations")

    assert response.status_code == 200
    assert response.data == [
        {
            "name": "Stripe",
            "slug": "stripe",
            "description": "Stripe Payment Integration",
            "is_enabled": False,
        }
    ]


def test_list_integrations_connections_rejects_foreign_account(api_client, user, account):
    StripeConnectionFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/integrations")

    assert response.status_code == 200
    assert response.data == [
        {
            "name": "Stripe",
            "slug": "stripe",
            "description": "Stripe Payment Integration",
            "is_enabled": False,
        }
    ]


def test_list_integrations_requires_authentication(api_client):
    response = api_client.get("/api/v1/integrations")

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


def test_list_integrations_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.get("/api/v1/integrations")

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
