import pytest

from openinvoice.coupons.choices import CouponStatus
from tests.factories import CouponFactory

pytestmark = pytest.mark.django_db


def test_restore_coupon(api_client, user, account):
    coupon = CouponFactory(account=account, status=CouponStatus.ARCHIVED)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/coupons/{coupon.id}/restore")

    assert response.status_code == 200
    assert response.data["status"] == "active"
    assert response.data["archived_at"] is None


def test_restore_coupon_already_active(api_client, user, account):
    coupon = CouponFactory(account=account, status=CouponStatus.ACTIVE)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/coupons/{coupon.id}/restore")

    assert response.status_code == 200
    assert response.data["status"] == "active"


def test_restore_coupon_requires_account(api_client, user):
    coupon = CouponFactory(status=CouponStatus.ARCHIVED)

    api_client.force_login(user)
    response = api_client.post(f"/api/v1/coupons/{coupon.id}/restore")

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


def test_restore_coupon_requires_authentication(api_client, account):
    coupon = CouponFactory(account=account, status=CouponStatus.ARCHIVED)

    response = api_client.post(f"/api/v1/coupons/{coupon.id}/restore")

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


def test_restore_coupon_rejects_foreign_account(api_client, user, account):
    coupon = CouponFactory(status=CouponStatus.ARCHIVED)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/coupons/{coupon.id}/restore")

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
