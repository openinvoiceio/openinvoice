import uuid
from decimal import Decimal

import pytest
from drf_standardized_errors.types import ErrorType

from apps.invoices.enums import InvoiceStatus
from apps.invoices.models import InvoiceTax
from tests.factories import InvoiceFactory, InvoiceLineFactory, InvoiceTaxFactory

pytestmark = pytest.mark.django_db


def test_delete_invoice_line_tax(api_client, user, account):
    invoice = InvoiceFactory(
        account=account,
        subtotal_amount=Decimal("10"),
        total_tax_amount=Decimal("1"),
        total_amount=Decimal("11"),
    )
    line = InvoiceLineFactory(
        invoice=invoice,
        quantity=1,
        unit_amount=Decimal("10"),
        amount=Decimal("10"),
    )
    tax = InvoiceTaxFactory(invoice_line=line, amount=Decimal("1"))

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/invoice-lines/{line.id}/taxes/{tax.id}")

    assert response.status_code == 204
    assert not InvoiceTax.objects.filter(id=tax.id).exists()
    invoice.refresh_from_db()
    assert invoice.total_tax_amount.amount == Decimal("0.00")
    assert invoice.total_amount.amount == Decimal("10.00")


def test_delete_invoice_line_tax_with_remaining(api_client, user, account):
    invoice = InvoiceFactory(
        account=account,
        subtotal_amount=Decimal("10"),
        total_tax_amount=Decimal("2"),
        total_amount=Decimal("12"),
    )
    line = InvoiceLineFactory(
        invoice=invoice,
        quantity=1,
        unit_amount=Decimal("10"),
        amount=Decimal("10"),
    )
    tax1 = InvoiceTaxFactory(invoice_line=line, amount=Decimal("1"))
    tax2 = InvoiceTaxFactory(invoice_line=line, amount=Decimal("1"))

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/invoice-lines/{line.id}/taxes/{tax1.id}")

    assert response.status_code == 204
    invoice.refresh_from_db()
    assert invoice.total_tax_amount.amount == Decimal("1.00")
    assert invoice.total_amount.amount == Decimal("11.00")
    assert InvoiceTax.objects.filter(id=tax2.id).exists()


def test_delete_invoice_line_tax_not_found(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    line = InvoiceLineFactory(invoice=invoice)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/invoice-lines/{line.id}/taxes/{uuid.uuid4()}")

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


def test_delete_invoice_line_tax_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.delete(f"/api/v1/invoice-lines/{uuid.uuid4()}/taxes/{uuid.uuid4()}")

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


def test_delete_invoice_line_tax_rejects_foreign_account(api_client, user, account):
    other_invoice = InvoiceFactory()
    line = InvoiceLineFactory(invoice=other_invoice)
    tax = InvoiceTaxFactory(invoice_line=line)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/invoice-lines/{line.id}/taxes/{tax.id}")

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
def test_delete_invoice_line_tax_non_draft_invoice(api_client, user, account, status):
    invoice = InvoiceFactory(account=account, status=status)
    line = InvoiceLineFactory(invoice=invoice)
    tax = InvoiceTaxFactory(invoice_line=line)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/invoice-lines/{line.id}/taxes/{tax.id}")

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Only draft invoices can be modified",
            }
        ],
    }


def test_delete_invoice_line_tax_requires_authentication(api_client, account):
    invoice = InvoiceFactory(account=account)
    line = InvoiceLineFactory(invoice=invoice)
    tax = InvoiceTaxFactory(invoice_line=line)

    response = api_client.delete(f"/api/v1/invoice-lines/{line.id}/taxes/{tax.id}")

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
