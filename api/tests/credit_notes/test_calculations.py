from decimal import Decimal

import pytest
from djmoney.money import Money

from apps.credit_notes.calculations import calculate_credit_note_line_amounts
from tests.factories import (
    CreditNoteFactory,
    CreditNoteLineFactory,
    InvoiceFactory,
    InvoiceLineFactory,
)

pytestmark = pytest.mark.django_db


def test_calculate_credit_note_line_amounts_from_amount():
    invoice_line = InvoiceLineFactory(
        invoice=InvoiceFactory(currency="USD"),
        quantity=4,
        unit_amount=Money("50.00", "USD"),
        amount=Money("200.00", "USD"),
        total_excluding_tax_amount=Money("200.00", "USD"),
        total_tax_amount=Money("40.00", "USD"),
        total_amount=Money("240.00", "USD"),
    )

    amount_value, total_excl_tax, total_tax, total_amount, ratio = calculate_credit_note_line_amounts(
        invoice_line,
        amount=Money("120.00", "USD"),
    )

    assert amount_value == Money("120.00", "USD")
    assert total_excl_tax == Money("120.00", "USD")
    assert total_tax == Money("24.00", "USD")
    assert total_amount == Money("144.00", "USD")
    assert ratio == Decimal("0.6")


def test_calculate_credit_note_line_amounts_invoice_line_amount_zero():
    invoice_line = InvoiceLineFactory(
        invoice=InvoiceFactory(currency="USD"),
        quantity=3,
        unit_amount=Money("0.00", "USD"),
        amount=Money("0.00", "USD"),
        total_excluding_tax_amount=Money("0.00", "USD"),
        total_tax_amount=Money("0.00", "USD"),
        total_amount=Money("0.00", "USD"),
    )

    amount_value, total_excl_tax, total_tax, total_amount, ratio = calculate_credit_note_line_amounts(
        invoice_line,
        amount=Money("10.00", "USD"),
    )

    assert ratio == Decimal("0")
    assert amount_value == Money("0.00", "USD")
    assert total_excl_tax == Money("0.00", "USD")
    assert total_tax == Money("0.00", "USD")
    assert total_amount == Money("0.00", "USD")


def test_calculate_credit_note_line_amounts_from_quantity():
    invoice_line = InvoiceLineFactory(
        invoice=InvoiceFactory(currency="USD"),
        quantity=4,
        unit_amount=Money("30.00", "USD"),
        amount=Money("120.00", "USD"),
        total_excluding_tax_amount=Money("120.00", "USD"),
        total_tax_amount=Money("24.00", "USD"),
        total_amount=Money("144.00", "USD"),
    )

    amount_value, total_excl_tax, total_tax, total_amount, ratio = calculate_credit_note_line_amounts(
        invoice_line,
        quantity=2,
    )

    assert ratio == Decimal("0.5")
    assert amount_value == Money("60.00", "USD")
    assert total_excl_tax == Money("60.00", "USD")
    assert total_tax == Money("12.00", "USD")
    assert total_amount == Money("72.00", "USD")


def test_calculate_credit_note_line_amounts_defaults_to_invoice_line_values():
    invoice_line = InvoiceLineFactory(
        invoice=InvoiceFactory(currency="USD"),
        quantity=2,
        unit_amount=Money("15.00", "USD"),
        amount=Money("30.00", "USD"),
        total_excluding_tax_amount=Money("30.00", "USD"),
        total_tax_amount=Money("6.00", "USD"),
        total_amount=Money("36.00", "USD"),
    )

    amount_value, total_excl_tax, total_tax, total_amount, ratio = calculate_credit_note_line_amounts(invoice_line)

    assert ratio == Decimal("1")
    assert amount_value == invoice_line.amount
    assert total_excl_tax == invoice_line.total_excluding_tax_amount
    assert total_tax == invoice_line.total_tax_amount
    assert total_amount == invoice_line.total_amount


def test_calculate_credit_note_line_amounts_clamps_ratio_to_one():
    invoice_line = InvoiceLineFactory(
        invoice=InvoiceFactory(currency="USD"),
        quantity=3,
        unit_amount=Money("20.00", "USD"),
        amount=Money("60.00", "USD"),
        total_excluding_tax_amount=Money("60.00", "USD"),
        total_tax_amount=Money("12.00", "USD"),
        total_amount=Money("72.00", "USD"),
    )

    amount_value, total_excl_tax, total_tax, total_amount, ratio = calculate_credit_note_line_amounts(
        invoice_line,
        quantity=10,
    )

    assert ratio == Decimal("1")
    assert amount_value == invoice_line.amount
    assert total_excl_tax == invoice_line.total_excluding_tax_amount
    assert total_tax == invoice_line.total_tax_amount
    assert total_amount == invoice_line.total_amount


def test_calculate_credit_note_line_amounts_clamps_ratio_to_zero():
    invoice_line = InvoiceLineFactory(
        invoice=InvoiceFactory(currency="USD"),
        quantity=3,
        unit_amount=Money("25.00", "USD"),
        amount=Money("75.00", "USD"),
        total_excluding_tax_amount=Money("75.00", "USD"),
        total_tax_amount=Money("15.00", "USD"),
        total_amount=Money("90.00", "USD"),
    )

    amount_value, total_excl_tax, total_tax, total_amount, ratio = calculate_credit_note_line_amounts(
        invoice_line,
        amount=Money("-10.00", "USD"),
    )

    assert ratio == Decimal("0")
    assert amount_value == Money("0.00", "USD")
    assert total_excl_tax == Money("0.00", "USD")
    assert total_tax == Money("0.00", "USD")
    assert total_amount == Money("0.00", "USD")


def test_calculate_credit_note_line_amounts_handles_zero_invoice_quantity():
    invoice_line = InvoiceLineFactory(
        invoice=InvoiceFactory(currency="USD"),
        quantity=0,
        unit_amount=Money("0.00", "USD"),
        amount=Money("0.00", "USD"),
        total_excluding_tax_amount=Money("0.00", "USD"),
        total_tax_amount=Money("0.00", "USD"),
        total_amount=Money("0.00", "USD"),
    )

    amount_value, total_excl_tax, total_tax, total_amount, ratio = calculate_credit_note_line_amounts(
        invoice_line,
        quantity=5,
    )

    assert ratio == Decimal("0")
    assert amount_value == Money("0.00", "USD")
    assert total_excl_tax == Money("0.00", "USD")
    assert total_tax == Money("0.00", "USD")
    assert total_amount == Money("0.00", "USD")


def test_recalculate_credit_note_updates_totals():
    invoice = InvoiceFactory(currency="USD")
    credit_note = CreditNoteFactory(
        invoice=invoice,
        subtotal_amount=Money("1.00", "USD"),
        total_amount_excluding_tax=Money("1.00", "USD"),
        total_tax_amount=Money("1.00", "USD"),
        total_amount=Money("2.00", "USD"),
    )

    CreditNoteLineFactory(
        credit_note=credit_note,
        invoice_line=InvoiceLineFactory(invoice=invoice),
        quantity=1,
        unit_amount=Money("30.00", "USD"),
        amount=Money("30.00", "USD"),
        total_amount_excluding_tax=Money("30.00", "USD"),
        total_tax_amount=Money("6.00", "USD"),
        total_amount=Money("36.00", "USD"),
    )
    CreditNoteLineFactory(
        credit_note=credit_note,
        invoice_line=InvoiceLineFactory(invoice=invoice),
        quantity=1,
        unit_amount=Money("40.00", "USD"),
        amount=Money("40.00", "USD"),
        total_amount_excluding_tax=Money("40.00", "USD"),
        total_tax_amount=Money("8.00", "USD"),
        total_amount=Money("48.00", "USD"),
    )

    credit_note.recalculate()
    credit_note.refresh_from_db()

    assert credit_note.subtotal_amount == Money("70.00", "USD")
    assert credit_note.total_amount_excluding_tax == Money("70.00", "USD")
    assert credit_note.total_tax_amount == Money("14.00", "USD")
    assert credit_note.total_amount == Money("84.00", "USD")


def test_recalculate_credit_note_without_lines_zeroes_totals():
    credit_note = CreditNoteFactory(
        invoice=InvoiceFactory(currency="USD"),
        subtotal_amount=Money("5.00", "USD"),
        total_amount_excluding_tax=Money("5.00", "USD"),
        total_tax_amount=Money("2.00", "USD"),
        total_amount=Money("7.00", "USD"),
    )

    credit_note.recalculate()
    credit_note.refresh_from_db()

    assert credit_note.subtotal_amount == Money("0.00", "USD")
    assert credit_note.total_amount_excluding_tax == Money("0.00", "USD")
    assert credit_note.total_tax_amount == Money("0.00", "USD")
    assert credit_note.total_amount == Money("0.00", "USD")
