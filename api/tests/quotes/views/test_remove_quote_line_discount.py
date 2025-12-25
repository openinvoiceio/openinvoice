import uuid
from decimal import Decimal

import pytest

from apps.quotes.enums import QuoteStatus
from apps.quotes.models import QuoteDiscount
from tests.factories import (
    CouponFactory,
    CustomerFactory,
    QuoteFactory,
    QuoteLineFactory,
)

pytestmark = pytest.mark.django_db


def test_remove_quote_line_discount(api_client, user, account):
    customer = CustomerFactory(account=account)
    quote = QuoteFactory(account=account, customer=customer)
    line = QuoteLineFactory(quote=quote, unit_amount="80.00")
    coupon = CouponFactory(account=account, currency=quote.currency, amount=Decimal("10.00"), percentage=None)
    discount = line.add_discount(coupon)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/quote-lines/{line.id}/discounts/{discount.id}")

    assert response.status_code == 204
    assert QuoteDiscount.objects.filter(id=discount.id).exists() is False


@pytest.mark.parametrize("status", [QuoteStatus.OPEN, QuoteStatus.CANCELED, QuoteStatus.ACCEPTED])
def test_remove_quote_line_discount_requires_draft_quote_status(api_client, user, account, status):
    customer = CustomerFactory(account=account)
    quote = QuoteFactory(account=account, customer=customer, status=status, number="QT-303")
    line = QuoteLineFactory(quote=quote, unit_amount="80.00")
    coupon = CouponFactory(account=account, currency=quote.currency, amount=Decimal("10.00"), percentage=None)
    discount = line.add_discount(coupon)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/quote-lines/{line.id}/discounts/{discount.id}")

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


def test_remove_quote_line_discount_not_found(api_client, user, account):
    quote = QuoteFactory(account=account)
    line = QuoteLineFactory(quote=quote, unit_amount="80.00")
    discount_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/quote-lines/{line.id}/discounts/{discount_id}")

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


def test_remove_quote_line_discount_requires_authentication(api_client, account):
    quote = QuoteFactory(account=account)
    line = QuoteLineFactory(quote=quote)
    discount_id = uuid.uuid4()

    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/quote-lines/{line.id}/discounts/{discount_id}")

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


def test_remove_quote_line_discount_requires_account(api_client, user):
    quote = QuoteFactory()
    line = QuoteLineFactory(quote=quote)
    discount_id = uuid.uuid4()

    api_client.force_login(user)
    response = api_client.delete(f"/api/v1/quote-lines/{line.id}/discounts/{discount_id}")

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
