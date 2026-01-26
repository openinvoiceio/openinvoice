from datetime import timedelta
from decimal import Decimal
from unittest.mock import ANY

import pytest
from django.utils import timezone

from apps.credit_notes.choices import CreditNoteStatus
from apps.credit_notes.models import CreditNote
from apps.invoices.models import InvoiceAccount, InvoiceCustomer
from apps.numbering_systems.choices import NumberingSystemAppliesTo
from tests.factories import (
    AddressFactory,
    CreditNoteFactory,
    CreditNoteLineFactory,
    CustomerFactory,
    InvoiceFactory,
    NumberingSystemFactory,
)

pytestmark = pytest.mark.django_db


def _assign_invoice_snapshots(invoice):
    invoice.customer_on_invoice = InvoiceCustomer.objects.create(
        name=invoice.customer.name,
        legal_name=invoice.customer.legal_name,
        legal_number=invoice.customer.legal_number,
        email=invoice.customer.email,
        phone=invoice.customer.phone,
        description=invoice.customer.description,
        address=AddressFactory(),
        logo=None,
    )
    invoice.account_on_invoice = InvoiceAccount.objects.create(
        name=invoice.account.name,
        legal_name=invoice.account.legal_name,
        legal_number=invoice.account.legal_number,
        email=invoice.account.email,
        phone=invoice.account.phone,
        address=AddressFactory(),
        logo=None,
    )
    invoice.save(update_fields=["customer_on_invoice", "account_on_invoice"])


def test_list_credit_notes(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    _assign_invoice_snapshots(invoice)
    credit_note = CreditNoteFactory(
        invoice=invoice,
        status=CreditNoteStatus.DRAFT,
        subtotal_amount=Decimal("15.00"),
        total_amount_excluding_tax=Decimal("15.00"),
        total_tax_amount=Decimal("0.00"),
        total_amount=Decimal("15.00"),
    )
    line = CreditNoteLineFactory(
        credit_note=credit_note,
        description="Refunded service",
        quantity=2,
        unit_amount=Decimal("7.50"),
        amount=Decimal("15.00"),
        total_amount_excluding_tax=Decimal("15.00"),
        total_tax_amount=Decimal("0.00"),
        total_amount=Decimal("15.00"),
    )
    CreditNoteFactory()  # other account

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/credit-notes")

    assert response.status_code == 200
    line.refresh_from_db()
    customer_snapshot = invoice.customer_on_invoice
    account_snapshot = invoice.account_on_invoice
    assert response.data == {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": str(credit_note.id),
                "invoice_id": str(invoice.id),
                "status": credit_note.status,
                "reason": credit_note.reason,
                "number": credit_note.effective_number,
                "numbering_system_id": None,
                "currency": credit_note.currency,
                "issue_date": None,
                "metadata": credit_note.metadata,
                "description": credit_note.description,
                "delivery_method": credit_note.delivery_method,
                "recipients": [],
                "subtotal_amount": f"{credit_note.subtotal_amount.amount:.2f}",
                "total_amount_excluding_tax": f"{credit_note.total_amount_excluding_tax.amount:.2f}",
                "total_tax_amount": f"{credit_note.total_tax_amount.amount:.2f}",
                "total_amount": f"{credit_note.total_amount.amount:.2f}",
                "payment_provider": None,
                "payment_connection_id": None,
                "created_at": ANY,
                "updated_at": ANY,
                "issued_at": None,
                "voided_at": None,
                "pdf_id": None,
                "customer": {
                    "id": str(customer_snapshot.id),
                    "name": customer_snapshot.name,
                    "legal_name": customer_snapshot.legal_name,
                    "legal_number": customer_snapshot.legal_number,
                    "email": customer_snapshot.email,
                    "phone": customer_snapshot.phone,
                    "description": customer_snapshot.description,
                    "address": {
                        "line1": customer_snapshot.address.line1,
                        "line2": customer_snapshot.address.line2,
                        "locality": customer_snapshot.address.locality,
                        "state": customer_snapshot.address.state,
                        "postal_code": customer_snapshot.address.postal_code,
                        "country": str(customer_snapshot.address.country),
                    },
                    "logo_id": None,
                    "tax_ids": [],
                },
                "account": {
                    "id": str(account_snapshot.id),
                    "name": account_snapshot.name,
                    "legal_name": account_snapshot.legal_name,
                    "legal_number": account_snapshot.legal_number,
                    "email": account_snapshot.email,
                    "phone": account_snapshot.phone,
                    "address": {
                        "line1": account_snapshot.address.line1,
                        "line2": account_snapshot.address.line2,
                        "locality": account_snapshot.address.locality,
                        "state": account_snapshot.address.state,
                        "postal_code": account_snapshot.address.postal_code,
                        "country": str(account_snapshot.address.country),
                    },
                    "logo_id": None,
                    "tax_ids": [],
                },
                "lines": [
                    {
                        "id": str(line.id),
                        "invoice_line_id": str(line.invoice_line_id),
                        "description": line.description,
                        "quantity": line.quantity,
                        "unit_amount": f"{line.unit_amount.amount:.2f}",
                        "amount": f"{line.amount.amount:.2f}",
                        "total_amount_excluding_tax": f"{line.total_amount_excluding_tax.amount:.2f}",
                        "total_tax_amount": f"{line.total_tax_amount.amount:.2f}",
                        "total_amount": f"{line.total_amount.amount:.2f}",
                        "taxes": [],
                    }
                ],
                "taxes": [],
                "tax_breakdown": [],
            }
        ],
    }


def test_list_credit_notes_requires_authentication(api_client):
    response = api_client.get("/api/v1/credit-notes")

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


def test_list_credit_notes_requires_account(api_client, user):
    api_client.force_login(user)

    response = api_client.get("/api/v1/credit-notes")

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


def test_list_credit_notes_filter_by_status(api_client, user, account):
    CreditNoteFactory(invoice=InvoiceFactory(account=account))
    issued = CreditNoteFactory(
        invoice=InvoiceFactory(account=account),
        status=CreditNoteStatus.ISSUED,
        number="CN-100",
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/credit-notes", {"status": CreditNoteStatus.ISSUED})

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert [result["id"] for result in response.data["results"]] == [str(issued.id)]


def test_list_credit_notes_filter_by_invoice_id(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    matching = CreditNoteFactory(invoice=invoice)
    CreditNoteFactory(invoice=InvoiceFactory(account=account))

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/credit-notes", {"invoice_id": str(invoice.id)})

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert [result["id"] for result in response.data["results"]] == [str(matching.id)]


def test_list_credit_notes_filter_by_customer_id(api_client, user, account):
    customer = CustomerFactory(account=account)
    matching = CreditNoteFactory(invoice=InvoiceFactory(account=account, customer=customer))
    CreditNoteFactory(invoice=InvoiceFactory(account=account))

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/credit-notes", {"customer_id": str(customer.id)})

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert [result["id"] for result in response.data["results"]] == [str(matching.id)]


def test_list_credit_notes_filter_by_created_at_after(api_client, user, account):
    base = timezone.now()
    older = CreditNoteFactory(invoice=InvoiceFactory(account=account))
    CreditNote.objects.filter(id=older.id).update(created_at=base - timedelta(days=2))
    newer = CreditNoteFactory(invoice=InvoiceFactory(account=account))

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(
        "/api/v1/credit-notes",
        {"created_at_after": (base - timedelta(days=1)).isoformat()},
    )

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert [result["id"] for result in response.data["results"]] == [str(newer.id)]


def test_list_credit_notes_filter_by_created_at_before(api_client, user, account):
    base = timezone.now()
    older = CreditNoteFactory(invoice=InvoiceFactory(account=account))
    CreditNote.objects.filter(id=older.id).update(created_at=base - timedelta(days=2))
    CreditNoteFactory(invoice=InvoiceFactory(account=account))

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(
        "/api/v1/credit-notes",
        {"created_at_before": (base - timedelta(days=1)).isoformat()},
    )

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert [result["id"] for result in response.data["results"]] == [str(older.id)]


def test_list_credit_notes_filter_by_issue_date_range(api_client, user, account):
    CreditNoteFactory(
        invoice=InvoiceFactory(account=account),
        status=CreditNoteStatus.ISSUED,
        number="CN-101",
        issue_date=timezone.now().date() - timedelta(days=5),
    )
    newer = CreditNoteFactory(
        invoice=InvoiceFactory(account=account),
        status=CreditNoteStatus.ISSUED,
        number="CN-102",
        issue_date=timezone.now().date(),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(
        "/api/v1/credit-notes",
        {
            "issue_date_after": (timezone.now().date() - timedelta(days=1)).isoformat(),
            "issue_date_before": timezone.now().date().isoformat(),
        },
    )

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert [result["id"] for result in response.data["results"]] == [str(newer.id)]


def test_list_credit_notes_filter_by_total_amount_min(api_client, user, account):
    CreditNoteFactory(invoice=InvoiceFactory(account=account), total_amount=Decimal("20.00"))
    matching = CreditNoteFactory(
        invoice=InvoiceFactory(account=account),
        total_amount=Decimal("50.00"),
        subtotal_amount=Decimal("50.00"),
        total_amount_excluding_tax=Decimal("50.00"),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/credit-notes", {"total_amount_min": "40"})

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert [result["id"] for result in response.data["results"]] == [str(matching.id)]


def test_list_credit_notes_filter_by_total_amount_max(api_client, user, account):
    matching = CreditNoteFactory(
        invoice=InvoiceFactory(account=account),
        total_amount=Decimal("30.00"),
        subtotal_amount=Decimal("30.00"),
        total_amount_excluding_tax=Decimal("30.00"),
    )
    CreditNoteFactory(
        invoice=InvoiceFactory(account=account),
        total_amount=Decimal("70.00"),
        subtotal_amount=Decimal("70.00"),
        total_amount_excluding_tax=Decimal("70.00"),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/credit-notes", {"total_amount_max": "40"})

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert [result["id"] for result in response.data["results"]] == [str(matching.id)]


def test_list_credit_notes_filter_by_numbering_system(api_client, user, account):
    numbering_system = NumberingSystemFactory(
        account=account,
        applies_to=NumberingSystemAppliesTo.CREDIT_NOTE,
        template="CN-{n}",
    )
    matching = CreditNoteFactory(
        invoice=InvoiceFactory(account=account),
        number="CN-50",
        numbering_system=numbering_system,
    )
    CreditNoteFactory(invoice=InvoiceFactory(account=account))

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(
        "/api/v1/credit-notes",
        {"numbering_system_id": str(numbering_system.id)},
    )

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert [result["id"] for result in response.data["results"]] == [str(matching.id)]
