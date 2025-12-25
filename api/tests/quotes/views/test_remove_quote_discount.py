import uuid
from decimal import Decimal

import pytest

from apps.quotes.enums import QuoteStatus
from apps.quotes.models import QuoteDiscount
from tests.factories import CouponFactory, QuoteFactory

pytestmark = pytest.mark.django_db

# TODO: add test for recalculating logic


def test_remove_quote_discount(api_client, user, account):
    quote = QuoteFactory(account=account)
    coupon = CouponFactory(account=account, currency=quote.currency, amount=Decimal("30.00"), percentage=None)
    discount = quote.add_discount(coupon)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/quotes/{quote.id}/discounts/{discount.id}")

    assert response.status_code == 204
    assert QuoteDiscount.objects.filter(id=discount.id).exists() is False


@pytest.mark.parametrize("status", [QuoteStatus.OPEN, QuoteStatus.CANCELED, QuoteStatus.ACCEPTED])
def test_remove_quote_discount_requires_draft_status(api_client, user, account, status):
    quote = QuoteFactory(account=account, status=status, number="QT-202")
    coupon = CouponFactory(account=account, currency=quote.currency, amount=Decimal("30.00"), percentage=None)
    discount = quote.add_discount(coupon)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/quotes/{quote.id}/discounts/{discount.id}")

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


def test_remove_quote_discount_not_found(api_client, user, account):
    quote = QuoteFactory(account=account)
    discount_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/quotes/{quote.id}/discounts/{discount_id}")

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


def test_remove_quote_discount_requires_authentication(api_client, account):
    quote = QuoteFactory(account=account)
    discount_id = uuid.uuid4()

    response = api_client.delete(f"/api/v1/quotes/{quote.id}/discounts/{discount_id}")

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


def test_remove_quote_discount_requires_account(api_client, user):
    quote = QuoteFactory()
    discount_id = uuid.uuid4()

    api_client.force_login(user)
    response = api_client.delete(f"/api/v1/quotes/{quote.id}/discounts/{discount_id}")

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
