import uuid
from decimal import Decimal
from unittest.mock import ANY

import pytest
from drf_standardized_errors.types import ErrorType

from apps.invoices.enums import InvoiceStatus
from tests.factories import InvoiceFactory, InvoiceLineFactory, InvoiceTaxFactory, TaxRateFactory

pytestmark = pytest.mark.django_db


def test_apply_invoice_line_tax(api_client, user, account):
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
    tax_rate = TaxRateFactory(account=account, percentage=Decimal("10.00"))

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/invoice-lines/{line.id}/taxes",
        {"tax_rate_id": str(tax_rate.id)},
    )

    assert response.status_code == 200
    assert response.data == {
        "id": ANY,
        "tax_rate_id": str(tax_rate.id),
        "name": tax_rate.name,
        "description": tax_rate.description,
        "rate": "10.00",
        "amount": "1.00",
    }
    invoice.refresh_from_db()
    assert invoice.total_tax_amount.amount == Decimal("1.00")
    assert invoice.total_amount.amount == Decimal("11.00")


def test_apply_invoice_line_tax_invoice_line_not_found(api_client, user, account):
    tax_rate = TaxRateFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/invoice-lines/{uuid.uuid4()}/taxes",
        {"tax_rate_id": str(tax_rate.id)},
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


def test_apply_invoice_line_tax_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.post(
        f"/api/v1/invoice-lines/{uuid.uuid4()}/taxes",
        {"tax_rate_id": str(uuid.uuid4())},
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


@pytest.mark.parametrize(
    "status",
    [
        InvoiceStatus.OPEN,
        InvoiceStatus.PAID,
        InvoiceStatus.VOIDED,
    ],
)
def test_apply_invoice_line_tax_non_draft_invoice(api_client, user, account, status):
    invoice = InvoiceFactory(account=account, status=status)
    line = InvoiceLineFactory(invoice=invoice)
    tax_rate = TaxRateFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/invoice-lines/{line.id}/taxes",
        {"tax_rate_id": str(tax_rate.id)},
    )

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


def test_apply_invoice_line_tax_tax_rate_not_found(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    line = InvoiceLineFactory(invoice=invoice)
    tax_rate_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/invoice-lines/{line.id}/taxes",
        {"tax_rate_id": str(tax_rate_id)},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "tax_rate_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{tax_rate_id}" - object does not exist.',
            }
        ],
    }


def test_apply_invoice_line_tax_duplicate(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    line = InvoiceLineFactory(invoice=invoice)
    tax_rate = TaxRateFactory(account=account)

    InvoiceTaxFactory(invoice_line=line, tax_rate=tax_rate, rate=tax_rate.percentage, amount=Decimal("0"))

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/invoice-lines/{line.id}/taxes",
        {"tax_rate_id": str(tax_rate.id)},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "tax_rate_id",
                "code": "invalid",
                "detail": "Given tax rate is already applied to this invoice line",
            }
        ],
    }


def test_apply_invoice_line_tax_limit(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    line = InvoiceLineFactory(invoice=invoice)
    tax_rates = TaxRateFactory.create_batch(6, account=account)

    for tax_rate in tax_rates[:5]:
        InvoiceTaxFactory(invoice_line=line, tax_rate=tax_rate, rate=tax_rate.percentage, amount=Decimal("0"))

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        f"/api/v1/invoice-lines/{line.id}/taxes",
        {"tax_rate_id": str(tax_rates[5].id)},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Maximum number of invoice line taxes reached",
            }
        ],
    }


def test_apply_invoice_line_tax_requires_authentication(api_client, account):
    invoice = InvoiceFactory(account=account)
    line = InvoiceLineFactory(invoice=invoice)
    tax_rate = TaxRateFactory(account=account)

    response = api_client.post(
        f"/api/v1/invoice-lines/{line.id}/taxes",
        {"tax_rate_id": str(tax_rate.id)},
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
