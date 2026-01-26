import pytest

from openinvoice.coupons.choices import CouponStatus
from tests.factories import CouponFactory

pytestmark = pytest.mark.django_db


def test_archive_coupon(api_client, user, account):
    coupon = CouponFactory(account=account, status=CouponStatus.ACTIVE)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/coupons/{coupon.id}/archive")

    assert response.status_code == 200
    assert response.data["status"] == "archived"
    assert response.data["archived_at"] is not None


def test_archive_coupon_already_archived(api_client, user, account):
    coupon = CouponFactory(account=account, status=CouponStatus.ARCHIVED)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/coupons/{coupon.id}/archive")

    assert response.status_code == 200
    assert response.data["status"] == "archived"


def test_archive_coupon_requires_account(api_client, user):
    coupon = CouponFactory()

    api_client.force_login(user)
    response = api_client.post(f"/api/v1/coupons/{coupon.id}/archive")

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


def test_archive_coupon_requires_authentication(api_client, account):
    coupon = CouponFactory(account=account)

    response = api_client.post(f"/api/v1/coupons/{coupon.id}/archive")

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


def test_archive_coupon_rejects_foreign_account(api_client, user, account):
    coupon = CouponFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/coupons/{coupon.id}/archive")

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
