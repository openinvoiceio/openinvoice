from unittest.mock import ANY

import pytest
from drf_standardized_errors.types import ErrorType

from tests.factories import (
    AccountFactory,
    CustomerFactory,
    InvoiceFactory,
    ProductFactory,
)

pytestmark = pytest.mark.django_db


def test_search_all(api_client, user, account):
    product_alpha = ProductFactory(account=account, name="Alpha Product")
    customer_alpha = CustomerFactory(account=account, name="Alpha Customer", email="alpha@example.com")
    invoice_alpha = InvoiceFactory(
        account=account,
        customer=customer_alpha,
        number="INV-ALPHA",
    )

    # Non-matching or different account objects
    ProductFactory(account=account, name="Beta Product")
    CustomerFactory(account=account, name="Beta Customer", email="beta@example.com")
    InvoiceFactory(
        account=account,
        customer=CustomerFactory(account=account, name="Beta Customer", email="beta@example.com"),
        number="INV-BETA",
    )
    other_account = AccountFactory()
    ProductFactory(account=other_account, name="Alpha Product")
    CustomerFactory(account=other_account, name="Alpha Customer", email="alpha@example.com")
    InvoiceFactory(
        account=other_account,
        customer=CustomerFactory(account=other_account, name="Alpha Customer", email="alpha@example.com"),
        number="INV-ALPHA",
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/search", {"search": "Alpha"})

    assert response.status_code == 200
    assert response.data == {
        "products": [
            {
                "id": str(product_alpha.id),
                "account_id": str(product_alpha.account_id),
                "name": product_alpha.name,
                "description": product_alpha.description,
                "is_active": product_alpha.is_active,
                "url": product_alpha.url,
                "image_url": None,
                "image_id": None,
                "default_price": None,
                "metadata": product_alpha.metadata,
                "created_at": ANY,
                "updated_at": ANY,
            }
        ],
        "customers": [
            {
                "id": str(customer_alpha.id),
                "account_id": str(customer_alpha.account_id),
                "name": customer_alpha.name,
                "legal_name": customer_alpha.legal_name,
                "legal_number": customer_alpha.legal_number,
                "email": customer_alpha.email,
                "phone": customer_alpha.phone,
                "currency": customer_alpha.currency,
                "net_payment_term": customer_alpha.net_payment_term,
                "invoice_numbering_system_id": None,
                "credit_note_numbering_system_id": None,
                "description": customer_alpha.description,
                "metadata": customer_alpha.metadata,
                "billing_address": {
                    "line1": customer_alpha.billing_address.line1,
                    "line2": customer_alpha.billing_address.line2,
                    "locality": customer_alpha.billing_address.locality,
                    "state": customer_alpha.billing_address.state,
                    "postal_code": customer_alpha.billing_address.postal_code,
                    "country": customer_alpha.billing_address.country,
                },
                "shipping_address": {
                    "line1": customer_alpha.shipping_address.line1,
                    "line2": customer_alpha.shipping_address.line2,
                    "locality": customer_alpha.shipping_address.locality,
                    "state": customer_alpha.shipping_address.state,
                    "postal_code": customer_alpha.shipping_address.postal_code,
                    "country": customer_alpha.shipping_address.country,
                },
                "tax_rates": [],
                "tax_ids": [],
                "logo_id": None,
                "logo_url": None,
                "created_at": ANY,
                "updated_at": ANY,
            }
        ],
        "invoices": [
            {
                "id": str(invoice_alpha.id),
                "status": invoice_alpha.status,
                "number": invoice_alpha.number,
                "numbering_system_id": None,
                "previous_revision_id": None,
                "latest_revision_id": None,
                "currency": invoice_alpha.currency,
                "issue_date": None,
                "sell_date": None,
                "due_date": ANY,
                "net_payment_term": invoice_alpha.net_payment_term,
                "customer": {
                    "id": str(invoice_alpha.customer.id),
                    "name": invoice_alpha.customer.name,
                    "legal_name": invoice_alpha.customer.legal_name,
                    "legal_number": invoice_alpha.customer.legal_number,
                    "email": invoice_alpha.customer.email,
                    "phone": invoice_alpha.customer.phone,
                    "description": invoice_alpha.customer.description,
                    "billing_address": {
                        "line1": invoice_alpha.customer.billing_address.line1,
                        "line2": invoice_alpha.customer.billing_address.line2,
                        "locality": invoice_alpha.customer.billing_address.locality,
                        "state": invoice_alpha.customer.billing_address.state,
                        "postal_code": invoice_alpha.customer.billing_address.postal_code,
                        "country": invoice_alpha.customer.billing_address.country,
                    },
                    "shipping_address": {
                        "line1": invoice_alpha.customer.shipping_address.line1,
                        "line2": invoice_alpha.customer.shipping_address.line2,
                        "locality": invoice_alpha.customer.shipping_address.locality,
                        "state": invoice_alpha.customer.shipping_address.state,
                        "postal_code": invoice_alpha.customer.shipping_address.postal_code,
                        "country": invoice_alpha.customer.shipping_address.country,
                    },
                    "logo_id": None,
                },
                "account": {
                    "id": str(invoice_alpha.account.id),
                    "name": invoice_alpha.account.name,
                    "legal_name": invoice_alpha.account.legal_name,
                    "legal_number": invoice_alpha.account.legal_number,
                    "email": invoice_alpha.account.email,
                    "phone": invoice_alpha.account.phone,
                    "address": {
                        "line1": invoice_alpha.account.address.line1,
                        "line2": invoice_alpha.account.address.line2,
                        "locality": invoice_alpha.account.address.locality,
                        "state": invoice_alpha.account.address.state,
                        "postal_code": invoice_alpha.account.address.postal_code,
                        "country": invoice_alpha.account.address.country,
                    },
                    "logo_id": None,
                },
                "metadata": invoice_alpha.metadata,
                "custom_fields": invoice_alpha.custom_fields,
                "footer": invoice_alpha.footer,
                "description": invoice_alpha.description,
                "delivery_method": invoice_alpha.delivery_method,
                "recipients": invoice_alpha.recipients,
                "subtotal_amount": f"{invoice_alpha.subtotal_amount.amount:.2f}",
                "total_discount_amount": f"{invoice_alpha.total_discount_amount.amount:.2f}",
                "total_amount_excluding_tax": f"{invoice_alpha.total_amount_excluding_tax.amount:.2f}",
                "shipping_amount": f"{invoice_alpha.shipping_amount.amount:.2f}",
                "total_tax_amount": f"{invoice_alpha.total_tax_amount.amount:.2f}",
                "total_amount": f"{invoice_alpha.total_amount.amount:.2f}",
                "total_credit_amount": f"{invoice_alpha.total_credit_amount.amount:.2f}",
                "total_paid_amount": f"{invoice_alpha.total_paid_amount.amount:.2f}",
                "outstanding_amount": f"{invoice_alpha.outstanding_amount.amount:.2f}",
                "payment_provider": None,
                "payment_connection_id": None,
                "created_at": ANY,
                "updated_at": ANY,
                "opened_at": None,
                "paid_at": None,
                "voided_at": None,
                "pdf_id": None,
                "lines": [],
                "taxes": [],
                "discounts": [],
                "tax_breakdown": [],
                "discount_breakdown": [],
                "shipping": None,
            }
        ],
    }


def test_search_products_by_id(api_client, user, account):
    product = ProductFactory(account=account)
    ProductFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/search", {"search": str(product.id)})

    assert [p["id"] for p in response.data["products"]] == [str(product.id)]
    assert response.data["customers"] == []
    assert response.data["invoices"] == []


def test_search_products_by_name(api_client, user, account):
    product = ProductFactory(account=account, name="Gamma")
    ProductFactory(account=account, name="Delta")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/search", {"search": "Gamma"})

    assert [p["id"] for p in response.data["products"]] == [str(product.id)]
    assert response.data["customers"] == []
    assert response.data["invoices"] == []


def test_search_products_by_description(api_client, user, account):
    product = ProductFactory(account=account, description="Special description")
    ProductFactory(account=account, description="Other description")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/search", {"search": "Special description"})

    assert [p["id"] for p in response.data["products"]] == [str(product.id)]
    assert response.data["customers"] == []
    assert response.data["invoices"] == []


def test_search_customers_by_id(api_client, user, account):
    customer = CustomerFactory(account=account)
    CustomerFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/search", {"search": str(customer.id)})

    assert [c["id"] for c in response.data["customers"]] == [str(customer.id)]
    assert response.data["products"] == []
    assert response.data["invoices"] == []


def test_search_customers_by_name(api_client, user, account):
    customer = CustomerFactory(account=account, name="Delta")
    CustomerFactory(account=account, name="Epsilon")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/search", {"search": "Delta"})

    assert [c["id"] for c in response.data["customers"]] == [str(customer.id)]
    assert response.data["products"] == []
    assert response.data["invoices"] == []


def test_search_customers_by_email(api_client, user, account):
    customer = CustomerFactory(account=account, email="delta@example.com")
    CustomerFactory(account=account, email="other@example.com")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/search", {"search": "delta@example.com"})

    assert [c["id"] for c in response.data["customers"]] == [str(customer.id)]
    assert response.data["products"] == []
    assert response.data["invoices"] == []


def test_search_customers_by_phone(api_client, user, account):
    customer = CustomerFactory(account=account, phone="555123")
    CustomerFactory(account=account, phone="555000")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/search", {"search": "555123"})

    assert [c["id"] for c in response.data["customers"]] == [str(customer.id)]
    assert response.data["products"] == []
    assert response.data["invoices"] == []


def test_search_customers_by_description(api_client, user, account):
    customer = CustomerFactory(account=account, description="VIP")
    CustomerFactory(account=account, description="Regular")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/search", {"search": "VIP"})

    assert [c["id"] for c in response.data["customers"]] == [str(customer.id)]
    assert response.data["products"] == []
    assert response.data["invoices"] == []


def test_search_invoices_by_id(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    InvoiceFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/search", {"search": str(invoice.id)})

    assert [i["id"] for i in response.data["invoices"]] == [str(invoice.id)]
    assert response.data["products"] == []
    assert response.data["customers"] == []


def test_search_invoices_by_number(api_client, user, account):
    invoice = InvoiceFactory(account=account, number="INV-XYZ")
    InvoiceFactory(account=account, number="INV-OTHER")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/search", {"search": "INV-XYZ"})

    assert [i["id"] for i in response.data["invoices"]] == [str(invoice.id)]
    assert response.data["products"] == []
    assert response.data["customers"] == []


def test_search_invoices_by_customer_name(api_client, user, account):
    customer = CustomerFactory(account=account, name="Zeta")
    invoice = InvoiceFactory(account=account, customer=customer)
    InvoiceFactory(
        account=account,
        customer=CustomerFactory(account=account, name="Eta"),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/search", {"search": "Zeta"})

    assert [i["id"] for i in response.data["invoices"]] == [str(invoice.id)]
    assert response.data["products"] == []
    assert [i["id"] for i in response.data["customers"]] == [str(customer.id)]


def test_search_invoices_by_customer_email(api_client, user, account):
    customer = CustomerFactory(account=account, email="zeta@example.com")
    invoice = InvoiceFactory(account=account, customer=customer)
    InvoiceFactory(
        account=account,
        customer=CustomerFactory(account=account, email="eta@example.com"),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/search", {"search": "zeta@example.com"})

    assert [i["id"] for i in response.data["invoices"]] == [str(invoice.id)]
    assert response.data["products"] == []
    assert [i["id"] for i in response.data["customers"]] == [str(customer.id)]


def test_search_result_limited(api_client, user, account):
    for i in range(6):
        customer = CustomerFactory(
            account=account,
            name=f"Alpha Customer {i}",
            email=f"alpha{i}@example.com",
        )
        ProductFactory(account=account, name=f"Alpha Product {i}")
        InvoiceFactory(
            account=account,
            number=f"INV-ALPHA-{i}",
            customer=customer,
        )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/search", {"search": "Alpha"})

    assert len(response.data["products"]) == 5
    assert len(response.data["customers"]) == 5
    assert len(response.data["invoices"]) == 5


def test_search_returns_empty(api_client, user, account):
    CustomerFactory(account=account, name="Existing", email="exist@example.com")
    ProductFactory(account=account, name="Existing")
    InvoiceFactory(
        account=account,
        number="INV-EXISTING",
        customer=CustomerFactory(account=account, name="Existing", email="exist2@example.com"),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/search", {"search": "Nope"})

    assert response.status_code == 200
    assert response.data["products"] == []
    assert response.data["customers"] == []
    assert response.data["invoices"] == []


def test_search_requires_authentication(api_client):
    response = api_client.get("/api/v1/search", {"search": "anything"})

    assert response.status_code == 403
    assert response.data == {
        "type": ErrorType.CLIENT_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "not_authenticated",
                "detail": "Authentication credentials were not provided.",
            }
        ],
    }


def test_search_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.get("/api/v1/search", {"search": "anything"})

    assert response.status_code == 403
    assert response.data == {
        "type": ErrorType.CLIENT_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "permission_denied",
                "detail": "You do not have permission to perform this action.",
            }
        ],
    }
