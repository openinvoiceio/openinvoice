from unittest.mock import ANY, MagicMock, patch

import pytest
from drf_standardized_errors.types import ErrorType

from apps.integrations.stripe.models import StripeConnection
from common.choices import FeatureCode

pytestmark = pytest.mark.django_db


@pytest.fixture
def webhook_endpoint_mock():
    with patch("apps.integrations.stripe.managers.StripeClient") as mock:
        yield mock.return_value.webhook_endpoints.create


def test_create_stripe_connection(api_client, user, account, settings, webhook_endpoint_mock):
    webhook_endpoint_mock.return_value = MagicMock(id="we_1234567890", secret="whsec_1234567890")  # noqa: S106

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/integrations/stripe/connections",
        data={
            "name": "My Connection",
            "code": "test_code",
            "api_key": "sk_test_1234567890",
            "redirect_url": "https://example.com",
        },
    )

    assert response.status_code == 201
    assert response.data == {
        "id": ANY,
        "name": "My Connection",
        "code": "test_code",
        "redirect_url": "https://example.com",
        "created_at": ANY,
        "updated_at": ANY,
    }
    connection = StripeConnection.objects.get(id=response.data["id"])
    assert connection.webhook_endpoint_id == "we_1234567890"
    assert connection.webhook_secret == "whsec_1234567890"  # noqa: S105
    webhook_endpoint_mock.assert_called_once_with(
        url=f"{settings.BASE_URL}/api/v1/integrations/stripe/connections/{connection.id}/webhook",
        description="OpenInvoice connection - test_code",
        enabled_events=[
            "checkout.session.completed",
            "checkout.session.async_payment_succeeded",
            "checkout.session.async_payment_failed",
            "checkout.session.expired",
        ],
    )


def test_create_stripe_connection_stripe_webhook_endpoint_failure(api_client, user, account, webhook_endpoint_mock):
    api_client.raise_request_exception = False
    webhook_endpoint_mock.side_effect = Exception("Stripe API error")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/integrations/stripe/connections",
        data={
            "name": "My Connection",
            "code": "test_code",
            "api_key": "sk_test_1234567890",
            "redirect_url": "https://example.com",
        },
    )

    assert response.status_code == 500
    assert response.data == {
        "type": ErrorType.SERVER_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "error",
                "detail": "Stripe API error",
            }
        ],
    }


def test_create_stripe_connection_requires_authentication(api_client):
    response = api_client.post(
        "/api/v1/integrations/stripe/connections",
        data={
            "name": "Connection",
            "code": "test_code",
            "api_key": "sk_test_1234567890",
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


def test_create_stripe_connection_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.post(
        "/api/v1/integrations/stripe/connections",
        data={
            "name": "Updated",
            "code": "updated_code",
            "api_key": "sk_test_updated",
        },
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


def test_create_stripe_connection_without_available_feature(api_client, user, account, settings):
    settings.DEFAULT_PLAN = "test"
    settings.PLANS = {"test": {"features": {FeatureCode.STRIPE_INTEGRATION: False}}}

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/integrations/stripe/connections",
        data={
            "name": "My Connection",
            "code": "test_code",
            "api_key": "sk_test_1234567890",
            "redirect_url": "https://example.com",
        },
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
