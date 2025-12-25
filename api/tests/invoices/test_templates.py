from decimal import Decimal

import pytest
from django.template.loader import render_to_string

from tests.factories import (
    CouponFactory,
    InvoiceDiscountFactory,
    InvoiceFactory,
    InvoiceLineFactory,
    InvoiceTaxFactory,
    PaymentFactory,
    TaxRateFactory,
)

pytestmark = pytest.mark.django_db


def test_invoice_email_subject_template():
    invoice = InvoiceFactory()
    context = {"invoice": invoice}
    subject = render_to_string("invoices/email/invoice_email_subject.txt", context).strip()
    assert subject == f"Invoice {invoice.effective_number} from {invoice.account.name}"


def test_invoice_email_message_text_template():
    invoice = InvoiceFactory()
    context = {"invoice": invoice}
    body = render_to_string("invoices/email/invoice_email_message.txt", context).strip()
    assert body == ""


def test_invoice_email_message_html_template():
    invoice = InvoiceFactory()
    context = {"invoice": invoice}
    body = render_to_string("invoices/email/invoice_email_message.html", context)
    assert invoice.effective_number in body
    assert invoice.account.name in body
    assert invoice.customer.name in body


def test_invoice_email_message_text_template_with_payment_url():
    invoice = InvoiceFactory()
    payment = PaymentFactory(url="https://pay.example.com")
    invoice.payments.add(payment)
    body = render_to_string("invoices/email/invoice_email_message.txt", {"invoice": invoice}).strip()
    assert "https://pay.example.com" in body


def test_invoice_email_message_html_template_with_payment_url():
    invoice = InvoiceFactory()
    payment = PaymentFactory(url="https://pay.example.com")
    invoice.payments.add(payment)
    body = render_to_string("invoices/email/invoice_email_message.html", {"invoice": invoice})
    assert "https://pay.example.com" in body


def test_invoice_pdf_template():
    invoice = InvoiceFactory()
    line = InvoiceLineFactory(invoice=invoice, description="Line item")
    line.recalculate()
    body = render_to_string(
        "invoices/pdf/classic.html",
        {"invoice": invoice, "language": "en", "include_fonts": False},
    )
    assert invoice.effective_number in body
    assert "Line item" in body


def test_invoice_pdf_template_with_discounts_and_taxes():
    invoice = InvoiceFactory(
        subtotal_amount=Decimal("100"),
        total_discount_amount=Decimal("15"),
        total_amount_excluding_tax=Decimal("85"),
        total_tax_amount=Decimal("34"),
        total_amount=Decimal("119"),
    )
    line = InvoiceLineFactory(
        invoice=invoice,
        description="Line item",
        unit_amount=Decimal("100"),
        quantity=1,
        amount=Decimal("100"),
        total_discount_amount=Decimal("5"),
        total_amount_excluding_tax=Decimal("95"),
        total_tax_amount=Decimal("19"),
        total_tax_rate=Decimal("20"),
        total_amount=Decimal("114"),
    )
    coupon = CouponFactory(account=invoice.account, currency=invoice.currency)
    InvoiceDiscountFactory(invoice_line=line, coupon=coupon, amount=Decimal("5"))
    tax_rate = TaxRateFactory(account=invoice.account, percentage=Decimal("20"))
    InvoiceTaxFactory(invoice_line=line, tax_rate=tax_rate, rate=tax_rate.percentage, amount=Decimal("20"))
    InvoiceDiscountFactory(invoice=invoice, coupon=coupon, amount=Decimal("10"))
    InvoiceTaxFactory(invoice=invoice, tax_rate=tax_rate, rate=tax_rate.percentage, amount=Decimal("20"))
    line.recalculate()

    body = render_to_string(
        "invoices/pdf/classic.html",
        {
            "invoice": invoice,
            "include_fonts": False,
        },
    )

    assert "Tax" in body
    assert coupon.name in body
    assert f'style="padding-left:20px;">{coupon.name}</td>' in body
    assert tax_rate.name in body
    assert "20%" in body


def test_invoice_pdf_template_without_line_tax_column():
    invoice = InvoiceFactory()
    line = InvoiceLineFactory(invoice=invoice, description="Line item")
    line.recalculate()
    body = render_to_string(
        "invoices/pdf/classic.html",
        {"invoice": invoice, "language": "en", "include_fonts": False},
    )
    assert '<th style="width:15%; text-align: end">Tax</th>' not in body
