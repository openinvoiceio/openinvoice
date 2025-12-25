import uuid

import pytest
from drf_standardized_errors.types import ErrorType

from tests.factories import CouponFactory

pytestmark = pytest.mark.django_db


def test_delete_coupon(api_client, user, account):
    coupon = CouponFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/coupons/{coupon.id}")

    assert response.status_code == 200
    coupon.refresh_from_db()
    assert not coupon.is_active
    assert response.data["id"] == str(coupon.id)


def test_delete_coupon_not_found(api_client, user, account):
    api_client.force_login(user)
    api_client.force_account(account)

    response = api_client.delete(f"/api/v1/coupons/{uuid.uuid4()}")

    assert response.status_code == 404
    assert response.data == {
        "type": ErrorType.CLIENT_ERROR,
        "errors": [{"attr": None, "code": "not_found", "detail": "Not found."}],
    }


def test_delete_coupon_requires_account(api_client, user):
    coupon = CouponFactory()

    api_client.force_login(user)
    response = api_client.delete(f"/api/v1/coupons/{coupon.id}")

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


def test_delete_inactive_coupon_not_allowed(api_client, user, account):
    coupon = CouponFactory(account=account, is_active=False)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/coupons/{coupon.id}")

    assert response.status_code == 404
    assert response.data == {
        "type": ErrorType.CLIENT_ERROR,
        "errors": [{"attr": None, "code": "not_found", "detail": "Not found."}],
    }


def test_delete_coupon_requires_authentication(api_client, account):
    coupon = CouponFactory(account=account)

    response = api_client.delete(f"/api/v1/coupons/{coupon.id}")

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


def test_delete_coupon_rejects_foreign_account(api_client, user, account):
    coupon = CouponFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/coupons/{coupon.id}")

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
