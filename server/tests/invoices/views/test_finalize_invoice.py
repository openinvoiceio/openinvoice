import uuid
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import ANY, patch

import pytest
from django.utils import timezone

from openinvoice.integrations.choices import PaymentProvider
from openinvoice.integrations.exceptions import IntegrationError
from openinvoice.invoices.choices import InvoiceDeliveryMethod, InvoiceDocumentAudience, InvoiceStatus
from openinvoice.payments.choices import PaymentStatus
from tests.factories import (
    AddressFactory,
    BillingProfileFactory,
    CustomerFactory,
    CustomerShippingFactory,
    InvoiceDocumentFactory,
    InvoiceFactory,
    InvoiceLineFactory,
    ShippingRateFactory,
    StripeConnectionFactory,
    TaxIdFactory,
    TaxRateFactory,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def stripe_checkout_mock():
    with patch("openinvoice.integrations.stripe.integration.StripeIntegration.checkout") as mock:
        yield mock


def test_finalize_invoice(api_client, user, account):
    invoice = InvoiceFactory(account=account, total_amount=Decimal("10.00"))
    document = InvoiceDocumentFactory(invoice=invoice, audience=[InvoiceDocumentAudience.CUSTOMER])
    line = InvoiceLineFactory(invoice=invoice, description="Test line", quantity=1, unit_amount=Decimal("10.00"))
    invoice.recalculate()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{invoice.id}/finalize")

    assert response.status_code == 200
    invoice.refresh_from_db()
    document.refresh_from_db()
    assert response.data == {
        "id": str(invoice.id),
        "status": invoice.status,
        "number": invoice.effective_number,
        "numbering_system_id": None,
        "currency": invoice.currency,
        "tax_behavior": invoice.tax_behavior,
        "issue_date": invoice.issue_date.isoformat(),
        "due_date": invoice.due_date.isoformat(),
        "net_payment_term": invoice.net_payment_term,
        "delivery_method": invoice.delivery_method,
        "recipients": invoice.recipients,
        "billing_profile": {
            "id": str(invoice.billing_profile.id),
            "name": invoice.billing_profile.name,
            "legal_name": invoice.billing_profile.legal_name,
            "legal_number": invoice.billing_profile.legal_number,
            "email": invoice.billing_profile.email,
            "phone": invoice.billing_profile.phone,
            "address": {
                "line1": invoice.billing_profile.address.line1,
                "line2": invoice.billing_profile.address.line2,
                "locality": invoice.billing_profile.address.locality,
                "state": invoice.billing_profile.address.state,
                "postal_code": invoice.billing_profile.address.postal_code,
                "country": str(invoice.billing_profile.address.country),
            },
            "currency": invoice.billing_profile.currency,
            "language": invoice.billing_profile.language,
            "net_payment_term": invoice.billing_profile.net_payment_term,
            "invoice_numbering_system_id": invoice.billing_profile.invoice_numbering_system_id,
            "credit_note_numbering_system_id": invoice.billing_profile.credit_note_numbering_system_id,
            "tax_rates": [],
            "tax_ids": [],
            "created_at": ANY,
            "updated_at": ANY,
        },
        "business_profile": {
            "id": str(invoice.business_profile.id),
            "name": invoice.business_profile.name,
            "legal_name": invoice.business_profile.legal_name,
            "legal_number": invoice.business_profile.legal_number,
            "email": invoice.business_profile.email,
            "phone": invoice.business_profile.phone,
            "address": {
                "line1": invoice.business_profile.address.line1,
                "line2": invoice.business_profile.address.line2,
                "locality": invoice.business_profile.address.locality,
                "state": invoice.business_profile.address.state,
                "postal_code": invoice.business_profile.address.postal_code,
                "country": str(invoice.business_profile.address.country),
            },
            "tax_ids": [],
            "created_at": ANY,
            "updated_at": ANY,
        },
        "metadata": {},
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
        "previous_revision_id": None,
        "documents": [
            {
                "id": str(document.id),
                "audience": document.audience,
                "language": document.language,
                "footer": document.footer,
                "memo": document.memo,
                "custom_fields": document.custom_fields,
                "url": document.file.data.url,
                "created_at": ANY,
                "updated_at": ANY,
            }
        ],
        "lines": [
            {
                "id": str(line.id),
                "description": line.description,
                "quantity": line.quantity,
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


def test_finalize_invoice_clones_customer_tax_ids(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    InvoiceDocumentFactory(invoice=invoice, audience=[InvoiceDocumentAudience.CUSTOMER])
    customer_tax_id = TaxIdFactory()
    invoice.customer.default_billing_profile.tax_ids.add(customer_tax_id)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{invoice.id}/finalize")

    assert response.status_code == 200
    invoice.refresh_from_db()

    customer_snapshot_tax_ids = list(invoice.billing_profile.tax_ids.all())
    assert len(customer_snapshot_tax_ids) == 1
    customer_snapshot_tax_id = customer_snapshot_tax_ids[0]
    assert customer_snapshot_tax_id.id != customer_tax_id.id
    assert customer_snapshot_tax_id.type == customer_tax_id.type
    assert customer_snapshot_tax_id.number == customer_tax_id.number
    assert customer_snapshot_tax_id.country == customer_tax_id.country


def test_finalize_invoice_clones_account_tax_ids(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    InvoiceDocumentFactory(invoice=invoice, audience=[InvoiceDocumentAudience.CUSTOMER])
    account_tax_id = TaxIdFactory()
    invoice.account.default_business_profile.tax_ids.add(account_tax_id)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{invoice.id}/finalize")

    assert response.status_code == 200
    invoice.refresh_from_db()

    account_snapshot_tax_ids = list(invoice.business_profile.tax_ids.all())
    assert len(account_snapshot_tax_ids) == 1
    account_snapshot_tax_id = account_snapshot_tax_ids[0]
    assert account_snapshot_tax_id.id != account_tax_id.id
    assert account_snapshot_tax_id.type == account_tax_id.type
    assert account_snapshot_tax_id.number == account_tax_id.number
    assert account_snapshot_tax_id.country == account_tax_id.country


def test_finalize_invoice_with_shipping_uses_customer_shipping_snapshot(api_client, user, account):
    shipping_address = AddressFactory(line1="123 Shipping St", country="US")
    customer_shipping = CustomerShippingFactory(name="Ship to", phone="555", address=shipping_address)
    customer = CustomerFactory(
        account=account,
        default_billing_profile=BillingProfileFactory(name="Bill to", phone="111"),
        shipping=customer_shipping,
    )
    invoice = InvoiceFactory(account=account, customer=customer, total_amount=Decimal("0.00"))
    InvoiceDocumentFactory(invoice=invoice, audience=[InvoiceDocumentAudience.CUSTOMER])
    shipping_rate = ShippingRateFactory(account=account, amount=Decimal("12.00"))
    tax_rate = TaxRateFactory(account=account, percentage=Decimal("10.00"))
    invoice.add_shipping(
        shipping_rate=shipping_rate,
        tax_rates=[tax_rate],
        shipping_profile=customer.default_shipping_profile,
    )
    invoice.recalculate()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{invoice.id}/finalize")

    assert response.status_code == 200
    assert response.data["shipping"]["profile"]["name"] == customer_shipping.name
    assert response.data["shipping"]["profile"]["phone"] == customer_shipping.phone
    assert response.data["shipping"]["profile"]["address"]["line1"] == shipping_address.line1
    assert response.data["shipping"]["profile"]["address"]["country"] == shipping_address.country


def test_finalize_invoice_with_shipping_uses_customer_fallback(api_client, user, account):
    customer = CustomerFactory(
        account=account,
        default_billing_profile=BillingProfileFactory(name="Bill to", phone="111"),
        shipping=None,
    )
    invoice = InvoiceFactory(account=account, customer=customer, total_amount=Decimal("0.00"))
    InvoiceDocumentFactory(invoice=invoice, audience=[InvoiceDocumentAudience.CUSTOMER])
    shipping_rate = ShippingRateFactory(account=account, amount=Decimal("8.00"))
    tax_rate = TaxRateFactory(account=account, percentage=Decimal("5.00"))
    invoice.add_shipping(shipping_rate=shipping_rate, tax_rates=[tax_rate])
    invoice.recalculate()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{invoice.id}/finalize")

    assert response.status_code == 200
    assert response.data["shipping"]["profile"] is None


def test_finalize_invoice_with_zero_outstanding_amount(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    document = InvoiceDocumentFactory(invoice=invoice, audience=[InvoiceDocumentAudience.CUSTOMER])

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{invoice.id}/finalize")

    assert response.status_code == 200
    invoice.refresh_from_db()
    document.refresh_from_db()
    assert response.data == {
        "id": str(invoice.id),
        "status": invoice.status,
        "number": invoice.effective_number,
        "numbering_system_id": None,
        "currency": invoice.currency,
        "tax_behavior": invoice.tax_behavior,
        "issue_date": invoice.issue_date.isoformat(),
        "due_date": invoice.due_date.isoformat(),
        "net_payment_term": invoice.net_payment_term,
        "delivery_method": invoice.delivery_method,
        "recipients": invoice.recipients,
        "billing_profile": {
            "id": str(invoice.billing_profile.id),
            "name": invoice.billing_profile.name,
            "legal_name": invoice.billing_profile.legal_name,
            "legal_number": invoice.billing_profile.legal_number,
            "email": invoice.billing_profile.email,
            "phone": invoice.billing_profile.phone,
            "address": {
                "line1": invoice.billing_profile.address.line1,
                "line2": invoice.billing_profile.address.line2,
                "locality": invoice.billing_profile.address.locality,
                "state": invoice.billing_profile.address.state,
                "postal_code": invoice.billing_profile.address.postal_code,
                "country": str(invoice.billing_profile.address.country),
            },
            "currency": invoice.billing_profile.currency,
            "language": invoice.billing_profile.language,
            "net_payment_term": invoice.billing_profile.net_payment_term,
            "invoice_numbering_system_id": invoice.billing_profile.invoice_numbering_system_id,
            "credit_note_numbering_system_id": invoice.billing_profile.credit_note_numbering_system_id,
            "tax_rates": [],
            "tax_ids": [],
            "created_at": ANY,
            "updated_at": ANY,
        },
        "business_profile": {
            "id": str(invoice.business_profile.id),
            "name": invoice.business_profile.name,
            "legal_name": invoice.business_profile.legal_name,
            "legal_number": invoice.business_profile.legal_number,
            "email": invoice.business_profile.email,
            "phone": invoice.business_profile.phone,
            "address": {
                "line1": invoice.business_profile.address.line1,
                "line2": invoice.business_profile.address.line2,
                "locality": invoice.business_profile.address.locality,
                "state": invoice.business_profile.address.state,
                "postal_code": invoice.business_profile.address.postal_code,
                "country": str(invoice.business_profile.address.country),
            },
            "tax_ids": [],
            "created_at": ANY,
            "updated_at": ANY,
        },
        "metadata": {},
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
        "previous_revision_id": None,
        "documents": [
            {
                "id": str(document.id),
                "audience": document.audience,
                "language": document.language,
                "footer": document.footer,
                "memo": document.memo,
                "custom_fields": document.custom_fields,
                "url": document.file.data.url,
                "created_at": ANY,
                "updated_at": ANY,
            }
        ],
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
    InvoiceDocumentFactory(invoice=invoice, audience=[InvoiceDocumentAudience.CUSTOMER])
    revision = InvoiceFactory(account=account, customer=invoice.customer, previous_revision=invoice, head=invoice.head)
    InvoiceDocumentFactory(invoice=revision, audience=[InvoiceDocumentAudience.CUSTOMER])
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
    InvoiceDocumentFactory(invoice=invoice, audience=[InvoiceDocumentAudience.CUSTOMER])
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
    InvoiceDocumentFactory(invoice=invoice, audience=[InvoiceDocumentAudience.CUSTOMER])
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
    InvoiceDocumentFactory(invoice=invoice, audience=[InvoiceDocumentAudience.CUSTOMER])
    InvoiceLineFactory(invoice=invoice, description="Test line", quantity=1, unit_amount=Decimal("10.00"))

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{invoice.id}/finalize")

    assert response.status_code == 200
    assert len(mailoutbox) == 1
    email = mailoutbox[0]
    assert email.subject == f"Invoice {invoice.effective_number} from {invoice.account.default_business_profile.name}"
    assert email.to == ["test@example.com"]


def test_finalize_invoice_with_automatic_delivery_method_no_recipients(api_client, user, account, mailoutbox):
    invoice = InvoiceFactory(
        account=account, delivery_method=InvoiceDeliveryMethod.AUTOMATIC, recipients=[], total_amount=Decimal("10.00")
    )
    InvoiceDocumentFactory(invoice=invoice, audience=[InvoiceDocumentAudience.CUSTOMER])
    InvoiceLineFactory(invoice=invoice, description="Test line", quantity=1, unit_amount=Decimal("10.00"))

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{invoice.id}/finalize")

    assert response.status_code == 200
    assert len(mailoutbox) == 0


@pytest.mark.parametrize("status", [InvoiceStatus.PAID, InvoiceStatus.VOIDED, InvoiceStatus.OPEN])
def test_finalize_invoice_non_draft(api_client, user, account, status):
    invoice = InvoiceFactory(account=account, status=status)
    InvoiceDocumentFactory(invoice=invoice, audience=[InvoiceDocumentAudience.CUSTOMER])

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/invoices/{invoice.id}/finalize")

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
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
        "type": "validation_error",
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
        "type": "client_error",
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
        "type": "client_error",
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
        "type": "client_error",
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
        "type": "client_error",
        "errors": [
            {
                "attr": None,
                "code": "not_authenticated",
                "detail": "Authentication credentials were not provided.",
            }
        ],
    }
