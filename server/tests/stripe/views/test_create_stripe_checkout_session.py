from unittest.mock import MagicMock

import pytest
import stripe

from tests.factories import StripeCustomerFactory

pytestmark = pytest.mark.django_db


def test_create_stripe_checkout(api_client, user, account, mock_checkout_session, price_id, session_id):
    StripeCustomerFactory(account=account, customer_id="cus_123")
    session = MagicMock(id=session_id, url=f"https://checkout.stripe.com/pay/{session_id}")
    mock_checkout_session.return_value = session

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post("/api/v1/stripe/checkout", data={"price_id": price_id})

    assert response.status_code == 200
    assert response.data == {"session_url": session.url}
    mock_checkout_session.assert_called_once()


def test_create_stripe_checkout_requires_authentication(api_client, price_id):
    response = api_client.post("/api/v1/stripe/checkout", data={"price_id": price_id})

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


def test_create_stripe_checkout_requires_account(api_client, user, mock_checkout_session, price_id):
    api_client.force_login(user)
    response = api_client.post("/api/v1/stripe/checkout", data={"price_id": price_id})

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
    mock_checkout_session.assert_not_called()


def test_create_stripe_checkout_stripe_error(api_client, user, account, mock_checkout_session, price_id):
    StripeCustomerFactory(account=account, customer_id="cus_123")
    mock_checkout_session.side_effect = stripe.StripeError("err")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post("/api/v1/stripe/checkout", data={"price_id": price_id})

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Failed to create checkout session",
            }
        ],
    }
