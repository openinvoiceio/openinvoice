import uuid
from decimal import Decimal
from unittest.mock import ANY

import pytest
from drf_standardized_errors.types import ErrorType

from apps.invoices.choices import InvoiceDeliveryMethod
from tests.factories import (
    AccountFactory,
    CouponFactory,
    InvoiceFactory,
    InvoiceLineFactory,
    TaxRateFactory,
)

pytestmark = pytest.mark.django_db


def test_retrieve_invoice(api_client, user, account):
    invoice = InvoiceFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/invoices/{invoice.id}")

    assert response.status_code == 200
    assert response.data == {
        "id": str(invoice.id),
        "status": invoice.status,
        "number": invoice.effective_number,
        "numbering_system_id": None,
        "currency": invoice.currency,
        "issue_date": None,
        "sell_date": None,
        "due_date": invoice.due_date.isoformat(),
        "net_payment_term": invoice.net_payment_term,
        "customer": {
            "id": str(invoice.customer.id),
            "name": invoice.customer.name,
            "legal_name": invoice.customer.legal_name,
            "legal_number": invoice.customer.legal_number,
            "email": invoice.customer.email,
            "phone": invoice.customer.phone,
            "description": invoice.customer.description,
            "billing_address": {
                "line1": invoice.customer.billing_address.line1,
                "line2": invoice.customer.billing_address.line2,
                "locality": invoice.customer.billing_address.locality,
                "state": invoice.customer.billing_address.state,
                "postal_code": invoice.customer.billing_address.postal_code,
                "country": invoice.customer.billing_address.country,
            },
            "shipping_address": {
                "line1": invoice.customer.shipping_address.line1,
                "line2": invoice.customer.shipping_address.line2,
                "locality": invoice.customer.shipping_address.locality,
                "state": invoice.customer.shipping_address.state,
                "postal_code": invoice.customer.shipping_address.postal_code,
                "country": invoice.customer.shipping_address.country,
            },
            "logo_id": None,
        },
        "account": {
            "id": str(invoice.account.id),
            "name": invoice.account.name,
            "legal_name": invoice.account.legal_name,
            "legal_number": invoice.account.legal_number,
            "email": invoice.account.email,
            "phone": invoice.account.phone,
            "address": {
                "line1": invoice.account.address.line1,
                "line2": invoice.account.address.line2,
                "locality": invoice.account.address.locality,
                "state": invoice.account.address.state,
                "postal_code": invoice.account.address.postal_code,
                "country": invoice.account.address.country,
            },
            "logo_id": None,
        },
        "metadata": {},
        "custom_fields": {},
        "footer": None,
        "description": None,
        "delivery_method": InvoiceDeliveryMethod.MANUAL,
        "recipients": [],
        "subtotal_amount": "0.00",
        "total_discount_amount": "0.00",
        "total_amount_excluding_tax": "0.00",
        "shipping_amount": "0.00",
        "total_tax_amount": "0.00",
        "total_amount": "0.00",
        "total_credit_amount": "0.00",
        "total_paid_amount": "0.00",
        "outstanding_amount": "0.00",
        "payment_provider": None,
        "payment_connection_id": None,
        "created_at": ANY,
        "updated_at": ANY,
        "opened_at": None,
        "paid_at": None,
        "voided_at": None,
        "pdf_id": None,
        "lines": [],
        "coupons": [],
        "discounts": [],
        "total_discounts": [],
        "tax_rates": [],
        "taxes": [],
        "total_taxes": [],
        "shipping": None,
    }


def test_retrieve_invoice_with_line(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    line = InvoiceLineFactory(
        invoice=invoice,
        quantity=1,
        unit_amount=Decimal("10"),
        amount=Decimal("10"),
        total_discount_amount=Decimal("0"),
        total_amount_excluding_tax=Decimal("10"),
        total_tax_amount=Decimal("0"),
        total_tax_rate=Decimal("0"),
        total_amount=Decimal("10"),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/invoices/{invoice.id}")

    assert response.status_code == 200
    assert response.data["lines"] == [
        {
            "id": str(line.id),
            "description": line.description,
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
            "credit_quantity": 0,
            "outstanding_amount": "10.00",
            "outstanding_quantity": 1,
            "coupons": [],
            "discounts": [],
            "total_discounts": [],
            "tax_rates": [],
            "taxes": [],
            "total_taxes": [],
        }
    ]


def test_retrieve_invoice_excludes_line_discounts_from_invoice_level(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    line = InvoiceLineFactory(
        invoice=invoice,
        quantity=1,
        unit_amount=Decimal("10"),
        amount=Decimal("10"),
        total_discount_amount=Decimal("2"),
        total_amount_excluding_tax=Decimal("8"),
        total_tax_amount=Decimal("0"),
        total_tax_rate=Decimal("0"),
        total_amount=Decimal("8"),
    )
    coupon = CouponFactory(account=account, currency=invoice.currency, amount=Decimal("2"), percentage=None)
    line.set_coupons([coupon])
    invoice.recalculate()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/invoices/{invoice.id}")

    assert response.status_code == 200
    assert response.data["discounts"] == []
    assert response.data["total_discounts"] == [
        {
            "coupon_id": str(coupon.id),
            "amount": "2.00",
        }
    ]
    line_data = response.data["lines"][0]
    assert line_data["discounts"] == [
        {
            "coupon_id": str(coupon.id),
            "amount": "2.00",
        }
    ]
    assert line_data["total_discounts"] == [
        {
            "coupon_id": str(coupon.id),
            "amount": "2.00",
        }
    ]


def test_retrieve_invoice_excludes_line_taxes_from_invoice_level(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    line = InvoiceLineFactory(
        invoice=invoice,
        quantity=1,
        unit_amount=Decimal("10"),
        amount=Decimal("10"),
        total_discount_amount=Decimal("0"),
        total_amount_excluding_tax=Decimal("10"),
        total_tax_amount=Decimal("2"),
        total_tax_rate=Decimal("20"),
        total_amount=Decimal("12"),
    )
    tax_rate = TaxRateFactory(percentage=Decimal("20"))
    line.set_tax_rates([tax_rate])
    invoice.recalculate()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/invoices/{invoice.id}")

    assert response.status_code == 200
    assert response.data["taxes"] == []
    assert response.data["total_taxes"] == [
        {
            "tax_rate_id": str(tax_rate.id),
            "amount": "2.00",
        }
    ]
    line_data = response.data["lines"][0]
    assert line_data["taxes"] == [
        {
            "tax_rate_id": str(tax_rate.id),
            "amount": "2.00",
        }
    ]
    assert line_data["total_taxes"] == [
        {
            "tax_rate_id": str(tax_rate.id),
            "amount": "2.00",
        }
    ]


def test_retrieve_finalized_invoice_returns_snapshot(
    api_client,
    user,
    account,
):
    invoice = InvoiceFactory(account=account)
    original_account_name = invoice.account.name
    original_customer_name = invoice.customer.name

    api_client.force_login(user)
    api_client.force_account(account)
    send_response = api_client.post(f"/api/v1/invoices/{invoice.id}/finalize")
    assert send_response.status_code == 200

    invoice.account.name = "Updated account"
    invoice.account.save(update_fields=["name"])
    invoice.customer.name = "Updated customer"
    invoice.customer.save(update_fields=["name"])

    response = api_client.get(f"/api/v1/invoices/{invoice.id}")

    assert response.status_code == 200
    assert response.data["account"]["name"] == original_account_name
    assert response.data["customer"]["name"] == original_customer_name


def test_retrieve_invoice_rejects_foreign_account(api_client, user, account):
    other_account = AccountFactory()
    invoice = InvoiceFactory(account=other_account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/invoices/{invoice.id}")

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


def test_retrieve_invoice_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.get(f"/api/v1/invoices/{uuid.uuid4()}")

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


def test_retrieve_invoice_not_found(api_client, user, account):
    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/invoices/{uuid.uuid4()}")

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


def test_retrieve_invoice_requires_authentication(api_client, account):
    invoice = InvoiceFactory(account=account)

    response = api_client.get(f"/api/v1/invoices/{invoice.id}")

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
