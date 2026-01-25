import uuid
from decimal import Decimal
from unittest.mock import ANY

import pytest

from apps.invoices.choices import InvoiceStatus
from apps.numbering_systems.choices import NumberingSystemAppliesTo
from common.choices import FeatureCode, LimitCode
from tests.factories import (
    AccountFactory,
    CreditNoteFactory,
    CustomerFactory,
    InvoiceFactory,
    InvoiceLineFactory,
    NumberingSystemFactory,
)

pytestmark = pytest.mark.django_db


def test_create_credit_note(api_client, user, account):
    customer = CustomerFactory(account=account)
    invoice = InvoiceFactory(
        account=account,
        customer=customer,
        status=InvoiceStatus.OPEN,
        subtotal_amount=Decimal("30.00"),
        total_excluding_tax_amount=Decimal("30.00"),
        total_tax_amount=Decimal("0.00"),
        total_amount=Decimal("30.00"),
    )

    line_one = InvoiceLineFactory(
        invoice=invoice,
        description="Service A",
        quantity=1,
        unit_amount=Decimal("10.00"),
        amount=Decimal("10.00"),
        total_excluding_tax_amount=Decimal("10.00"),
        total_tax_amount=Decimal("0.00"),
        total_amount=Decimal("10.00"),
    )
    line_two = InvoiceLineFactory(
        invoice=invoice,
        description="Service B",
        quantity=2,
        unit_amount=Decimal("10.00"),
        amount=Decimal("20.00"),
        total_excluding_tax_amount=Decimal("20.00"),
        total_tax_amount=Decimal("0.00"),
        total_amount=Decimal("20.00"),
    )

    api_client.force_login(user)
    api_client.force_account(account)

    response = api_client.post(
        "/api/v1/credit-notes",
        {"invoice_id": str(invoice.id)},
    )

    assert response.status_code == 201
    assert response.data["subtotal_amount"] == "30.00"
    assert response.data["total_amount_excluding_tax"] == "30.00"
    assert response.data["total_amount"] == "30.00"

    assert response.data["lines"] == [
        {
            "id": ANY,
            "invoice_line_id": str(line_one.id),
            "description": "Service A",
            "quantity": 1,
            "unit_amount": "10.00",
            "amount": "10.00",
            "total_amount_excluding_tax": "10.00",
            "total_tax_amount": "0.00",
            "total_amount": "10.00",
            "taxes": [],
        },
        {
            "id": ANY,
            "invoice_line_id": str(line_two.id),
            "description": "Service B",
            "quantity": 2,
            "unit_amount": "10.00",
            "amount": "20.00",
            "total_amount_excluding_tax": "20.00",
            "total_tax_amount": "0.00",
            "total_amount": "20.00",
            "taxes": [],
        },
    ]


def test_create_credit_note_with_automatic_delivery_and_without_entitlement(api_client, user, account, settings):
    settings.DEFAULT_PLAN = "test"
    settings.PLANS = {"test": {"features": {FeatureCode.AUTOMATIC_CREDIT_NOTE_DELIVERY: False}}}
    invoice = InvoiceFactory(account=account, status=InvoiceStatus.OPEN, outstanding_amount=10)

    api_client.force_login(user)
    api_client.force_account(account)

    response = api_client.post(
        "/api/v1/credit-notes",
        {
            "invoice_id": str(invoice.id),
            "delivery_method": "automatic",
            "recipients": ["test@example.com"],
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "delivery_method",
                "code": "invalid",
                "detail": "Automatic delivery is forbidden for your account.",
            }
        ],
    }


def test_create_credit_note_requires_authentication(api_client):
    response = api_client.post(
        "/api/v1/credit-notes",
        {"invoice_id": str(uuid.uuid4())},
    )

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


def test_create_credit_note_requires_account(api_client, user):
    api_client.force_login(user)

    response = api_client.post(
        "/api/v1/credit-notes",
        {"invoice_id": str(uuid.uuid4())},
    )

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


def test_create_credit_note_requires_finalized_invoice(api_client, user, account):
    invoice = InvoiceFactory(account=account, status=InvoiceStatus.DRAFT)

    api_client.force_login(user)
    api_client.force_account(account)

    response = api_client.post(
        "/api/v1/credit-notes",
        {"invoice_id": str(invoice.id)},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "invoice_id",
                "code": "invalid",
                "detail": "Invoice must be finalized before creating credit notes",
            }
        ],
    }


def test_create_credit_note_invoice_not_found(api_client, user, account):
    invoice_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/credit-notes",
        {"invoice_id": str(invoice_id)},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "invoice_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{invoice_id}" - object does not exist.',
            }
        ],
    }


def test_create_credit_note_rejects_foreign_account(api_client, user, account):
    invoice = InvoiceFactory()

    api_client.force_login(user)
    api_client.force_account(account)

    response = api_client.post(
        "/api/v1/credit-notes",
        {"invoice_id": str(invoice.id)},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "invoice_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{invoice.id}" - object does not exist.',
            }
        ],
    }


def test_create_credit_note_requires_outstanding_balance(api_client, user, account):
    invoice = InvoiceFactory(
        account=account,
        status=InvoiceStatus.OPEN,
        total_amount=Decimal("25.00"),
        total_excluding_tax_amount=Decimal("25.00"),
        subtotal_amount=Decimal("25.00"),
        total_credit_amount=Decimal("25.00"),
        outstanding_amount=Decimal("0.00"),
    )

    api_client.force_login(user)
    api_client.force_account(account)

    response = api_client.post(
        "/api/v1/credit-notes",
        {"invoice_id": str(invoice.id)},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "invoice_id",
                "code": "invalid",
                "detail": "Invoice has no outstanding balance to credit",
            }
        ],
    }


def test_create_credit_note_only_one_draft_allowed(api_client, user, account):
    invoice = InvoiceFactory(
        account=account,
        status=InvoiceStatus.OPEN,
        subtotal_amount=Decimal("10.00"),
        total_excluding_tax_amount=Decimal("10.00"),
        total_tax_amount=Decimal("0.00"),
        total_amount=Decimal("10.00"),
    )
    CreditNoteFactory(invoice=invoice)

    api_client.force_login(user)
    api_client.force_account(account)

    response = api_client.post(
        "/api/v1/credit-notes",
        {"invoice_id": str(invoice.id)},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "invoice_id",
                "code": "invalid",
                "detail": "Only one draft credit note is allowed per invoice",
            }
        ],
    }


def test_create_credit_note_numbering_system_not_found(api_client, user, account):
    invoice = InvoiceFactory(account=account, status=InvoiceStatus.OPEN, outstanding_amount=10)
    numbering_system_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/credit-notes",
        {
            "invoice_id": str(invoice.id),
            "numbering_system_id": str(numbering_system_id),
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "numbering_system_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{numbering_system_id}" - object does not exist.',
            }
        ],
    }


def test_create_credit_note_rejects_foreign_numbering_system(api_client, user, account):
    invoice = InvoiceFactory(account=account, status=InvoiceStatus.OPEN, outstanding_amount=10)
    numbering_system = NumberingSystemFactory(account=AccountFactory())

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/credit-notes",
        {
            "invoice_id": str(invoice.id),
            "numbering_system_id": str(numbering_system.id),
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "numbering_system_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{numbering_system.id}" - object does not exist.',
            }
        ],
    }


def test_create_credit_note_numbering_system_mismatch(api_client, user, account):
    invoice = InvoiceFactory(account=account, status=InvoiceStatus.OPEN, outstanding_amount=10)
    numbering_system = NumberingSystemFactory(account=account, applies_to=NumberingSystemAppliesTo.INVOICE)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/credit-notes",
        {
            "invoice_id": str(invoice.id),
            "numbering_system_id": str(numbering_system.id),
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "numbering_system_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{numbering_system.id}" - object does not exist.',
            }
        ],
    }


def test_create_credit_note_with_numbering_system(api_client, user, account):
    invoice = InvoiceFactory(account=account, status=InvoiceStatus.OPEN, outstanding_amount=10)

    numbering_system = NumberingSystemFactory(
        account=account,
        applies_to=NumberingSystemAppliesTo.CREDIT_NOTE,
        template="CN-{n}",
    )

    api_client.force_login(user)
    api_client.force_account(account)

    response = api_client.post(
        "/api/v1/credit-notes",
        {
            "invoice_id": str(invoice.id),
            "numbering_system_id": str(numbering_system.id),
        },
    )

    assert response.status_code == 201
    assert response.data["number"].startswith("CN-")


def test_create_credit_note_limit_exceeded(api_client, user, account, settings):
    settings.DEFAULT_PLAN = "test"
    settings.PLANS = {"test": {"limits": {LimitCode.MAX_CREDIT_NOTES_PER_MONTH: 0}}}
    invoice = InvoiceFactory(account=account, status=InvoiceStatus.OPEN, outstanding_amount=10)

    api_client.force_login(user)
    api_client.force_account(account)

    response = api_client.post(
        "/api/v1/credit-notes",
        {"invoice_id": str(invoice.id)},
    )

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
