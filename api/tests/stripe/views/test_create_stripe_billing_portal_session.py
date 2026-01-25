from unittest.mock import MagicMock

import pytest
import stripe

from tests.factories import StripeCustomerFactory

pytestmark = pytest.mark.django_db


def test_create_billing_portal(
    api_client,
    user,
    account,
    mock_billing_configuration_list,
    mock_billing_session_create,
):
    StripeCustomerFactory(account=account, customer_id="cus_123")
    mock_billing_configuration_list.return_value = MagicMock(data=[MagicMock(id="conf_123")])
    session = MagicMock(url="https://example.com")
    mock_billing_session_create.return_value = session

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post("/api/v1/stripe/billing-portal")

    assert response.status_code == 200
    assert response.data == {"url": "https://example.com"}
    mock_billing_session_create.assert_called_once()


def test_create_billing_portal_requires_authentication(api_client):
    response = api_client.post("/api/v1/stripe/billing-portal")

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


def test_create_billing_portal_requires_account(api_client, user, mock_billing_session_create):
    api_client.force_login(user)
    response = api_client.post("/api/v1/stripe/billing-portal")

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
    mock_billing_session_create.assert_not_called()


def test_create_billing_portal_stripe_error(
    api_client,
    user,
    account,
    mock_billing_configuration_list,
    mock_billing_session_create,
):
    StripeCustomerFactory(account=account, customer_id="cus_123")
    mock_billing_configuration_list.return_value = MagicMock(data=[MagicMock(id="conf_123")])
    mock_billing_session_create.side_effect = stripe.StripeError("err")

    api_client.raise_request_exception = False
    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post("/api/v1/stripe/billing-portal")

    assert response.status_code == 500
    assert response.data == {
        "type": "server_error",
        "errors": [
            {
                "attr": None,
                "code": "error",
                "detail": "Failed to create billing portal session",
            }
        ],
    }
