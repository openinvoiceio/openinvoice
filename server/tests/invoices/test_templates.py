from decimal import Decimal

import pytest
from django.template.loader import render_to_string

from tests.factories import (
    AccountFactory,
    BillingProfileFactory,
    CouponFactory,
    CustomerFactory,
    CustomerShippingFactory,
    InvoiceDocumentFactory,
    InvoiceFactory,
    InvoiceLineFactory,
    PaymentFactory,
    ShippingRateFactory,
    TaxRateFactory,
)

pytestmark = pytest.mark.django_db


def test_invoice_email_subject_template():
    invoice = InvoiceFactory()
    context = {"invoice": invoice}
    subject = render_to_string("invoices/email/invoice_email_subject.txt", context).strip()
    assert subject == f"Invoice {invoice.effective_number} from {invoice.account.default_business_profile.name}"


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
    assert invoice.account.default_business_profile.name in body
    assert invoice.billing_profile.name in body


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
    InvoiceLineFactory(invoice=invoice, description="Line item")
    document = InvoiceDocumentFactory(invoice=invoice)

    invoice.recalculate()

    body = render_to_string(
        "invoices/pdf/classic.html",
        {"invoice": invoice, "document": document},
    )
    assert invoice.effective_number in body
    assert "Line item" in body


def test_invoice_pdf_template_with_discounts_and_taxes():
    invoice = InvoiceFactory(
        subtotal_amount=Decimal("100"),
        total_discount_amount=Decimal("15"),
        total_excluding_tax_amount=Decimal("85"),
        total_tax_amount=Decimal("34"),
        total_amount=Decimal("119"),
    )
    document = InvoiceDocumentFactory(invoice=invoice)
    line = InvoiceLineFactory(
        invoice=invoice,
        description="Line item",
        unit_amount=Decimal("100"),
        quantity=1,
        amount=Decimal("100"),
        total_discount_amount=Decimal("5"),
        total_excluding_tax_amount=Decimal("95"),
        total_tax_amount=Decimal("19"),
        total_tax_rate=Decimal("20"),
        total_amount=Decimal("114"),
    )
    coupon = CouponFactory(account=invoice.account, currency=invoice.currency)
    tax_rate = TaxRateFactory(account=invoice.account, percentage=Decimal("20"))

    line.set_coupons([coupon])
    line.set_tax_rates([tax_rate])
    invoice.set_coupons([coupon])
    invoice.set_tax_rates([tax_rate])
    invoice.recalculate()

    body = render_to_string("invoices/pdf/classic.html", {"invoice": invoice, "document": document})

    assert "Tax" in body
    assert coupon.name in body
    assert f'style="padding-left:20px;">{coupon.name}</td>' in body
    assert tax_rate.name in body
    assert "20%" in body


def test_invoice_pdf_template_with_shipping_and_discount_summary():
    account = AccountFactory()
    customer_shipping = CustomerShippingFactory()
    customer = CustomerFactory(
        account=account,
        default_billing_profile=BillingProfileFactory(currency=account.default_currency),
        shipping=customer_shipping,
    )
    invoice = InvoiceFactory(account=account, customer=customer)
    document = InvoiceDocumentFactory(invoice=invoice)
    InvoiceLineFactory(
        invoice=invoice,
        description="Line item",
        unit_amount=Decimal("100"),
        quantity=1,
        amount=Decimal("100"),
    )
    shipping_rate = ShippingRateFactory(account=invoice.account, currency=invoice.currency)
    coupon = CouponFactory(account=invoice.account, currency=invoice.currency)

    invoice.add_shipping(
        shipping_rate=shipping_rate,
        tax_rates=[],
        shipping_profile=customer.default_shipping_profile,
    )
    invoice.set_coupons([coupon])
    invoice.recalculate()

    body = render_to_string("invoices/pdf/classic.html", {"invoice": invoice, "document": document})

    assert "Ship to" in body
    assert customer_shipping.name in body
    assert customer_shipping.phone in body
    assert "Shipping fee" in body
    assert body.index(coupon.name) < body.index("Shipping fee")


def test_invoice_pdf_template_without_line_tax_column():
    invoice = InvoiceFactory()
    InvoiceLineFactory(invoice=invoice, description="Line item")
    document = InvoiceDocumentFactory(invoice=invoice)

    invoice.recalculate()

    body = render_to_string(
        "invoices/pdf/classic.html",
        {"invoice": invoice, "document": document},
    )
    assert '<th style="width:15%; text-align: end">Tax</th>' not in body
