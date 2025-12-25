import pytest
from drf_standardized_errors.types import ErrorType

from apps.integrations.models import StripeConnection
from tests.factories import (
    StripeConnectionFactory,
)

pytestmark = pytest.mark.django_db


def test_delete_stripe_connection(api_client, user, subscribed_account):
    connection = StripeConnectionFactory(account=subscribed_account)

    api_client.force_login(user)
    api_client.force_account(subscribed_account)
    response = api_client.delete("/api/v1/integrations/stripe")

    assert response.status_code == 204
    assert not StripeConnection.objects.filter(id=connection.id).exists()


def test_delete_stripe_connection_without_subscription(api_client, user, account):
    StripeConnectionFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete("/api/v1/integrations/stripe")

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


def test_delete_stripe_connection_requires_authentication(api_client):
    response = api_client.delete("/api/v1/integrations/stripe")

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


def test_delete_stripe_connection_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.delete("/api/v1/integrations/stripe")

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


def test_delete_stripe_connection_rejects_foreign_account(api_client, user, subscribed_account):
    StripeConnectionFactory()

    api_client.force_login(user)
    api_client.force_account(subscribed_account)
    response = api_client.delete("/api/v1/integrations/stripe")

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
