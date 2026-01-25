import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import ANY

import pytest
from drf_standardized_errors.types import ErrorType

from apps.coupons.choices import CouponStatus
from apps.integrations.choices import PaymentProvider
from apps.invoices.choices import InvoiceDeliveryMethod, InvoiceStatus
from apps.invoices.models import Invoice
from apps.tax_rates.choices import TaxRateStatus
from common.choices import LimitCode
from tests.factories import (
    CouponFactory,
    CustomerFactory,
    InvoiceFactory,
    InvoiceLineFactory,
    InvoiceShippingFactory,
    NumberingSystemFactory,
    ShippingRateFactory,
    TaxRateFactory,
)

pytestmark = pytest.mark.django_db


def test_clone_invoice(api_client, user, account):
    customer = CustomerFactory(account=account, currency="USD")
    numbering_system = NumberingSystemFactory(account=account)
    shipping_rate = ShippingRateFactory(account=account, currency=customer.currency, amount=Decimal("10"))
    shipping = InvoiceShippingFactory(shipping_rate=shipping_rate, amount=Decimal("10"))
    shipping_tax_rate = TaxRateFactory(account=account, percentage=Decimal("10.00"))
    shipping.set_tax_rates([shipping_tax_rate])
    payment_connection_id = uuid.uuid4()

    invoice = InvoiceFactory(
        account=account,
        customer=customer,
        status=InvoiceStatus.OPEN,
        issue_date=date(2024, 1, 5),
        sell_date=date(2024, 1, 6),
        due_date=date(2024, 1, 7),
        metadata={"note": "keep"},
        custom_fields={"po": "123"},
        footer="Original footer",
        description="Original description",
        numbering_system=numbering_system,
        net_payment_term=10,
        delivery_method=InvoiceDeliveryMethod.MANUAL,
        recipients=[customer.email],
        payment_provider=PaymentProvider.STRIPE,
        payment_connection_id=payment_connection_id,
        shipping=shipping,
    )

    line = InvoiceLineFactory(
        invoice=invoice,
        description="Service fee",
        quantity=2,
        unit_amount=Decimal("100"),
        unit_excluding_tax_amount=Decimal("100"),
        total_tax_rate=Decimal("10"),
    )

    line_coupon = CouponFactory(account=account, currency=invoice.currency, amount=Decimal("10"), percentage=None)
    invoice_coupon = CouponFactory(account=account, currency=invoice.currency, amount=Decimal("5"), percentage=None)
    line.set_coupons([line_coupon])
    invoice.set_coupons([invoice_coupon])

    line_tax_rate = TaxRateFactory(account=account, percentage=Decimal("10.00"))
    invoice_tax_rate = TaxRateFactory(account=account, percentage=Decimal("5.00"))
    line.set_tax_rates([line_tax_rate])
    invoice.set_tax_rates([invoice_tax_rate])

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{invoice.id}/clone")

    assert response.status_code == 201
    assert response.data == {
        "id": response.data["id"],
        "status": InvoiceStatus.DRAFT,
        "number": "INV-2",
        "numbering_system_id": str(numbering_system.id),
        "currency": invoice.currency,
        "tax_behavior": invoice.tax_behavior,
        "issue_date": None,
        "sell_date": None,
        "due_date": None,
        "net_payment_term": invoice.net_payment_term,
        "customer": {
            "id": str(customer.id),
            "name": customer.name,
            "legal_name": customer.legal_name,
            "legal_number": customer.legal_number,
            "email": customer.email,
            "phone": customer.phone,
            "description": customer.description,
            "address": {
                "line1": customer.address.line1,
                "line2": customer.address.line2,
                "locality": customer.address.locality,
                "state": customer.address.state,
                "postal_code": customer.address.postal_code,
                "country": customer.address.country,
            },
            "logo_id": None,
        },
        "account": {
            "id": str(account.id),
            "name": account.name,
            "legal_name": account.legal_name,
            "legal_number": account.legal_number,
            "email": account.email,
            "phone": account.phone,
            "address": {
                "line1": account.address.line1,
                "line2": account.address.line2,
                "locality": account.address.locality,
                "state": account.address.state,
                "postal_code": account.address.postal_code,
                "country": account.address.country,
            },
            "logo_id": None,
        },
        "metadata": {},
        "custom_fields": invoice.custom_fields,
        "footer": invoice.footer,
        "description": invoice.description,
        "delivery_method": invoice.delivery_method,
        "recipients": invoice.recipients,
        "subtotal_amount": "190.00",
        "total_discount_amount": "10.00",
        "total_excluding_tax_amount": "200.00",
        "shipping_amount": "10.00",
        "total_tax_amount": "20.00",
        "total_amount": "220.00",
        "total_credit_amount": "0.00",
        "total_paid_amount": "0.00",
        "outstanding_amount": "220.00",
        "payment_provider": PaymentProvider.STRIPE,
        "payment_connection_id": str(payment_connection_id),
        "created_at": ANY,
        "updated_at": ANY,
        "opened_at": None,
        "paid_at": None,
        "voided_at": None,
        "pdf_id": None,
        "previous_revision_id": None,
        "lines": [
            {
                "id": response.data["lines"][0]["id"],
                "description": line.description,
                "quantity": line.quantity,
                "unit_amount": "100.00",
                "price_id": None,
                "product_id": None,
                "amount": "200.00",
                "subtotal_amount": "190.00",
                "total_discount_amount": "10.00",
                "total_excluding_tax_amount": "190.00",
                "total_tax_amount": "19.00",
                "total_tax_rate": "10.00",
                "total_amount": "209.00",
                "total_credit_amount": "0.00",
                "credit_quantity": 0,
                "outstanding_amount": "209.00",
                "outstanding_quantity": line.quantity,
                "coupons": [
                    {
                        "id": str(line_coupon.id),
                        "account_id": str(account.id),
                        "name": line_coupon.name,
                        "currency": line_coupon.currency,
                        "amount": "10.00",
                        "percentage": None,
                        "status": line_coupon.status,
                        "created_at": ANY,
                        "updated_at": ANY,
                        "archived_at": None,
                    }
                ],
                "discounts": [
                    {
                        "coupon_id": str(line_coupon.id),
                        "name": line_coupon.name,
                        "amount": "10.00",
                    }
                ],
                "total_discounts": [
                    {
                        "coupon_id": str(line_coupon.id),
                        "name": line_coupon.name,
                        "amount": "10.00",
                    }
                ],
                "tax_rates": [
                    {
                        "id": str(line_tax_rate.id),
                        "account_id": str(account.id),
                        "name": line_tax_rate.name,
                        "description": line_tax_rate.description,
                        "country": line_tax_rate.country,
                        "percentage": "10.00",
                        "status": line_tax_rate.status,
                        "created_at": ANY,
                        "updated_at": ANY,
                        "archived_at": line_tax_rate.archived_at,
                    }
                ],
                "taxes": [
                    {
                        "tax_rate_id": str(line_tax_rate.id),
                        "name": line_tax_rate.name,
                        "percentage": "10.00",
                        "amount": "19.00",
                    }
                ],
                "total_taxes": [
                    {
                        "tax_rate_id": str(line_tax_rate.id),
                        "name": line_tax_rate.name,
                        "percentage": "10.00",
                        "amount": "19.00",
                    }
                ],
            }
        ],
        "coupons": [
            {
                "id": str(invoice_coupon.id),
                "account_id": str(account.id),
                "name": invoice_coupon.name,
                "currency": invoice_coupon.currency,
                "amount": "5.00",
                "percentage": None,
                "status": invoice_coupon.status,
                "created_at": ANY,
                "updated_at": ANY,
                "archived_at": None,
            }
        ],
        "discounts": [],
        "total_discounts": [
            {
                "coupon_id": str(line_coupon.id),
                "name": line_coupon.name,
                "amount": "10.00",
            }
        ],
        "tax_rates": [
            {
                "id": str(invoice_tax_rate.id),
                "account_id": str(account.id),
                "name": invoice_tax_rate.name,
                "description": invoice_tax_rate.description,
                "country": invoice_tax_rate.country,
                "percentage": "5.00",
                "status": invoice_tax_rate.status,
                "created_at": ANY,
                "updated_at": ANY,
                "archived_at": None,
            }
        ],
        "taxes": [],
        "total_taxes": [
            {
                "tax_rate_id": str(line_tax_rate.id),
                "name": line_tax_rate.name,
                "percentage": "10.00",
                "amount": "19.00",
            },
            {
                "tax_rate_id": str(shipping_tax_rate.id),
                "name": shipping_tax_rate.name,
                "percentage": "10.00",
                "amount": "1.00",
            },
        ],
        "shipping": {
            "name": customer.name,
            "phone": customer.phone,
            "address": {
                "line1": customer.address.line1,
                "line2": customer.address.line2,
                "locality": customer.address.locality,
                "state": customer.address.state,
                "postal_code": customer.address.postal_code,
                "country": customer.address.country,
            },
            "amount": "10.00",
            "total_excluding_tax_amount": "10.00",
            "total_tax_amount": "1.00",
            "total_tax_rate": "10.00",
            "total_amount": "11.00",
            "shipping_rate_id": str(shipping_rate.id),
            "tax_rates": [
                {
                    "id": str(shipping_tax_rate.id),
                    "account_id": str(account.id),
                    "name": shipping_tax_rate.name,
                    "description": shipping_tax_rate.description,
                    "country": shipping_tax_rate.country,
                    "percentage": "10.00",
                    "status": shipping_tax_rate.status,
                    "created_at": ANY,
                    "updated_at": ANY,
                    "archived_at": shipping_tax_rate.archived_at,
                }
            ],
            "total_taxes": [
                {
                    "tax_rate_id": str(shipping_tax_rate.id),
                    "name": shipping_tax_rate.name,
                    "percentage": "10.00",
                    "amount": "1.00",
                }
            ],
        },
    }

    new_invoice = Invoice.objects.get(id=response.data["id"])
    assert new_invoice.id != invoice.id
    assert new_invoice.head_id != invoice.head_id
    assert new_invoice.head.root_id == new_invoice.id
    assert new_invoice.head.current_id is None
    assert new_invoice.previous_revision_id is None
    assert new_invoice.status == InvoiceStatus.DRAFT
    assert new_invoice.number is None
    assert new_invoice.issue_date is None
    assert new_invoice.sell_date is None
    assert new_invoice.due_date is None
    assert new_invoice.metadata == {}
    assert new_invoice.custom_fields == invoice.custom_fields
    assert new_invoice.footer == invoice.footer
    assert new_invoice.description == invoice.description
    assert new_invoice.numbering_system_id == invoice.numbering_system_id
    assert new_invoice.net_payment_term == invoice.net_payment_term
    assert new_invoice.delivery_method == invoice.delivery_method
    assert new_invoice.recipients == invoice.recipients
    assert new_invoice.payment_provider == invoice.payment_provider
    assert new_invoice.payment_connection_id == invoice.payment_connection_id

    assert new_invoice.coupons.count() == 1
    assert new_invoice.tax_rates.count() == 1
    assert new_invoice.shipping.shipping_rate_id == shipping_rate.id
    assert new_invoice.shipping.tax_rates.count() == 1

    cloned_line = new_invoice.lines.get(description="Service fee")
    assert cloned_line.quantity == line.quantity
    assert cloned_line.unit_amount == line.unit_amount
    assert cloned_line.coupons.count() == 1
    assert cloned_line.tax_rates.count() == 1


def test_clone_invoice_skips_archived_coupons(api_client, user, account):
    invoice = InvoiceFactory(account=account, status=InvoiceStatus.OPEN)
    line = InvoiceLineFactory(invoice=invoice)
    archived_line_coupon = CouponFactory(account=account, currency=invoice.currency, status=CouponStatus.ARCHIVED)
    archived_invoice_coupon = CouponFactory(account=account, currency=invoice.currency, status=CouponStatus.ARCHIVED)
    line.set_coupons([archived_line_coupon])
    invoice.set_coupons([archived_invoice_coupon])

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{invoice.id}/clone")

    assert response.status_code == 201

    cloned_invoice = Invoice.objects.get(id=response.data["id"])
    cloned_line = cloned_invoice.lines.get(description=line.description)
    assert cloned_line.coupons.count() == 0
    assert cloned_invoice.coupons.count() == 0


def test_clone_invoice_skips_archived_tax_rates(api_client, user, account):
    invoice = InvoiceFactory(account=account, status=InvoiceStatus.OPEN)
    line = InvoiceLineFactory(invoice=invoice)
    archived_line_tax_rate = TaxRateFactory(account=account, percentage=Decimal("10.00"), status=TaxRateStatus.ARCHIVED)
    archived_invoice_tax_rate = TaxRateFactory(
        account=account,
        percentage=Decimal("5.00"),
        status=TaxRateStatus.ARCHIVED,
    )
    line.set_tax_rates([archived_line_tax_rate])
    invoice.set_tax_rates([archived_invoice_tax_rate])

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{invoice.id}/clone")

    assert response.status_code == 201

    cloned_invoice = Invoice.objects.get(id=response.data["id"])
    cloned_line = cloned_invoice.lines.get(description=line.description)
    assert cloned_line.tax_rates.count() == 0
    assert cloned_invoice.tax_rates.count() == 0


def test_clone_invoice_overflow_returns_validation_error(api_client, user, account):
    invoice = InvoiceFactory(account=account, status=InvoiceStatus.OPEN)
    InvoiceLineFactory(
        invoice=invoice,
        quantity=2,
        unit_amount=Decimal("50000000000000000.00"),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{invoice.id}/clone")

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Amount exceeds the maximum allowed value",
            }
        ],
    }


def test_clone_invoice_not_found(api_client, user, account):
    invoice_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{invoice_id}/clone")

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


def test_clone_invoice_foreign_account(api_client, user, account):
    invoice = InvoiceFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{invoice.id}/clone")

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


def test_clone_invoice_requires_authentication(api_client):
    invoice_id = uuid.uuid4()

    response = api_client.post(f"/api/v1/invoices/{invoice_id}/clone")

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


def test_clone_invoice_requires_account(api_client, user):
    invoice_id = uuid.uuid4()

    api_client.force_login(user)
    response = api_client.post(f"/api/v1/invoices/{invoice_id}/clone")

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


def test_clone_invoice_limit_exceeded(api_client, user, account, settings):
    settings.DEFAULT_PLAN = "test"
    settings.PLANS = {"test": {"limits": {LimitCode.MAX_INVOICES_PER_MONTH: 0}}}

    invoice_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{invoice_id}/clone")

    assert response.status_code == 403
    assert response.data == {
        "type": "client_error",
        "errors": [
            {
                "attr": None,
                "code": "limit_exceeded",
                "detail": "Limit has been exceeded for your account.",
            }
        ],
    }
