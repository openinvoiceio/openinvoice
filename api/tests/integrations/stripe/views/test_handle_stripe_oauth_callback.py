import pytest
from drf_standardized_errors.types import ErrorType

from apps.integrations.models import StripeConnection
from tests.factories import AccountFactory

pytestmark = pytest.mark.django_db


def test_handle_stripe_oauth_callback(api_client, user, account, monkeypatch, settings):
    def fake_stripe_oauth_token(**_):
        return {
            "access_token": "sk_test_123",
            "stripe_user_id": "acct_123",
            "scope": "read_write",
        }

    monkeypatch.setattr("apps.integrations.stripe.views.stripe.OAuth.token", fake_stripe_oauth_token)
    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/integrations/stripe/oauth/callback?code=auth_code_123")

    assert response.status_code == 302
    assert response.url == f"{settings.BASE_URL}/settings/integrations/stripe?error=None&error_description=None"
    connection = StripeConnection.objects.get(account=account)
    assert connection.connected_account_id == "acct_123"
    assert connection.redirect_url is None


def test_handle_stripe_oauth_callback_error(api_client, user, account, settings):
    error = "access_denied"
    error_description = "The%20user%20denied%20your%20request"

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(
        "/api/v1/integrations/stripe/oauth/callback", {"error": error, "error_description": error_description}
    )

    assert response.status_code == 302
    assert (
        response.url
        == f"{settings.BASE_URL}/settings/integrations/stripe?error={error}&error_description={error_description}"
    )
    assert not StripeConnection.objects.filter(account=account).exists()


def test_handle_stripe_oauth_callback_requires_account(api_client, user):
    api_client.force_login(user)

    response = api_client.get("/api/v1/integrations/stripe/oauth/callback?code=auth_code_123")

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


def test_handle_stripe_oauth_callback_rejects_foreign_account(api_client, user):
    other_account = AccountFactory()

    api_client.force_login(user)
    api_client.force_account(other_account)
    response = api_client.get("/api/v1/integrations/stripe/oauth/callback?code=auth_code_123")

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
