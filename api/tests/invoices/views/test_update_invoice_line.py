import uuid
from decimal import Decimal

import pytest
from drf_standardized_errors.types import ErrorType

from apps.invoices.enums import InvoiceStatus
from tests.factories import InvoiceFactory, InvoiceLineFactory, PriceFactory

pytestmark = pytest.mark.django_db


def test_update_invoice_line_from_unit_amount(api_client, user, account):
    invoice = InvoiceFactory(
        account=account,
        subtotal_amount=Decimal("10"),
        total_tax_amount=Decimal("0"),
        total_amount=Decimal("10"),
    )
    line = InvoiceLineFactory(
        invoice=invoice,
        quantity=1,
        unit_amount=Decimal("10"),
        amount=Decimal("10"),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoice-lines/{line.id}",
        {
            "description": "Updated",
            "quantity": 2,
            "unit_amount": "5.00",
        },
    )

    assert response.status_code == 200
    assert response.data == {
        "id": str(line.id),
        "description": "Updated",
        "quantity": 2,
        "unit_amount": "5.00",
        "price_id": None,
        "product_id": None,
        "amount": "10.00",
        "total_discount_amount": "0.00",
        "total_amount_excluding_tax": "10.00",
        "total_tax_amount": "0.00",
        "total_tax_rate": "0.00",
        "total_amount": "10.00",
        "total_credit_amount": "0.00",
        "outstanding_amount": "10.00",
        "credit_quantity": 0,
        "outstanding_quantity": 2,
        "discounts": [],
        "taxes": [],
    }
    invoice.refresh_from_db()
    assert invoice.subtotal_amount.amount == Decimal("10.00")
    assert invoice.total_tax_amount.amount == Decimal("0.00")
    assert invoice.total_amount.amount == Decimal("10.00")


def test_update_invoice_line_from_price(api_client, user, account):
    price1 = PriceFactory(account=account, currency=account.default_currency, amount=Decimal("10"))
    price2 = PriceFactory(account=account, currency=account.default_currency, amount=Decimal("20"))

    invoice = InvoiceFactory(
        account=account,
        currency=price1.currency,
        subtotal_amount=price1.amount,
        total_tax_amount=Decimal("0"),
        total_amount=price1.amount,
    )

    line = InvoiceLineFactory(
        invoice=invoice,
        price=price1,
        quantity=1,
        unit_amount=price1.amount,
        amount=price1.amount,
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoice-lines/{line.id}",
        {
            "description": "Updated",
            "quantity": 1,
            "price_id": str(price2.id),
        },
    )

    assert response.status_code == 200
    assert response.data == {
        "id": str(line.id),
        "description": "Updated",
        "quantity": 1,
        "unit_amount": "20.00",
        "price_id": str(price2.id),
        "product_id": str(price2.product_id),
        "amount": "20.00",
        "total_discount_amount": "0.00",
        "total_amount_excluding_tax": "20.00",
        "total_tax_amount": "0.00",
        "total_tax_rate": "0.00",
        "total_amount": "20.00",
        "total_credit_amount": "0.00",
        "outstanding_amount": "20.00",
        "credit_quantity": 0,
        "outstanding_quantity": 1,
        "discounts": [],
        "taxes": [],
    }
    invoice.refresh_from_db()
    assert invoice.subtotal_amount.amount == Decimal("20.00")
    assert invoice.total_tax_amount.amount == Decimal("0.00")
    assert invoice.total_amount.amount == Decimal("20.00")


def test_update_invoice_line_not_found(api_client, user, account):
    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoice-lines/{uuid.uuid4()}",
        {
            "description": "Updated",
            "quantity": 1,
            "unit_amount": "5.00",
        },
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


def test_update_invoice_line_rejects_foreign_account(api_client, user, account):
    other_invoice = InvoiceFactory()
    line = InvoiceLineFactory(invoice=other_invoice)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoice-lines/{line.id}",
        {
            "description": "Updated",
            "quantity": 1,
            "unit_amount": "5.00",
        },
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


@pytest.mark.parametrize(
    "status",
    [
        InvoiceStatus.OPEN,
        InvoiceStatus.PAID,
        InvoiceStatus.VOIDED,
    ],
)
def test_update_invoice_line_non_draft_invoice(api_client, user, account, status):
    invoice = InvoiceFactory(account=account, status=status)
    line = InvoiceLineFactory(invoice=invoice)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoice-lines/{line.id}",
        {
            "description": "Updated",
            "quantity": 1,
            "unit_amount": "5.00",
        },
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


def test_update_invoice_line_requires_authentication(api_client, account):
    invoice = InvoiceFactory(account=account)
    line = InvoiceLineFactory(invoice=invoice)

    response = api_client.put(
        f"/api/v1/invoice-lines/{line.id}",
        {
            "description": "Updated",
            "quantity": 1,
            "unit_amount": "5.00",
        },
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


def test_update_invoice_line_price_or_unit_required(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    line = InvoiceLineFactory(invoice=invoice)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoice-lines/{line.id}",
        {
            "description": "Updated",
            "quantity": 1,
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "non_field_errors",
                "code": "invalid",
                "detail": "Price or unit amount is required",
            }
        ],
    }


def test_update_invoice_line_price_and_unit_mutually_exclusive(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    line = InvoiceLineFactory(invoice=invoice)
    price = PriceFactory(account=account, currency=invoice.currency)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoice-lines/{line.id}",
        {
            "description": "Updated",
            "quantity": 1,
            "unit_amount": "5.00",
            "price_id": str(price.id),
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "non_field_errors",
                "code": "invalid",
                "detail": "Price and unit amount are mutually exclusive",
            }
        ],
    }


def test_update_invoice_line_price_not_found(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    line = InvoiceLineFactory(invoice=invoice)
    price_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoice-lines/{line.id}",
        {
            "description": "Updated",
            "quantity": 1,
            "price_id": str(price_id),
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "price_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{price_id}" - object does not exist.',
            }
        ],
    }


def test_update_invoice_line_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.put(
        f"/api/v1/invoice-lines/{uuid.uuid4()}",
        {
            "description": "Updated",
            "quantity": 1,
            "unit_amount": "5.00",
        },
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


def test_update_invoice_line_currency_mismatch(api_client, user, account):
    invoice = InvoiceFactory(account=account, currency="USD")
    line = InvoiceLineFactory(invoice=invoice)
    price = PriceFactory(account=account, currency="PLN")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoice-lines/{line.id}",
        {
            "description": "Updated",
            "quantity": 1,
            "price_id": str(price.id),
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "price_id",
                "code": "invalid",
                "detail": "Price currency does not match invoice currency",
            }
        ],
    }
