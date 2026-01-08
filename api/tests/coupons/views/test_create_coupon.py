from unittest.mock import ANY

import pytest
from drf_standardized_errors.types import ErrorType

from common.enums import LimitCode

pytestmark = pytest.mark.django_db


def test_create_coupon_with_amount(api_client, user, account):
    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/coupons",
        data={"name": "Coupon 1", "amount": "10.00"},
    )

    assert response.status_code == 201
    assert response.data == {
        "id": ANY,
        "account_id": str(account.id),
        "name": "Coupon 1",
        "currency": account.default_currency,
        "amount": "10.00",
        "percentage": None,
        "created_at": ANY,
        "updated_at": ANY,
    }


def test_create_coupon_with_percentage(api_client, user, account):
    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/coupons",
        data={"name": "Coupon 1", "percentage": "5.00"},
    )

    assert response.status_code == 201
    assert response.data == {
        "id": ANY,
        "account_id": str(account.id),
        "name": "Coupon 1",
        "currency": account.default_currency,
        "amount": None,
        "percentage": "5.00",
        "created_at": ANY,
        "updated_at": ANY,
    }


def test_create_coupon_both_amount_and_percentage(api_client, user, account):
    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/coupons",
        data={"name": "Coupon", "amount": "10.00", "percentage": "5.00"},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "non_field_errors",
                "code": "invalid",
                "detail": "Exactly one of the fields amount, percentage must be provided.",
            }
        ],
    }


def test_create_coupon_without_amount_or_percentage(api_client, user, account):
    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post("/api/v1/coupons", data={"name": "Coupon"})

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "non_field_errors",
                "code": "invalid",
                "detail": "Exactly one of the fields amount, percentage must be provided.",
            }
        ],
    }


def test_create_coupon_limit_exceeded(api_client, user, account, settings):
    settings.DEFAULT_PLAN = "test"
    settings.PLANS = {"test": {"limits": {LimitCode.MAX_COUPONS: 0}}}

    api_client.force_login(user)
    api_client.force_account(account)

    response = api_client.post(
        "/api/v1/coupons",
        data={"name": "Another", "amount": "10.00"},
    )

    assert response.status_code == 403
    assert response.data == {
        "type": ErrorType.CLIENT_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "limit_exceeded",
                "detail": "Limit has been exceeded for your account.",
            }
        ],
    }


def test_create_coupon_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.post(
        "/api/v1/coupons",
        data={"name": "NoAccount", "amount": "10.00"},
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


def test_create_coupon_requires_authentication(api_client):
    response = api_client.post(
        "/api/v1/coupons",
        data={"name": "Coupon", "amount": "10.00"},
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
