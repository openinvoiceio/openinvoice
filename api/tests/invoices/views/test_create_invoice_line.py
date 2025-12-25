import uuid
from decimal import Decimal

import pytest
from djmoney.money import Money
from drf_standardized_errors.types import ErrorType

from apps.invoices.enums import InvoiceStatus
from apps.prices.enums import PriceModel
from tests.factories import InvoiceFactory, PriceFactory, ProductFactory

pytestmark = pytest.mark.django_db


def test_create_invoice_line_from_unit_amount(api_client, user, account):
    invoice = InvoiceFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoice-lines",
        {
            "invoice_id": str(invoice.id),
            "description": "Item",
            "quantity": 1,
            "unit_amount": "10.00",
        },
    )

    assert response.status_code == 200
    assert response.data == {
        "id": response.data["id"],
        "description": "Item",
        "quantity": 1,
        "unit_amount": "10.00",
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
        "outstanding_quantity": 1,
        "discounts": [],
        "taxes": [],
    }
    invoice.refresh_from_db()
    assert invoice.subtotal_amount.amount == Decimal("10.00")
    assert invoice.total_tax_amount.amount == Decimal("0.00")
    assert invoice.total_discount_amount.amount == Decimal("0.00")
    assert invoice.total_amount.amount == Decimal("10.00")


def test_create_invoice_line_from_flat_price(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    price = PriceFactory(account=account, currency=invoice.currency)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoice-lines",
        {
            "invoice_id": str(invoice.id),
            "description": "Item",
            "quantity": 1,
            "price_id": str(price.id),
        },
    )

    assert response.status_code == 200
    assert response.data == {
        "id": response.data["id"],
        "description": "Item",
        "quantity": 1,
        "unit_amount": "10.00",
        "price_id": str(price.id),
        "product_id": str(price.product_id),
        "amount": "10.00",
        "total_discount_amount": "0.00",
        "total_amount_excluding_tax": "10.00",
        "total_tax_amount": "0.00",
        "total_tax_rate": "0.00",
        "total_amount": "10.00",
        "total_credit_amount": "0.00",
        "outstanding_amount": "10.00",
        "credit_quantity": 0,
        "outstanding_quantity": 1,
        "discounts": [],
        "taxes": [],
    }
    invoice.refresh_from_db()
    assert invoice.subtotal_amount.amount == Decimal("10.00")
    assert invoice.total_tax_amount.amount == Decimal("0.00")
    assert invoice.total_discount_amount.amount == Decimal("0.00")
    assert invoice.total_amount.amount == Decimal("10.00")


def test_create_invoice_line_from_graduated_price(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    product = ProductFactory(account=account)
    price = PriceFactory(
        amount=0,
        product=product,
        currency=invoice.currency,
        model=PriceModel.GRADUATED,
        account=account,
    )
    price.add_tier(unit_amount=Money("10", invoice.currency), from_value=0, to_value=10)
    price.add_tier(unit_amount=Money("8", invoice.currency), from_value=11, to_value=None)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoice-lines",
        {
            "invoice_id": str(invoice.id),
            "description": "Item",
            "quantity": 15,
            "price_id": str(price.id),
        },
    )

    assert response.status_code == 200
    assert response.data["price_id"] == str(price.id)
    assert response.data["unit_amount"] == "9.47"
    assert response.data["amount"] == "142.00"
    assert response.data["total_amount_excluding_tax"] == "142.00"
    invoice.refresh_from_db()
    assert invoice.subtotal_amount.amount == Decimal("142.00")
    assert invoice.total_amount.amount == Decimal("142.00")


def test_create_invoice_line_from_volume_price(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    product = ProductFactory(account=account)
    price = PriceFactory(
        amount=0,
        product=product,
        currency=invoice.currency,
        model=PriceModel.VOLUME,
        account=account,
    )
    price.add_tier(unit_amount=Money("10", invoice.currency), from_value=0, to_value=10)
    price.add_tier(unit_amount=Money("8", invoice.currency), from_value=11, to_value=None)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoice-lines",
        {
            "invoice_id": str(invoice.id),
            "description": "Item",
            "quantity": 15,
            "price_id": str(price.id),
        },
    )

    assert response.status_code == 200
    assert response.data["price_id"] == str(price.id)
    assert response.data["unit_amount"] == "8.00"
    assert response.data["amount"] == "120.00"
    assert response.data["total_amount_excluding_tax"] == "120.00"
    invoice.refresh_from_db()
    assert invoice.subtotal_amount.amount == Decimal("120.00")
    assert invoice.total_amount.amount == Decimal("120.00")


def test_create_invoice_line_invoice_not_found(api_client, user, account):
    invoice_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoice-lines",
        {
            "invoice_id": str(invoice_id),
            "description": "Item",
            "quantity": 1,
            "unit_amount": "10.00",
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "invoice_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{invoice_id}" - object does not exist.',
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
def test_create_invoice_line_non_draft_invoice(api_client, user, account, status):
    invoice = InvoiceFactory(account=account, status=status)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoice-lines",
        {
            "invoice_id": str(invoice.id),
            "description": "Item",
            "quantity": 1,
            "unit_amount": "10.00",
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "non_field_errors",
                "code": "invalid",
                "detail": "Only draft invoices can be modified",
            }
        ],
    }


def test_create_invoice_line_price_or_unit_required(api_client, user, account):
    invoice = InvoiceFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoice-lines",
        {
            "invoice_id": str(invoice.id),
            "description": "Item",
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


def test_create_invoice_line_price_and_unit_mutually_exclusive(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    price = PriceFactory(account=account, currency=invoice.currency)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoice-lines",
        {
            "invoice_id": str(invoice.id),
            "description": "Item",
            "quantity": 1,
            "unit_amount": "10.00",
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


def test_create_invoice_line_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.post(
        "/api/v1/invoice-lines",
        {
            "invoice_id": str(uuid.uuid4()),
            "description": "Item",
            "quantity": 1,
            "unit_amount": "10.00",
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


def test_create_invoice_line_price_not_found(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    price_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoice-lines",
        {
            "invoice_id": str(invoice.id),
            "description": "Item",
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


def test_create_invoice_line_currency_mismatch(api_client, user, account):
    invoice = InvoiceFactory(account=account, currency="USD")
    price = PriceFactory(account=account, currency="PLN")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoice-lines",
        {
            "invoice_id": str(invoice.id),
            "description": "Item",
            "quantity": 1,
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
                "detail": "Price currency does not match invoice currency",
            }
        ],
    }


def test_create_invoice_line_price_archived(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    price = PriceFactory(account=account, is_active=False, currency=invoice.currency)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoice-lines",
        {
            "invoice_id": str(invoice.id),
            "description": "Item",
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
                "detail": "Given price is archived",
            }
        ],
    }


def test_create_invoice_line_product_archived(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    product = ProductFactory(account=account, is_active=False)
    price = PriceFactory(account=account, product=product, currency=invoice.currency)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoice-lines",
        {
            "invoice_id": str(invoice.id),
            "description": "Item",
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
                "detail": "Given price product is archived",
            }
        ],
    }


def test_create_invoice_line_requires_authentication(api_client, account):
    invoice = InvoiceFactory(account=account)

    response = api_client.post(
        "/api/v1/invoice-lines",
        {
            "invoice_id": str(invoice.id),
            "description": "Item",
            "quantity": 1,
            "unit_amount": "10.00",
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
