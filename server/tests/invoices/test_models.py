import pytest

from openinvoice.invoices.choices import InvoiceTaxBehavior
from tests.factories import InvoiceFactory

pytestmark = pytest.mark.django_db


def test_effective_tax_behavior_automatic_exclusive_currency():
    invoice = InvoiceFactory(currency="USD", tax_behavior=InvoiceTaxBehavior.AUTOMATIC)

    assert invoice.effective_tax_behavior == InvoiceTaxBehavior.EXCLUSIVE


def test_effective_tax_behavior_automatic_inclusive_currency():
    invoice = InvoiceFactory(currency="EUR", tax_behavior=InvoiceTaxBehavior.AUTOMATIC)

    assert invoice.effective_tax_behavior == InvoiceTaxBehavior.INCLUSIVE
