import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import ANY

import pytest
from django.utils import timezone
from djmoney.money import Money
from drf_standardized_errors.types import ErrorType

from apps.integrations.enums import PaymentProvider
from apps.invoices.enums import InvoiceDeliveryMethod, InvoiceStatus
from apps.invoices.models import Invoice, InvoiceDiscount, InvoiceTax
from common.enums import EntitlementCode
from tests.factories import (
    CouponFactory,
    CustomerFactory,
    InvoiceFactory,
    InvoiceLineFactory,
    StripeConnectionFactory,
    TaxRateFactory,
)

pytestmark = pytest.mark.django_db


def test_create_invoice(api_client, user, account):
    customer = CustomerFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoices",
        {"customer_id": str(customer.id)},
    )

    assert response.status_code == 201
    assert response.data == {
        "id": response.data["id"],
        "status": InvoiceStatus.DRAFT,
        "number": None,
        "numbering_system_id": None,
        "previous_revision_id": None,
        "latest_revision_id": None,
        "currency": customer.currency,
        "issue_date": None,
        "sell_date": None,
        "due_date": None,
        "net_payment_term": 0,
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
        "total_tax_amount": "0.00",
        "total_amount": "0.00",
        "total_credit_amount": "0.00",
        "total_paid_amount": "0.00",
        "outstanding_amount": "0.00",
        "payment_provider": None,
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
    }

    invoice = Invoice.objects.get(id=response.data["id"])
    assert invoice.customer_id == customer.id
    assert invoice.latest_revision_id is None


def test_create_invoice_with_customer_tax_rates(api_client, user, account):
    tax_rate = TaxRateFactory(account=account)
    customer = CustomerFactory(account=account)
    customer.tax_rates.add(tax_rate)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoices",
        {"customer_id": str(customer.id)},
    )

    assert response.status_code == 201
    assert response.data["taxes"] == [
        {
            "id": ANY,
            "tax_rate_id": str(tax_rate.id),
            "name": tax_rate.name,
            "description": tax_rate.description,
            "rate": f"{tax_rate.percentage:.2f}",
            "amount": "0.00",
        }
    ]


def test_create_invoice_ignores_inactive_customer_tax_rates(api_client, user, account):
    active_rate = TaxRateFactory(account=account, is_active=True)
    inactive_rate = TaxRateFactory(account=account, is_active=False)
    customer = CustomerFactory(account=account)
    customer.tax_rates.add(active_rate, inactive_rate)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoices",
        {"customer_id": str(customer.id)},
    )

    assert response.status_code == 201
    assert response.data["taxes"] == [
        {
            "id": ANY,
            "tax_rate_id": str(active_rate.id),
            "name": active_rate.name,
            "description": active_rate.description,
            "rate": f"{active_rate.percentage:.2f}",
            "amount": "0.00",
        }
    ]


def test_create_invoice_with_automatic_delivery_and_without_entitlement(api_client, user, account, settings):
    settings.DEFAULT_ENTITLEMENT_GROUP = "test"
    settings.ENTITLEMENTS = {"test": {EntitlementCode.AUTOMATIC_INVOICE_DELIVERY: False}}
    customer = CustomerFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoices",
        {
            "customer_id": str(customer.id),
            "delivery_method": InvoiceDeliveryMethod.AUTOMATIC,
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "delivery_method",
                "code": "invalid",
                "detail": "Automatic delivery is forbidden for your account.",
            }
        ],
    }


def test_create_invoice_customer_not_found(api_client, user, account):
    customer = CustomerFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoices",
        {"customer_id": str(customer.id)},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "customer_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{customer.id}" - object does not exist.',
            }
        ],
    }


def test_create_invoice_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.post(
        "/api/v1/invoices",
        {"customer_id": str(uuid.uuid4())},
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


def test_create_invoice_requires_authentication(api_client, account):
    customer = CustomerFactory(account=account)

    response = api_client.post(
        "/api/v1/invoices",
        {"customer_id": str(customer.id)},
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


def test_create_invoice_numbering_system_not_found(api_client, user, account):
    customer = CustomerFactory(account=account)
    numbering_system_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoices",
        {
            "customer_id": str(customer.id),
            "numbering_system_id": str(numbering_system_id),
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "numbering_system_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{numbering_system_id}" - object does not exist.',
            }
        ],
    }


def test_create_invoice_with_payment_provider(api_client, user, account):
    customer = CustomerFactory(account=account)
    StripeConnectionFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoices",
        {
            "customer_id": str(customer.id),
            "payment_provider": PaymentProvider.STRIPE,
        },
    )

    assert response.status_code == 201
    assert response.data["payment_provider"] == PaymentProvider.STRIPE


def test_create_invoice_without_connected_payment_provider(api_client, user, account):
    customer = CustomerFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoices",
        {
            "customer_id": str(customer.id),
            "payment_provider": PaymentProvider.STRIPE,
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "payment_provider",
                "code": "invalid",
                "detail": "Payment provider connection not found",
            }
        ],
    }


def test_create_invoice_revision(api_client, user, account):
    original_issue_date = date(2024, 1, 5)
    original = InvoiceFactory(
        account=account,
        status=InvoiceStatus.OPEN,
        issue_date=original_issue_date,
    )
    original.latest_revision = original
    original.save(update_fields=["latest_revision"])

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoices",
        {
            "previous_revision_id": str(original.id),
        },
    )

    assert response.status_code == 201
    assert response.data["previous_revision_id"] == str(original.id)
    assert response.data["latest_revision_id"] is None
    assert response.data["customer"]["id"] == str(original.customer.id)

    revision = Invoice.objects.get(id=response.data["id"])
    assert revision.previous_revision_id == original.id
    assert revision.latest_revision_id is None
    original.refresh_from_db()
    assert original.latest_revision_id == original.id


def test_create_invoice_revision_clones_previous_details(api_client, user, account):
    original = InvoiceFactory(
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
    Invoice.objects.filter(id=original.id).update(latest_revision_id=original.id)

    line = InvoiceLineFactory(
        invoice=original,
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

    line_coupon = CouponFactory(account=account, currency=original.currency, amount=Decimal("10"), percentage=None)
    invoice_coupon = CouponFactory(account=account, currency=original.currency, amount=Decimal("5"), percentage=None)

    line_discount = InvoiceDiscount.objects.create(
        invoice=original,
        invoice_line=line,
        coupon=line_coupon,
        currency=original.currency,
        amount=Money(Decimal("10"), original.currency),
    )
    invoice_discount = InvoiceDiscount.objects.create(
        invoice=original,
        invoice_line=None,
        coupon=invoice_coupon,
        currency=original.currency,
        amount=Money(Decimal("5"), original.currency),
    )

    line_tax_rate = TaxRateFactory(account=account, percentage=Decimal("10.00"))
    invoice_tax_rate = TaxRateFactory(account=account, percentage=Decimal("5.00"))

    line_tax = InvoiceTax.objects.create(
        invoice=original,
        invoice_line=line,
        tax_rate=line_tax_rate,
        name=line_tax_rate.name,
        description=line_tax_rate.description,
        rate=line_tax_rate.percentage,
        currency=original.currency,
        amount=Money(Decimal("10"), original.currency),
    )
    invoice_tax = InvoiceTax.objects.create(
        invoice=original,
        invoice_line=None,
        tax_rate=invoice_tax_rate,
        name=invoice_tax_rate.name,
        description=invoice_tax_rate.description,
        rate=invoice_tax_rate.percentage,
        currency=original.currency,
        amount=Money(Decimal("5"), original.currency),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoices",
        {"previous_revision_id": str(original.id)},
    )

    assert response.status_code == 201

    revision = Invoice.objects.get(id=response.data["id"])
    revision_line = revision.lines.get(description="Service fee")

    assert revision.previous_revision_id == original.id
    assert revision.metadata == {}
    assert revision.custom_fields == original.custom_fields
    assert revision.footer == original.footer
    assert revision.description == original.description
    assert revision.subtotal_amount == original.subtotal_amount
    assert revision.total_discount_amount == original.total_discount_amount
    assert revision.total_amount_excluding_tax == original.total_amount_excluding_tax
    assert revision.total_tax_amount == original.total_tax_amount
    assert revision.total_amount == original.total_amount

    assert revision_line.quantity == line.quantity
    assert revision_line.unit_amount == line.unit_amount
    assert revision_line.total_amount == line.total_amount

    assert revision_line.discounts.count() == 1
    assert revision_line.discounts.first().coupon_id == line_discount.coupon_id

    assert revision_line.taxes.count() == 1
    assert revision_line.taxes.first().tax_rate_id == line_tax.tax_rate_id

    assert revision.discounts.for_invoice().count() == 1
    assert revision.discounts.for_invoice().first().coupon_id == invoice_discount.coupon_id

    assert revision.taxes.for_invoice().count() == 1
    assert revision.taxes.for_invoice().first().tax_rate_id == invoice_tax.tax_rate_id


def test_create_invoice_revision_skips_archived_coupons(api_client, user, account):
    original = InvoiceFactory(account=account, status=InvoiceStatus.OPEN)
    Invoice.objects.filter(id=original.id).update(latest_revision_id=original.id)

    line = InvoiceLineFactory(invoice=original)

    archived_line_coupon = CouponFactory(account=account, currency=original.currency, is_active=False)
    archived_invoice_coupon = CouponFactory(account=account, currency=original.currency, is_active=False)

    InvoiceDiscount.objects.create(
        invoice=original,
        invoice_line=line,
        coupon=archived_line_coupon,
        currency=original.currency,
        amount=Money(Decimal("5"), original.currency),
    )
    InvoiceDiscount.objects.create(
        invoice=original,
        invoice_line=None,
        coupon=archived_invoice_coupon,
        currency=original.currency,
        amount=Money(Decimal("5"), original.currency),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoices",
        {"previous_revision_id": str(original.id)},
    )

    assert response.status_code == 201

    revision = Invoice.objects.get(id=response.data["id"])
    revision_line = revision.lines.get(description=line.description)

    assert revision_line.discounts.count() == 0
    assert revision.discounts.for_invoice().count() == 0


@pytest.mark.parametrize("status", [InvoiceStatus.DRAFT, InvoiceStatus.PAID, InvoiceStatus.VOIDED])
def test_create_invoice_revision_requires_open_status(api_client, user, account, status):
    invoice = InvoiceFactory(account=account, status=status)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoices",
        {
            "previous_revision_id": str(invoice.id),
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "previous_revision_id",
                "code": "invalid",
                "detail": "Only open invoices can be revised",
            }
        ],
    }


def test_create_invoice_revision_rejects_existing_revision(api_client, user, account):
    original = InvoiceFactory(account=account, status=InvoiceStatus.OPEN)
    InvoiceFactory(account=account, customer=original.customer, previous_revision=original)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoices",
        {
            "previous_revision_id": str(original.id),
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "previous_revision_id",
                "code": "invalid",
                "detail": "Invoice already has a subsequent revision",
            }
        ],
    }


def test_create_invoice_revision_requires_latest_revision(api_client, user, account):
    original = InvoiceFactory(account=account, status=InvoiceStatus.OPEN)
    newer = InvoiceFactory(account=account)
    Invoice.objects.filter(id=original.id).update(latest_revision_id=newer.id)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoices",
        {
            "previous_revision_id": str(original.id),
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "previous_revision_id",
                "code": "invalid",
                "detail": "Only the latest revision can be revised",
            }
        ],
    }


def test_create_invoice_revision_after_voided_revision(api_client, user, account):
    original = InvoiceFactory(account=account, status=InvoiceStatus.OPEN)
    Invoice.objects.filter(id=original.id).update(latest_revision_id=original.id)
    InvoiceFactory(
        account=account,
        customer=original.customer,
        previous_revision=original,
        status=InvoiceStatus.VOIDED,
        voided_at=timezone.now(),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoices",
        {
            "previous_revision_id": str(original.id),
        },
    )

    assert response.status_code == 201
    assert response.data["previous_revision_id"] == str(original.id)


def test_create_invoice_requires_customer_or_previous_revision(api_client, user, account):
    api_client.force_login(user)
    api_client.force_account(account)

    response = api_client.post(
        "/api/v1/invoices",
        {},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "non_field_errors",
                "code": "invalid",
                "detail": "customer_id or previous_revision_id is required",
            }
        ],
    }


def test_create_invoice_rejects_customer_and_previous_revision(api_client, user, account):
    original = InvoiceFactory(account=account, status=InvoiceStatus.OPEN)
    original.latest_revision_id = original.id
    original.save()

    api_client.force_login(user)
    api_client.force_account(account)

    response = api_client.post(
        "/api/v1/invoices",
        {
            "customer_id": str(original.customer.id),
            "previous_revision_id": str(original.id),
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "non_field_errors",
                "code": "invalid",
                "detail": "Provide either customer_id or previous_revision_id",
            }
        ],
    }


def test_create_invoice_limit_exceeded(api_client, user, account, settings):
    settings.DEFAULT_ENTITLEMENT_GROUP = "test"
    settings.ENTITLEMENTS = {"test": {EntitlementCode.MAX_INVOICES_PER_MONTH: 0}}

    customer = CustomerFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoices",
        {"customer_id": str(customer.id)},
    )

    assert response.status_code == 403
    assert response.data == {
        "type": ErrorType.CLIENT_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "limit_exceeded",
                "detail": "Limit has been exceeded for your account.",
            }
        ],
    }
