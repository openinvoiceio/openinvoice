import uuid
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import ANY, patch

import pytest
from django.utils import timezone
from drf_standardized_errors.types import ErrorType

from apps.integrations.choices import PaymentProvider
from apps.integrations.exceptions import IntegrationError
from apps.invoices.choices import InvoiceDeliveryMethod, InvoiceStatus
from apps.payments.choices import PaymentStatus
from tests.factories import InvoiceFactory, InvoiceLineFactory, StripeConnectionFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def stripe_checkout_mock():
    with patch("apps.integrations.stripe.integration.StripeIntegration.checkout") as mock:
        yield mock


def test_finalize_invoice(api_client, user, account):
    invoice = InvoiceFactory(account=account, total_amount=Decimal("10.00"))
    line = InvoiceLineFactory(invoice=invoice, description="Test line", quantity=1, unit_amount=Decimal("10.00"))
    invoice.recalculate()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{invoice.id}/finalize")

    assert response.status_code == 200
    invoice.refresh_from_db()
    assert response.data == {
        "id": str(invoice.id),
        "status": invoice.status,
        "number": invoice.effective_number,
        "numbering_system_id": None,
        "currency": invoice.currency,
        "tax_behavior": invoice.tax_behavior,
        "issue_date": invoice.issue_date.isoformat(),
        "sell_date": None,
        "due_date": invoice.due_date.isoformat(),
        "net_payment_term": invoice.net_payment_term,
        "delivery_method": invoice.delivery_method,
        "recipients": invoice.recipients,
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
        "subtotal_amount": "10.00",
        "total_discount_amount": "0.00",
        "total_excluding_tax_amount": "10.00",
        "shipping_amount": "0.00",
        "total_tax_amount": "0.00",
        "total_amount": "10.00",
        "total_credit_amount": "0.00",
        "total_paid_amount": "0.00",
        "outstanding_amount": "10.00",
        "payment_provider": None,
        "payment_connection_id": None,
        "created_at": ANY,
        "updated_at": ANY,
        "opened_at": ANY,
        "paid_at": ANY,
        "voided_at": None,
        "pdf_id": str(invoice.pdf_id),
        "lines": [
            {
                "id": str(line.id),
                "description": line.description,
                "quantity": line.quantity,
                "unit_amount": "10.00",
                "price_id": None,
                "product_id": None,
                "amount": "10.00",
                "total_discount_amount": "0.00",
                "total_excluding_tax_amount": "10.00",
                "total_tax_amount": "0.00",
                "total_tax_rate": "0.00",
                "total_amount": "10.00",
                "total_credit_amount": "0.00",
                "outstanding_amount": "10.00",
                "credit_quantity": 0,
                "outstanding_quantity": 1,
                "coupons": [],
                "discounts": [],
                "total_discounts": [],
                "tax_rates": [],
                "taxes": [],
                "total_taxes": [],
            }
        ],
        "coupons": [],
        "discounts": [],
        "total_discounts": [],
        "tax_rates": [],
        "taxes": [],
        "total_taxes": [],
        "shipping": None,
    }
    assert invoice.status == InvoiceStatus.OPEN
    assert invoice.opened_at is not None


def test_finalize_invoice_with_zero_outstanding_amount(api_client, user, account):
    invoice = InvoiceFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{invoice.id}/finalize")

    assert response.status_code == 200
    invoice.refresh_from_db()
    assert response.data == {
        "id": str(invoice.id),
        "status": invoice.status,
        "number": invoice.effective_number,
        "numbering_system_id": None,
        "currency": invoice.currency,
        "tax_behavior": invoice.tax_behavior,
        "issue_date": invoice.issue_date.isoformat(),
        "sell_date": None,
        "due_date": invoice.due_date.isoformat(),
        "net_payment_term": invoice.net_payment_term,
        "delivery_method": invoice.delivery_method,
        "recipients": invoice.recipients,
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
        "opened_at": ANY,
        "paid_at": ANY,
        "voided_at": None,
        "pdf_id": str(invoice.pdf_id),
        "lines": [],
        "coupons": [],
        "discounts": [],
        "total_discounts": [],
        "tax_rates": [],
        "taxes": [],
        "total_taxes": [],
        "shipping": None,
    }
    assert invoice.status == InvoiceStatus.PAID
    assert invoice.paid_at is not None


def test_finalize_invoice_revision_voids_original(api_client, user, account):
    original_issue_date = date(2023, 12, 1)
    invoice = InvoiceFactory(
        account=account,
        status=InvoiceStatus.OPEN,
        issue_date=original_issue_date,
    )
    revision = InvoiceFactory(account=account, customer=invoice.customer, previous_revision=invoice, head=invoice.head)
    InvoiceLineFactory(
        invoice=revision,
        quantity=1,
        unit_amount=Decimal("5.00"),
        amount=Decimal("5.00"),
        total_discount_amount=Decimal("0.00"),
        total_excluding_tax_amount=Decimal("5.00"),
        total_tax_amount=Decimal("0.00"),
        total_tax_rate=Decimal("0.00"),
        total_amount=Decimal("5.00"),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{revision.id}/finalize")

    assert response.status_code == 200
    invoice.refresh_from_db()
    revision.refresh_from_db()
    assert invoice.status == InvoiceStatus.VOIDED
    assert invoice.voided_at is not None
    assert invoice.previous_revision_id is None
    assert invoice.head.root_id == invoice.id
    assert invoice.head.current_id == revision.id


def test_finalize_invoice_with_payment_provider(api_client, user, account, stripe_checkout_mock):
    connection = StripeConnectionFactory(account=account)
    invoice = InvoiceFactory(
        account=account,
        payment_provider=PaymentProvider.STRIPE,
        payment_connection_id=connection.id,
        total_amount=Decimal("10.00"),
        outstanding_amount=Decimal("10.00"),
    )
    InvoiceLineFactory(invoice=invoice, description="Test line", quantity=1, unit_amount=Decimal("10.00"))
    stripe_checkout_mock.return_value = ("cs_123", "https://stripe.example/checkout")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{invoice.id}/finalize")

    assert response.status_code == 200
    invoice.refresh_from_db()
    payment = invoice.payments.first()
    assert payment.transaction_id == "cs_123"
    assert payment.url == "https://stripe.example/checkout"
    assert payment.status == PaymentStatus.PENDING
    assert payment.provider == PaymentProvider.STRIPE
    assert payment.connection_id == connection.id
    stripe_checkout_mock.assert_called_once_with(invoice=invoice, payment_id=payment.id)


def test_finalize_invoice_with_payment_provider_checkout_error(api_client, user, account, stripe_checkout_mock):
    connection = StripeConnectionFactory(account=account)
    invoice = InvoiceFactory(
        account=account,
        payment_provider=PaymentProvider.STRIPE,
        payment_connection_id=connection.id,
        total_amount=Decimal("10.00"),
        outstanding_amount=Decimal("10.00"),
    )
    InvoiceLineFactory(invoice=invoice, description="Test line", quantity=1, unit_amount=Decimal("10.00"))
    stripe_checkout_mock.side_effect = IntegrationError("Checkout error")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{invoice.id}/finalize")

    assert response.status_code == 200
    invoice.refresh_from_db()
    assert invoice.payments.count() == 1
    payment = invoice.payments.first()
    assert payment.status == PaymentStatus.FAILED
    assert payment.transaction_id is None
    assert payment.url is None
    assert payment.message == "Checkout error"
    assert payment.extra_data == {}
    assert payment.received_at is not None
    stripe_checkout_mock.assert_called_once_with(invoice=invoice, payment_id=payment.id)


def test_finalize_invoice_without_due_date(api_client, user, account):
    net_payment_term = 30
    invoice = InvoiceFactory(
        account=account, due_date=None, net_payment_term=net_payment_term, total_amount=Decimal("10.00")
    )
    InvoiceLineFactory(invoice=invoice, description="Test line", quantity=1, unit_amount=Decimal("10.00"))

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{invoice.id}/finalize")

    assert response.status_code == 200
    invoice.refresh_from_db()
    assert response.data["due_date"] == (timezone.now().date() + timedelta(days=net_payment_term)).isoformat()
    assert invoice.due_date == timezone.now().date() + timedelta(days=net_payment_term)
    assert invoice.status == InvoiceStatus.OPEN


def test_finalize_invoice_with_automatic_delivery_method(api_client, user, account, mailoutbox):
    invoice = InvoiceFactory(
        account=account,
        delivery_method=InvoiceDeliveryMethod.AUTOMATIC,
        recipients=["test@example.com"],
        total_amount=Decimal("10.00"),
    )
    InvoiceLineFactory(invoice=invoice, description="Test line", quantity=1, unit_amount=Decimal("10.00"))

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{invoice.id}/finalize")

    assert response.status_code == 200
    assert len(mailoutbox) == 1
    email = mailoutbox[0]
    assert email.subject == f"Invoice {invoice.effective_number} from {invoice.account.name}"
    assert email.to == ["test@example.com"]


def test_finalize_invoice_with_automatic_delivery_method_no_recipients(api_client, user, account, mailoutbox):
    invoice = InvoiceFactory(
        account=account, delivery_method=InvoiceDeliveryMethod.AUTOMATIC, recipients=[], total_amount=Decimal("10.00")
    )
    InvoiceLineFactory(invoice=invoice, description="Test line", quantity=1, unit_amount=Decimal("10.00"))

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{invoice.id}/finalize")

    assert response.status_code == 200
    assert len(mailoutbox) == 0


@pytest.mark.parametrize("status", [InvoiceStatus.PAID, InvoiceStatus.VOIDED, InvoiceStatus.OPEN])
def test_finalize_invoice_non_draft(api_client, user, account, status):
    invoice = InvoiceFactory(account=account, status=status)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{invoice.id}/finalize")

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Only draft invoices can be finalized",
            }
        ],
    }


def test_finalize_invoice_number_missing(api_client, user, account):
    invoice = InvoiceFactory(account=account, number=None, numbering_system=None)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{invoice.id}/finalize")

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Invoice number or numbering system is missing",
            }
        ],
    }


def test_finalize_invoice_not_found(api_client, user, account):
    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{uuid.uuid4()}/finalize")

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


def test_finalize_invoice_rejects_foreign_account(api_client, user, account):
    other_invoice = InvoiceFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{other_invoice.id}/finalize")

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


def test_finalize_invoice_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.post(f"/api/v1/invoices/{uuid.uuid4()}/finalize")

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


def test_finalize_invoice_requires_authentication(api_client, account):
    invoice = InvoiceFactory(account=account)

    response = api_client.post(f"/api/v1/invoices/{invoice.id}/finalize")

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
