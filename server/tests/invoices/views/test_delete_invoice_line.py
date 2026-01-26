import uuid
from decimal import Decimal

import pytest

from openinvoice.invoices.choices import InvoiceStatus
from openinvoice.invoices.models import InvoiceLine
from tests.factories import InvoiceFactory, InvoiceLineFactory

pytestmark = pytest.mark.django_db


def test_delete_invoice_line(api_client, user, account):
    invoice = InvoiceFactory(
        account=account,
        subtotal_amount=Decimal("10"),
        total_tax_amount=Decimal("0"),
        total_amount=Decimal("10"),
    )
    line = InvoiceLineFactory(
        invoice=invoice,
        quantity=1,
        unit_amount=Decimal("10"),
        amount=Decimal("10"),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/invoice-lines/{line.id}")

    assert response.status_code == 204
    assert not InvoiceLine.objects.filter(id=line.id).exists()
    invoice.refresh_from_db()
    assert invoice.subtotal_amount.amount == Decimal("0.00")
    assert invoice.total_tax_amount.amount == Decimal("0.00")
    assert invoice.total_amount.amount == Decimal("0.00")


def test_delete_invoice_line_with_remaining_line(api_client, user, account):
    invoice = InvoiceFactory(
        account=account,
        subtotal_amount=Decimal("30"),
        total_excluding_tax_amount=Decimal("30"),
        total_tax_amount=Decimal("0"),
        total_amount=Decimal("30"),
    )
    line1 = InvoiceLineFactory(
        invoice=invoice,
        quantity=1,
        unit_amount=Decimal("10"),
        amount=Decimal("10"),
        total_excluding_tax_amount=Decimal("10"),
    )
    line2 = InvoiceLineFactory(
        invoice=invoice,
        quantity=2,
        unit_amount=Decimal("10"),
        amount=Decimal("20"),
        total_excluding_tax_amount=Decimal("20"),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/invoice-lines/{line1.id}")

    assert response.status_code == 204
    invoice.refresh_from_db()
    assert invoice.subtotal_amount.amount == Decimal("20.00")
    assert invoice.total_tax_amount.amount == Decimal("0.00")
    assert invoice.total_amount.amount == Decimal("20.00")
    assert not InvoiceLine.objects.filter(id=line1.id).exists()
    assert InvoiceLine.objects.filter(id=line2.id).exists()


def test_delete_invoice_line_overflow_returns_validation_error(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    huge_line = InvoiceLineFactory(
        invoice=invoice,
        quantity=2,
        unit_amount=Decimal("50000000000000000.00"),
    )
    small_line = InvoiceLineFactory(
        invoice=invoice,
        quantity=1,
        unit_amount=Decimal("10"),
        amount=Decimal("10"),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/invoice-lines/{small_line.id}")

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Amount exceeds the maximum allowed value",
            }
        ],
    }
    assert InvoiceLine.objects.filter(id=huge_line.id).exists()


def test_delete_invoice_line_not_found(api_client, user, account):
    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/invoice-lines/{uuid.uuid4()}")

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


def test_delete_invoice_line_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.delete(f"/api/v1/invoice-lines/{uuid.uuid4()}")

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


def test_delete_invoice_line_rejects_foreign_account(api_client, user, account):
    other_invoice = InvoiceFactory()
    line = InvoiceLineFactory(invoice=other_invoice)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/invoice-lines/{line.id}")

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


@pytest.mark.parametrize(
    "status",
    [
        InvoiceStatus.OPEN,
        InvoiceStatus.PAID,
        InvoiceStatus.VOIDED,
    ],
)
def test_delete_invoice_line_non_draft(api_client, user, account, status):
    invoice = InvoiceFactory(account=account, status=status)
    line = InvoiceLineFactory(invoice=invoice)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/invoice-lines/{line.id}")

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Only draft invoices can be modified",
            }
        ],
    }


def test_delete_invoice_line_requires_authentication(api_client, account):
    invoice = InvoiceFactory(account=account)
    line = InvoiceLineFactory(invoice=invoice)

    response = api_client.delete(f"/api/v1/invoice-lines/{line.id}")

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
