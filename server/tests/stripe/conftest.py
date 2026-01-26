from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def price_id():
    return "price_1AbCdEfGhIjKlmN"


@pytest.fixture
def session_id():
    return "cs_test_a1b2c3d4e5f6g7h8i9j"


@pytest.fixture
def mock_list_prices():
    with patch("openinvoice.stripe.models.stripe.Price.list") as mock:
        mock.return_value = MagicMock(data=[])
        yield mock


@pytest.fixture
def mock_checkout_session():
    with patch("openinvoice.stripe.models.stripe.checkout.Session.create") as mock:
        yield mock


@pytest.fixture
def mock_billing_configuration_list():
    with patch("openinvoice.stripe.models.stripe.billing_portal.Configuration.list") as mock:
        yield mock


@pytest.fixture
def mock_billing_session_create():
    with patch("openinvoice.stripe.models.stripe.billing_portal.Session.create") as mock:
        yield mock


@pytest.fixture
def mock_construct_event():
    with patch("openinvoice.stripe.views.stripe.Webhook.construct_event") as mock:
        yield mock


@pytest.fixture(autouse=True)
def mock_stripe_settings(settings):
    settings.STRIPE_API_KEY = "sk_test_api_key"
    settings.STRIPE_WEBHOOK_SECRET = "whsec_test_secret"  # noqa: S105
    settings.STRIPE_STANDARD_PRICE_ID = "price_standard_test"
    settings.STRIPE_ENTERPRISE_PRICE_ID = "price_enterprise_test"
    settings.STRIPE_TRIAL_DAYS = 14
    settings.STRIPE_PAYMENT_METHOD_TYPES = ["card"]
    settings.STRIPE_BILLING_PORTAL_CONFIGURATION = {}
