import pytest
from djmoney.money import Money

from openinvoice.prices.choices import PriceModel
from openinvoice.prices.models import Price
from tests.factories import ProductFactory

pytestmark = pytest.mark.django_db


def create_tiered_price(model: str) -> Price:
    product = ProductFactory()
    currency = product.account.default_currency
    price = Price.objects.create_price(
        amount=None,
        product=product,
        currency=currency,
        model=model,
    )
    price.add_tier(unit_amount=Money("10", currency), from_value=0, to_value=10)
    price.add_tier(unit_amount=Money("8", currency), from_value=11, to_value=None)
    return Price.objects.get(id=price.id)


def test_volume_price_calculations():
    price = create_tiered_price(PriceModel.VOLUME)

    assert price.calculate_amount(5) == Money(50, price.currency)
    assert price.calculate_amount(12) == Money(96, price.currency)
    assert price.calculate_unit_amount(12) == Money(8, price.currency)


def test_graduated_price_calculations():
    price = create_tiered_price(PriceModel.GRADUATED)

    total = price.calculate_amount(15)
    assert total == Money(142, price.currency)
    unit_amount = price.calculate_unit_amount(15)
    assert unit_amount.currency.code == price.currency
    assert unit_amount * 15 == total


def test_tiered_price_without_tiers_returns_zero():
    product = ProductFactory()
    currency = product.account.default_currency
    price = Price.objects.create_price(
        amount=None,
        product=product,
        currency=currency,
        model=PriceModel.GRADUATED,
    )

    assert price.calculate_amount(10) == Money(0, currency)
    assert price.calculate_unit_amount(10) == Money(0, currency)
