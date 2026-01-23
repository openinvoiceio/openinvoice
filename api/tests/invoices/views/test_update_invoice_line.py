import uuid
from decimal import Decimal

import pytest
from drf_standardized_errors.types import ErrorType

from apps.invoices.choices import InvoiceStatus
from apps.invoices.models import InvoiceLineCoupon, InvoiceLineTaxRate
from tests.factories import (
    CouponFactory,
    InvoiceFactory,
    InvoiceLineCouponFactory,
    InvoiceLineFactory,
    InvoiceLineTaxRateFactory,
    PriceFactory,
    TaxRateFactory,
)

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
            "description": "Updated Line",
            "quantity": 3,
            "unit_amount": "5.00",
        },
    )

    assert response.status_code == 200
    assert response.data == {
        "id": str(line.id),
        "description": "Updated Line",
        "quantity": 3,
        "unit_amount": "5.00",
        "price_id": None,
        "product_id": None,
        "amount": "15.00",
        "total_discount_amount": "0.00",
        "total_excluding_tax_amount": "15.00",
        "total_tax_amount": "0.00",
        "total_tax_rate": "0.00",
        "total_amount": "15.00",
        "total_credit_amount": "0.00",
        "outstanding_amount": "15.00",
        "credit_quantity": 0,
        "outstanding_quantity": 3,
        "coupons": [],
        "discounts": [],
        "total_discounts": [],
        "tax_rates": [],
        "taxes": [],
        "total_taxes": [],
    }
    invoice.refresh_from_db()
    assert invoice.subtotal_amount.amount == Decimal("15.00")
    assert invoice.total_tax_amount.amount == Decimal("0.00")
    assert invoice.total_amount.amount == Decimal("15.00")


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
            "description": "Updated Line",
            "price_id": str(price2.id),
            "quantity": 2,
        },
    )

    assert response.status_code == 200
    assert response.data == {
        "id": str(line.id),
        "description": "Updated Line",
        "quantity": 2,
        "unit_amount": "20.00",
        "price_id": str(price2.id),
        "product_id": str(price2.product_id),
        "amount": "40.00",
        "total_discount_amount": "0.00",
        "total_excluding_tax_amount": "40.00",
        "total_tax_amount": "0.00",
        "total_tax_rate": "0.00",
        "total_amount": "40.00",
        "total_credit_amount": "0.00",
        "outstanding_amount": "40.00",
        "credit_quantity": 0,
        "outstanding_quantity": 2,
        "coupons": [],
        "discounts": [],
        "total_discounts": [],
        "tax_rates": [],
        "taxes": [],
        "total_taxes": [],
    }
    invoice.refresh_from_db()
    assert invoice.subtotal_amount.amount == Decimal("40.00")
    assert invoice.total_tax_amount.amount == Decimal("0.00")
    assert invoice.total_amount.amount == Decimal("40.00")


def test_update_invoice_line_not_found(api_client, user, account):
    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoice-lines/{uuid.uuid4()}",
        {
            "description": "Updated Line",
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
            "description": "Updated Line",
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
            "description": "Updated Line",
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
            "description": "Updated Line",
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


def test_update_invoice_line_description(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    line = InvoiceLineFactory(invoice=invoice, description="Original", quantity=2, unit_amount=Decimal("10"))

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoice-lines/{line.id}",
        {
            "description": "Updated",
        },
    )

    assert response.status_code == 200
    assert response.data["description"] == "Updated"
    assert response.data["quantity"] == 2
    assert response.data["unit_amount"] == "10.00"


def test_update_invoice_line_unit_amount(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    line = InvoiceLineFactory(invoice=invoice, unit_amount=Decimal("10"))

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoice-lines/{line.id}",
        {
            "unit_amount": "5.00",
        },
    )

    assert response.status_code == 200
    assert response.data["description"] == line.description
    assert response.data["unit_amount"] == "5.00"
    assert response.data["quantity"] == line.quantity


def test_update_invoice_line_unit_amount_with_price(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    price = PriceFactory(account=account, currency=invoice.currency)
    line = InvoiceLineFactory(invoice=invoice, price=price, unit_amount=price.amount)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoice-lines/{line.id}",
        {
            "unit_amount": "5.00",
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "non_field_errors",
                "code": "invalid",
                "detail": "Cannot change pricing method",
            }
        ],
    }


def test_update_invoice_line_price_with_unit_amount(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    line = InvoiceLineFactory(invoice=invoice, unit_amount=Decimal("10"))
    price = PriceFactory(account=account, currency=invoice.currency)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoice-lines/{line.id}",
        {
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
                "detail": "Cannot change pricing method",
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
            "description": "Updated Line",
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


def test_update_invoice_line_with_coupons(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    line = InvoiceLineFactory(invoice=invoice)
    coupon1 = CouponFactory(account=account, currency=invoice.currency)
    coupon2 = CouponFactory(account=account, currency=invoice.currency)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoice-lines/{line.id}",
        {"coupons": [str(coupon1.id), str(coupon2.id)]},
    )

    assert response.status_code == 200
    assert [r["id"] for r in response.data["coupons"]] == [str(coupon1.id), str(coupon2.id)]


def test_update_invoice_line_with_coupons_change_position(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    line = InvoiceLineFactory(invoice=invoice)
    coupon1 = CouponFactory(account=account, currency=invoice.currency)
    coupon2 = CouponFactory(account=account, currency=invoice.currency)
    line_coupon1 = InvoiceLineCouponFactory(invoice_line=line, coupon=coupon1, position=0)
    line_coupon2 = InvoiceLineCouponFactory(invoice_line=line, coupon=coupon2, position=1)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoice-lines/{line.id}",
        {"coupons": [str(coupon2.id), str(coupon1.id)]},
    )

    assert response.status_code == 200
    assert [r["id"] for r in response.data["coupons"]] == [str(coupon2.id), str(coupon1.id)]
    assert InvoiceLineCoupon.objects.filter(id__in=[line_coupon1.id, line_coupon2.id]).exists() is False
    assert line.coupons.filter(id__in=[coupon1.id, coupon2.id]).exists() is True
    assert line.invoice_line_coupons.get(coupon_id=coupon1.id).position == 1
    assert line.invoice_line_coupons.get(coupon_id=coupon2.id).position == 0


def test_update_invoice_line_remove_coupons(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    line = InvoiceLineFactory(invoice=invoice)
    coupon1 = CouponFactory(account=account, currency=invoice.currency)
    coupon2 = CouponFactory(account=account, currency=invoice.currency)
    InvoiceLineCouponFactory(invoice_line=line, coupon=coupon1, position=0)
    InvoiceLineCouponFactory(invoice_line=line, coupon=coupon2, position=1)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoice-lines/{line.id}",
        {"coupons": []},
    )

    assert response.status_code == 200
    assert response.data["coupons"] == []
    assert line.coupons.count() == 0


def test_update_invoice_line_with_coupons_invalid_currency(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    line = InvoiceLineFactory(invoice=invoice)
    coupon1 = CouponFactory(account=account, currency=invoice.currency)
    coupon2 = CouponFactory(account=account, currency="EUR")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoice-lines/{line.id}",
        {"coupons": [str(coupon1.id), str(coupon2.id)]},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "coupons.1",
                "code": "invalid",
                "detail": "Invalid coupon currency for this invoice.",
            }
        ],
    }


def test_update_invoice_line_with_duplicate_coupons(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    line = InvoiceLineFactory(invoice=invoice)
    coupon = CouponFactory(account=account, currency=invoice.currency)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoice-lines/{line.id}",
        {"coupons": [str(coupon.id), str(coupon.id)]},
    )

    assert response.status_code == 400

    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "coupons",
                "code": "duplicate",
                "detail": "Duplicate values are not allowed.",
            }
        ],
    }


def test_update_invoice_line_with_foreign_coupon(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    line = InvoiceLineFactory(invoice=invoice)
    coupon1 = CouponFactory(account=account, currency=invoice.currency)
    coupon2 = CouponFactory(currency=invoice.currency)  # Not linked to the account

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoice-lines/{line.id}",
        {"coupons": [str(coupon1.id), str(coupon2.id)]},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "coupons",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{coupon2.id}" - object does not exist.',
            }
        ],
    }


def test_update_invoice_line_coupons_limit_exceeded(api_client, user, account, settings):
    settings.MAX_INVOICE_COUPONS = 1
    invoice = InvoiceFactory(account=account)
    line = InvoiceLineFactory(invoice=invoice)
    coupon1 = CouponFactory(account=account, currency=invoice.currency)
    coupon2 = CouponFactory(account=account, currency=invoice.currency)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoice-lines/{line.id}",
        {"coupons": [str(coupon1.id), str(coupon2.id)]},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "coupons",
                "code": "invalid",
                "detail": "Ensure this list contains at most 1 items.",
            }
        ],
    }


def test_update_invoice_line_with_tax_rates(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    line = InvoiceLineFactory(invoice=invoice)
    tax_rate1 = TaxRateFactory(account=account)
    tax_rate2 = TaxRateFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoice-lines/{line.id}",
        {"tax_rates": [str(tax_rate1.id), str(tax_rate2.id)]},
    )

    assert response.status_code == 200
    assert [r["id"] for r in response.data["tax_rates"]] == [str(tax_rate1.id), str(tax_rate2.id)]


def test_update_invoice_line_with_tax_rates_change_position(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    line = InvoiceLineFactory(invoice=invoice)
    tax_rate1 = TaxRateFactory(account=account)
    tax_rate2 = TaxRateFactory(account=account)
    line_tax_rate1 = InvoiceLineTaxRateFactory(invoice_line=line, tax_rate=tax_rate1, position=0)
    line_tax_rate2 = InvoiceLineTaxRateFactory(invoice_line=line, tax_rate=tax_rate2, position=1)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoice-lines/{line.id}",
        {"tax_rates": [str(tax_rate2.id), str(tax_rate1.id)]},
    )

    assert response.status_code == 200
    assert [r["id"] for r in response.data["tax_rates"]] == [str(tax_rate2.id), str(tax_rate1.id)]
    assert InvoiceLineTaxRate.objects.filter(id__in=[line_tax_rate1.id, line_tax_rate2.id]).exists() is False
    assert line.tax_rates.count() == 2
    assert line.invoice_line_tax_rates.get(tax_rate_id=tax_rate1.id).position == 1
    assert line.invoice_line_tax_rates.get(tax_rate_id=tax_rate2.id).position == 0


def test_update_invoice_line_with_duplicate_tax_rates(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    line = InvoiceLineFactory(invoice=invoice)
    tax_rate = TaxRateFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoice-lines/{line.id}",
        {"tax_rates": [str(tax_rate.id), str(tax_rate.id)]},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "tax_rates",
                "code": "duplicate",
                "detail": "Duplicate values are not allowed.",
            }
        ],
    }


def test_update_invoice_line_with_foreign_tax_rate(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    line = InvoiceLineFactory(invoice=invoice)
    tax_rate1 = TaxRateFactory(account=account)
    tax_rate2 = TaxRateFactory()  # Not linked to the account

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoice-lines/{line.id}",
        {"tax_rates": [str(tax_rate1.id), str(tax_rate2.id)]},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "tax_rates",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{tax_rate2.id}" - object does not exist.',
            }
        ],
    }


def test_update_invoice_line_tax_rates_limit_exceeded(api_client, user, account, settings):
    settings.MAX_INVOICE_TAX_RATES = 1
    invoice = InvoiceFactory(account=account)
    line = InvoiceLineFactory(invoice=invoice)
    tax_rate1 = TaxRateFactory(account=account)
    tax_rate2 = TaxRateFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoice-lines/{line.id}",
        {"tax_rates": [str(tax_rate1.id), str(tax_rate2.id)]},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "tax_rates",
                "code": "invalid",
                "detail": "Ensure this list contains at most 1 items.",
            }
        ],
    }
