import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import ANY

import pytest
from freezegun import freeze_time

from openinvoice.quotes.choices import QuoteDeliveryMethod, QuoteStatus
from tests.factories import (
    BillingProfileFactory,
    CustomerFactory,
    PriceFactory,
    QuoteFactory,
    QuoteLineFactory,
)

pytestmark = pytest.mark.django_db


@freeze_time("2024-07-10T12:34:56Z")
def test_accept_quote(api_client, user, account):
    customer = CustomerFactory(
        account=account,
        default_billing_profile=BillingProfileFactory(name="Acme Corp", currency="USD"),
    )
    price = PriceFactory(account=account, amount=Decimal("120.00"), currency="USD")

    quote = QuoteFactory(
        account=account,
        customer=customer,
        status=QuoteStatus.OPEN,
        number="QT-0001",
        currency="USD",
        issue_date=date(2024, 7, 1),
    )
    line = QuoteLineFactory(
        quote=quote,
        price=price,
        description="Consulting hours",
        quantity=2,
        unit_amount=Decimal("120.00"),
        amount=Decimal("240.00"),
        total_amount_excluding_tax=Decimal("240.00"),
        total_amount=Decimal("240.00"),
    )
    quote.recalculate()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/quotes/{quote.id}/accept")

    assert response.status_code == 200
    assert response.data == {
        "id": str(quote.id),
        "status": QuoteStatus.ACCEPTED,
        "number": "QT-0001",
        "numbering_system_id": None,
        "currency": "USD",
        "issue_date": "2024-07-01",
        "billing_profile": {
            "id": str(customer.default_billing_profile.id),
            "name": customer.default_billing_profile.name,
            "legal_name": customer.default_billing_profile.legal_name,
            "legal_number": customer.default_billing_profile.legal_number,
            "email": customer.default_billing_profile.email,
            "phone": customer.default_billing_profile.phone,
            "address": {
                "line1": customer.default_billing_profile.address.line1,
                "line2": customer.default_billing_profile.address.line2,
                "locality": customer.default_billing_profile.address.locality,
                "state": customer.default_billing_profile.address.state,
                "postal_code": customer.default_billing_profile.address.postal_code,
                "country": str(customer.default_billing_profile.address.country),
            },
            "currency": customer.default_billing_profile.currency,
            "language": customer.default_billing_profile.language,
            "net_payment_term": customer.default_billing_profile.net_payment_term,
            "invoice_numbering_system_id": customer.default_billing_profile.invoice_numbering_system_id,
            "credit_note_numbering_system_id": customer.default_billing_profile.credit_note_numbering_system_id,
            "tax_rates": [],
            "tax_ids": [],
            "created_at": ANY,
            "updated_at": ANY,
        },
        "business_profile": {
            "id": str(account.default_business_profile.id),
            "name": account.default_business_profile.name,
            "legal_name": account.default_business_profile.legal_name,
            "legal_number": account.default_business_profile.legal_number,
            "email": account.default_business_profile.email,
            "phone": account.default_business_profile.phone,
            "address": {
                "line1": account.default_business_profile.address.line1,
                "line2": account.default_business_profile.address.line2,
                "locality": account.default_business_profile.address.locality,
                "state": account.default_business_profile.address.state,
                "postal_code": account.default_business_profile.address.postal_code,
                "country": str(account.default_business_profile.address.country),
            },
            "tax_ids": [],
            "created_at": ANY,
            "updated_at": ANY,
        },
        "metadata": {},
        "custom_fields": {},
        "footer": None,
        "delivery_method": QuoteDeliveryMethod.MANUAL,
        "recipients": [],
        "subtotal_amount": "240.00",
        "total_discount_amount": "0.00",
        "total_amount_excluding_tax": "240.00",
        "total_tax_amount": "0.00",
        "total_amount": "240.00",
        "created_at": ANY,
        "updated_at": ANY,
        "opened_at": None,
        "accepted_at": "2024-07-10T12:34:56Z",
        "canceled_at": None,
        "pdf_id": None,
        "invoice_id": ANY,
        "lines": [
            {
                "id": str(line.id),
                "description": "Consulting hours",
                "quantity": 2,
                "unit_amount": "120.00",
                "price_id": str(price.id),
                "product_id": ANY,
                "amount": "240.00",
                "total_discount_amount": "0.00",
                "total_amount_excluding_tax": "240.00",
                "total_tax_amount": "0.00",
                "total_tax_rate": "0.00",
                "total_amount": "240.00",
                "discounts": [],
                "taxes": [],
            }
        ],
        "discounts": [],
        "taxes": [],
    }

    quote.refresh_from_db()
    invoice = quote.invoice
    assert invoice is not None
    assert invoice.currency == "USD"
    assert invoice.total_amount.amount == Decimal("240.00")
    assert invoice.lines.count() == 1
    invoice_line = invoice.lines.get()
    assert invoice_line.quantity == 2
    assert invoice_line.unit_amount.amount == Decimal("120.00")


def test_accept_quote_not_found(api_client, user, account):
    quote_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/quotes/{quote_id}/accept")

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


@pytest.mark.parametrize(
    "status",
    [
        QuoteStatus.DRAFT,
        QuoteStatus.CANCELED,
        QuoteStatus.ACCEPTED,
    ],
)
def test_accept_quote_requires_open_status(api_client, user, account, status):
    quote = QuoteFactory(account=account, status=status, number="QT-99")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/quotes/{quote.id}/accept")

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Only open quotes can be accepted",
            }
        ],
    }


def test_accept_quote_requires_account(api_client, user):
    quote_id = uuid.uuid4()

    api_client.force_login(user)
    response = api_client.post(f"/api/v1/quotes/{quote_id}/accept")

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


def test_accept_quote_requires_authentication(api_client):
    quote_id = uuid.uuid4()

    response = api_client.post(f"/api/v1/quotes/{quote_id}/accept")

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
