import uuid
from decimal import Decimal
from unittest.mock import ANY

import pytest
from drf_standardized_errors.types import ErrorType

from apps.invoices.enums import InvoiceStatus
from tests.factories import (
    CouponFactory,
    InvoiceDiscountFactory,
    InvoiceFactory,
    InvoiceLineFactory,
)

pytestmark = pytest.mark.django_db


def test_apply_invoice_discount(api_client, user, account):
    invoice = InvoiceFactory(
        account=account,
        subtotal_amount=Decimal("10"),
        total_discount_amount=Decimal("0"),
        total_amount_excluding_tax=Decimal("10"),
        total_tax_amount=Decimal("0"),
        total_amount=Decimal("10"),
    )
    line = InvoiceLineFactory(
        invoice=invoice,
        quantity=1,
        unit_amount=Decimal("10"),
        amount=Decimal("10"),
        total_amount_excluding_tax=Decimal("10"),
    )
    coupon = CouponFactory(account=account, currency=invoice.currency, amount=Decimal("1"), percentage=None)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/invoices/{invoice.id}/discounts",
        {"coupon_id": str(coupon.id)},
    )

    assert response.status_code == 200
    assert response.data == {
        "id": ANY,
        "amount": "1.00",
        "coupon": {
            "id": str(coupon.id),
            "account_id": str(coupon.account_id),
            "name": coupon.name,
            "currency": coupon.currency,
            "amount": f"{coupon.amount.amount:.2f}",
            "percentage": None,
            "created_at": ANY,
            "updated_at": ANY,
        },
    }
    invoice.refresh_from_db()
    assert invoice.total_discount_amount.amount == Decimal("1.00")
    assert invoice.total_amount.amount == Decimal("9.00")
    line.refresh_from_db()
    assert line.total_discount_amount.amount == Decimal("0.00")
    assert line.amount.amount == Decimal("10.00")


def test_apply_invoice_discount_invoice_not_found(api_client, user, account):
    coupon = CouponFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/invoices/{uuid.uuid4()}/discounts",
        {"coupon_id": str(coupon.id)},
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


def test_apply_invoice_discount_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.post(
        f"/api/v1/invoices/{uuid.uuid4()}/discounts",
        {"coupon_id": str(uuid.uuid4())},
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


@pytest.mark.parametrize(
    "status",
    [
        InvoiceStatus.OPEN,
        InvoiceStatus.PAID,
        InvoiceStatus.VOIDED,
    ],
)
def test_apply_invoice_discount_non_draft_invoice(api_client, user, account, status):
    invoice = InvoiceFactory(account=account, status=status)
    coupon = CouponFactory(account=account, currency=invoice.currency)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/invoices/{invoice.id}/discounts",
        {"coupon_id": str(coupon.id)},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Only draft invoices can be modified",
            }
        ],
    }


def test_apply_invoice_discount_coupon_not_found(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    coupon_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/invoices/{invoice.id}/discounts",
        {"coupon_id": str(coupon_id)},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "coupon_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{coupon_id}" - object does not exist.',
            }
        ],
    }


def test_apply_invoice_discount_currency_mismatch(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    coupon = CouponFactory(account=account, currency="USD")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/invoices/{invoice.id}/discounts",
        {"coupon_id": str(coupon.id)},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "coupon_id",
                "code": "invalid",
                "detail": "Coupon currency mismatch",
            }
        ],
    }


def test_apply_invoice_discount_duplicate(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    coupon = CouponFactory(account=account, currency=invoice.currency)
    InvoiceDiscountFactory(invoice=invoice, coupon=coupon, amount=Decimal("0"))

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/invoices/{invoice.id}/discounts",
        {"coupon_id": str(coupon.id)},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "coupon_id",
                "code": "invalid",
                "detail": "Given coupon is already applied to this invoice",
            }
        ],
    }


def test_apply_invoice_discount_limit(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    coupons = CouponFactory.create_batch(11, account=account, currency=invoice.currency)
    for coupon in coupons[:10]:
        InvoiceDiscountFactory(invoice=invoice, coupon=coupon, amount=Decimal("0"))

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/invoices/{invoice.id}/discounts",
        {"coupon_id": str(coupons[10].id)},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Maximum number of invoice discounts reached",
            }
        ],
    }


def test_apply_invoice_discount_requires_authentication(api_client, account):
    invoice = InvoiceFactory(account=account)
    coupon = CouponFactory(account=account, currency=invoice.currency)

    response = api_client.post(
        f"/api/v1/invoices/{invoice.id}/discounts",
        {"coupon_id": str(coupon.id)},
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
