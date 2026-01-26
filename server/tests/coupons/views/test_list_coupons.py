from unittest.mock import ANY

import pytest

from openinvoice.coupons.choices import CouponStatus
from tests.factories import CouponFactory

pytestmark = pytest.mark.django_db


def test_list_coupons(api_client, user, account):
    coupon_1 = CouponFactory(account=account, name="Coupon 1")
    coupon_2 = CouponFactory(account=account, name="Coupon 2")
    CouponFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/coupons")

    assert response.status_code == 200
    assert response.data["count"] == 2
    assert response.data["results"] == [
        {
            "id": str(c.id),
            "account_id": str(c.account_id),
            "name": c.name,
            "currency": c.currency,
            "amount": f"{c.amount.amount:.2f}" if c.amount else None,
            "percentage": str(c.percentage) if c.percentage is not None else None,
            "status": c.status,
            "created_at": ANY,
            "updated_at": ANY,
            "archived_at": c.archived_at,
        }
        for c in [coupon_2, coupon_1]
    ]


def test_list_coupons_search(api_client, user, account):
    CouponFactory(account=account, name="Alpha")
    coupon_2 = CouponFactory(account=account, name="Beta")
    CouponFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/coupons", {"search": "Beta"})

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert [r["id"] for r in response.data["results"]] == [str(coupon_2.id)]


def test_list_coupons_filter_by_currency(api_client, user, account):
    coupon_usd = CouponFactory(account=account, currency="USD")
    coupon_pln = CouponFactory(account=account, currency="PLN")
    CouponFactory(account=account, currency="EUR")
    CouponFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/coupons", {"currency": "USD,PLN"})

    assert response.status_code == 200
    assert response.data["count"] == 2
    assert response.data["results"][0]["id"] == str(coupon_pln.id)
    assert response.data["results"][1]["id"] == str(coupon_usd.id)


def test_list_coupons_order_by_created_at_asc(api_client, user, account):
    coupon_1 = CouponFactory(account=account, name="Coupon 1")
    coupon_2 = CouponFactory(account=account, name="Coupon 2")
    CouponFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/coupons", {"ordering": "created_at"})

    assert response.status_code == 200
    assert [r["id"] for r in response.data["results"]] == [
        str(coupon_1.id),
        str(coupon_2.id),
    ]


def test_list_coupons_order_by_created_at_desc(api_client, user, account):
    coupon_1 = CouponFactory(account=account, name="Coupon 1")
    coupon_2 = CouponFactory(account=account, name="Coupon 2")
    CouponFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/coupons", {"ordering": "-created_at"})

    assert response.status_code == 200
    assert [r["id"] for r in response.data["results"]] == [
        str(coupon_2.id),
        str(coupon_1.id),
    ]


def test_list_coupons_filter_by_status(api_client, user, account):
    CouponFactory(account=account, name="Active")
    archived = CouponFactory(account=account, status=CouponStatus.ARCHIVED, name="Inactive")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/coupons", {"status": "archived"})

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert [r["id"] for r in response.data["results"]] == [str(archived.id)]


def test_list_coupons_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.get("/api/v1/coupons")

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


def test_list_coupons_requires_authentication(api_client, account):
    CouponFactory(account=account)

    response = api_client.get("/api/v1/coupons")

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


def test_list_coupons_rejects_foreign_account(api_client, user, account):
    owned = CouponFactory(account=account)
    CouponFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/coupons")

    assert response.status_code == 200
    assert [result["id"] for result in response.data["results"]] == [str(owned.id)]
