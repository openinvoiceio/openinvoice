import uuid
from decimal import Decimal
from unittest.mock import ANY

import pytest

from openinvoice.invoices.choices import InvoiceDeliveryMethod
from tests.factories import (
    AccountFactory,
    AddressFactory,
    CouponFactory,
    CustomerFactory,
    CustomerShippingFactory,
    InvoiceFactory,
    InvoiceLineFactory,
    ShippingRateFactory,
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
        "tax_behavior": invoice.tax_behavior,
        "issue_date": None,
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
            "address": {
                "line1": invoice.customer.address.line1,
                "line2": invoice.customer.address.line2,
                "locality": invoice.customer.address.locality,
                "state": invoice.customer.address.state,
                "postal_code": invoice.customer.address.postal_code,
                "country": invoice.customer.address.country,
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
        "total_excluding_tax_amount": "0.00",
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
        "previous_revision_id": None,
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
        subtotal_amount=Decimal("10"),
        total_discount_amount=Decimal("0"),
        total_excluding_tax_amount=Decimal("10"),
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
            "subtotal_amount": "10.00",
            "total_discount_amount": "0.00",
            "total_excluding_tax_amount": "10.00",
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
        total_excluding_tax_amount=Decimal("8"),
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
            "name": coupon.name,
            "amount": "2.00",
        }
    ]
    line_data = response.data["lines"][0]
    assert line_data["discounts"] == [
        {
            "coupon_id": str(coupon.id),
            "name": coupon.name,
            "amount": "2.00",
        }
    ]
    assert line_data["total_discounts"] == [
        {
            "coupon_id": str(coupon.id),
            "name": coupon.name,
            "amount": "2.00",
        }
    ]


def test_retrieve_invoice_total_discounts_uses_distinct_allocations(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    InvoiceLineFactory(invoice=invoice, quantity=1, unit_amount=Decimal("200"))
    percentage_coupon = CouponFactory(
        account=account,
        currency=invoice.currency,
        amount=None,
        percentage=Decimal("20.00"),
    )
    fixed_coupon = CouponFactory(
        account=account,
        currency=invoice.currency,
        amount=Decimal("10.00"),
        percentage=None,
    )
    invoice.set_coupons([percentage_coupon, fixed_coupon])
    invoice.recalculate()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/invoices/{invoice.id}")

    assert response.status_code == 200
    expected_discounts = [
        {
            "coupon_id": str(percentage_coupon.id),
            "name": percentage_coupon.name,
            "amount": "40.00",
        },
        {
            "coupon_id": str(fixed_coupon.id),
            "name": fixed_coupon.name,
            "amount": "10.00",
        },
    ]
    assert response.data["discounts"] == expected_discounts
    assert response.data["total_discounts"] == expected_discounts
    line_data = response.data["lines"][0]
    assert line_data["discounts"] == []
    assert line_data["total_discounts"] == expected_discounts


def test_retrieve_invoice_total_taxes_uses_distinct_allocations(api_client, user, account):
    invoice = InvoiceFactory(account=account, currency="USD")
    InvoiceLineFactory(invoice=invoice, quantity=1, unit_amount=Decimal("100"))
    tax_rate = TaxRateFactory(account=account, percentage=Decimal("10"))
    secondary_tax_rate = TaxRateFactory(account=account, percentage=Decimal("5"))
    invoice.set_tax_rates([tax_rate, secondary_tax_rate])
    invoice.recalculate()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/invoices/{invoice.id}")

    assert response.status_code == 200
    expected_taxes = [
        {
            "tax_rate_id": str(tax_rate.id),
            "name": tax_rate.name,
            "percentage": "10.00",
            "amount": "10.00",
        },
        {
            "tax_rate_id": str(secondary_tax_rate.id),
            "name": secondary_tax_rate.name,
            "percentage": "5.00",
            "amount": "5.00",
        },
    ]
    assert response.data["taxes"] == expected_taxes
    assert response.data["total_taxes"] == expected_taxes
    line_data = response.data["lines"][0]
    assert line_data["taxes"] == []
    assert line_data["total_taxes"] == expected_taxes


def test_retrieve_invoice_excludes_line_taxes_from_invoice_level(api_client, user, account):
    invoice = InvoiceFactory(account=account, currency="USD")
    line = InvoiceLineFactory(
        invoice=invoice,
        quantity=1,
        unit_amount=Decimal("10"),
        amount=Decimal("10"),
        total_discount_amount=Decimal("0"),
        total_excluding_tax_amount=Decimal("10"),
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
            "name": tax_rate.name,
            "percentage": "20.00",
            "amount": "2.00",
        }
    ]
    line_data = response.data["lines"][0]
    assert line_data["taxes"] == [
        {
            "tax_rate_id": str(tax_rate.id),
            "name": tax_rate.name,
            "percentage": "20.00",
            "amount": "2.00",
        }
    ]
    assert line_data["total_taxes"] == [
        {
            "tax_rate_id": str(tax_rate.id),
            "name": tax_rate.name,
            "percentage": "20.00",
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


def test_retrieve_draft_invoice_shipping_uses_customer_shipping(api_client, user, account):
    shipping_address = AddressFactory(line1="Ship Line 1", country="US")
    customer_shipping = CustomerShippingFactory(name="Ship Draft", phone="111", address=shipping_address)
    customer = CustomerFactory(account=account, name="Bill Draft", phone="222", shipping=customer_shipping)
    invoice = InvoiceFactory(account=account, customer=customer)
    shipping_rate = ShippingRateFactory(account=account, amount=Decimal("5.00"))
    invoice.add_shipping(shipping_rate=shipping_rate, tax_rates=[])
    invoice.recalculate()

    customer_shipping.name = "Updated Ship"
    customer_shipping.phone = "123"
    customer_shipping.address = AddressFactory(line1="Ship Line 2", country="CA")
    customer_shipping.save()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/invoices/{invoice.id}")

    assert response.status_code == 200
    assert response.data["shipping"]["name"] == "Updated Ship"
    assert response.data["shipping"]["phone"] == "123"
    assert response.data["shipping"]["address"]["line1"] == "Ship Line 2"
    assert response.data["shipping"]["address"]["country"] == "CA"


def test_retrieve_finalized_invoice_shipping_uses_snapshot(api_client, user, account):
    shipping_address = AddressFactory(line1="Ship Line 1", country="US")
    customer_shipping = CustomerShippingFactory(name="Ship Final", phone="222", address=shipping_address)
    customer = CustomerFactory(account=account, name="Bill Final", phone="333", shipping=customer_shipping)
    invoice = InvoiceFactory(account=account, customer=customer)
    shipping_rate = ShippingRateFactory(account=account, amount=Decimal("7.00"))
    invoice.add_shipping(shipping_rate=shipping_rate, tax_rates=[])
    invoice.recalculate()
    invoice.finalize()

    customer.name = "Updated Final"
    customer.phone = "444"
    customer.address = AddressFactory(line1="Bill Line 2", country="US")
    customer.save()
    customer_shipping.name = "Updated Ship"
    customer_shipping.phone = "123"
    customer_shipping.address = AddressFactory(line1="Ship Line 2", country="CA")
    customer_shipping.save()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/invoices/{invoice.id}")

    assert response.status_code == 200
    assert response.data["shipping"]["name"] == "Ship Final"
    assert response.data["shipping"]["phone"] == "222"
    assert response.data["shipping"]["address"]["line1"] == "Ship Line 1"
    assert response.data["shipping"]["address"]["country"] == "US"


def test_retrieve_invoice_rejects_foreign_account(api_client, user, account):
    other_account = AccountFactory()
    invoice = InvoiceFactory(account=other_account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/invoices/{invoice.id}")

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


def test_retrieve_invoice_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.get(f"/api/v1/invoices/{uuid.uuid4()}")

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


def test_retrieve_invoice_not_found(api_client, user, account):
    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/invoices/{uuid.uuid4()}")

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


def test_retrieve_invoice_requires_authentication(api_client, account):
    invoice = InvoiceFactory(account=account)

    response = api_client.get(f"/api/v1/invoices/{invoice.id}")

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
