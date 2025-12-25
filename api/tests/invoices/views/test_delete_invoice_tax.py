import uuid
from decimal import Decimal

import pytest
from drf_standardized_errors.types import ErrorType

from apps.invoices.enums import InvoiceStatus
from apps.invoices.models import InvoiceTax
from tests.factories import InvoiceFactory, InvoiceLineFactory, InvoiceTaxFactory

pytestmark = pytest.mark.django_db


def test_delete_invoice_tax(api_client, user, account):
    invoice = InvoiceFactory(
        account=account,
        subtotal_amount=Decimal("10"),
        total_tax_amount=Decimal("1"),
        total_amount=Decimal("11"),
    )
    InvoiceLineFactory(
        invoice=invoice,
        quantity=1,
        unit_amount=Decimal("10"),
        amount=Decimal("10"),
    )
    tax = InvoiceTaxFactory(invoice=invoice, amount=Decimal("1"))

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/invoices/{invoice.id}/taxes/{tax.id}")

    assert response.status_code == 204
    assert not InvoiceTax.objects.filter(id=tax.id).exists()
    # TODO: fix it
    # invoice.refresh_from_db()
    # assert invoice.total_tax_amount.amount == Decimal("0.00")
    # assert invoice.total_amount.amount == Decimal("10.00")


def test_delete_invoice_tax_with_remaining(api_client, user, account):
    invoice = InvoiceFactory(
        account=account,
        subtotal_amount=Decimal("10"),
        total_tax_amount=Decimal("2"),
        total_amount=Decimal("12"),
    )
    InvoiceLineFactory(
        invoice=invoice,
        quantity=1,
        unit_amount=Decimal("10"),
        amount=Decimal("10"),
    )
    tax1 = InvoiceTaxFactory(invoice=invoice, amount=Decimal("1"))
    tax2 = InvoiceTaxFactory(invoice=invoice, amount=Decimal("1"))

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/invoices/{invoice.id}/taxes/{tax1.id}")

    assert response.status_code == 204
    assert InvoiceTax.objects.filter(id=tax2.id).exists()
    # TODO: fix it
    # invoice.refresh_from_db()
    # assert invoice.total_tax_amount.amount == Decimal("1.00")
    # assert invoice.total_amount.amount == Decimal("11.00")


def test_delete_invoice_tax_not_found(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    tax_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/invoices/{invoice.id}/taxes/{tax_id}")

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


def test_delete_invoice_tax_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.delete(f"/api/v1/invoices/{uuid.uuid4()}/taxes/{uuid.uuid4()}")

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


def test_delete_invoice_tax_rejects_foreign_account(api_client, user, account):
    other_invoice = InvoiceFactory()
    tax = InvoiceTaxFactory(invoice=other_invoice)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/invoices/{other_invoice.id}/taxes/{tax.id}")

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
def test_delete_invoice_tax_non_draft_invoice(api_client, user, account, status):
    invoice = InvoiceFactory(account=account, status=status)
    tax = InvoiceTaxFactory(invoice=invoice)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/invoices/{invoice.id}/taxes/{tax.id}")

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


def test_delete_invoice_tax_requires_authentication(api_client, account):
    invoice = InvoiceFactory(account=account)
    tax = InvoiceTaxFactory(invoice=invoice)

    response = api_client.delete(f"/api/v1/invoices/{invoice.id}/taxes/{tax.id}")

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
