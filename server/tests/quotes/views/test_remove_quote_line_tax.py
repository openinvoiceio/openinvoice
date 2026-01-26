import uuid
from decimal import Decimal

import pytest

from openinvoice.quotes.choices import QuoteStatus
from openinvoice.quotes.models import QuoteTax
from tests.factories import (
    CustomerFactory,
    QuoteFactory,
    QuoteLineFactory,
    TaxRateFactory,
)

pytestmark = pytest.mark.django_db


def test_remove_quote_line_tax(api_client, user, account):
    customer = CustomerFactory(account=account)
    quote = QuoteFactory(account=account, customer=customer)
    line = QuoteLineFactory(quote=quote, unit_amount="120.00")
    tax_rate = TaxRateFactory(account=account, percentage=Decimal("5.00"))
    tax = line.add_tax(tax_rate)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/quote-lines/{line.id}/taxes/{tax.id}")

    assert response.status_code == 204
    assert QuoteTax.objects.filter(id=tax.id).exists() is False


@pytest.mark.parametrize("status", [QuoteStatus.OPEN, QuoteStatus.CANCELED, QuoteStatus.ACCEPTED])
def test_remove_quote_line_tax_requires_draft_quote_status(api_client, user, account, status):
    customer = CustomerFactory(account=account)
    quote = QuoteFactory(account=account, customer=customer, status=status, number="QT-404")
    line = QuoteLineFactory(quote=quote, unit_amount="120.00")
    tax_rate = TaxRateFactory(account=account, percentage=Decimal("5.00"))
    tax = line.add_tax(tax_rate)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/quote-lines/{line.id}/taxes/{tax.id}")

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Only draft quotes can be modified",
            }
        ],
    }


def test_remove_quote_line_tax_not_found(api_client, user, account):
    quote = QuoteFactory(account=account)
    line = QuoteLineFactory(quote=quote, unit_amount="120.00")
    tax_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/quote-lines/{line.id}/taxes/{tax_id}")

    assert response.status_code == 404
    assert response.data == {
        "type": "client_error",
        "errors": [
            {
                "attr": None,
                "code": "not_found",
                "detail": "Not found.",
            }
        ],
    }


def test_remove_quote_line_tax_requires_authentication(api_client, account):
    quote = QuoteFactory(account=account)
    line = QuoteLineFactory(quote=quote, unit_amount="120.00")
    tax_rate = TaxRateFactory(account=account, percentage=Decimal("5.00"))
    tax = line.add_tax(tax_rate)

    response = api_client.delete(f"/api/v1/quote-lines/{line.id}/taxes/{tax.id}")

    assert response.status_code == 403
    assert response.data == {
        "type": "client_error",
        "errors": [
            {
                "attr": None,
                "code": "not_authenticated",
                "detail": "Authentication credentials were not provided.",
            }
        ],
    }


def test_remove_quote_line_tax_requires_account(api_client, user):
    quote = QuoteFactory()
    line = QuoteLineFactory(quote=quote, unit_amount="120.00")
    tax_rate = TaxRateFactory(percentage=Decimal("5.00"))
    tax = line.add_tax(tax_rate)

    api_client.force_login(user)
    response = api_client.delete(f"/api/v1/quote-lines/{line.id}/taxes/{tax.id}")

    assert response.status_code == 403
    assert response.data == {
        "type": "client_error",
        "errors": [
            {
                "attr": None,
                "code": "permission_denied",
                "detail": "You do not have permission to perform this action.",
            }
        ],
    }
