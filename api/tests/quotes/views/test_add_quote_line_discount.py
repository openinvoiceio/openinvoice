import uuid
from decimal import Decimal
from unittest.mock import ANY

import pytest
from freezegun import freeze_time

from apps.quotes.choices import QuoteStatus
from tests.factories import (
    CouponFactory,
    QuoteFactory,
    QuoteLineFactory,
)

pytestmark = pytest.mark.django_db


@freeze_time("2025-07-01T09:00:00Z")
def test_add_quote_line_discount(api_client, user, account):
    quote = QuoteFactory(account=account, currency="USD")
    line = QuoteLineFactory(quote=quote, description="Consulting", quantity=1, unit_amount="100.00")
    coupon = CouponFactory(account=account, currency="USD", amount=Decimal("25.00"), percentage=None)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/quote-lines/{line.id}/discounts",
        {"coupon_id": str(coupon.id)},
    )

    assert response.status_code == 200
    assert response.data == {
        "id": ANY,
        "coupon": {
            "id": str(coupon.id),
            "account_id": str(account.id),
            "name": coupon.name,
            "currency": "USD",
            "amount": "25.00",
            "percentage": None,
            "created_at": "2025-07-01T09:00:00Z",
            "updated_at": "2025-07-01T09:00:00Z",
        },
        "amount": "25.00",
    }


def test_add_quote_line_discount_not_found(api_client, user, account):
    coupon = CouponFactory(account=account)
    line_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/quote-lines/{line_id}/discounts",
        {"coupon_id": str(coupon.id)},
    )

    assert response.status_code == 404
    assert response.data == {
        "type": "client_error",
        "errors": [
            {
                "attr": None,
                "code": "not_found",
                "detail": "Not found.",
            }
        ],
    }


@pytest.mark.parametrize("status", [QuoteStatus.OPEN, QuoteStatus.ACCEPTED, QuoteStatus.CANCELED])
def test_add_quote_line_discount_requires_draft(api_client, user, account, status):
    quote = QuoteFactory(account=account, number="QT-0001", currency="USD", status=status)
    line = QuoteLineFactory(quote=quote, description="Consulting", quantity=1, unit_amount="100.00")
    coupon = CouponFactory(account=account, currency="USD")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/quote-lines/{line.id}/discounts",
        {"coupon_id": str(coupon.id)},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Only draft quotes can be modified",
            }
        ],
    }


def test_add_quote_line_discount_currency_mismatch(api_client, user, account):
    quote = QuoteFactory(account=account, currency="USD")
    line = QuoteLineFactory(quote=quote, description="Consulting", quantity=1, unit_amount="100.00")
    coupon = CouponFactory(account=account, currency="EUR")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/quote-lines/{line.id}/discounts",
        {"coupon_id": str(coupon.id)},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "coupon_id",
                "code": "invalid",
                "detail": "Coupon currency mismatch",
            }
        ],
    }


def test_add_quote_line_discount_invalid_coupon(api_client, user, account):
    quote = QuoteFactory(account=account, currency="USD")
    line = QuoteLineFactory(quote=quote, description="Consulting", quantity=1, unit_amount="100.00")
    coupon_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/quote-lines/{line.id}/discounts",
        {"coupon_id": str(coupon_id)},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "coupon_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{coupon_id}" - object does not exist.',
            }
        ],
    }


def test_add_quote_line_discount_coupon_already_applied(api_client, user, account):
    quote = QuoteFactory(account=account, currency="USD")
    line = QuoteLineFactory(quote=quote, description="Consulting", quantity=1, unit_amount="100.00")
    coupon = CouponFactory(account=account, currency="USD")
    line.add_discount(coupon)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/quote-lines/{line.id}/discounts",
        {"coupon_id": str(coupon.id)},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "coupon_id",
                "code": "invalid",
                "detail": "Given coupon is already applied to this quote line",
            }
        ],
    }


def test_add_quote_line_requires_account(api_client, user):
    line_id = uuid.uuid4()
    coupon_id = uuid.uuid4()

    api_client.force_login(user)
    response = api_client.post(
        f"/api/v1/quote-lines/{line_id}/discounts",
        {"coupon_id": str(coupon_id)},
    )

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


def test_add_quote_line_requires_authentication(api_client):
    line_id = uuid.uuid4()
    coupon_id = uuid.uuid4()

    response = api_client.post(
        f"/api/v1/quote-lines/{line_id}/discounts",
        {"coupon_id": str(coupon_id)},
    )

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
