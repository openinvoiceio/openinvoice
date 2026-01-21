import uuid

import pytest
from drf_standardized_errors.types import ErrorType

from apps.integrations.stripe.models import StripeConnection
from common.choices import FeatureCode
from tests.factories import StripeConnectionFactory

pytestmark = pytest.mark.django_db


def test_delete_stripe_connection(api_client, user, account):
    connection = StripeConnectionFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/integrations/stripe/connections/{connection.id}")

    assert response.status_code == 204
    assert not StripeConnection.objects.filter(id=connection.id).exists()


def test_delete_stripe_connection_requires_authentication(api_client):
    connection_id = uuid.uuid4()

    response = api_client.delete(f"/api/v1/integrations/stripe/connections/{connection_id}")

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
    connection_id = uuid.uuid4()

    api_client.force_login(user)
    response = api_client.delete(f"/api/v1/integrations/stripe/connections/{connection_id}")

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


def test_delete_stripe_connection_not_found(api_client, user, account):
    connection_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/integrations/stripe/connections/{connection_id}")

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


def test_delete_stripe_connection_rejects_foreign_account(api_client, user, account):
    connection = StripeConnectionFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/integrations/stripe/connections/{connection.id}")

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


def test_delete_stripe_connection_without_available_feature(api_client, user, account, settings):
    connection_id = uuid.uuid4()
    settings.DEFAULT_PLAN = "test"
    settings.PLANS = {"test": {"features": {FeatureCode.STRIPE_INTEGRATION: False}}}

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/integrations/stripe/connections/{connection_id}")

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
