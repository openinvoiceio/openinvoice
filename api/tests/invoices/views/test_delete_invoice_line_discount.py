import uuid
from decimal import Decimal

import pytest
from drf_standardized_errors.types import ErrorType

from apps.invoices.enums import InvoiceStatus
from apps.invoices.models import InvoiceDiscount
from tests.factories import CouponFactory, InvoiceDiscountFactory, InvoiceFactory, InvoiceLineFactory

pytestmark = pytest.mark.django_db


def test_delete_invoice_line_discount(api_client, user, account):
    invoice = InvoiceFactory(
        account=account,
        subtotal_amount=Decimal("10"),
        total_tax_amount=Decimal("0"),
        total_amount=Decimal("9"),
        total_discount_amount=Decimal("1"),
    )
    line = InvoiceLineFactory(
        invoice=invoice,
        quantity=1,
        unit_amount=Decimal("10"),
        amount=Decimal("10"),
    )
    coupon = CouponFactory(amount=Decimal("1"), percentage=None, currency=invoice.currency)
    discount = InvoiceDiscountFactory(invoice_line=line, amount=Decimal("1"), coupon=coupon)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/invoice-lines/{line.id}/discounts/{discount.id}")

    assert response.status_code == 204
    assert not InvoiceDiscount.objects.filter(id=discount.id).exists()
    line.refresh_from_db()
    invoice.refresh_from_db()
    assert line.discounts.count() == 0
    assert invoice.total_discount_amount.amount == Decimal("0.00")
    assert invoice.total_amount.amount == Decimal("10.00")


def test_delete_invoice_line_discount_with_remaining(api_client, user, account):
    invoice = InvoiceFactory(
        account=account,
        subtotal_amount=Decimal("10"),
        total_tax_amount=Decimal("0"),
        total_amount=Decimal("8"),
        total_discount_amount=Decimal("2"),
    )
    line = InvoiceLineFactory(
        invoice=invoice,
        quantity=1,
        unit_amount=Decimal("10"),
        amount=Decimal("10"),
    )
    discount1 = InvoiceDiscountFactory(invoice_line=line, amount=Decimal("1"))
    discount2 = InvoiceDiscountFactory(invoice_line=line, amount=Decimal("1"))

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/invoice-lines/{line.id}/discounts/{discount1.id}")

    assert response.status_code == 204
    line.refresh_from_db()
    invoice.refresh_from_db()
    assert line.discounts.count() == 1
    assert invoice.total_discount_amount.amount == Decimal("1.00")
    assert InvoiceDiscount.objects.filter(id=discount2.id).exists()


def test_delete_invoice_line_discount_not_found(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    line = InvoiceLineFactory(invoice=invoice)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/invoice-lines/{line.id}/discounts/{uuid.uuid4()}")

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


def test_delete_invoice_line_discount_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.delete(f"/api/v1/invoice-lines/{uuid.uuid4()}/discounts/{uuid.uuid4()}")

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


def test_delete_invoice_line_discount_rejects_foreign_account(api_client, user, account):
    other_invoice = InvoiceFactory()
    line = InvoiceLineFactory(invoice=other_invoice)
    discount = InvoiceDiscountFactory(invoice_line=line)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/invoice-lines/{line.id}/discounts/{discount.id}")

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
def test_delete_invoice_line_discount_non_draft_invoice(api_client, user, account, status):
    invoice = InvoiceFactory(account=account, status=status)
    line = InvoiceLineFactory(invoice=invoice)
    discount = InvoiceDiscountFactory(invoice_line=line)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/invoice-lines/{line.id}/discounts/{discount.id}")

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


def test_delete_invoice_line_discount_requires_authentication(api_client, account):
    invoice = InvoiceFactory(account=account)
    line = InvoiceLineFactory(invoice=invoice)
    discount = InvoiceDiscountFactory(invoice_line=line)

    response = api_client.delete(f"/api/v1/invoice-lines/{line.id}/discounts/{discount.id}")

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
