import uuid
from decimal import Decimal

import pytest
from drf_standardized_errors.types import ErrorType

from apps.invoices.enums import InvoiceStatus
from apps.invoices.models import InvoiceDiscount
from tests.factories import CouponFactory, InvoiceDiscountFactory, InvoiceFactory, InvoiceLineFactory

pytestmark = pytest.mark.django_db


def test_delete_invoice_discount(api_client, user, account):
    invoice = InvoiceFactory(
        account=account,
        subtotal_amount=Decimal("10"),
        total_tax_amount=Decimal("0"),
        total_amount=Decimal("9"),
        total_discount_amount=Decimal("1"),
    )
    coupon = CouponFactory(amount=Decimal("1"), percentage=None, currency=invoice.currency)
    discount = InvoiceDiscountFactory(invoice=invoice, amount=Decimal("1"), coupon=coupon)
    InvoiceLineFactory(
        invoice=invoice,
        unit_amount=Decimal("10"),
        quantity=1,
        amount=Decimal("10"),
        total_discount_amount=Decimal("0"),
        total_amount_excluding_tax=Decimal("10"),
        total_tax_amount=Decimal("0"),
        total_tax_rate=Decimal("0"),
        total_amount=Decimal("10"),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/invoices/{invoice.id}/discounts/{discount.id}")

    assert response.status_code == 204
    assert not InvoiceDiscount.objects.filter(id=discount.id).exists()
    invoice.refresh_from_db()
    assert invoice.discounts.count() == 0
    assert invoice.total_discount_amount.amount == Decimal("0.00")
    assert invoice.total_amount.amount == Decimal("10.00")


def test_delete_invoice_discount_with_remaining(api_client, user, account):
    invoice = InvoiceFactory(
        account=account,
        subtotal_amount=Decimal("10"),
        total_tax_amount=Decimal("0"),
        total_amount=Decimal("8"),
        total_discount_amount=Decimal("2"),
    )
    discount1 = InvoiceDiscountFactory(invoice=invoice, amount=Decimal("1"))
    discount2 = InvoiceDiscountFactory(invoice=invoice, amount=Decimal("1"))
    InvoiceLineFactory(
        invoice=invoice,
        unit_amount=Decimal("10"),
        quantity=1,
        amount=Decimal("10"),
        total_discount_amount=Decimal("0"),
        total_amount_excluding_tax=Decimal("10"),
        total_tax_amount=Decimal("0"),
        total_tax_rate=Decimal("0"),
        total_amount=Decimal("10"),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/invoices/{invoice.id}/discounts/{discount1.id}")

    assert response.status_code == 204
    invoice.refresh_from_db()
    assert invoice.discounts.count() == 1
    assert InvoiceDiscount.objects.filter(id=discount2.id).exists()
    assert invoice.total_discount_amount.amount == Decimal("1.00")


def test_delete_invoice_discount_not_found(api_client, user, account):
    invoice = InvoiceFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/invoices/{invoice.id}/discounts/{uuid.uuid4()}")

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


def test_delete_invoice_discount_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.delete(f"/api/v1/invoices/{uuid.uuid4()}/discounts/{uuid.uuid4()}")

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


def test_delete_invoice_discount_rejects_foreign_account(api_client, user, account):
    other_invoice = InvoiceFactory()
    discount = InvoiceDiscountFactory(invoice=other_invoice)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/invoices/{other_invoice.id}/discounts/{discount.id}")

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


@pytest.mark.parametrize(
    "status",
    [
        InvoiceStatus.OPEN,
        InvoiceStatus.PAID,
        InvoiceStatus.VOIDED,
    ],
)
def test_delete_invoice_discount_non_draft_invoice(api_client, user, account, status):
    invoice = InvoiceFactory(account=account, status=status)
    discount = InvoiceDiscountFactory(invoice=invoice)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/invoices/{invoice.id}/discounts/{discount.id}")

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


def test_delete_invoice_discount_requires_authentication(api_client, account):
    invoice = InvoiceFactory(account=account)
    discount = InvoiceDiscountFactory(invoice=invoice)

    response = api_client.delete(f"/api/v1/invoices/{invoice.id}/discounts/{discount.id}")

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
