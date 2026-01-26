from datetime import date, timedelta
from unittest.mock import ANY

import pytest
from django.utils import timezone
from freezegun import freeze_time

from openinvoice.numbering_systems.choices import NumberingSystemAppliesTo
from openinvoice.quotes.choices import QuoteStatus
from openinvoice.quotes.models import Quote
from tests.factories import CustomerFactory, NumberingSystemFactory, PriceFactory, QuoteFactory, QuoteLineFactory

pytestmark = pytest.mark.django_db


@freeze_time("2025-01-15T10:00:00Z")
def test_list_quotes(api_client, user, account):
    customer = CustomerFactory(account=account)
    quote_1 = QuoteFactory(account=account, customer=customer, number="QT-2025-0001", currency="USD")
    quote_2 = QuoteFactory(
        account=account,
        customer=customer,
        number="QT-2025-0002",
        currency="USD",
        status=QuoteStatus.DRAFT,
        issue_date=date(2025, 1, 11),
        metadata={"channel": "direct"},
        custom_fields={"po_number": "PO-456"},
        footer="Warm regards",
        description="February retainer",
    )
    QuoteFactory()  # other account

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/quotes")

    assert response.status_code == 200
    assert response.data == {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": str(quote.id),
                "status": quote.status,
                "number": quote.number,
                "numbering_system_id": None,
                "currency": quote.currency,
                "issue_date": quote.issue_date.isoformat(),
                "customer": {
                    "id": str(customer.id),
                    "name": customer.name,
                    "legal_name": customer.legal_name,
                    "legal_number": customer.legal_number,
                    "email": customer.email,
                    "phone": customer.phone,
                    "description": customer.description,
                    "address": {
                        "line1": customer.address.line1,
                        "line2": customer.address.line2,
                        "locality": customer.address.locality,
                        "state": customer.address.state,
                        "postal_code": customer.address.postal_code,
                        "country": customer.address.country,
                    },
                    "logo_id": None,
                },
                "account": {
                    "id": str(account.id),
                    "name": account.name,
                    "legal_name": account.legal_name,
                    "legal_number": account.legal_number,
                    "email": account.email,
                    "phone": account.phone,
                    "address": {
                        "line1": account.address.line1,
                        "line2": account.address.line2,
                        "locality": account.address.locality,
                        "state": account.address.state,
                        "postal_code": account.address.postal_code,
                        "country": account.address.country,
                    },
                    "logo_id": None,
                },
                "metadata": quote.metadata,
                "custom_fields": quote.custom_fields,
                "footer": quote.footer,
                "description": quote.description,
                "delivery_method": quote.delivery_method,
                "recipients": quote.recipients,
                "subtotal_amount": "0.00",
                "total_discount_amount": "0.00",
                "total_amount_excluding_tax": "0.00",
                "total_tax_amount": "0.00",
                "total_amount": "0.00",
                "created_at": "2025-01-15T10:00:00Z",
                "updated_at": "2025-01-15T10:00:00Z",
                "opened_at": None,
                "accepted_at": None,
                "canceled_at": None,
                "pdf_id": ANY,
                "invoice_id": None,
                "lines": [],
                "discounts": [],
                "taxes": [],
            }
            for quote in [quote_1, quote_2]
        ],
    }


def test_list_quotes_filter_by_status(api_client, user, account):
    QuoteFactory(account=account, status=QuoteStatus.OPEN, number="QT-0001")
    matching = QuoteFactory(account=account, status=QuoteStatus.DRAFT)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/quotes", {"status": QuoteStatus.DRAFT})

    assert response.status_code == 200
    assert [r["id"] for r in response.data["results"]] == [str(matching.id)]


def test_list_quotes_filter_by_currency(api_client, user, account):
    usd = QuoteFactory(account=account, currency="USD")
    QuoteFactory(account=account, currency="EUR")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/quotes", {"currency": "USD"})

    assert response.status_code == 200
    assert [r["id"] for r in response.data["results"]] == [str(usd.id)]


def test_list_quotes_filter_by_customer_id(api_client, user, account):
    customer = CustomerFactory(account=account)
    matching = QuoteFactory(account=account, customer=customer)
    QuoteFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/quotes", {"customer_id": str(customer.id)})

    assert response.status_code == 200
    assert [r["id"] for r in response.data["results"]] == [str(matching.id)]


def test_list_quotes_filter_by_created_at_after(api_client, user, account):
    base = timezone.now()
    older = QuoteFactory(account=account)
    Quote.objects.filter(id=older.id).update(created_at=base - timedelta(days=1))
    newer = QuoteFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/quotes", {"created_at_after": (base - timedelta(hours=12)).isoformat()})

    assert response.status_code == 200
    assert [r["id"] for r in response.data["results"]] == [str(newer.id)]


def test_list_quotes_filter_by_created_at_before(api_client, user, account):
    base = timezone.now()
    older = QuoteFactory(account=account)
    Quote.objects.filter(id=older.id).update(created_at=base - timedelta(days=1))
    QuoteFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/quotes", {"created_at_before": base.isoformat()})

    assert response.status_code == 200
    assert [r["id"] for r in response.data["results"]] == [str(older.id)]


def test_list_quotes_filter_by_issue_date_range(api_client, user, account):
    QuoteFactory(account=account, issue_date=date(2025, 1, 1))
    matching = QuoteFactory(account=account, issue_date=date(2025, 2, 1))

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(
        "/api/v1/quotes",
        {
            "issue_date_after": date(2025, 1, 15).isoformat(),
            "issue_date_before": date(2025, 2, 15).isoformat(),
        },
    )

    assert response.status_code == 200
    assert [r["id"] for r in response.data["results"]] == [str(matching.id)]


def test_list_quotes_filter_by_subtotal_amount_min(api_client, user, account):
    QuoteFactory(account=account, subtotal_amount="10.00")
    matching = QuoteFactory(account=account, subtotal_amount="50.00")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/quotes", {"subtotal_amount_min": "20"})

    assert response.status_code == 200
    assert [r["id"] for r in response.data["results"]] == [str(matching.id)]


def test_list_quotes_filter_by_subtotal_amount_max(api_client, user, account):
    matching = QuoteFactory(account=account, subtotal_amount="20.00")
    QuoteFactory(account=account, subtotal_amount="70.00")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/quotes", {"subtotal_amount_max": "40"})

    assert response.status_code == 200
    assert [r["id"] for r in response.data["results"]] == [str(matching.id)]


def test_list_quotes_filter_by_total_amount_min(api_client, user, account):
    QuoteFactory(account=account, total_amount="10.00")
    matching = QuoteFactory(account=account, total_amount="50.00")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/quotes", {"total_amount_min": "20"})

    assert response.status_code == 200
    assert [r["id"] for r in response.data["results"]] == [str(matching.id)]


def test_list_quotes_filter_by_total_amount_max(api_client, user, account):
    matching = QuoteFactory(account=account, total_amount="20.00")
    QuoteFactory(account=account, total_amount="70.00")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/quotes", {"total_amount_max": "40"})

    assert response.status_code == 200
    assert [r["id"] for r in response.data["results"]] == [str(matching.id)]


def test_list_quotes_filter_by_product_id(api_client, user, account):
    quote = QuoteFactory(account=account)
    price = PriceFactory(account=account)
    matching_line = QuoteLineFactory(quote=quote, price=price)
    QuoteFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(
        "/api/v1/quotes",
        {"product_id": str(price.product_id)},
    )

    assert response.status_code == 200
    assert [r["id"] for r in response.data["results"]] == [str(matching_line.quote_id)]


def test_list_quotes_filter_by_numbering_system_id(api_client, user, account):
    numbering_system = NumberingSystemFactory(account=account, applies_to=NumberingSystemAppliesTo.QUOTE)
    matching = QuoteFactory(account=account, numbering_system=numbering_system)
    QuoteFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/quotes", {"numbering_system_id": str(numbering_system.id)})

    assert response.status_code == 200
    assert [r["id"] for r in response.data["results"]] == [str(matching.id)]


def test_list_quotes_requires_authentication(api_client):
    response = api_client.get("/api/v1/quotes")

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


def test_list_quotes_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.get("/api/v1/quotes")

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
