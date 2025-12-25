from decimal import Decimal

import pytest
from djmoney.money import Money

from apps.invoices.models import InvoiceDiscount, InvoiceTax
from common.calculations import MAX_AMOUNT, calculate_percentage_amount
from tests.factories import (
    CouponFactory,
    InvoiceDiscountFactory,
    InvoiceFactory,
    InvoiceLineFactory,
    InvoiceTaxFactory,
    TaxRateFactory,
)

pytestmark = pytest.mark.django_db


def test_calculate_discount_amount_fixed():
    coupon = CouponFactory(currency="USD", amount=Money(10, "USD"), percentage=None)
    base = Money(50, "USD")
    assert InvoiceDiscount.calculate_amount(base, coupon) == Money("10.00", "USD")


def test_calculate_discount_amount_percentage():
    coupon = CouponFactory(currency="USD", amount=None, percentage=Decimal("10"))
    base = Money(50, "USD")
    assert InvoiceDiscount.calculate_amount(base, coupon) == Money("5.00", "USD")


def test_calculate_discount_amount_percentage_cap():
    coupon = CouponFactory(currency="USD", amount=None, percentage=Decimal("150"))
    base = Money(50, "USD")
    assert InvoiceDiscount.calculate_amount(base, coupon) == Money("50.00", "USD")


def test_discount_amount_non_positive_values():
    base = Money(100, "USD")
    zero_coupon = CouponFactory(currency="USD", amount=Money(0, "USD"), percentage=None)
    negative_coupon = CouponFactory(currency="USD", amount=None, percentage=Decimal("-10"))
    assert InvoiceDiscount.calculate_amount(base, zero_coupon) == Money("0.00", "USD")
    assert InvoiceDiscount.calculate_amount(base, negative_coupon) == Money("0.00", "USD")


def test_calculate_percentage_amount_non_positive():
    base = Money(100, "USD")
    assert calculate_percentage_amount(base, Decimal("0")) == Money("0.00", "USD")
    assert calculate_percentage_amount(base, Decimal("-5")) == Money("0.00", "USD")


def test_calculate_tax_amount_percentage():
    base = Money(50, "USD")
    assert InvoiceTax.calculate_amount(base, Decimal("20")) == Money("10.00", "USD")


def test_calculate_tax_amount_zero_percentage():
    base = Money(50, "USD")
    assert InvoiceTax.calculate_amount(base, Decimal("0")) == Money("0.00", "USD")


def test_calculate_tax_amount_tax_rate():
    tax_rate = TaxRateFactory(percentage=Decimal("20"))
    base = Money(50, "USD")
    assert InvoiceTax.calculate_amount(base, tax_rate) == Money("10.00", "USD")


def test_calculate_tax_amount_negative_rate():
    line = InvoiceLineFactory()
    tax = InvoiceTaxFactory(invoice_line=line, rate=Decimal("-5"))
    assert InvoiceTax.calculate_amount(Money(100, line.currency), tax.rate) == Money("0", line.currency)


def test_calculate_tax_amount_zero_rate():
    line = InvoiceLineFactory()
    tax = InvoiceTaxFactory(invoice_line=line, rate=Decimal("0"))
    assert InvoiceTax.calculate_amount(Money(100, line.currency), tax.rate) == Money("0", line.currency)


def test_apply_line_discounts_sequential_percentages():
    line = InvoiceLineFactory(unit_amount=Decimal("100"), quantity=1, amount=Decimal("0"))
    coupon_1 = CouponFactory(account=line.invoice.account, currency=line.currency, percentage=Decimal("50"))
    coupon_2 = CouponFactory(account=line.invoice.account, currency=line.currency, percentage=Decimal("50"))
    discount_1 = InvoiceDiscountFactory(invoice_line=line, coupon=coupon_1, amount=Decimal("0"))
    discount_2 = InvoiceDiscountFactory(invoice_line=line, coupon=coupon_2, amount=Decimal("0"))

    total, taxable = line.discounts.select_related("coupon").all().recalculate(Money(100, line.currency))

    assert total == Money("75.00", line.currency)
    assert taxable == Money("25.00", line.currency)
    discount_1.refresh_from_db()
    discount_2.refresh_from_db()
    assert discount_1.amount == Money("50.00", line.currency)
    assert discount_2.amount == Money("25.00", line.currency)


def test_apply_line_taxes_zero_taxable():
    line = InvoiceLineFactory()
    tax_rate = TaxRateFactory(account=line.invoice.account, percentage=Decimal("20"))
    tax = InvoiceTaxFactory(invoice_line=line, tax_rate=tax_rate, rate=tax_rate.percentage, amount=Decimal("0"))

    total, _ = line.taxes.all().recalculate(Money(0, line.currency))

    tax.refresh_from_db()
    assert total == Money("0.00", line.currency)
    assert tax.amount == Money("0.00", line.currency)


def test_recalculate_invoice_line_no_discounts_no_taxes():
    line = InvoiceLineFactory(unit_amount=Decimal("20"), quantity=2, amount=Decimal("0"))

    line.recalculate()

    line.refresh_from_db()
    line.invoice.refresh_from_db()
    assert line.invoice.subtotal_amount == Money("40.00", line.currency)
    assert line.invoice.total_discount_amount == Money("0.00", line.currency)
    assert line.invoice.total_tax_amount == Money("0.00", line.currency)
    assert line.invoice.total_amount == Money("40.00", line.currency)
    assert line.total_amount_excluding_tax == Money("40.00", line.currency)
    assert line.total_amount == Money("40.00", line.currency)
    assert line.total_discount_amount == Money("0.00", line.currency)
    assert line.total_tax_amount == Money("0.00", line.currency)
    assert line.total_tax_rate == Decimal("0")


def test_recalculate_invoice_line_with_discounts_and_taxes():
    line = InvoiceLineFactory(unit_amount=Decimal("100"), quantity=1, amount=Decimal("0"))
    invoice = line.invoice
    percent_coupon = CouponFactory(
        account=line.invoice.account, currency=line.currency, amount=None, percentage=Decimal("10")
    )
    amount_coupon = CouponFactory(
        account=line.invoice.account, currency=line.currency, amount=Money(20, line.currency), percentage=None
    )
    InvoiceDiscountFactory(invoice_line=line, coupon=percent_coupon, amount=Decimal("0"))
    InvoiceDiscountFactory(invoice_line=line, coupon=amount_coupon, amount=Decimal("0"))
    tax_rate = TaxRateFactory(account=line.invoice.account, percentage=Decimal("20"))
    InvoiceTaxFactory(invoice_line=line, tax_rate=tax_rate, rate=tax_rate.percentage, amount=Decimal("0"))

    line.recalculate()

    discounts = list(line.discounts.all())
    assert discounts[0].amount == Money("10.00", line.currency)
    assert discounts[1].amount == Money("20.00", line.currency)
    invoice.refresh_from_db()
    assert invoice.subtotal_amount == Money("100.00", line.currency)
    assert invoice.total_discount_amount == Money("30.00", line.currency)
    assert invoice.total_amount_excluding_tax == Money("70.00", line.currency)
    assert invoice.total_tax_amount == Money("14.00", line.currency)
    assert invoice.total_amount == Money("84.00", line.currency)
    line.refresh_from_db()
    assert line.total_amount_excluding_tax == Money("70.00", line.currency)
    assert line.total_amount == Money("84.00", line.currency)
    assert line.total_discount_amount == Money("30.00", line.currency)
    assert line.total_tax_amount == Money("14.00", line.currency)
    assert line.total_tax_rate == Decimal("20.00")


def test_recalculate_invoice_line_discount_exceeds_amount():
    line = InvoiceLineFactory(unit_amount=Decimal("50"), quantity=1, amount=Decimal("0"))
    invoice = line.invoice
    big_coupon_1 = CouponFactory(
        account=line.invoice.account, currency=line.currency, amount=Money(60, line.currency), percentage=None
    )
    big_coupon_2 = CouponFactory(
        account=line.invoice.account, currency=line.currency, amount=Money(60, line.currency), percentage=None
    )
    InvoiceDiscountFactory(invoice_line=line, coupon=big_coupon_1, amount=Decimal("0"))
    InvoiceDiscountFactory(invoice_line=line, coupon=big_coupon_2, amount=Decimal("0"))

    line.recalculate()

    invoice.refresh_from_db()
    assert invoice.subtotal_amount == Money("50.00", line.currency)
    assert invoice.total_discount_amount == Money("50.00", line.currency)
    assert invoice.total_amount_excluding_tax == Money("0.00", line.currency)
    assert invoice.total_tax_amount == Money("0.00", line.currency)
    assert invoice.total_amount == Money("0.00", line.currency)


def test_recalculate_invoice_line_partial_second_discount():
    line = InvoiceLineFactory(unit_amount=Decimal("25"), quantity=1, amount=Decimal("0"))
    invoice = line.invoice
    first_coupon = CouponFactory(
        account=line.invoice.account, currency=line.currency, amount=Money(10, line.currency), percentage=None
    )
    second_coupon = CouponFactory(
        account=line.invoice.account,
        currency=line.currency,
        amount=Money(20, line.currency),
        percentage=None,
    )
    InvoiceDiscountFactory(invoice_line=line, coupon=first_coupon, amount=Decimal("0"))
    InvoiceDiscountFactory(invoice_line=line, coupon=second_coupon, amount=Decimal("0"))

    line.recalculate()

    discounts = list(line.discounts.all())
    assert discounts[0].amount == Money("10.00", line.currency)
    assert discounts[1].amount == Money("15.00", line.currency)
    invoice.refresh_from_db()
    assert invoice.total_discount_amount == Money("25.00", line.currency)
    assert invoice.total_amount == Money("0.00", line.currency)


def test_recalculate_invoice_line_rounding():
    line = InvoiceLineFactory(unit_amount=Decimal("100"), quantity=1, amount=Decimal("0"))
    percent_coupon = CouponFactory(
        account=line.invoice.account,
        currency=line.currency,
        percentage=Decimal("33.3333"),
    )
    InvoiceDiscountFactory(invoice_line=line, coupon=percent_coupon, amount=Decimal("0"))
    tax_rate = TaxRateFactory(account=line.invoice.account, percentage=Decimal("10"))
    InvoiceTaxFactory(invoice_line=line, tax_rate=tax_rate, rate=tax_rate.percentage, amount=Decimal("0"))

    line.recalculate()

    line.refresh_from_db()
    assert line.discounts.first().amount == Money("33.33", line.currency)
    assert line.taxes.first().amount == Money("6.67", line.currency)
    assert line.invoice.total_amount == Money("73.34", line.currency)


def test_recalculate_invoice_line_multiple_taxes():
    line = InvoiceLineFactory(unit_amount=Decimal("100"), quantity=1, amount=Decimal("0"))
    tax_rate1 = TaxRateFactory(account=line.invoice.account, percentage=Decimal("10"))
    tax_rate2 = TaxRateFactory(account=line.invoice.account, percentage=Decimal("5"))
    InvoiceTaxFactory(invoice_line=line, tax_rate=tax_rate1, rate=tax_rate1.percentage, amount=Decimal("0"))
    InvoiceTaxFactory(invoice_line=line, tax_rate=tax_rate2, rate=tax_rate2.percentage, amount=Decimal("0"))

    line.recalculate()

    line.invoice.refresh_from_db()
    assert line.invoice.total_tax_amount == Money("15.00", line.currency)
    assert line.invoice.total_amount == Money("115.00", line.currency)


def test_recalculate_invoice_multiple_lines():
    line1 = InvoiceLineFactory(unit_amount=Decimal("100"), quantity=1, amount=Decimal("0"))
    line2 = InvoiceLineFactory(invoice=line1.invoice, unit_amount=Decimal("50"), quantity=2, amount=Decimal("0"))
    percent_coupon = CouponFactory(
        account=line1.invoice.account, currency=line2.currency, percentage=Decimal("10"), amount=None
    )
    InvoiceDiscountFactory(invoice_line=line2, coupon=percent_coupon, amount=Decimal("0"))
    tax_rate = TaxRateFactory(account=line1.invoice.account, percentage=Decimal("20"))
    InvoiceTaxFactory(invoice_line=line1, tax_rate=tax_rate, rate=tax_rate.percentage, amount=Decimal("0"))
    InvoiceTaxFactory(invoice_line=line2, tax_rate=tax_rate, rate=tax_rate.percentage, amount=Decimal("0"))

    line1.recalculate()
    line2.recalculate()
    invoice = line1.invoice
    invoice.recalculate()

    assert invoice.subtotal_amount == Money("200.00", invoice.currency)
    assert invoice.total_discount_amount == Money("10.00", invoice.currency)
    assert invoice.total_tax_amount == Money("38.00", invoice.currency)
    assert invoice.total_amount == Money("228.00", invoice.currency)


def test_recalculate_invoice_line_full_discount_zero_tax():
    line = InvoiceLineFactory(unit_amount=Decimal("50"), quantity=1, amount=Decimal("0"))
    big_coupon = CouponFactory(
        account=line.invoice.account, currency=line.currency, amount=Money(100, line.currency), percentage=None
    )
    InvoiceDiscountFactory(invoice_line=line, coupon=big_coupon, amount=Decimal("0"))
    tax_rate = TaxRateFactory(account=line.invoice.account, percentage=Decimal("20"))
    InvoiceTaxFactory(invoice_line=line, tax_rate=tax_rate, rate=tax_rate.percentage, amount=Decimal("0"))

    line.recalculate()

    line.refresh_from_db()
    assert line.invoice.total_amount == Money("0.00", line.currency)
    assert line.invoice.total_tax_amount == Money("0.00", line.currency)


def test_recalculate_invoice_line_multiple_percentage_discounts():
    line = InvoiceLineFactory(unit_amount=Decimal("100"), quantity=1, amount=Decimal("0"))
    first = CouponFactory(account=line.invoice.account, currency=line.currency, percentage=Decimal("10"), amount=None)
    second = CouponFactory(account=line.invoice.account, currency=line.currency, percentage=Decimal("20"), amount=None)
    InvoiceDiscountFactory(invoice_line=line, coupon=first, amount=Decimal("0"))
    InvoiceDiscountFactory(invoice_line=line, coupon=second, amount=Decimal("0"))

    line.recalculate()

    line.refresh_from_db()
    discounts = list(line.discounts.all())
    assert discounts[0].amount == Money("10.00", line.currency)
    assert discounts[1].amount == Money("18.00", line.currency)
    assert line.invoice.total_discount_amount == Money("28.00", line.currency)


def test_recalculate_invoice_line_clamps_large_amount():
    line = InvoiceLineFactory(unit_amount=Decimal("1000000000"), quantity=1, amount=Decimal("0"))

    line.recalculate()

    line.refresh_from_db()
    line.invoice.refresh_from_db()
    assert line.amount == Money(MAX_AMOUNT, line.currency)
    assert line.invoice.total_amount == Money(MAX_AMOUNT, line.currency)


def test_apply_line_discounts_exceeding_base():
    line = InvoiceLineFactory(unit_amount=Decimal("50"), quantity=1, amount=Decimal("0"))
    big_coupon = CouponFactory(
        account=line.invoice.account,
        currency=line.currency,
        amount=Money(80, line.currency),
        percentage=None,
    )
    discount = InvoiceDiscountFactory(invoice_line=line, coupon=big_coupon, amount=Decimal("0"))

    total, taxable = line.discounts.select_related("coupon").all().recalculate(Money(50, line.currency))

    discount.refresh_from_db()
    assert total == Money("50.00", line.currency)
    assert taxable == Money("0.00", line.currency)
    assert discount.amount == Money("50.00", line.currency)


def test_apply_line_taxes_multiple_rates():
    line = InvoiceLineFactory()
    tax_rate1 = TaxRateFactory(account=line.invoice.account, percentage=Decimal("10"))
    tax_rate2 = TaxRateFactory(account=line.invoice.account, percentage=Decimal("5"))
    tax1 = InvoiceTaxFactory(invoice_line=line, tax_rate=tax_rate1, rate=tax_rate1.percentage, amount=Decimal("0"))
    tax2 = InvoiceTaxFactory(invoice_line=line, tax_rate=tax_rate2, rate=tax_rate2.percentage, amount=Decimal("0"))

    total, rate_total = line.taxes.all().recalculate(Money(100, line.currency))

    tax1.refresh_from_db()
    tax2.refresh_from_db()
    assert total == Money("15.00", line.currency)
    assert rate_total == Decimal("15")
    assert tax1.amount == Money("10.00", line.currency)
    assert tax2.amount == Money("5.00", line.currency)


def test_recalculate_invoice_line_zero_quantity():
    line = InvoiceLineFactory(unit_amount=Decimal("100"), quantity=0, amount=Decimal("0"))
    coupon = CouponFactory(
        account=line.invoice.account,
        currency=line.currency,
        amount=Money(10, line.currency),
        percentage=None,
    )
    tax_rate = TaxRateFactory(account=line.invoice.account, percentage=Decimal("20"))
    InvoiceDiscountFactory(invoice_line=line, coupon=coupon, amount=Decimal("0"))
    InvoiceTaxFactory(invoice_line=line, tax_rate=tax_rate, rate=tax_rate.percentage, amount=Decimal("0"))

    line.recalculate()

    line.refresh_from_db()
    line.invoice.refresh_from_db()
    assert line.amount == Money("0.00", line.currency)
    assert line.discounts.first().amount == Money("0.00", line.currency)
    assert line.taxes.first().amount == Money("0.00", line.currency)
    assert line.invoice.total_amount == Money("0.00", line.currency)


def test_recalculate_invoice_with_invoice_discount_and_tax():
    line = InvoiceLineFactory(
        quantity=1,
        unit_amount=Decimal("100"),
        amount=Decimal("100"),
        total_amount_excluding_tax=Decimal("100"),
    )
    invoice = line.invoice
    coupon = CouponFactory(account=invoice.account, currency=invoice.currency, amount=None, percentage=Decimal("10"))
    tax_rate = TaxRateFactory(account=invoice.account, percentage=Decimal("20"))
    InvoiceDiscountFactory(invoice=invoice, coupon=coupon, amount=Decimal("0"))
    InvoiceTaxFactory(invoice=invoice, tax_rate=tax_rate, rate=tax_rate.percentage, amount=Decimal("0"))

    invoice.recalculate()

    invoice.refresh_from_db()
    discount = invoice.discounts.first()
    tax = invoice.taxes.first()
    assert discount.amount == Money("10.00", invoice.currency)
    assert tax.amount == Money("18.00", invoice.currency)
    assert invoice.subtotal_amount == Money("100.00", invoice.currency)
    assert invoice.total_discount_amount == Money("10.00", invoice.currency)
    assert invoice.total_amount_excluding_tax == Money("90.00", invoice.currency)
    assert invoice.total_tax_amount == Money("18.00", invoice.currency)
    assert invoice.total_amount == Money("108.00", invoice.currency)


def test_apply_invoice_discounts_sequential_and_amount():
    invoice = InvoiceFactory()
    percent_coupon = CouponFactory(
        account=invoice.account, currency=invoice.currency, amount=None, percentage=Decimal("10")
    )
    amount_coupon = CouponFactory(
        account=invoice.account, currency=invoice.currency, amount=Money(15, invoice.currency), percentage=None
    )
    d1 = InvoiceDiscountFactory(invoice=invoice, coupon=percent_coupon, amount=Decimal("0"))
    d2 = InvoiceDiscountFactory(invoice=invoice, coupon=amount_coupon, amount=Decimal("0"))

    total, taxable = invoice.discounts.select_related("coupon").all().recalculate(Money(100, invoice.currency))

    d1.refresh_from_db()
    d2.refresh_from_db()
    assert total == Money("25.00", invoice.currency)
    assert taxable == Money("75.00", invoice.currency)
    assert d1.amount == Money("10.00", invoice.currency)
    assert d2.amount == Money("15.00", invoice.currency)


def test_apply_invoice_discounts_exceeding_base():
    invoice = InvoiceFactory()
    big_coupon = CouponFactory(
        account=invoice.account, currency=invoice.currency, amount=Money(80, invoice.currency), percentage=None
    )
    extra_coupon = CouponFactory(
        account=invoice.account, currency=invoice.currency, amount=Money(50, invoice.currency), percentage=None
    )
    d1 = InvoiceDiscountFactory(invoice=invoice, coupon=big_coupon, amount=Decimal("0"))
    d2 = InvoiceDiscountFactory(invoice=invoice, coupon=extra_coupon, amount=Decimal("0"))

    total, taxable = invoice.discounts.select_related("coupon").all().recalculate(Money(100, invoice.currency))

    d1.refresh_from_db()
    d2.refresh_from_db()
    assert total == Money("100.00", invoice.currency)
    assert taxable == Money("0.00", invoice.currency)
    assert d1.amount == Money("80.00", invoice.currency)
    assert d2.amount == Money("20.00", invoice.currency)


def test_apply_invoice_taxes_multiple_rates():
    invoice = InvoiceFactory()
    tax_rate1 = TaxRateFactory(account=invoice.account, percentage=Decimal("10"))
    tax_rate2 = TaxRateFactory(account=invoice.account, percentage=Decimal("5"))
    tax1 = InvoiceTaxFactory(invoice=invoice, tax_rate=tax_rate1, rate=tax_rate1.percentage, amount=Decimal("0"))
    tax2 = InvoiceTaxFactory(invoice=invoice, tax_rate=tax_rate2, rate=tax_rate2.percentage, amount=Decimal("0"))

    total, rate_total = invoice.taxes.all().recalculate(Money(100, invoice.currency))

    tax1.refresh_from_db()
    tax2.refresh_from_db()
    assert total == Money("15.00", invoice.currency)
    assert rate_total == Decimal("15")
    assert tax1.amount == Money("10.00", invoice.currency)
    assert tax2.amount == Money("5.00", invoice.currency)


def test_apply_invoice_taxes_zero_taxable():
    invoice = InvoiceFactory()
    tax_rate = TaxRateFactory(account=invoice.account, percentage=Decimal("20"))
    tax = InvoiceTaxFactory(invoice=invoice, tax_rate=tax_rate, rate=tax_rate.percentage, amount=Decimal("0"))

    total, _ = invoice.taxes.all().recalculate(Money(0, invoice.currency))

    tax.refresh_from_db()
    assert total == Money("0.00", invoice.currency)
    assert tax.amount == Money("0.00", invoice.currency)


def test_recalculate_invoice_multiple_invoice_discounts_and_taxes():
    line1 = InvoiceLineFactory(unit_amount=Decimal("100"), quantity=2, amount=Decimal("0"))
    line2 = InvoiceLineFactory(invoice=line1.invoice, unit_amount=Decimal("50"), quantity=1, amount=Decimal("0"))
    invoice = line1.invoice
    percent_coupon = CouponFactory(
        account=invoice.account, currency=invoice.currency, amount=None, percentage=Decimal("10")
    )
    amount_coupon = CouponFactory(
        account=invoice.account, currency=invoice.currency, amount=Money(30, invoice.currency), percentage=None
    )
    InvoiceDiscountFactory(invoice=invoice, coupon=percent_coupon, amount=Decimal("0"))
    InvoiceDiscountFactory(invoice=invoice, coupon=amount_coupon, amount=Decimal("0"))
    tax_rate1 = TaxRateFactory(account=invoice.account, percentage=Decimal("20"))
    tax_rate2 = TaxRateFactory(account=invoice.account, percentage=Decimal("5"))
    InvoiceTaxFactory(invoice=invoice, tax_rate=tax_rate1, rate=tax_rate1.percentage, amount=Decimal("0"))
    InvoiceTaxFactory(invoice=invoice, tax_rate=tax_rate2, rate=tax_rate2.percentage, amount=Decimal("0"))

    line1.recalculate()
    line2.recalculate()
    invoice.recalculate()

    invoice.refresh_from_db()
    assert invoice.subtotal_amount == Money("250.00", invoice.currency)
    assert invoice.total_discount_amount == Money("55.00", invoice.currency)
    assert invoice.total_amount_excluding_tax == Money("195.00", invoice.currency)
    assert invoice.total_tax_amount == Money("48.75", invoice.currency)
    assert invoice.total_amount == Money("243.75", invoice.currency)


def test_recalculate_invoice_invoice_discount_exceeds_subtotal():
    line = InvoiceLineFactory(unit_amount=Decimal("40"), quantity=1, amount=Decimal("0"))
    invoice = line.invoice
    big_coupon = CouponFactory(
        account=invoice.account, currency=invoice.currency, amount=Money(100, invoice.currency), percentage=None
    )
    tax_rate = TaxRateFactory(account=invoice.account, percentage=Decimal("10"))
    InvoiceDiscountFactory(invoice=invoice, coupon=big_coupon, amount=Decimal("0"))
    InvoiceTaxFactory(invoice=invoice, tax_rate=tax_rate, rate=tax_rate.percentage, amount=Decimal("0"))

    line.recalculate()
    invoice.recalculate()

    invoice.refresh_from_db()
    discount = invoice.discounts.first()
    tax = invoice.taxes.first()
    assert discount.amount == Money("40.00", invoice.currency)
    assert tax.amount == Money("0.00", invoice.currency)
    assert invoice.total_amount == Money("0.00", invoice.currency)


def test_recalculate_invoice_with_line_and_invoice_discounts_and_taxes():
    line = InvoiceLineFactory(unit_amount=Decimal("100"), quantity=1, amount=Decimal("0"))
    invoice = line.invoice
    percent_coupon_line = CouponFactory(
        account=invoice.account, currency=invoice.currency, amount=None, percentage=Decimal("10")
    )
    InvoiceDiscountFactory(invoice_line=line, coupon=percent_coupon_line, amount=Decimal("0"))
    tax_rate_line = TaxRateFactory(account=invoice.account, percentage=Decimal("10"))
    InvoiceTaxFactory(invoice_line=line, tax_rate=tax_rate_line, rate=tax_rate_line.percentage, amount=Decimal("0"))
    coupon_inv = CouponFactory(
        account=invoice.account, currency=invoice.currency, amount=Money(5, invoice.currency), percentage=None
    )
    tax_rate_inv = TaxRateFactory(account=invoice.account, percentage=Decimal("5"))
    InvoiceDiscountFactory(invoice=invoice, coupon=coupon_inv, amount=Decimal("0"))
    InvoiceTaxFactory(invoice=invoice, tax_rate=tax_rate_inv, rate=tax_rate_inv.percentage, amount=Decimal("0"))

    line.recalculate()
    invoice.recalculate()

    invoice.refresh_from_db()
    assert invoice.subtotal_amount == Money("100.00", invoice.currency)
    assert invoice.total_discount_amount == Money("15.00", invoice.currency)
    assert invoice.total_amount_excluding_tax == Money("85.00", invoice.currency)
    assert invoice.total_tax_amount == Money("9.00", invoice.currency)
    assert invoice.total_amount == Money("94.00", invoice.currency)
    tax = invoice.taxes.for_invoice().first()
    assert tax.amount == Money("0.00", invoice.currency)


def test_recalculate_invoice_line_discount_and_invoice_tax():
    line = InvoiceLineFactory(unit_amount=Decimal("100"), quantity=1, amount=Decimal("0"))
    invoice = line.invoice
    coupon = CouponFactory(account=invoice.account, currency=invoice.currency, amount=None, percentage=Decimal("10"))
    InvoiceDiscountFactory(invoice_line=line, coupon=coupon, amount=Decimal("0"))
    tax_rate = TaxRateFactory(account=invoice.account, percentage=Decimal("20"))
    InvoiceTaxFactory(invoice=invoice, tax_rate=tax_rate, rate=tax_rate.percentage, amount=Decimal("0"))

    line.recalculate()
    invoice.recalculate()

    invoice.refresh_from_db()
    assert invoice.subtotal_amount == Money("100.00", invoice.currency)
    assert invoice.total_discount_amount == Money("10.00", invoice.currency)
    assert invoice.total_amount_excluding_tax == Money("90.00", invoice.currency)
    assert invoice.total_tax_amount == Money("18.00", invoice.currency)
    assert invoice.total_amount == Money("108.00", invoice.currency)


def test_recalculate_invoice_line_tax_and_invoice_discount():
    line = InvoiceLineFactory(unit_amount=Decimal("100"), quantity=1, amount=Decimal("0"))
    invoice = line.invoice
    tax_rate = TaxRateFactory(account=invoice.account, percentage=Decimal("20"))
    InvoiceTaxFactory(invoice_line=line, tax_rate=tax_rate, rate=tax_rate.percentage, amount=Decimal("0"))
    coupon = CouponFactory(account=invoice.account, currency=invoice.currency, amount=None, percentage=Decimal("10"))
    InvoiceDiscountFactory(invoice=invoice, coupon=coupon, amount=Decimal("0"))

    line.recalculate()
    invoice.recalculate()

    invoice.refresh_from_db()
    assert invoice.subtotal_amount == Money("100.00", invoice.currency)
    assert invoice.total_discount_amount == Money("10.00", invoice.currency)
    assert invoice.total_amount_excluding_tax == Money("90.00", invoice.currency)
    assert invoice.total_tax_amount == Money("20.00", invoice.currency)
    assert invoice.total_amount == Money("110.00", invoice.currency)


def test_recalculate_invoice_invoice_tax_excludes_lines_with_line_taxes():
    line_with_tax = InvoiceLineFactory(unit_amount=Decimal("100"), quantity=1, amount=Decimal("0"))
    line_without_tax = InvoiceLineFactory(
        invoice=line_with_tax.invoice,
        unit_amount=Decimal("50"),
        quantity=1,
        amount=Decimal("0"),
    )
    invoice = line_with_tax.invoice

    tax_rate_line = TaxRateFactory(account=invoice.account, percentage=Decimal("10"))
    InvoiceTaxFactory(
        invoice_line=line_with_tax,
        tax_rate=tax_rate_line,
        rate=tax_rate_line.percentage,
        amount=Decimal("0"),
    )
    tax_rate_invoice = TaxRateFactory(account=invoice.account, percentage=Decimal("10"))
    invoice_tax = InvoiceTaxFactory(
        invoice=invoice,
        tax_rate=tax_rate_invoice,
        rate=tax_rate_invoice.percentage,
        amount=Decimal("0"),
    )

    line_with_tax.recalculate()
    line_without_tax.recalculate()
    invoice.recalculate()

    invoice.refresh_from_db()
    invoice_tax.refresh_from_db()
    assert invoice.subtotal_amount == Money("150.00", invoice.currency)
    assert invoice.total_amount_excluding_tax == Money("150.00", invoice.currency)
    assert invoice.total_tax_amount == Money("15.00", invoice.currency)
    assert invoice.total_amount == Money("165.00", invoice.currency)
    assert invoice_tax.amount == Money("5.00", invoice.currency)


def test_recalculate_invoice_mixed_line_and_invoice_adjustments():
    line_with_discount = InvoiceLineFactory(unit_amount=Decimal("100"), quantity=1, amount=Decimal("0"))
    line_with_tax = InvoiceLineFactory(
        invoice=line_with_discount.invoice,
        unit_amount=Decimal("100"),
        quantity=1,
        amount=Decimal("0"),
    )
    invoice = line_with_discount.invoice

    coupon_line = CouponFactory(
        account=invoice.account, currency=invoice.currency, amount=None, percentage=Decimal("10")
    )
    InvoiceDiscountFactory(invoice_line=line_with_discount, coupon=coupon_line, amount=Decimal("0"))
    tax_rate_line = TaxRateFactory(account=invoice.account, percentage=Decimal("10"))
    InvoiceTaxFactory(
        invoice_line=line_with_tax, tax_rate=tax_rate_line, rate=tax_rate_line.percentage, amount=Decimal("0")
    )

    coupon_inv = CouponFactory(
        account=invoice.account, currency=invoice.currency, amount=Money(10, invoice.currency), percentage=None
    )
    tax_rate_inv = TaxRateFactory(account=invoice.account, percentage=Decimal("5"))
    InvoiceDiscountFactory(invoice=invoice, coupon=coupon_inv, amount=Decimal("0"))
    InvoiceTaxFactory(invoice=invoice, tax_rate=tax_rate_inv, rate=tax_rate_inv.percentage, amount=Decimal("0"))

    line_with_discount.recalculate()
    line_with_tax.recalculate()
    invoice.recalculate()

    invoice.refresh_from_db()
    assert invoice.subtotal_amount == Money("200.00", invoice.currency)
    assert invoice.total_discount_amount == Money("20.00", invoice.currency)
    assert invoice.total_amount_excluding_tax == Money("180.00", invoice.currency)
    assert invoice.total_tax_amount == Money("14.26", invoice.currency)
    assert invoice.total_amount == Money("194.26", invoice.currency)
