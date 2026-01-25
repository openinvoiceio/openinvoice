from decimal import Decimal

import pytest
from djmoney.money import Money

from apps.invoices.choices import InvoiceStatus
from apps.prices.choices import PriceModel
from apps.prices.models import Price
from tests.factories import CreditNoteFactory, CreditNoteLineFactory, InvoiceFactory, InvoiceLineFactory, ProductFactory

pytestmark = pytest.mark.django_db


def test_issue_credit_note_updates_outstanding_balances():
    invoice = InvoiceFactory(
        status=InvoiceStatus.OPEN,
        subtotal_amount=Decimal("100.00"),
        total_excluding_tax_amount=Decimal("100.00"),
        total_tax_amount=Decimal("0.00"),
        total_amount=Decimal("100.00"),
        outstanding_amount=Decimal("100.00"),
    )
    invoice_line = InvoiceLineFactory(
        invoice=invoice,
        quantity=2,
        unit_amount=Decimal("50.00"),
        amount=Decimal("100.00"),
        total_excluding_tax_amount=Decimal("100.00"),
        total_tax_amount=Decimal("0.00"),
        total_amount=Decimal("100.00"),
        outstanding_amount=Decimal("100.00"),
        outstanding_quantity=2,
    )
    credit_note = CreditNoteFactory(invoice=invoice, number="CN-001")
    CreditNoteLineFactory(
        credit_note=credit_note,
        invoice_line=invoice_line,
        quantity=1,
        unit_amount=Decimal("50.00"),
        amount=Decimal("50.00"),
        total_amount_excluding_tax=Decimal("50.00"),
        total_tax_amount=Decimal("0.00"),
        total_amount=Decimal("50.00"),
    )

    credit_note.recalculate()
    credit_note.issue()

    invoice.refresh_from_db()
    invoice_line.refresh_from_db()

    assert invoice.total_credit_amount == Money("50.00", invoice.currency)
    assert invoice.outstanding_amount == Money("50.00", invoice.currency)
    assert invoice_line.total_credit_amount == Money("50.00", invoice_line.currency)
    assert invoice_line.credit_quantity == 1
    assert invoice_line.outstanding_amount == Money("50.00", invoice_line.currency)
    assert invoice_line.outstanding_quantity == 1


def test_void_credit_note_restores_outstanding_balances():
    invoice = InvoiceFactory(
        status=InvoiceStatus.OPEN,
        subtotal_amount=Decimal("60.00"),
        total_excluding_tax_amount=Decimal("60.00"),
        total_tax_amount=Decimal("0.00"),
        total_amount=Decimal("60.00"),
        outstanding_amount=Decimal("60.00"),
    )
    invoice_line = InvoiceLineFactory(
        invoice=invoice,
        quantity=3,
        unit_amount=Decimal("20.00"),
        amount=Decimal("60.00"),
        total_excluding_tax_amount=Decimal("60.00"),
        total_tax_amount=Decimal("0.00"),
        total_amount=Decimal("60.00"),
        outstanding_amount=Decimal("60.00"),
        outstanding_quantity=3,
    )
    credit_note = CreditNoteFactory(invoice=invoice, number="CN-002")
    CreditNoteLineFactory(
        credit_note=credit_note,
        invoice_line=invoice_line,
        quantity=2,
        unit_amount=Decimal("20.00"),
        amount=Decimal("40.00"),
        total_amount_excluding_tax=Decimal("40.00"),
        total_tax_amount=Decimal("0.00"),
        total_amount=Decimal("40.00"),
    )

    credit_note.recalculate()
    credit_note.issue()
    credit_note.void()

    invoice.refresh_from_db()
    invoice_line.refresh_from_db()

    assert invoice.total_credit_amount == Money("0.00", invoice.currency)
    assert invoice.outstanding_amount == Money("60.00", invoice.currency)
    assert invoice_line.total_credit_amount == Money("0.00", invoice_line.currency)
    assert invoice_line.credit_quantity == 0
    assert invoice_line.outstanding_amount == Money("60.00", invoice_line.currency)
    assert invoice_line.outstanding_quantity == 3


def test_credit_note_line_from_graduated_invoice_line():
    invoice = InvoiceFactory()
    product = ProductFactory(account=invoice.account)
    price = Price.objects.create_price(
        amount=None,
        product=product,
        currency=invoice.currency,
        model=PriceModel.GRADUATED,
    )
    price.add_tier(unit_amount=Money("10", invoice.currency), from_value=0, to_value=10)
    price.add_tier(unit_amount=Money("8", invoice.currency), from_value=11, to_value=None)

    invoice_line = invoice.lines.create_line(
        invoice,
        description="Item",
        quantity=15,
        price=price,
    )
    invoice_line.refresh_from_db()

    credit_note = CreditNoteFactory(invoice=invoice, account=invoice.account, customer=invoice.customer)
    credit_note_line = credit_note.lines.from_invoice_line(credit_note, invoice_line)
    credit_note_line.refresh_from_db()

    assert credit_note_line.unit_amount.amount == Decimal("9.47")
    assert credit_note_line.amount.amount == Decimal("142.00")
