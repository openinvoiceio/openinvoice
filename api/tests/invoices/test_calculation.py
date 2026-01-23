from decimal import Decimal

import pytest
from djmoney.money import Money

from apps.invoices.choices import InvoiceTaxBehavior, InvoiceTaxSource
from common.calculations import MAX_AMOUNT
from tests.factories import (
    CouponFactory,
    InvoiceFactory,
    InvoiceLineFactory,
    ShippingRateFactory,
    TaxRateFactory,
)

pytestmark = pytest.mark.django_db


def test_calculate_coupon_amount_fixed():
    coupon = CouponFactory(currency="USD", amount=Money(10, "USD"), percentage=None)
    base_amount = Money(50, "USD")
    assert coupon.calculate_amount(base_amount) == Money("10.00", "USD")


def test_calculate_coupon_amount_percentage():
    coupon = CouponFactory(currency="USD", amount=None, percentage=Decimal("10"))
    base_amount = Money(50, "USD")
    assert coupon.calculate_amount(base_amount) == Money("5.00", "USD")


def test_calculate_coupon_amount_percentage_cap():
    coupon = CouponFactory(currency="USD", amount=None, percentage=Decimal("150"))
    base_amount = Money(50, "USD")
    assert coupon.calculate_amount(base_amount) == Money("50.00", "USD")


def test_calculate_coupon_amount_non_positive_values():
    base_amount = Money(100, "USD")
    zero_coupon = CouponFactory(currency="USD", amount=Money(0, "USD"), percentage=None)
    negative_coupon = CouponFactory(currency="USD", amount=None, percentage=Decimal("-10"))
    assert zero_coupon.calculate_amount(base_amount) == Money("0.00", "USD")
    assert negative_coupon.calculate_amount(base_amount) == Money("0.00", "USD")


def test_calculate_tax_rate_amount_percentage():
    base_amount = Money(50, "USD")
    tax_rate = TaxRateFactory(percentage=Decimal("20"))
    assert tax_rate.calculate_amount(base_amount) == Money("10.00", "USD")


def test_calculate_tax_rate_amount_zero_percentage():
    base_amount = Money(50, "USD")
    tax_rate = TaxRateFactory(percentage=Decimal("0"))
    assert tax_rate.calculate_amount(base_amount) == Money("0.00", "USD")


def test_calculate_tax_rate_amount_negative_rate():
    base_amount = Money(100, "USD")
    tax_rate = TaxRateFactory(percentage=Decimal("-5"))
    assert tax_rate.calculate_amount(base_amount) == Money("0", base_amount.currency)


def test_recalculate_invoice_line_with_inclusive_tax_behavior():
    invoice = InvoiceFactory(tax_behavior=InvoiceTaxBehavior.INCLUSIVE)
    line = InvoiceLineFactory(invoice=invoice, unit_amount=Decimal("120"), quantity=1, amount=Decimal("0"))
    tax_rate = TaxRateFactory(account=invoice.account, percentage=Decimal("20"))

    line.set_tax_rates([tax_rate])
    invoice.recalculate()

    line.refresh_from_db()
    assert line.amount == Money("120.00", line.currency)
    assert line.unit_excluding_tax_amount == Money("100.00", line.currency)
    assert line.total_taxable_amount == Money("100.00", line.currency)
    assert line.total_tax_amount == Money("20.00", line.currency)
    assert line.total_amount == Money("120.00", line.currency)

    invoice.refresh_from_db()
    assert invoice.total_excluding_tax_amount == Money("100.00", line.currency)
    assert invoice.total_tax_amount == Money("20.00", line.currency)
    assert invoice.total_amount == Money("120.00", line.currency)


def test_recalculate_invoice_line_with_automatic_tax_behavior_exclusive():
    invoice = InvoiceFactory(currency="USD", tax_behavior=InvoiceTaxBehavior.AUTOMATIC)
    line = InvoiceLineFactory(invoice=invoice, unit_amount=Decimal("100"), quantity=1, amount=Decimal("0"))
    tax_rate = TaxRateFactory(account=invoice.account, percentage=Decimal("10"))

    line.set_tax_rates([tax_rate])
    invoice.recalculate()

    line.refresh_from_db()
    assert line.amount == Money("100.00", line.currency)
    assert line.unit_excluding_tax_amount == Money("100.00", line.currency)
    assert line.total_tax_amount == Money("10.00", line.currency)
    assert line.total_amount == Money("110.00", line.currency)


def test_recalculate_invoice_line_with_automatic_tax_behavior_inclusive():
    invoice = InvoiceFactory(currency="EUR", tax_behavior=InvoiceTaxBehavior.AUTOMATIC)
    line = InvoiceLineFactory(invoice=invoice, unit_amount=Decimal("120"), quantity=2, amount=Decimal("0"))
    tax_rate = TaxRateFactory(account=invoice.account, percentage=Decimal("20"))

    line.set_tax_rates([tax_rate])
    invoice.recalculate()

    line.refresh_from_db()
    assert line.amount == Money("240.00", line.currency)
    assert line.unit_excluding_tax_amount == Money("100.00", line.currency)
    assert line.total_taxable_amount == Money("200.00", line.currency)
    assert line.total_tax_amount == Money("40.00", line.currency)
    assert line.total_amount == Money("240.00", line.currency)


def test_recalculate_invoice_inclusive_with_discount_and_taxes():
    invoice = InvoiceFactory(currency="EUR", tax_behavior=InvoiceTaxBehavior.INCLUSIVE)
    line = InvoiceLineFactory(invoice=invoice, unit_amount=Decimal("120"), quantity=1, amount=Decimal("0"))
    coupon = CouponFactory(account=invoice.account, currency=line.currency, percentage=Decimal("10"), amount=None)
    tax_rate = TaxRateFactory(account=invoice.account, percentage=Decimal("20"))

    line.set_coupons([coupon])
    line.set_tax_rates([tax_rate])
    invoice.recalculate()

    line.refresh_from_db()
    assert line.unit_excluding_tax_amount == Money("100.00", line.currency)
    assert line.amount == Money("120.00", line.currency)
    assert line.subtotal_amount == Money("108.00", line.currency)
    assert line.total_discount_amount == Money("12.00", line.currency)
    assert line.total_excluding_tax_amount == Money("88.00", line.currency)
    assert line.total_taxable_amount == Money("88.00", line.currency)
    assert line.total_tax_amount == Money("17.60", line.currency)
    assert line.total_amount == Money("105.60", line.currency)

    invoice.refresh_from_db()
    assert invoice.subtotal_amount == Money("108.00", line.currency)
    assert invoice.total_excluding_tax_amount == Money("88.00", line.currency)
    assert invoice.total_tax_amount == Money("17.60", line.currency)
    assert invoice.total_amount == Money("105.60", line.currency)


def test_recalculate_invoice_inclusive_with_multiple_tax_rates():
    invoice = InvoiceFactory(currency="EUR", tax_behavior=InvoiceTaxBehavior.INCLUSIVE)
    line = InvoiceLineFactory(invoice=invoice, unit_amount=Decimal("115"), quantity=1, amount=Decimal("0"))
    tax_rate1 = TaxRateFactory(account=invoice.account, percentage=Decimal("10"))
    tax_rate2 = TaxRateFactory(account=invoice.account, percentage=Decimal("5"))

    line.set_tax_rates([tax_rate1, tax_rate2])
    invoice.recalculate()

    line.refresh_from_db()
    assert line.unit_excluding_tax_amount == Money("100.00", line.currency)
    assert line.total_tax_amount == Money("15.00", line.currency)
    assert line.total_amount == Money("115.00", line.currency)


def test_recalculate_invoice_inclusive_line_tax_overrides_invoice_tax():
    invoice = InvoiceFactory(currency="EUR", tax_behavior=InvoiceTaxBehavior.INCLUSIVE)
    line = InvoiceLineFactory(invoice=invoice, unit_amount=Decimal("110"), quantity=1, amount=Decimal("0"))
    invoice_tax_rate = TaxRateFactory(account=invoice.account, percentage=Decimal("20"))
    line_tax_rate = TaxRateFactory(account=invoice.account, percentage=Decimal("10"))

    invoice.set_tax_rates([invoice_tax_rate])
    line.set_tax_rates([line_tax_rate])
    invoice.recalculate()

    line.refresh_from_db()
    assert line.total_tax_rate == Decimal("10")
    assert line.total_tax_amount == Money("10.00", line.currency)
    assert line.total_amount == Money("110.00", line.currency)


def test_recalculate_invoice_inclusive_with_zero_tax_rate():
    invoice = InvoiceFactory(currency="EUR", tax_behavior=InvoiceTaxBehavior.INCLUSIVE)
    line = InvoiceLineFactory(invoice=invoice, unit_amount=Decimal("50"), quantity=2, amount=Decimal("0"))
    tax_rate = TaxRateFactory(account=invoice.account, percentage=Decimal("0"))

    line.set_tax_rates([tax_rate])
    invoice.recalculate()

    line.refresh_from_db()
    assert line.unit_excluding_tax_amount == Money("50.00", line.currency)
    assert line.total_tax_amount == Money("0.00", line.currency)
    assert line.total_amount == Money("100.00", line.currency)


def test_recalculate_invoice_inclusive_with_zero_base_amount():
    invoice = InvoiceFactory(currency="EUR", tax_behavior=InvoiceTaxBehavior.INCLUSIVE)
    line = InvoiceLineFactory(invoice=invoice, unit_amount=Decimal("0"), quantity=1, amount=Decimal("0"))
    tax_rate = TaxRateFactory(account=invoice.account, percentage=Decimal("20"))

    line.set_tax_rates([tax_rate])
    invoice.recalculate()

    line.refresh_from_db()
    assert line.unit_excluding_tax_amount == Money("0.00", line.currency)
    assert line.total_tax_amount == Money("0.00", line.currency)
    assert line.total_amount == Money("0.00", line.currency)


def test_apply_line_discounts_sequential_percentages():
    invoice = InvoiceFactory(tax_behavior=InvoiceTaxBehavior.EXCLUSIVE)
    line = InvoiceLineFactory(invoice=invoice, unit_amount=Decimal("100"), quantity=1, amount=Decimal("0"))
    coupon_1 = CouponFactory(account=line.invoice.account, currency=line.currency, percentage=Decimal("50"))
    coupon_2 = CouponFactory(account=line.invoice.account, currency=line.currency, percentage=Decimal("50"))

    line.set_coupons([coupon_1, coupon_2])
    invoice.recalculate()

    line.refresh_from_db()
    assert line.total_discount_amount == Money("75.00", line.currency)
    assert line.total_excluding_tax_amount == Money("25.00", line.currency)
    assert line.discount_allocations.count() == 2
    assert line.discount_allocations.get(coupon=coupon_1).amount == Money("50.00", line.currency)
    assert line.discount_allocations.get(coupon=coupon_2).amount == Money("25.00", line.currency)


def test_apply_line_taxes_zero_taxable():
    invoice = InvoiceFactory(tax_behavior=InvoiceTaxBehavior.EXCLUSIVE)
    line = InvoiceLineFactory(invoice=invoice, unit_amount=Decimal("0"), quantity=1, amount=Decimal("0"))
    tax_rate = TaxRateFactory(account=line.invoice.account, percentage=Decimal("20"))

    line.set_tax_rates([tax_rate])
    invoice.recalculate()

    line.refresh_from_db()
    assert line.total_tax_amount == Money("0.00", line.currency)
    assert line.total_tax_rate == Decimal("20")
    assert line.tax_allocations.count() == 0


def test_recalculate_invoice_line_no_discounts_no_taxes():
    invoice = InvoiceFactory(tax_behavior=InvoiceTaxBehavior.EXCLUSIVE)
    line = InvoiceLineFactory(invoice=invoice, unit_amount=Decimal("20"), quantity=2, amount=Decimal("0"))

    invoice.recalculate()

    line.refresh_from_db()
    assert line.amount == Money("40.00", line.currency)
    assert line.total_discount_amount == Money("0.00", line.currency)
    assert line.total_taxable_amount == Money("40.00", line.currency)
    assert line.total_excluding_tax_amount == Money("40.00", line.currency)
    assert line.total_tax_amount == Money("0.00", line.currency)
    assert line.total_tax_rate == Decimal("0")
    assert line.total_amount == Money("40.00", line.currency)

    invoice.refresh_from_db()
    assert invoice.subtotal_amount == Money("40.00", line.currency)
    assert invoice.total_discount_amount == Money("0.00", line.currency)
    assert invoice.total_excluding_tax_amount == Money("40.00", line.currency)
    assert invoice.total_tax_amount == Money("0.00", line.currency)
    assert invoice.total_amount == Money("40.00", line.currency)


def test_recalculate_invoice_line_with_discounts_and_taxes():
    invoice = InvoiceFactory(tax_behavior=InvoiceTaxBehavior.EXCLUSIVE)
    line = InvoiceLineFactory(invoice=invoice, unit_amount=Decimal("100"), quantity=1, amount=Decimal("0"))
    percent_coupon = CouponFactory(
        account=invoice.account, currency=line.currency, amount=None, percentage=Decimal("10")
    )
    amount_coupon = CouponFactory(
        account=invoice.account, currency=line.currency, amount=Money(20, line.currency), percentage=None
    )
    tax_rate = TaxRateFactory(account=invoice.account, percentage=Decimal("20"))

    line.set_coupons([percent_coupon, amount_coupon])
    line.set_tax_rates([tax_rate])
    invoice.recalculate()

    assert line.discount_allocations.count() == 2
    assert line.discount_allocations.get(coupon=percent_coupon).amount == Money("10.00", line.currency)
    assert line.discount_allocations.get(coupon=amount_coupon).amount == Money("20.00", line.currency)

    line.refresh_from_db()
    assert line.amount == Money("100.00", line.currency)
    assert line.subtotal_amount == Money("70.00", line.currency)
    assert line.total_discount_amount == Money("30.00", line.currency)
    assert line.total_taxable_amount == Money("70.00", line.currency)
    assert line.total_excluding_tax_amount == Money("70.00", line.currency)
    assert line.total_tax_amount == Money("14.00", line.currency)
    assert line.total_tax_rate == Decimal("20.00")
    assert line.total_amount == Money("84.00", line.currency)

    invoice.refresh_from_db()
    assert invoice.subtotal_amount == Money("70.00", line.currency)
    assert invoice.total_discount_amount == Money("30.00", line.currency)
    assert invoice.total_excluding_tax_amount == Money("70.00", line.currency)
    assert invoice.total_tax_amount == Money("14.00", line.currency)
    assert invoice.total_amount == Money("84.00", line.currency)


def test_recalculate_invoice_line_discount_exceeds_amount():
    invoice = InvoiceFactory(tax_behavior=InvoiceTaxBehavior.EXCLUSIVE)
    line = InvoiceLineFactory(invoice=invoice, unit_amount=Decimal("50"), quantity=1, amount=Decimal("0"))
    big_coupon_1 = CouponFactory(
        account=invoice.account, currency=line.currency, amount=Money(60, line.currency), percentage=None
    )
    big_coupon_2 = CouponFactory(
        account=invoice.account, currency=line.currency, amount=Money(60, line.currency), percentage=None
    )

    line.set_coupons([big_coupon_1, big_coupon_2])
    invoice.recalculate()

    assert line.discount_allocations.count() == 1
    assert line.discount_allocations.get(coupon=big_coupon_1).amount == Money("50.00", line.currency)

    line.refresh_from_db()
    assert line.amount == Money("50.00", line.currency)
    assert line.total_discount_amount == Money("50.00", line.currency)
    assert line.total_taxable_amount == Money("0.00", line.currency)
    assert line.total_excluding_tax_amount == Money("0.00", line.currency)
    assert line.total_tax_amount == Money("0.00", line.currency)
    assert line.total_amount == Money("0.00", line.currency)

    invoice.refresh_from_db()
    assert invoice.subtotal_amount == Money("0.00", line.currency)
    assert invoice.total_discount_amount == Money("50.00", line.currency)
    assert invoice.total_excluding_tax_amount == Money("0.00", line.currency)
    assert invoice.total_tax_amount == Money("0.00", line.currency)
    assert invoice.total_amount == Money("0.00", line.currency)


def test_recalculate_invoice_line_partial_second_discount():
    invoice = InvoiceFactory(tax_behavior=InvoiceTaxBehavior.EXCLUSIVE)
    line = InvoiceLineFactory(invoice=invoice, unit_amount=Decimal("25"), quantity=1, amount=Decimal("0"))
    first_coupon = CouponFactory(
        account=invoice.account, currency=line.currency, amount=Money(10, line.currency), percentage=None
    )
    second_coupon = CouponFactory(
        account=invoice.account,
        currency=line.currency,
        amount=Money(20, line.currency),
        percentage=None,
    )

    line.set_coupons(coupons=[first_coupon, second_coupon])
    invoice.recalculate()

    line.refresh_from_db()
    assert line.discount_allocations.count() == 2
    assert line.discount_allocations.get(coupon=first_coupon).amount == Money("10.00", line.currency)
    assert line.discount_allocations.get(coupon=second_coupon).amount == Money("15.00", line.currency)

    invoice.refresh_from_db()
    assert invoice.total_discount_amount == Money("25.00", line.currency)
    assert invoice.total_amount == Money("0.00", line.currency)


def test_recalculate_invoice_line_rounding():
    invoice = InvoiceFactory(tax_behavior=InvoiceTaxBehavior.EXCLUSIVE)
    line = InvoiceLineFactory(invoice=invoice, unit_amount=Decimal("100"), quantity=1, amount=Decimal("0"))
    percent_coupon = CouponFactory(
        account=invoice.account,
        currency=line.currency,
        percentage=Decimal("33.3333"),
    )
    tax_rate = TaxRateFactory(account=invoice.account, percentage=Decimal("10"))

    line.set_coupons([percent_coupon])
    line.set_tax_rates([tax_rate])
    invoice.recalculate()

    line.refresh_from_db()
    assert line.discount_allocations.get(coupon=percent_coupon).amount == Money("33.33", line.currency)
    assert line.tax_allocations.get(tax_rate=tax_rate).amount == Money("6.67", line.currency)
    assert line.amount == Money("100.00", line.currency)
    assert line.subtotal_amount == Money("66.67", line.currency)
    assert line.total_discount_amount == Money("33.33", line.currency)
    assert line.total_taxable_amount == Money("66.67", line.currency)
    assert line.total_tax_amount == Money("6.67", line.currency)
    assert line.total_amount == Money("73.34", line.currency)

    invoice.refresh_from_db()
    assert invoice.subtotal_amount == Money("66.67", line.currency)
    assert invoice.total_discount_amount == Money("33.33", line.currency)
    assert invoice.total_excluding_tax_amount == Money("66.67", line.currency)
    assert invoice.total_tax_amount == Money("6.67", line.currency)
    assert invoice.total_amount == Money("73.34", line.currency)


def test_recalculate_invoice_line_multiple_taxes():
    invoice = InvoiceFactory(tax_behavior=InvoiceTaxBehavior.EXCLUSIVE)
    line = InvoiceLineFactory(invoice=invoice, unit_amount=Decimal("100"), quantity=1, amount=Decimal("0"))
    tax_rate1 = TaxRateFactory(account=invoice.account, percentage=Decimal("10"))
    tax_rate2 = TaxRateFactory(account=invoice.account, percentage=Decimal("5"))

    line.set_tax_rates([tax_rate1, tax_rate2])
    invoice.recalculate()

    line.refresh_from_db()
    assert line.tax_allocations.get(tax_rate=tax_rate1).amount == Money("10.00", line.currency)
    assert line.tax_allocations.get(tax_rate=tax_rate2).amount == Money("5.00", line.currency)
    assert line.total_tax_amount == Money("15.00", line.currency)
    assert line.total_amount == Money("115.00", line.currency)

    invoice.refresh_from_db()
    assert invoice.total_tax_amount == Money("15.00", line.currency)
    assert invoice.total_amount == Money("115.00", line.currency)


def test_recalculate_invoice_multiple_lines():
    invoice = InvoiceFactory(tax_behavior=InvoiceTaxBehavior.EXCLUSIVE)
    line1 = InvoiceLineFactory(invoice=invoice, unit_amount=Decimal("100"), quantity=1, amount=Decimal("0"))
    line2 = InvoiceLineFactory(invoice=invoice, unit_amount=Decimal("50"), quantity=2, amount=Decimal("0"))
    percent_coupon = CouponFactory(
        account=invoice.account, currency=invoice.currency, percentage=Decimal("10"), amount=None
    )
    tax_rate = TaxRateFactory(account=invoice.account, percentage=Decimal("20"))

    line1.set_tax_rates([tax_rate])
    line2.set_coupons([percent_coupon])
    line2.set_tax_rates([tax_rate])
    invoice.recalculate()

    line1.refresh_from_db()
    assert line1.tax_allocations.get(tax_rate=tax_rate).amount == Money("20.00", line1.currency)
    assert line1.amount == Money("100.00", line1.currency)
    assert line1.subtotal_amount == Money("100.00", line1.currency)
    assert line1.total_discount_amount == Money("0.00", line1.currency)
    assert line1.total_taxable_amount == Money("100.00", line1.currency)
    assert line1.total_excluding_tax_amount == Money("100.00", line1.currency)
    assert line1.total_tax_amount == Money("20.00", line1.currency)
    assert line1.total_amount == Money("120.00", line1.currency)

    line2.refresh_from_db()
    assert line2.discount_allocations.get(coupon=percent_coupon).amount == Money("10.00", line2.currency)
    assert line2.tax_allocations.get(tax_rate=tax_rate).amount == Money("18.00", line2.currency)
    assert line2.amount == Money("100.00", line2.currency)
    assert line2.subtotal_amount == Money("90.00", line2.currency)
    assert line2.total_discount_amount == Money("10.00", line2.currency)
    assert line2.total_taxable_amount == Money("90.00", line2.currency)
    assert line2.total_excluding_tax_amount == Money("90.00", line2.currency)
    assert line2.total_tax_amount == Money("18.00", line2.currency)
    assert line2.total_amount == Money("108.00", line2.currency)

    invoice.refresh_from_db()
    assert invoice.subtotal_amount == Money("190.00", invoice.currency)
    assert invoice.total_discount_amount == Money("10.00", invoice.currency)
    assert invoice.total_excluding_tax_amount == Money("190.00", invoice.currency)
    assert invoice.total_tax_amount == Money("38.00", invoice.currency)
    assert invoice.total_amount == Money("228.00", invoice.currency)


def test_recalculate_invoice_line_full_discount_zero_tax():
    invoice = InvoiceFactory(tax_behavior=InvoiceTaxBehavior.EXCLUSIVE)
    line = InvoiceLineFactory(invoice=invoice, unit_amount=Decimal("50"), quantity=1, amount=Decimal("0"))
    big_coupon = CouponFactory(
        account=invoice.account, currency=line.currency, amount=Money(100, line.currency), percentage=None
    )
    tax_rate = TaxRateFactory(account=invoice.account, percentage=Decimal("20"))

    line.set_coupons([big_coupon])
    line.set_tax_rates([tax_rate])
    invoice.recalculate()

    line.refresh_from_db()
    assert line.discount_allocations.get(coupon=big_coupon).amount == Money("50.00", line.currency)
    assert line.tax_allocations.count() == 0
    assert line.amount == Money("50.00", line.currency)
    assert line.total_discount_amount == Money("50.00", line.currency)
    assert line.total_taxable_amount == Money("0.00", line.currency)
    assert line.total_excluding_tax_amount == Money("0.00", line.currency)
    assert line.total_tax_amount == Money("0.00", line.currency)
    assert line.total_amount == Money("0.00", line.currency)

    invoice.refresh_from_db()
    assert invoice.subtotal_amount == Money("0.00", invoice.currency)
    assert invoice.total_discount_amount == Money("50.00", invoice.currency)
    assert invoice.total_excluding_tax_amount == Money("0.00", line.currency)
    assert invoice.total_tax_amount == Money("0.00", line.currency)
    assert invoice.total_amount == Money("0.00", line.currency)


def test_recalculate_invoice_line_multiple_percentage_discounts():
    invoice = InvoiceFactory(tax_behavior=InvoiceTaxBehavior.EXCLUSIVE)
    line = InvoiceLineFactory(invoice=invoice, unit_amount=Decimal("100"), quantity=1, amount=Decimal("0"))
    first = CouponFactory(account=invoice.account, currency=line.currency, percentage=Decimal("10"), amount=None)
    second = CouponFactory(account=invoice.account, currency=line.currency, percentage=Decimal("20"), amount=None)

    line.set_coupons([first, second])
    invoice.recalculate()

    line.refresh_from_db()
    assert line.discount_allocations.count() == 2
    assert line.discount_allocations.get(coupon=first).amount == Money("10.00", line.currency)
    assert line.discount_allocations.get(coupon=second).amount == Money("18.00", line.currency)
    assert line.amount == Money("100.00", line.currency)
    assert line.total_discount_amount == Money("28.00", line.currency)
    assert line.total_taxable_amount == Money("72.00", line.currency)
    assert line.total_excluding_tax_amount == Money("72.00", line.currency)
    assert line.total_amount == Money("72.00", line.currency)

    invoice.refresh_from_db()
    assert invoice.subtotal_amount == Money("72.00", line.currency)
    assert invoice.total_discount_amount == Money("28.00", line.currency)
    assert invoice.total_excluding_tax_amount == Money("72.00", line.currency)
    assert invoice.total_amount == Money("72.00", line.currency)


def test_recalculate_invoice_line_clamps_large_amount():
    invoice = InvoiceFactory(tax_behavior=InvoiceTaxBehavior.EXCLUSIVE)
    line = InvoiceLineFactory(
        invoice=invoice, unit_amount=Decimal("10000000000000000"), quantity=1000000000000, amount=Decimal("0")
    )

    invoice.recalculate()

    line.refresh_from_db()
    assert line.amount == Money(MAX_AMOUNT, line.currency)

    invoice.refresh_from_db()
    assert invoice.total_amount == Money(MAX_AMOUNT, line.currency)


def test_apply_line_discounts_exceeding_base():
    invoice = InvoiceFactory(tax_behavior=InvoiceTaxBehavior.EXCLUSIVE)
    line = InvoiceLineFactory(invoice=invoice, unit_amount=Decimal("50"), quantity=1, amount=Decimal("0"))
    big_coupon = CouponFactory(
        account=invoice.account,
        currency=line.currency,
        amount=Money(80, line.currency),
        percentage=None,
    )

    line.set_coupons([big_coupon])
    invoice.recalculate()

    line.refresh_from_db()
    assert line.discount_allocations.count() == 1
    assert line.discount_allocations.get(coupon=big_coupon).amount == Money("50.00", line.currency)
    assert line.amount == Money("50.00", line.currency)
    assert line.total_discount_amount == Money("50.00", line.currency)
    assert line.total_taxable_amount == Money("0.00", line.currency)
    assert line.total_excluding_tax_amount == Money("0.00", line.currency)


def test_apply_line_taxes_multiple_rates():
    invoice = InvoiceFactory(tax_behavior=InvoiceTaxBehavior.EXCLUSIVE)
    line = InvoiceLineFactory(invoice=invoice, unit_amount=Decimal("100"), quantity=1, amount=Decimal("0"))
    tax_rate1 = TaxRateFactory(account=invoice.account, percentage=Decimal("10"))
    tax_rate2 = TaxRateFactory(account=invoice.account, percentage=Decimal("5"))

    line.set_tax_rates([tax_rate1, tax_rate2])
    invoice.recalculate()

    line.refresh_from_db()
    assert line.tax_allocations.count() == 2
    assert line.tax_allocations.get(tax_rate=tax_rate1).amount == Money("10.00", line.currency)
    assert line.tax_allocations.get(tax_rate=tax_rate2).amount == Money("5.00", line.currency)
    assert line.total_tax_amount == Money("15.00", line.currency)
    assert line.total_tax_rate == Decimal("15")
    assert line.total_amount == Money("115.00", line.currency)

    invoice.refresh_from_db()
    assert invoice.total_tax_amount == Money("15.00", line.currency)
    assert invoice.total_amount == Money("115.00", line.currency)


def test_recalculate_invoice_line_zero_quantity():
    invoice = InvoiceFactory(tax_behavior=InvoiceTaxBehavior.EXCLUSIVE)
    line = InvoiceLineFactory(invoice=invoice, unit_amount=Decimal("100"), quantity=0, amount=Decimal("0"))
    coupon = CouponFactory(
        account=invoice.account,
        currency=line.currency,
        amount=Money(10, line.currency),
        percentage=None,
    )
    tax_rate = TaxRateFactory(account=line.invoice.account, percentage=Decimal("20"))

    line.set_coupons([coupon])
    line.set_tax_rates([tax_rate])
    invoice.recalculate()

    line.refresh_from_db()
    assert line.discount_allocations.count() == 0
    assert line.tax_allocations.count() == 0
    assert line.amount == Money("0.00", line.currency)
    assert line.total_taxable_amount == Money("0.00", line.currency)
    assert line.total_discount_amount == Money("0.00", line.currency)
    assert line.total_excluding_tax_amount == Money("0.00", line.currency)
    assert line.total_tax_amount == Money("0.00", line.currency)
    assert line.total_amount == Money("0.00", line.currency)

    invoice.refresh_from_db()
    assert invoice.total_discount_amount == Money("0.00", line.currency)
    assert invoice.total_tax_amount == Money("0.00", line.currency)
    assert invoice.total_amount == Money("0.00", line.currency)


def test_recalculate_invoice_with_invoice_discount_and_tax():
    invoice = InvoiceFactory(tax_behavior=InvoiceTaxBehavior.EXCLUSIVE)
    line = InvoiceLineFactory(
        invoice=invoice,
        quantity=1,
        unit_amount=Decimal("100"),
        amount=Decimal("100"),
    )
    coupon = CouponFactory(account=invoice.account, currency=invoice.currency, amount=None, percentage=Decimal("10"))
    tax_rate = TaxRateFactory(account=invoice.account, percentage=Decimal("20"))

    invoice.set_coupons([coupon])
    invoice.set_tax_rates([tax_rate])
    invoice.recalculate()

    line.refresh_from_db()
    assert line.discount_allocations.count() == 1
    assert line.discount_allocations.get(coupon=coupon).amount == Money("10.00", line.currency)
    assert line.tax_allocations.count() == 1
    assert line.tax_allocations.get(tax_rate=tax_rate).amount == Money("18.00", line.currency)
    assert line.amount == Money("100.00", line.currency)
    assert line.subtotal_amount == Money("100.00", line.currency)
    assert line.total_discount_amount == Money("10.00", line.currency)
    assert line.total_taxable_amount == Money("90.00", line.currency)
    assert line.total_excluding_tax_amount == Money("90.00", line.currency)
    assert line.total_tax_amount == Money("18.00", line.currency)
    assert line.total_amount == Money("108.00", line.currency)

    invoice.refresh_from_db()
    assert invoice.subtotal_amount == Money("100.00", invoice.currency)
    assert invoice.total_discount_amount == Money("10.00", invoice.currency)
    assert invoice.total_excluding_tax_amount == Money("90.00", invoice.currency)
    assert invoice.total_tax_amount == Money("18.00", invoice.currency)
    assert invoice.total_amount == Money("108.00", invoice.currency)


def test_apply_invoice_discounts_sequential_and_amount():
    invoice = InvoiceFactory(tax_behavior=InvoiceTaxBehavior.EXCLUSIVE)
    line = InvoiceLineFactory(invoice=invoice, unit_amount=Decimal("100"), quantity=1, amount=Decimal("0"))
    percent_coupon = CouponFactory(
        account=invoice.account, currency=invoice.currency, amount=None, percentage=Decimal("10")
    )
    amount_coupon = CouponFactory(
        account=invoice.account, currency=invoice.currency, amount=Money(15, invoice.currency), percentage=None
    )

    invoice.set_coupons([percent_coupon, amount_coupon])
    invoice.recalculate()

    line.refresh_from_db()
    assert line.discount_allocations.count() == 2
    assert line.discount_allocations.get(coupon=percent_coupon).amount == Money("10.00", line.currency)
    assert line.discount_allocations.get(coupon=amount_coupon).amount == Money("15.00", line.currency)
    assert line.amount == Money("100.00", line.currency)
    assert line.total_discount_amount == Money("25.00", line.currency)
    assert line.total_taxable_amount == Money("75.00", line.currency)
    assert line.total_excluding_tax_amount == Money("75.00", line.currency)
    assert line.total_tax_amount == Money("0.00", line.currency)
    assert line.total_amount == Money("75.00", line.currency)

    invoice.refresh_from_db()
    assert invoice.subtotal_amount == Money("100.00", line.currency)
    assert invoice.total_discount_amount == Money("25.00", line.currency)
    assert invoice.total_excluding_tax_amount == Money("75.00", invoice.currency)
    assert invoice.total_tax_amount == Money("0.00", line.currency)
    assert invoice.total_amount == Money("75.00", line.currency)


def test_apply_invoice_discounts_exceeding_base():
    invoice = InvoiceFactory(tax_behavior=InvoiceTaxBehavior.EXCLUSIVE)
    line = InvoiceLineFactory(invoice=invoice, unit_amount=Decimal("100"), quantity=1, amount=Decimal("0"))
    big_coupon = CouponFactory(
        account=invoice.account, currency=invoice.currency, amount=Money(80, invoice.currency), percentage=None
    )
    extra_coupon = CouponFactory(
        account=invoice.account, currency=invoice.currency, amount=Money(50, invoice.currency), percentage=None
    )

    invoice.set_coupons([big_coupon, extra_coupon])
    invoice.recalculate()

    line.refresh_from_db()
    assert line.discount_allocations.count() == 2
    assert line.discount_allocations.get(coupon=big_coupon).amount == Money("80.00", line.currency)
    assert line.discount_allocations.get(coupon=extra_coupon).amount == Money("20.00", line.currency)
    assert line.amount == Money("100.00", line.currency)
    assert line.total_discount_amount == Money("100.00", line.currency)
    assert line.total_taxable_amount == Money("0.00", line.currency)
    assert line.total_excluding_tax_amount == Money("0.00", line.currency)
    assert line.total_tax_amount == Money("0.00", line.currency)
    assert line.total_amount == Money("0.00", line.currency)

    invoice.refresh_from_db()
    assert invoice.subtotal_amount == Money("100.00", invoice.currency)
    assert invoice.total_discount_amount == Money("100.00", invoice.currency)
    assert invoice.total_excluding_tax_amount == Money("0.00", invoice.currency)
    assert invoice.total_tax_amount == Money("0.00", invoice.currency)
    assert invoice.total_amount == Money("0.00", invoice.currency)


def test_apply_invoice_taxes_multiple_rates():
    invoice = InvoiceFactory(tax_behavior=InvoiceTaxBehavior.EXCLUSIVE)
    line = InvoiceLineFactory(invoice=invoice, unit_amount=Decimal("100"), quantity=1, amount=Decimal("0"))
    tax_rate1 = TaxRateFactory(account=invoice.account, percentage=Decimal("10"))
    tax_rate2 = TaxRateFactory(account=invoice.account, percentage=Decimal("5"))

    invoice.set_tax_rates([tax_rate1, tax_rate2])
    invoice.recalculate()

    line.refresh_from_db()
    assert line.tax_allocations.count() == 2
    assert line.tax_allocations.get(tax_rate=tax_rate1).amount == Money("10.00", line.currency)
    assert line.tax_allocations.get(tax_rate=tax_rate2).amount == Money("5.00", line.currency)
    assert line.amount == Money("100.00", line.currency)
    assert line.subtotal_amount == Money("100.00", line.currency)
    assert line.total_taxable_amount == Money("100.00", line.currency)
    assert line.total_excluding_tax_amount == Money("100.00", line.currency)
    assert line.total_tax_amount == Money("15.00", line.currency)
    assert line.total_amount == Money("115.00", line.currency)

    invoice.refresh_from_db()
    assert invoice.subtotal_amount == Money("100.00", line.currency)
    assert invoice.total_excluding_tax_amount == Money("100.00", invoice.currency)
    assert invoice.total_tax_amount == Money("15.00", invoice.currency)
    assert invoice.total_amount == Money("115.00", invoice.currency)


def test_apply_invoice_taxes_zero_taxable():
    invoice = InvoiceFactory(tax_behavior=InvoiceTaxBehavior.EXCLUSIVE)
    tax_rate = TaxRateFactory(account=invoice.account, percentage=Decimal("20"))

    invoice.set_tax_rates([tax_rate])
    invoice.recalculate()

    invoice.refresh_from_db()
    assert invoice.total_tax_amount == Money("0.00", invoice.currency)


def test_recalculate_invoice_multiple_invoice_discounts_and_taxes():
    invoice = InvoiceFactory(tax_behavior=InvoiceTaxBehavior.EXCLUSIVE)
    line1 = InvoiceLineFactory(invoice=invoice, unit_amount=Decimal("100"), quantity=2, amount=Decimal("0"))
    line2 = InvoiceLineFactory(invoice=invoice, unit_amount=Decimal("50"), quantity=1, amount=Decimal("0"))
    percent_coupon = CouponFactory(
        account=invoice.account, currency=invoice.currency, amount=None, percentage=Decimal("10")
    )
    amount_coupon = CouponFactory(
        account=invoice.account, currency=invoice.currency, amount=Money(30, invoice.currency), percentage=None
    )
    tax_rate1 = TaxRateFactory(account=invoice.account, percentage=Decimal("20"))
    tax_rate2 = TaxRateFactory(account=invoice.account, percentage=Decimal("5"))

    invoice.set_coupons([percent_coupon, amount_coupon])
    invoice.set_tax_rates([tax_rate1, tax_rate2])
    invoice.recalculate()

    line1.refresh_from_db()
    assert line1.discount_allocations.get(coupon=percent_coupon).amount == Money("20.00", line1.currency)
    assert line1.discount_allocations.get(coupon=amount_coupon).amount == Money("24.00", line1.currency)
    assert line1.tax_allocations.get(tax_rate=tax_rate1).amount == Money("31.20", line1.currency)
    assert line1.tax_allocations.get(tax_rate=tax_rate2).amount == Money("7.80", line1.currency)
    assert line1.amount == Money("200.00", line1.currency)
    assert line1.subtotal_amount == Money("200.00", line1.currency)
    assert line1.total_discount_amount == Money("44.00", line1.currency)
    assert line1.total_taxable_amount == Money("156.00", line1.currency)
    assert line1.total_excluding_tax_amount == Money("156.00", line1.currency)
    assert line1.total_tax_amount == Money("39.00", line1.currency)
    assert line1.total_amount == Money("195.00", line1.currency)

    line2.refresh_from_db()
    assert line2.discount_allocations.get(coupon=percent_coupon).amount == Money("5.00", line2.currency)
    assert line2.discount_allocations.get(coupon=amount_coupon).amount == Money("6.00", line2.currency)
    assert line2.tax_allocations.get(tax_rate=tax_rate1).amount == Money("7.8", line2.currency)
    assert line2.tax_allocations.get(tax_rate=tax_rate2).amount == Money("1.95", line2.currency)
    assert line2.amount == Money("50.00", line2.currency)
    assert line2.subtotal_amount == Money("50.00", line2.currency)
    assert line2.total_discount_amount == Money("11.00", line2.currency)
    assert line2.total_taxable_amount == Money("39.00", line2.currency)
    assert line2.total_excluding_tax_amount == Money("39.00", line2.currency)
    assert line2.total_tax_amount == Money("9.75", line2.currency)
    assert line2.total_amount == Money("48.75", line2.currency)

    invoice.refresh_from_db()
    assert invoice.subtotal_amount == Money("250.00", invoice.currency)
    assert invoice.total_discount_amount == Money("55.00", invoice.currency)
    assert invoice.total_excluding_tax_amount == Money("195.00", invoice.currency)
    assert invoice.total_tax_amount == Money("48.75", invoice.currency)
    assert invoice.total_amount == Money("243.75", invoice.currency)


def test_recalculate_invoice_invoice_discount_exceeds_subtotal():
    invoice = InvoiceFactory(tax_behavior=InvoiceTaxBehavior.EXCLUSIVE)
    line = InvoiceLineFactory(invoice=invoice, unit_amount=Decimal("40"), quantity=1, amount=Decimal("0"))
    big_coupon = CouponFactory(
        account=invoice.account, currency=invoice.currency, amount=Money(100, invoice.currency), percentage=None
    )
    tax_rate = TaxRateFactory(account=invoice.account, percentage=Decimal("10"))

    invoice.set_coupons([big_coupon])
    invoice.set_tax_rates([tax_rate])
    invoice.recalculate()

    line.refresh_from_db()
    assert line.discount_allocations.get(coupon=big_coupon).amount == Money("40.00", line.currency)
    assert line.tax_allocations.count() == 0
    assert line.amount == Money("40.00", line.currency)
    assert line.subtotal_amount == Money("40.00", line.currency)
    assert line.total_discount_amount == Money("40.00", line.currency)
    assert line.total_taxable_amount == Money("0.00", line.currency)
    assert line.total_excluding_tax_amount == Money("0.00", line.currency)
    assert line.total_tax_amount == Money("0.00", line.currency)
    assert line.total_amount == Money("0.00", line.currency)

    invoice.refresh_from_db()
    assert invoice.subtotal_amount == Money("40.00", invoice.currency)
    assert invoice.total_discount_amount == Money("40.00", invoice.currency)
    assert invoice.total_excluding_tax_amount == Money("0.00", invoice.currency)
    assert invoice.total_tax_amount == Money("0.00", invoice.currency)
    assert invoice.total_amount == Money("0.00", invoice.currency)


def test_recalculate_invoice_with_line_and_invoice_discounts_and_taxes():
    invoice = InvoiceFactory(tax_behavior=InvoiceTaxBehavior.EXCLUSIVE)
    line = InvoiceLineFactory(invoice=invoice, unit_amount=Decimal("100"), quantity=1, amount=Decimal("0"))
    percent_coupon_line = CouponFactory(
        account=invoice.account, currency=invoice.currency, amount=None, percentage=Decimal("10")
    )
    tax_rate_line = TaxRateFactory(account=invoice.account, percentage=Decimal("10"))
    coupon_inv = CouponFactory(
        account=invoice.account, currency=invoice.currency, amount=Money(5, invoice.currency), percentage=None
    )
    tax_rate_inv = TaxRateFactory(account=invoice.account, percentage=Decimal("5"))

    line.set_coupons([percent_coupon_line])
    line.set_tax_rates([tax_rate_line])
    invoice.set_coupons([coupon_inv])
    invoice.set_tax_rates([tax_rate_inv])
    invoice.recalculate()

    line.refresh_from_db()
    assert line.discount_allocations.get(coupon=percent_coupon_line).amount == Money("10.00", line.currency)
    assert line.tax_allocations.get(tax_rate=tax_rate_line).amount == Money("9.00", line.currency)
    assert line.amount == Money("100.00", line.currency)
    assert line.subtotal_amount == Money("90.00", line.currency)
    assert line.total_discount_amount == Money("10.00", line.currency)
    assert line.total_taxable_amount == Money("90.00", line.currency)
    assert line.total_excluding_tax_amount == Money("90.00", line.currency)
    assert line.total_tax_amount == Money("9.00", line.currency)
    assert line.total_amount == Money("99.00", line.currency)

    invoice.refresh_from_db()
    assert invoice.subtotal_amount == Money("90.00", invoice.currency)
    assert invoice.total_discount_amount == Money("10.00", invoice.currency)
    assert invoice.total_excluding_tax_amount == Money("90.00", invoice.currency)
    assert invoice.total_tax_amount == Money("9.00", invoice.currency)
    assert invoice.total_amount == Money("99.00", invoice.currency)


def test_recalculate_invoice_line_discount_and_invoice_tax():
    invoice = InvoiceFactory(tax_behavior=InvoiceTaxBehavior.EXCLUSIVE)
    line = InvoiceLineFactory(invoice=invoice, unit_amount=Decimal("100"), quantity=1, amount=Decimal("0"))
    coupon = CouponFactory(account=invoice.account, currency=invoice.currency, amount=None, percentage=Decimal("10"))
    tax_rate = TaxRateFactory(account=invoice.account, percentage=Decimal("20"))

    line.set_coupons([coupon])
    invoice.set_tax_rates([tax_rate])
    invoice.recalculate()

    line.refresh_from_db()
    assert line.discount_allocations.get(coupon=coupon).amount == Money("10.00", line.currency)
    assert line.tax_allocations.get(tax_rate=tax_rate).amount == Money("18.00", line.currency)
    assert line.amount == Money("100.00", line.currency)
    assert line.subtotal_amount == Money("90.00", line.currency)
    assert line.total_discount_amount == Money("10.00", line.currency)
    assert line.total_taxable_amount == Money("90.00", line.currency)
    assert line.total_excluding_tax_amount == Money("90.00", line.currency)
    assert line.total_tax_amount == Money("18.00", line.currency)
    assert line.total_amount == Money("108.00", line.currency)

    invoice.refresh_from_db()
    assert invoice.subtotal_amount == Money("90.00", invoice.currency)
    assert invoice.total_discount_amount == Money("10.00", invoice.currency)
    assert invoice.total_excluding_tax_amount == Money("90.00", invoice.currency)
    assert invoice.total_tax_amount == Money("18.00", invoice.currency)
    assert invoice.total_amount == Money("108.00", invoice.currency)


def test_recalculate_invoice_line_tax_and_invoice_discount():
    invoice = InvoiceFactory(tax_behavior=InvoiceTaxBehavior.EXCLUSIVE)
    line = InvoiceLineFactory(invoice=invoice, unit_amount=Decimal("100"), quantity=1, amount=Decimal("0"))
    tax_rate = TaxRateFactory(account=invoice.account, percentage=Decimal("20"))
    coupon = CouponFactory(account=invoice.account, currency=invoice.currency, amount=None, percentage=Decimal("10"))

    line.set_tax_rates([tax_rate])
    invoice.set_coupons([coupon])
    invoice.recalculate()

    line.refresh_from_db()
    assert line.tax_allocations.get(tax_rate=tax_rate).amount == Money("18.00", line.currency)
    assert line.discount_allocations.get(coupon=coupon).amount == Money("10.00", line.currency)
    assert line.amount == Money("100.00", line.currency)
    assert line.subtotal_amount == Money("100.00", line.currency)
    assert line.total_discount_amount == Money("10.00", line.currency)
    assert line.total_taxable_amount == Money("90.00", line.currency)
    assert line.total_excluding_tax_amount == Money("90.00", line.currency)
    assert line.total_tax_amount == Money("18.00", line.currency)
    assert line.total_amount == Money("108.00", line.currency)

    invoice.refresh_from_db()
    assert invoice.subtotal_amount == Money("100.00", invoice.currency)
    assert invoice.total_discount_amount == Money("10.00", invoice.currency)
    assert invoice.total_excluding_tax_amount == Money("90.00", invoice.currency)
    assert invoice.total_tax_amount == Money("18.00", invoice.currency)
    assert invoice.total_amount == Money("108.00", invoice.currency)


def test_recalculate_invoice_mixed_line_and_invoice_coupons_and_taxes():
    invoice = InvoiceFactory(tax_behavior=InvoiceTaxBehavior.EXCLUSIVE)
    line_with_discount = InvoiceLineFactory(
        invoice=invoice, unit_amount=Decimal("100"), quantity=1, amount=Decimal("0")
    )
    line_with_tax = InvoiceLineFactory(
        invoice=invoice,
        unit_amount=Decimal("100"),
        quantity=1,
        amount=Decimal("0"),
    )
    coupon_line = CouponFactory(
        account=invoice.account, currency=invoice.currency, amount=None, percentage=Decimal("10")
    )
    tax_rate_line = TaxRateFactory(account=invoice.account, percentage=Decimal("10"))
    coupon_inv = CouponFactory(
        account=invoice.account, currency=invoice.currency, amount=Money(10, invoice.currency), percentage=None
    )
    tax_rate_inv = TaxRateFactory(account=invoice.account, percentage=Decimal("5"))

    line_with_discount.set_coupons([coupon_line])
    line_with_tax.set_tax_rates([tax_rate_line])
    invoice.set_coupons([coupon_inv])
    invoice.set_tax_rates([tax_rate_inv])
    invoice.recalculate()

    line_with_discount.refresh_from_db()
    assert line_with_discount.discount_allocations.get(coupon=coupon_line).amount == Money(
        "10.00", line_with_discount.currency
    )
    assert line_with_discount.tax_allocations.get(tax_rate=tax_rate_inv).amount == Money(
        "4.50", line_with_discount.currency
    )
    assert line_with_discount.amount == Money("100.00", line_with_discount.currency)
    assert line_with_discount.subtotal_amount == Money("90.00", line_with_discount.currency)
    assert line_with_discount.total_discount_amount == Money("10.00", line_with_discount.currency)
    assert line_with_discount.total_taxable_amount == Money("90.00", line_with_discount.currency)
    assert line_with_discount.total_excluding_tax_amount == Money("90.00", line_with_discount.currency)
    assert line_with_discount.total_tax_amount == Money("4.50", line_with_discount.currency)
    assert line_with_discount.total_amount == Money("94.50", line_with_discount.currency)

    line_with_tax.refresh_from_db()
    assert line_with_tax.discount_allocations.get(coupon=coupon_inv).amount == Money("10.00", line_with_tax.currency)
    assert line_with_tax.tax_allocations.get(tax_rate=tax_rate_line).amount == Money("9.00", line_with_tax.currency)
    assert line_with_tax.amount == Money("100.00", line_with_tax.currency)
    assert line_with_tax.subtotal_amount == Money("100.00", line_with_tax.currency)
    assert line_with_tax.total_discount_amount == Money("10.00", line_with_tax.currency)
    assert line_with_tax.total_taxable_amount == Money("90.00", line_with_tax.currency)
    assert line_with_tax.total_excluding_tax_amount == Money("90.00", line_with_tax.currency)
    assert line_with_tax.total_tax_amount == Money("9.00", line_with_tax.currency)
    assert line_with_tax.total_amount == Money("99.00", line_with_tax.currency)

    invoice.refresh_from_db()
    assert invoice.subtotal_amount == Money("190.00", invoice.currency)
    assert invoice.total_discount_amount == Money("20.00", invoice.currency)
    assert invoice.total_excluding_tax_amount == Money("180.00", invoice.currency)
    assert invoice.total_tax_amount == Money("13.50", invoice.currency)
    assert invoice.total_amount == Money("193.50", invoice.currency)


def test_recalculate_invoice_automatic_invoice_taxes_exclusive():
    invoice = InvoiceFactory(currency="USD", tax_behavior=InvoiceTaxBehavior.AUTOMATIC)
    line = InvoiceLineFactory(invoice=invoice, unit_amount=Decimal("100"), quantity=1, amount=Decimal("0"))
    tax_rate = TaxRateFactory(account=invoice.account, percentage=Decimal("10"))

    invoice.set_tax_rates([tax_rate])
    invoice.recalculate()

    line.refresh_from_db()
    assert line.unit_excluding_tax_amount == Money("100.00", line.currency)
    assert line.total_tax_amount == Money("10.00", line.currency)
    assert line.total_amount == Money("110.00", line.currency)
    assert line.tax_allocations.get(tax_rate=tax_rate).source == InvoiceTaxSource.INVOICE

    invoice.refresh_from_db()
    assert invoice.total_excluding_tax_amount == Money("100.00", invoice.currency)
    assert invoice.total_tax_amount == Money("10.00", invoice.currency)
    assert invoice.total_amount == Money("110.00", invoice.currency)


def test_recalculate_invoice_automatic_invoice_taxes_inclusive():
    invoice = InvoiceFactory(currency="EUR", tax_behavior=InvoiceTaxBehavior.AUTOMATIC)
    line = InvoiceLineFactory(invoice=invoice, unit_amount=Decimal("120"), quantity=1, amount=Decimal("0"))
    tax_rate = TaxRateFactory(account=invoice.account, percentage=Decimal("20"))

    invoice.set_tax_rates([tax_rate])
    invoice.recalculate()

    line.refresh_from_db()
    assert line.unit_excluding_tax_amount == Money("100.00", line.currency)
    assert line.total_taxable_amount == Money("100.00", line.currency)
    assert line.total_tax_amount == Money("20.00", line.currency)
    assert line.total_amount == Money("120.00", line.currency)
    assert line.tax_allocations.get(tax_rate=tax_rate).source == InvoiceTaxSource.INVOICE

    invoice.refresh_from_db()
    assert invoice.total_excluding_tax_amount == Money("100.00", invoice.currency)
    assert invoice.total_tax_amount == Money("20.00", invoice.currency)
    assert invoice.total_amount == Money("120.00", invoice.currency)


def test_recalculate_invoice_inclusive_invoice_taxes():
    invoice = InvoiceFactory(currency="EUR", tax_behavior=InvoiceTaxBehavior.INCLUSIVE)
    line = InvoiceLineFactory(invoice=invoice, unit_amount=Decimal("115"), quantity=1, amount=Decimal("0"))
    tax_rate = TaxRateFactory(account=invoice.account, percentage=Decimal("15"))

    invoice.set_tax_rates([tax_rate])
    invoice.recalculate()

    line.refresh_from_db()
    assert line.unit_excluding_tax_amount == Money("100.00", line.currency)
    assert line.total_tax_amount == Money("15.00", line.currency)
    assert line.total_amount == Money("115.00", line.currency)
    assert line.tax_allocations.get(tax_rate=tax_rate).source == InvoiceTaxSource.INVOICE

    invoice.refresh_from_db()
    assert invoice.total_excluding_tax_amount == Money("100.00", invoice.currency)
    assert invoice.total_tax_amount == Money("15.00", invoice.currency)
    assert invoice.total_amount == Money("115.00", invoice.currency)


def test_recalculate_invoice_inclusive_mixed_tax_sources():
    invoice = InvoiceFactory(currency="EUR", tax_behavior=InvoiceTaxBehavior.INCLUSIVE)
    line_with_tax = InvoiceLineFactory(invoice=invoice, unit_amount=Decimal("110"), quantity=1, amount=Decimal("0"))
    line_with_invoice_tax = InvoiceLineFactory(
        invoice=invoice, unit_amount=Decimal("105"), quantity=1, amount=Decimal("0")
    )
    line_tax_rate = TaxRateFactory(account=invoice.account, percentage=Decimal("10"))
    invoice_tax_rate = TaxRateFactory(account=invoice.account, percentage=Decimal("5"))

    line_with_tax.set_tax_rates([line_tax_rate])
    invoice.set_tax_rates([invoice_tax_rate])
    invoice.recalculate()

    line_with_tax.refresh_from_db()
    assert line_with_tax.unit_excluding_tax_amount == Money("100.00", line_with_tax.currency)
    assert line_with_tax.total_tax_amount == Money("10.00", line_with_tax.currency)
    assert line_with_tax.total_amount == Money("110.00", line_with_tax.currency)
    assert line_with_tax.tax_allocations.get(tax_rate=line_tax_rate).source == InvoiceTaxSource.LINE

    line_with_invoice_tax.refresh_from_db()
    assert line_with_invoice_tax.unit_excluding_tax_amount == Money("100.00", line_with_invoice_tax.currency)
    assert line_with_invoice_tax.total_tax_amount == Money("5.00", line_with_invoice_tax.currency)
    assert line_with_invoice_tax.total_amount == Money("105.00", line_with_invoice_tax.currency)
    assert line_with_invoice_tax.tax_allocations.get(tax_rate=invoice_tax_rate).source == InvoiceTaxSource.INVOICE

    invoice.refresh_from_db()
    assert invoice.total_excluding_tax_amount == Money("200.00", invoice.currency)
    assert invoice.total_tax_amount == Money("15.00", invoice.currency)
    assert invoice.total_amount == Money("215.00", invoice.currency)


def test_recalculate_invoice_inclusive_discount_zero_tax_rate():
    invoice = InvoiceFactory(currency="EUR", tax_behavior=InvoiceTaxBehavior.INCLUSIVE)
    line = InvoiceLineFactory(invoice=invoice, unit_amount=Decimal("100"), quantity=1, amount=Decimal("0"))
    coupon = CouponFactory(account=invoice.account, currency=invoice.currency, percentage=Decimal("10"), amount=None)
    tax_rate = TaxRateFactory(account=invoice.account, percentage=Decimal("0"))

    line.set_coupons([coupon])
    line.set_tax_rates([tax_rate])
    invoice.recalculate()

    line.refresh_from_db()
    assert line.total_discount_amount == Money("10.00", line.currency)
    assert line.total_taxable_amount == Money("90.00", line.currency)
    assert line.total_tax_amount == Money("0.00", line.currency)
    assert line.total_amount == Money("90.00", line.currency)

    invoice.refresh_from_db()
    assert invoice.total_discount_amount == Money("10.00", invoice.currency)
    assert invoice.total_excluding_tax_amount == Money("90.00", invoice.currency)
    assert invoice.total_tax_amount == Money("0.00", invoice.currency)
    assert invoice.total_amount == Money("90.00", invoice.currency)


def test_recalculate_invoice_with_shipping_taxes():
    invoice = InvoiceFactory(currency="USD", tax_behavior=InvoiceTaxBehavior.EXCLUSIVE)
    line = InvoiceLineFactory(invoice=invoice, unit_amount=Decimal("100"), quantity=1, amount=Decimal("0"))
    shipping_rate = ShippingRateFactory(account=invoice.account, currency=invoice.currency, amount=Decimal("20"))
    tax_rate = TaxRateFactory(account=invoice.account, percentage=Decimal("10"))

    shipping = invoice.add_shipping(shipping_rate, tax_rates=[tax_rate])
    shipping.set_tax_rates([tax_rate])
    invoice.recalculate()

    shipping.refresh_from_db()
    assert shipping.amount == Money("20.00", shipping.currency)
    assert shipping.total_excluding_tax_amount == Money("20.00", shipping.currency)
    assert shipping.total_taxable_amount == Money("20.00", shipping.currency)
    assert shipping.tax_amount == Money("2.00", shipping.currency)
    assert shipping.total_tax_rate == Decimal("10")
    assert shipping.total_amount == Money("22.00", shipping.currency)
    assert shipping.tax_allocations.get(tax_rate=tax_rate).source == InvoiceTaxSource.SHIPPING

    line.refresh_from_db()
    assert line.total_amount == Money("100.00", line.currency)

    invoice.refresh_from_db()
    assert invoice.subtotal_amount == Money("100.00", invoice.currency)
    assert invoice.shipping_amount == Money("20.00", invoice.currency)
    assert invoice.total_excluding_tax_amount == Money("120.00", invoice.currency)
    assert invoice.total_tax_amount == Money("2.00", invoice.currency)
    assert invoice.total_amount == Money("122.00", invoice.currency)


def test_recalculate_invoice_with_shipping_taxes_inclusive_behavior():
    invoice = InvoiceFactory(currency="USD", tax_behavior=InvoiceTaxBehavior.INCLUSIVE)
    line = InvoiceLineFactory(invoice=invoice, unit_amount=Decimal("100"), quantity=1, amount=Decimal("0"))
    shipping_rate = ShippingRateFactory(account=invoice.account, currency=invoice.currency, amount=Decimal("20"))
    tax_rate = TaxRateFactory(account=invoice.account, percentage=Decimal("10"))

    shipping = invoice.add_shipping(shipping_rate, tax_rates=[tax_rate])
    shipping.set_tax_rates([tax_rate])
    invoice.recalculate()

    shipping.refresh_from_db()
    assert shipping.amount == Money("20.00", shipping.currency)
    assert shipping.total_excluding_tax_amount == Money("18.18", shipping.currency)
    assert shipping.total_taxable_amount == Money("18.18", shipping.currency)
    assert shipping.tax_amount == Money("1.82", shipping.currency)
    assert shipping.total_tax_rate == Decimal("10")
    assert shipping.total_amount == Money("20.00", shipping.currency)
    assert shipping.tax_allocations.get(tax_rate=tax_rate).source == InvoiceTaxSource.SHIPPING

    line.refresh_from_db()
    assert line.total_amount == Money("100.00", line.currency)

    invoice.refresh_from_db()
    assert invoice.subtotal_amount == Money("100.00", invoice.currency)
    assert invoice.shipping_amount == Money("20.00", invoice.currency)
    assert invoice.total_excluding_tax_amount == Money("118.18", invoice.currency)
    assert invoice.total_tax_amount == Money("1.82", invoice.currency)
    assert invoice.total_amount == Money("120.00", invoice.currency)


def test_recalculate_invoice_with_no_lines():
    invoice = InvoiceFactory(currency="USD", tax_behavior=InvoiceTaxBehavior.EXCLUSIVE)

    invoice.recalculate()

    invoice.refresh_from_db()
    assert invoice.subtotal_amount == Money("0.00", invoice.currency)
    assert invoice.total_discount_amount == Money("0.00", invoice.currency)
    assert invoice.total_excluding_tax_amount == Money("0.00", invoice.currency)
    assert invoice.total_tax_amount == Money("0.00", invoice.currency)
    assert invoice.total_amount == Money("0.00", invoice.currency)
    assert invoice.outstanding_amount == Money("0.00", invoice.currency)


def test_recalculate_invoice_clamps_total_amount_with_tax():
    invoice = InvoiceFactory(tax_behavior=InvoiceTaxBehavior.EXCLUSIVE)
    line = InvoiceLineFactory(
        invoice=invoice, unit_amount=Decimal("10000000000000000"), quantity=1000000000000, amount=Decimal("0")
    )
    tax_rate = TaxRateFactory(account=invoice.account, percentage=Decimal("100"))

    invoice.set_tax_rates([tax_rate])
    invoice.recalculate()

    line.refresh_from_db()
    assert line.amount == Money(MAX_AMOUNT, line.currency)
    assert line.total_tax_amount == Money(MAX_AMOUNT, line.currency)

    invoice.refresh_from_db()
    assert invoice.total_excluding_tax_amount == Money(MAX_AMOUNT, invoice.currency)
    assert invoice.total_tax_amount == Money(MAX_AMOUNT, invoice.currency)
    assert invoice.total_amount == Money(MAX_AMOUNT, invoice.currency)
