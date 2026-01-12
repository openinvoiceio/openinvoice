import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import ANY

import pytest
from django.utils import timezone

from apps.invoices.enums import InvoiceDeliveryMethod, InvoiceStatus
from apps.invoices.models import Invoice
from common.enums import LimitCode
from tests.factories import (
    CouponFactory,
    CustomerFactory,
    InvoiceDiscountFactory,
    InvoiceFactory,
    InvoiceLineFactory,
    InvoiceTaxFactory,
    ShippingRateFactory,
    TaxRateFactory,
)

pytestmark = pytest.mark.django_db


def test_create_invoice_revision(api_client, user, account):
    original_issue_date = date(2024, 1, 5)
    customer = CustomerFactory(account=account)
    invoice = InvoiceFactory(
        account=account,
        customer=customer,
        status=InvoiceStatus.OPEN,
        issue_date=original_issue_date,
        recipients=[customer.email],
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{invoice.id}/revisions")

    assert response.status_code == 201
    assert response.data == {
        "id": response.data["id"],
        "status": InvoiceStatus.DRAFT,
        "number": None,
        "numbering_system_id": None,
        "currency": customer.currency,
        "issue_date": None,
        "sell_date": None,
        "due_date": None,
        "net_payment_term": 7,
        "customer": {
            "id": str(customer.id),
            "name": customer.name,
            "legal_name": customer.legal_name,
            "legal_number": customer.legal_number,
            "email": customer.email,
            "phone": customer.phone,
            "description": customer.description,
            "billing_address": {
                "line1": customer.billing_address.line1,
                "line2": customer.billing_address.line2,
                "locality": customer.billing_address.locality,
                "state": customer.billing_address.state,
                "postal_code": customer.billing_address.postal_code,
                "country": customer.billing_address.country,
            },
            "shipping_address": {
                "line1": customer.shipping_address.line1,
                "line2": customer.shipping_address.line2,
                "locality": customer.shipping_address.locality,
                "state": customer.shipping_address.state,
                "postal_code": customer.shipping_address.postal_code,
                "country": customer.shipping_address.country,
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
        "custom_fields": {},
        "footer": account.invoice_footer,
        "description": None,
        "delivery_method": InvoiceDeliveryMethod.MANUAL,
        "recipients": [customer.email],
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
        "taxes": [],
        "discounts": [],
        "tax_breakdown": [],
        "discount_breakdown": [],
        "shipping": None,
    }

    revision = Invoice.objects.get(id=response.data["id"])
    assert revision.previous_revision_id == invoice.id
    assert revision.head_id == invoice.head_id
    assert revision.head.root_id == invoice.id
    assert revision.head.current_id == invoice.id


def test_create_invoice_revision_clones_previous_details(api_client, user, account):
    invoice = InvoiceFactory(
        account=account,
        status=InvoiceStatus.OPEN,
        subtotal_amount=Decimal("100"),
        total_discount_amount=Decimal("15"),
        total_amount_excluding_tax=Decimal("85"),
        total_tax_amount=Decimal("9"),
        total_amount=Decimal("94"),
        metadata={"note": "keep"},
        custom_fields={"po": "123"},
        footer="Original footer",
        description="Original description",
    )

    line = InvoiceLineFactory(
        invoice=invoice,
        description="Service fee",
        quantity=1,
        unit_amount=Decimal("100"),
        amount=Decimal("100"),
        total_amount_excluding_tax=Decimal("90"),
        total_discount_amount=Decimal("10"),
        total_tax_amount=Decimal("9"),
        total_amount=Decimal("99"),
        total_tax_rate=Decimal("10"),
    )

    line_coupon = CouponFactory(account=account, currency=invoice.currency, amount=Decimal("10"), percentage=None)
    invoice_coupon = CouponFactory(account=account, currency=invoice.currency, amount=Decimal("5"), percentage=None)
    line_discount = InvoiceDiscountFactory(invoice_line=line, coupon=line_coupon, amount=Decimal("10"))
    invoice_discount = InvoiceDiscountFactory(invoice=invoice, coupon=invoice_coupon, amount=Decimal("5"))

    line_tax_rate = TaxRateFactory(account=account, percentage=Decimal("10.00"))
    invoice_tax_rate = TaxRateFactory(account=account, percentage=Decimal("5.00"))
    line_tax = InvoiceTaxFactory(invoice_line=line, tax_rate=line_tax_rate, amount=Decimal("10"))
    invoice_tax = InvoiceTaxFactory(invoice=invoice, tax_rate=invoice_tax_rate, amount=Decimal("5"))

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{invoice.id}/revisions")

    assert response.status_code == 201

    revision = Invoice.objects.get(id=response.data["id"])
    assert revision.previous_revision_id == invoice.id
    assert revision.metadata == {}
    assert revision.custom_fields == invoice.custom_fields
    assert revision.footer == invoice.footer
    assert revision.description == invoice.description
    assert revision.subtotal_amount == invoice.subtotal_amount
    assert revision.total_discount_amount == invoice.total_discount_amount
    assert revision.total_amount_excluding_tax == invoice.total_amount_excluding_tax
    assert revision.total_tax_amount == invoice.total_tax_amount
    assert revision.total_amount == invoice.total_amount
    assert revision.discounts.for_invoice().count() == 1
    assert revision.discounts.for_invoice().first().coupon_id == invoice_discount.coupon_id
    assert revision.taxes.for_invoice().count() == 1
    assert revision.taxes.for_invoice().first().tax_rate_id == invoice_tax.tax_rate_id

    revision_line = revision.lines.get(description="Service fee")
    assert revision_line.quantity == line.quantity
    assert revision_line.unit_amount == line.unit_amount
    assert revision_line.total_amount == line.total_amount
    assert revision_line.discounts.count() == 1
    assert revision_line.discounts.first().coupon_id == line_discount.coupon_id
    assert revision_line.taxes.count() == 1
    assert revision_line.taxes.first().tax_rate_id == line_tax.tax_rate_id


def test_create_invoice_revision_skips_archived_coupons(api_client, user, account):
    invoice = InvoiceFactory(account=account, status=InvoiceStatus.OPEN)

    line = InvoiceLineFactory(invoice=invoice)
    archived_line_coupon = CouponFactory(account=account, currency=invoice.currency, is_active=False)
    archived_invoice_coupon = CouponFactory(account=account, currency=invoice.currency, is_active=False)
    InvoiceDiscountFactory(invoice_line=line, coupon=archived_line_coupon, amount=Decimal("5"))
    InvoiceDiscountFactory(invoice=invoice, coupon=archived_invoice_coupon, amount=Decimal("5"))

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{invoice.id}/revisions")

    assert response.status_code == 201

    revision = Invoice.objects.get(id=response.data["id"])
    revision_line = revision.lines.get(description=line.description)
    assert revision_line.discounts.count() == 0
    assert revision.discounts.for_invoice().count() == 0


def test_create_invoice_revision_after_voided_revision(api_client, user, account):
    invoice = InvoiceFactory(account=account, status=InvoiceStatus.VOIDED)
    revision = InvoiceFactory(
        head=invoice.head,
        account=account,
        customer=invoice.customer,
        previous_revision=invoice,
        status=InvoiceStatus.VOIDED,
        opened_at=timezone.now(),
        voided_at=timezone.now(),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{revision.id}/revisions")

    assert response.status_code == 201
    new_revision = Invoice.objects.get(id=response.data["id"])
    assert new_revision.status == InvoiceStatus.DRAFT
    assert new_revision.previous_revision_id == revision.id
    assert new_revision.head_id == invoice.head_id
    assert new_revision.head.current_id == revision.id


@pytest.mark.parametrize("status", [InvoiceStatus.DRAFT, InvoiceStatus.PAID])
def test_create_invoice_revision_requires_open_or_voided_status(api_client, user, account, status):
    invoice = InvoiceFactory(account=account, status=status)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{invoice.id}/revisions")

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Only open and voided invoices can be revised",
            }
        ],
    }


def test_create_invoice_revision_from_another_draft_revision(api_client, user, account):
    invoice = InvoiceFactory(account=account, status=InvoiceStatus.OPEN)
    revision = InvoiceFactory(
        account=account,
        status=InvoiceStatus.DRAFT,
        customer=invoice.customer,
        previous_revision=invoice,
        head=invoice.head,
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{revision.id}/revisions")

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Only open and voided invoices can be revised",
            }
        ],
    }


def test_create_invoice_revision_rejects_existing_revision(api_client, user, account):
    invoice = InvoiceFactory(account=account, status=InvoiceStatus.OPEN)
    InvoiceFactory(
        account=account,
        status=InvoiceStatus.DRAFT,
        customer=invoice.customer,
        previous_revision=invoice,
        head=invoice.head,
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{invoice.id}/revisions")

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Invoice already has a subsequent revision",
            }
        ],
    }


# TODO: add shipping tests


def test_create_invoice_revision_shipping_tax_rates_limit_exceeded(api_client, user, account, settings):
    settings.MAX_INVOICE_TAX_RATES = 1
    invoice = InvoiceFactory(account=account, status=InvoiceStatus.OPEN)
    shipping_rate = ShippingRateFactory(account=account, currency=invoice.currency)
    tax_rate1 = TaxRateFactory(account=account)
    tax_rate2 = TaxRateFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/invoices/{invoice.id}/revisions",
        {"shipping": {"shipping_rate_id": str(shipping_rate.id), "tax_rates": [str(tax_rate1.id), str(tax_rate2.id)]}},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "shipping.tax_rates",
                "code": "invalid",
                "detail": "Ensure this list contains at most 1 items.",
            }
        ],
    }


def test_create_invoice_revision_limit_reached(api_client, user, account, settings):
    settings.MAX_REVISIONS_PER_INVOICE = 1
    invoice = InvoiceFactory(account=account, status=InvoiceStatus.VOIDED)
    revision = InvoiceFactory(
        head=invoice.head,
        account=account,
        customer=invoice.customer,
        previous_revision=invoice,
        status=InvoiceStatus.OPEN,
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{revision.id}/revisions")

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Maximum number of invoice revisions reached",
            }
        ],
    }


def test_create_invoice_revision_not_found(api_client, user, account):
    invoice_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{invoice_id}/revisions")

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


def test_create_invoice_revision_foreign_account(api_client, user, account):
    invoice = InvoiceFactory()  # Other account

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{invoice.id}/revisions")

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


def test_create_invoice_revision_requires_authentication(api_client):
    invoice_id = uuid.uuid4()

    response = api_client.post(f"/api/v1/invoices/{invoice_id}/revisions")

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


def test_create_invoice_revision_requires_account(api_client, user):
    invoice_id = uuid.uuid4()

    api_client.force_login(user)
    response = api_client.post(f"/api/v1/invoices/{invoice_id}/revisions")

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


def test_create_invoice_revision_limit_exceeded(api_client, user, account, settings):
    settings.DEFAULT_PLAN = "test"
    settings.PLANS = {"test": {"limits": {LimitCode.MAX_INVOICES_PER_MONTH: 0}}}

    invoice_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{invoice_id}/revisions")

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


def test_create_invoice_revision_with_coupons(api_client, user, account):
    currency = "USD"
    coupon1 = CouponFactory(account=account, currency=currency)
    coupon2 = CouponFactory(account=account, currency=currency)
    customer = CustomerFactory(account=account, currency=currency)
    invoice = InvoiceFactory(account=account, customer=customer, currency=currency, status=InvoiceStatus.OPEN)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/invoices/{invoice.id}/revisions",
        {"coupons": [str(coupon1.id), str(coupon2.id)]},
    )

    assert response.status_code == 201
    # TODO: add assert of created discounts when added


def test_create_invoice_revision_with_coupons_invalid_currency(api_client, user, account):
    coupon1 = CouponFactory(account=account, currency="USD")
    coupon2 = CouponFactory(account=account, currency="EUR")
    customer = CustomerFactory(account=account)
    invoice = InvoiceFactory(account=account, customer=customer, status=InvoiceStatus.OPEN, currency="USD")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/invoices/{invoice.id}/revisions",
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


def test_create_invoice_revision_with_duplicate_coupons(api_client, user, account):
    coupon = CouponFactory(account=account, currency="USD")
    customer = CustomerFactory(account=account, currency="USD")
    invoice = InvoiceFactory(account=account, customer=customer, status=InvoiceStatus.OPEN)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/invoices/{invoice.id}/revisions",
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


def test_create_invoice_revision_with_foreign_coupon(api_client, user, account):
    currency = "USD"
    coupon1 = CouponFactory(account=account, currency=currency)
    coupon2 = CouponFactory(currency=currency)  # Not linked to the account
    customer = CustomerFactory(account=account, currency=currency)
    invoice = InvoiceFactory(account=account, customer=customer, status=InvoiceStatus.OPEN)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/invoices/{invoice.id}/revisions",
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


def test_create_invoice_revision_coupons_limit_exceeded(api_client, user, account, settings):
    settings.MAX_INVOICE_COUPONS = 1
    currency = "USD"
    coupon1 = CouponFactory(account=account, currency=currency)
    coupon2 = CouponFactory(account=account, currency=currency)
    customer = CustomerFactory(account=account, currency=currency)
    invoice = InvoiceFactory(account=account, customer=customer, status=InvoiceStatus.OPEN)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/invoices/{invoice.id}/revisions",
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


def test_create_invoice_revision_with_tax_rates(api_client, user, account):
    tax_rate1 = TaxRateFactory(account=account)
    tax_rate2 = TaxRateFactory(account=account)
    customer = CustomerFactory(account=account)
    invoice = InvoiceFactory(account=account, customer=customer, status=InvoiceStatus.OPEN)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/invoices/{invoice.id}/revisions",
        {"tax_rates": [str(tax_rate1.id), str(tax_rate2.id)]},
    )

    assert response.status_code == 201
    # TODO: add assert of created taxes when added


def test_create_invoice_revision_with_duplicate_tax_rates(api_client, user, account):
    tax_rate = TaxRateFactory(account=account)
    customer = CustomerFactory(account=account)
    invoice = InvoiceFactory(account=account, customer=customer, status=InvoiceStatus.OPEN)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/invoices/{invoice.id}/revisions",
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


def test_create_invoice_revision_with_foreign_tax_rate(api_client, user, account):
    tax_rate1 = TaxRateFactory(account=account)
    tax_rate2 = TaxRateFactory()  # Not linked to the account
    customer = CustomerFactory(account=account)
    invoice = InvoiceFactory(account=account, customer=customer, status=InvoiceStatus.OPEN)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/invoices/{invoice.id}/revisions",
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


def test_create_invoice_revision_tax_rates_limit_exceeded(api_client, user, account, settings):
    settings.MAX_INVOICE_TAX_RATES = 1
    tax_rate1 = TaxRateFactory(account=account)
    tax_rate2 = TaxRateFactory(account=account)
    customer = CustomerFactory(account=account)
    invoice = InvoiceFactory(account=account, customer=customer, status=InvoiceStatus.OPEN)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/invoices/{invoice.id}/revisions",
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
