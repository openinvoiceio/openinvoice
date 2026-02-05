import uuid
from datetime import date

import pytest
from freezegun import freeze_time

from openinvoice.quotes.choices import QuoteDeliveryMethod, QuoteStatus
from tests.factories import CustomerFactory, QuoteFactory

pytestmark = pytest.mark.django_db


@freeze_time("2025-04-01T11:00:00Z")
def test_finalize_quote(api_client, user, account, pdf_generator):
    customer = CustomerFactory(account=account)
    quote = QuoteFactory(
        account=account,
        customer=customer,
        number="QT-2025-3001",
        currency="USD",
        issue_date=date(2025, 4, 1),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/quotes/{quote.id}/finalize")

    assert response.status_code == 200
    assert response.data["id"] == str(quote.id)
    assert response.data["status"] == "open"
    assert response.data["number"] == "QT-2025-3001"
    assert response.data["numbering_system_id"] is None
    assert response.data["currency"] == "USD"
    assert response.data["issue_date"] == "2025-04-01"
    assert response.data["metadata"] == {}
    assert response.data["custom_fields"] == {}
    assert response.data["footer"] is None
    assert response.data["delivery_method"] == QuoteDeliveryMethod.MANUAL
    assert response.data["recipients"] == []
    assert response.data["subtotal_amount"] == "0.00"
    assert response.data["total_discount_amount"] == "0.00"
    assert response.data["total_amount_excluding_tax"] == "0.00"
    assert response.data["total_tax_amount"] == "0.00"
    assert response.data["total_amount"] == "0.00"
    assert response.data["created_at"] == "2025-04-01T11:00:00Z"
    assert response.data["updated_at"] == "2025-04-01T11:00:00Z"
    assert response.data["opened_at"] == "2025-04-01T11:00:00Z"
    assert response.data["accepted_at"] is None
    assert response.data["canceled_at"] is None
    assert response.data["pdf_id"] is not None
    assert response.data["invoice_id"] is None
    assert response.data["lines"] == []
    assert response.data["discounts"] == []
    assert response.data["taxes"] == []
    assert response.data["billing_profile"]["id"] != str(customer.default_billing_profile.id)
    assert response.data["billing_profile"]["name"] == customer.default_billing_profile.name
    assert response.data["billing_profile"]["email"] == customer.default_billing_profile.email
    assert response.data["billing_profile"]["currency"] == customer.default_billing_profile.currency
    assert response.data["billing_profile"]["tax_rates"] == []
    assert response.data["billing_profile"]["tax_ids"] == []
    assert response.data["business_profile"]["id"] != str(account.default_business_profile.id)
    assert response.data["business_profile"]["name"] == account.default_business_profile.name
    assert response.data["business_profile"]["email"] == account.default_business_profile.email
    assert response.data["business_profile"]["tax_ids"] == []
    assert len(pdf_generator.requests) == 1


def test_finalize_quote_with_automatic_delivery(api_client, user, account, pdf_generator, mailoutbox):
    customer = CustomerFactory(account=account)
    quote = QuoteFactory(
        account=account,
        customer=customer,
        number="QT-2025-3002",
        delivery_method=QuoteDeliveryMethod.AUTOMATIC,
        recipients=["test@example.com"],
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/quotes/{quote.id}/finalize")

    assert response.status_code == 200
    assert len(pdf_generator.requests) == 1
    assert len(mailoutbox) == 1
    email = mailoutbox[0]
    assert email.subject == f"Quote {quote.number} from {account.default_business_profile.name}"
    assert email.to == ["test@example.com"]


def test_finalize_quote_with_no_recipients(api_client, user, account, pdf_generator, mailoutbox):
    customer = CustomerFactory(account=account)
    quote = QuoteFactory(
        account=account,
        customer=customer,
        number="QT-2025-300",
        delivery_method=QuoteDeliveryMethod.AUTOMATIC,
        recipients=[],
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/quotes/{quote.id}/finalize")

    assert response.status_code == 200
    assert len(pdf_generator.requests) == 1
    assert len(mailoutbox) == 0


def test_finalize_quote_not_found(api_client, user, account):
    quote_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/quotes/{quote_id}/finalize")

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


@pytest.mark.parametrize("status", [QuoteStatus.OPEN, QuoteStatus.ACCEPTED, QuoteStatus.CANCELED])
def test_finalize_quote_requires_draft(api_client, user, account, status):
    quote = QuoteFactory(account=account, currency="USD", status=status, number="QT-4001")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/quotes/{quote.id}/finalize")

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Only draft quotes can be finalized",
            }
        ],
    }


def test_finalize_quote_without_number_or_numbering_system(api_client, user, account):
    quote = QuoteFactory(account=account, currency="USD", status=QuoteStatus.DRAFT, number=None, numbering_system=None)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(f"/api/v1/quotes/{quote.id}/finalize")

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Number or numbering system is required before finalizing a quote",
            }
        ],
    }


def test_finalize_quote_requires_authentication(api_client):
    quote_id = uuid.uuid4()

    response = api_client.post(f"/api/v1/quotes/{quote_id}/finalize")

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


def test_finalize_quote_requires_account(api_client, user):
    quote_id = uuid.uuid4()

    api_client.force_login(user)
    response = api_client.post(f"/api/v1/quotes/{quote_id}/finalize")

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
