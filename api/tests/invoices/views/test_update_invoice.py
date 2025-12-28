import uuid
from unittest.mock import ANY

import pytest
from django.utils import timezone
from drf_standardized_errors.types import ErrorType

from apps.integrations.enums import PaymentProvider
from apps.invoices.enums import InvoiceDeliveryMethod, InvoiceStatus
from common.enums import FeatureCode
from tests.factories import (
    CustomerFactory,
    InvoiceFactory,
    NumberingSystemFactory,
    StripeConnectionFactory,
)

pytestmark = pytest.mark.django_db


def test_update_invoice(api_client, user, account):
    invoice = InvoiceFactory(account=account, currency="PLN")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {
            "customer_id": str(invoice.customer.id),
            "number": "INV-10",
            "numbering_system_id": None,
            "currency": "USD",
            "issue_date": None,
            "sell_date": None,
            "due_date": invoice.due_date.isoformat(),
            "metadata": {},
            "custom_fields": {},
            "footer": None,
            "description": None,
        },
    )

    assert response.status_code == 200
    invoice.refresh_from_db()
    assert response.data == {
        "id": str(invoice.id),
        "status": invoice.status,
        "number": invoice.effective_number,
        "numbering_system_id": None,
        "previous_revision_id": None,
        "latest_revision_id": invoice.latest_revision_id,
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
        "subtotal_amount": f"{invoice.subtotal_amount.amount:.2f}",
        "total_discount_amount": f"{invoice.total_discount_amount.amount:.2f}",
        "total_amount_excluding_tax": f"{invoice.total_amount_excluding_tax.amount:.2f}",
        "total_tax_amount": f"{invoice.total_tax_amount.amount:.2f}",
        "total_amount": f"{invoice.total_amount.amount:.2f}",
        "total_credit_amount": f"{invoice.total_credit_amount.amount:.2f}",
        "total_paid_amount": f"{invoice.total_paid_amount.amount:.2f}",
        "outstanding_amount": f"{invoice.outstanding_amount.amount:.2f}",
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


def test_update_invoice_change_customer(api_client, user, account):
    customer1 = CustomerFactory(account=account)
    invoice = InvoiceFactory(account=account, customer=customer1)
    customer2 = CustomerFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {
            "customer_id": str(customer2.id),
            "number": invoice.effective_number,
            "numbering_system_id": None,
            "currency": invoice.currency,
            "issue_date": None,
            "sell_date": None,
            "due_date": invoice.due_date.isoformat(),
            "metadata": {},
            "custom_fields": {},
            "footer": None,
            "description": None,
        },
    )

    assert response.status_code == 200
    invoice.refresh_from_db()
    assert invoice.customer_id == customer2.id
    assert response.data["customer"]["id"] == str(customer2.id)


def test_update_invoice_payment_provider(api_client, user, account):
    invoice = InvoiceFactory(account=account, currency="PLN")
    StripeConnectionFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {"payment_provider": PaymentProvider.STRIPE},
    )

    assert response.status_code == 200
    assert response.data["payment_provider"] == PaymentProvider.STRIPE


def test_update_invoice_without_connected_payment_provider(api_client, user, account):
    invoice = InvoiceFactory(account=account, currency="PLN")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {"payment_provider": PaymentProvider.STRIPE},
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


def test_update_revision_requires_same_customer(api_client, user, account):
    original = InvoiceFactory(account=account, status=InvoiceStatus.OPEN)
    revision = InvoiceFactory(account=account, customer=original.customer, previous_revision=original)
    other_customer = CustomerFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{revision.id}",
        {
            "customer_id": str(other_customer.id),
            "number": revision.number,
            "numbering_system_id": None,
            "currency": revision.currency,
            "issue_date": None,
            "sell_date": None,
            "due_date": revision.due_date.isoformat(),
            "metadata": {},
            "custom_fields": {},
            "footer": revision.footer,
            "description": revision.description,
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "customer_id",
                "code": "invalid",
                "detail": "Revision must use the same customer",
            }
        ],
    }


def test_update_invoice_customer_not_found(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    customer_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {
            "customer_id": str(customer_id),
            "number": invoice.effective_number,
            "numbering_system_id": None,
            "currency": invoice.currency,
            "issue_date": None,
            "sell_date": None,
            "due_date": invoice.due_date.isoformat(),
            "metadata": {},
            "custom_fields": {},
            "footer": None,
            "description": None,
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "customer_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{customer_id}" - object does not exist.',
            }
        ],
    }


def test_update_invoice_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.put(
        f"/api/v1/invoices/{uuid.uuid4()}",
        {
            "customer_id": str(uuid.uuid4()),
            "number": "INV-1",
            "numbering_system_id": None,
            "currency": "PLN",
            "issue_date": None,
            "sell_date": None,
            "due_date": None,
            "metadata": {},
            "custom_fields": {},
            "footer": None,
            "description": None,
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


def test_update_invoice_rejects_foreign_account(api_client, user, account):
    other_invoice = InvoiceFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{other_invoice.id}",
        {
            "customer_id": str(other_invoice.customer.id),
            "number": other_invoice.number,
            "numbering_system_id": None,
            "currency": other_invoice.currency,
            "issue_date": None,
            "sell_date": None,
            "due_date": other_invoice.due_date.isoformat(),
            "metadata": {},
            "custom_fields": {},
            "footer": None,
            "description": None,
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
def test_update_invoice_non_draft(api_client, user, account, status):
    invoice = InvoiceFactory(account=account, status=status)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {
            "customer_id": str(invoice.customer.id),
            "number": invoice.effective_number,
            "numbering_system_id": None,
            "currency": invoice.currency,
            "issue_date": None,
            "sell_date": None,
            "due_date": invoice.due_date.isoformat(),
            "metadata": {},
            "custom_fields": {},
            "footer": None,
            "description": None,
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Only draft invoices can be updated",
            }
        ],
    }


def test_update_invoice_numbering_system_not_found(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    numbering_system_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {
            "customer_id": str(invoice.customer.id),
            "number": None,
            "numbering_system_id": str(numbering_system_id),
            "currency": invoice.currency,
            "issue_date": None,
            "sell_date": None,
            "due_date": invoice.due_date.isoformat(),
            "metadata": {},
            "custom_fields": {},
            "footer": None,
            "description": None,
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


def test_update_invoice_assign_numbering_system(api_client, user, account):
    numbering_system = NumberingSystemFactory(account=account)
    invoice = InvoiceFactory(account=account, number="MANUAL", numbering_system=None)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {
            "customer_id": str(invoice.customer_id),
            "number": None,
            "numbering_system_id": str(numbering_system.id),
            "currency": invoice.currency,
            "issue_date": None,
            "sell_date": None,
            "due_date": invoice.due_date.isoformat(),
            "metadata": {},
            "custom_fields": {},
            "footer": None,
            "description": None,
        },
    )

    assert response.status_code == 200
    invoice.refresh_from_db()
    assert invoice.number is None
    assert invoice.effective_number == "INV-1"
    assert invoice.numbering_system_id == numbering_system.id
    assert response.data["number"] == "INV-1"
    assert response.data["numbering_system_id"] == str(numbering_system.id)


def test_update_invoice_assign_numbering_system_existing_invoices(api_client, user, account):
    numbering_system = NumberingSystemFactory(account=account)
    InvoiceFactory(
        account=account,
        numbering_system=numbering_system,
        number="INV-1",
        status=InvoiceStatus.OPEN,
        opened_at=timezone.now(),
    )
    invoice = InvoiceFactory(account=account, number="MANUAL", numbering_system=None)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {
            "customer_id": str(invoice.customer_id),
            "number": None,
            "numbering_system_id": str(numbering_system.id),
            "currency": invoice.currency,
            "issue_date": None,
            "sell_date": None,
            "due_date": invoice.due_date.isoformat(),
            "metadata": {},
            "custom_fields": {},
            "footer": None,
            "description": None,
        },
    )

    assert response.status_code == 200
    invoice.refresh_from_db()
    assert invoice.number is None
    assert invoice.effective_number == "INV-2"
    assert invoice.numbering_system_id == numbering_system.id
    assert response.data["number"] == "INV-2"
    assert response.data["numbering_system_id"] == str(numbering_system.id)


def test_update_invoice_switch_to_manual_number(api_client, user, account):
    numbering_system = NumberingSystemFactory(account=account)
    invoice = InvoiceFactory(account=account, numbering_system=numbering_system, number="INV-1")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {
            "customer_id": str(invoice.customer_id),
            "number": "MAN-1",
            "numbering_system_id": None,
            "currency": invoice.currency,
            "issue_date": None,
            "sell_date": None,
            "due_date": invoice.due_date.isoformat(),
            "metadata": {},
            "custom_fields": {},
            "footer": None,
            "description": None,
        },
    )

    assert response.status_code == 200
    invoice.refresh_from_db()
    assert invoice.number == "MAN-1"
    assert invoice.numbering_system_id is None
    assert response.data["number"] == "MAN-1"
    assert response.data["numbering_system_id"] is None


def test_update_invoice_with_automatic_delivery_and_without_entitlement(api_client, user, account, settings):
    settings.DEFAULT_PLAN = "test"
    settings.PLANS = {"test": {"features": {FeatureCode.AUTOMATIC_INVOICE_DELIVERY: False}}}
    invoice = InvoiceFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {"delivery_method": InvoiceDeliveryMethod.AUTOMATIC},
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


def test_update_invoice_requires_authentication(api_client, account):
    invoice = InvoiceFactory(account=account)

    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {
            "customer_id": str(invoice.customer_id),
            "number": invoice.effective_number,
            "numbering_system_id": None,
            "currency": invoice.currency,
            "issue_date": None,
            "sell_date": None,
            "due_date": invoice.due_date.isoformat(),
            "metadata": {},
            "custom_fields": {},
            "footer": None,
            "description": None,
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
