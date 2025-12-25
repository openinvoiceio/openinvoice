import uuid

import pytest
from drf_standardized_errors.types import ErrorType

from tests.factories import CouponFactory

pytestmark = pytest.mark.django_db


def test_update_coupon(api_client, user, account):
    coupon = CouponFactory(account=account, name="Old")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/coupons/{coupon.id}",
        data={"name": "New"},
    )

    assert response.status_code == 200
    assert response.data["name"] == "New"
    coupon.refresh_from_db()
    assert coupon.name == "New"


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("currency", "USD", "PLN"),
        ("amount", "20.00", None),
        ("percentage", "15.00", "10.00"),
    ],
)
def test_update_coupon_readonly_fields(api_client, user, account, field, value, expected):
    coupon = CouponFactory(account=account)
    original_name = coupon.name

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(f"/api/v1/coupons/{coupon.id}", data={"name": original_name, field: value})

    assert response.status_code == 200
    coupon.refresh_from_db()
    assert coupon.name == original_name
    if field == "currency":
        assert coupon.currency == expected
    elif field == "amount":
        assert coupon.amount is expected
    elif field == "percentage":
        assert str(coupon.percentage) == expected


def test_update_coupon_not_found(api_client, user, account):
    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/coupons/{uuid.uuid4()}",
        data={"name": "New"},
    )

    assert response.status_code == 404
    assert response.data == {
        "type": ErrorType.CLIENT_ERROR,
        "errors": [{"attr": None, "code": "not_found", "detail": "Not found."}],
    }


def test_update_coupon_requires_account(api_client, user):
    coupon = CouponFactory()

    api_client.force_login(user)
    response = api_client.put(
        f"/api/v1/coupons/{coupon.id}",
        data={"name": "New"},
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


def test_update_inactive_coupon_not_found(api_client, user, account):
    coupon = CouponFactory(account=account, is_active=False)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/coupons/{coupon.id}",
        data={"name": "New"},
    )

    assert response.status_code == 404
    assert response.data == {
        "type": ErrorType.CLIENT_ERROR,
        "errors": [{"attr": None, "code": "not_found", "detail": "Not found."}],
    }


def test_update_coupon_requires_authentication(api_client, account):
    coupon = CouponFactory(account=account)

    response = api_client.put(
        f"/api/v1/coupons/{coupon.id}",
        data={"name": "Updated"},
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


def test_update_coupon_rejects_foreign_account(api_client, user, account):
    coupon = CouponFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/coupons/{coupon.id}",
        data={"name": "New"},
    )

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
