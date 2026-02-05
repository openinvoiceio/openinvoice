from unittest.mock import ANY

import pytest

from openinvoice.invoices.choices import InvoiceDocumentAudience
from tests.factories import (
    AccountFactory,
    BillingProfileFactory,
    CustomerFactory,
    InvoiceDocumentFactory,
    InvoiceFactory,
    ProductFactory,
)

pytestmark = pytest.mark.django_db


def test_search_all(api_client, user, account):
    product_alpha = ProductFactory(account=account, name="Alpha Product")
    customer_alpha = CustomerFactory(
        account=account,
        default_billing_profile=BillingProfileFactory(name="Alpha Customer", email="alpha@example.com"),
    )
    invoice_alpha = InvoiceFactory(
        account=account,
        customer=customer_alpha,
        number="INV-ALPHA",
    )
    document = InvoiceDocumentFactory(invoice=invoice_alpha, audience=[InvoiceDocumentAudience.CUSTOMER])

    # Non-matching or different account objects
    ProductFactory(account=account, name="Beta Product")
    CustomerFactory(
        account=account,
        default_billing_profile=BillingProfileFactory(name="Beta Customer", email="beta@example.com"),
    )
    invoice_beta = InvoiceFactory(
        account=account,
        customer=CustomerFactory(
            account=account,
            default_billing_profile=BillingProfileFactory(name="Beta Customer", email="beta@example.com"),
        ),
        number="INV-BETA",
    )
    InvoiceDocumentFactory(invoice=invoice_beta, audience=[InvoiceDocumentAudience.CUSTOMER])
    other_account = AccountFactory()
    ProductFactory(account=other_account, name="Alpha Product")
    CustomerFactory(
        account=other_account,
        default_billing_profile=BillingProfileFactory(name="Alpha Customer", email="alpha@example.com"),
    )
    InvoiceFactory(
        account=other_account,
        customer=CustomerFactory(
            account=other_account,
            default_billing_profile=BillingProfileFactory(name="Alpha Customer", email="alpha@example.com"),
        ),
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
                "status": product_alpha.status,
                "url": product_alpha.url,
                "image_url": None,
                "image_id": None,
                "default_price": None,
                "metadata": product_alpha.metadata,
                "created_at": ANY,
                "updated_at": ANY,
                "archived_at": None,
            }
        ],
        "customers": [
            {
                "id": str(customer_alpha.id),
                "account_id": str(customer_alpha.account_id),
                "description": customer_alpha.description,
                "metadata": customer_alpha.metadata,
                "default_billing_profile": {
                    "id": str(customer_alpha.default_billing_profile.id),
                    "name": customer_alpha.default_billing_profile.name,
                    "legal_name": customer_alpha.default_billing_profile.legal_name,
                    "legal_number": customer_alpha.default_billing_profile.legal_number,
                    "email": customer_alpha.default_billing_profile.email,
                    "phone": customer_alpha.default_billing_profile.phone,
                    "address": {
                        "line1": customer_alpha.default_billing_profile.address.line1,
                        "line2": customer_alpha.default_billing_profile.address.line2,
                        "locality": customer_alpha.default_billing_profile.address.locality,
                        "state": customer_alpha.default_billing_profile.address.state,
                        "postal_code": customer_alpha.default_billing_profile.address.postal_code,
                        "country": str(customer_alpha.default_billing_profile.address.country),
                    },
                    "currency": customer_alpha.default_billing_profile.currency,
                    "language": customer_alpha.default_billing_profile.language,
                    "net_payment_term": customer_alpha.default_billing_profile.net_payment_term,
                    "invoice_numbering_system_id": customer_alpha.default_billing_profile.invoice_numbering_system_id,
                    "credit_note_numbering_system_id": (
                        customer_alpha.default_billing_profile.credit_note_numbering_system_id
                    ),
                    "tax_rates": [],
                    "tax_ids": [],
                    "created_at": ANY,
                    "updated_at": ANY,
                },
                "default_shipping_profile": None,
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
                "currency": invoice_alpha.currency,
                "tax_behavior": invoice_alpha.tax_behavior,
                "issue_date": None,
                "due_date": ANY,
                "net_payment_term": invoice_alpha.net_payment_term,
                "billing_profile": {
                    "id": str(invoice_alpha.billing_profile.id),
                    "name": invoice_alpha.billing_profile.name,
                    "legal_name": invoice_alpha.billing_profile.legal_name,
                    "legal_number": invoice_alpha.billing_profile.legal_number,
                    "email": invoice_alpha.billing_profile.email,
                    "phone": invoice_alpha.billing_profile.phone,
                    "address": {
                        "line1": invoice_alpha.billing_profile.address.line1,
                        "line2": invoice_alpha.billing_profile.address.line2,
                        "locality": invoice_alpha.billing_profile.address.locality,
                        "state": invoice_alpha.billing_profile.address.state,
                        "postal_code": invoice_alpha.billing_profile.address.postal_code,
                        "country": str(invoice_alpha.billing_profile.address.country),
                    },
                    "currency": invoice_alpha.billing_profile.currency,
                    "language": invoice_alpha.billing_profile.language,
                    "net_payment_term": invoice_alpha.billing_profile.net_payment_term,
                    "invoice_numbering_system_id": invoice_alpha.billing_profile.invoice_numbering_system_id,
                    "credit_note_numbering_system_id": invoice_alpha.billing_profile.credit_note_numbering_system_id,
                    "tax_rates": [],
                    "tax_ids": [],
                    "created_at": ANY,
                    "updated_at": ANY,
                },
                "business_profile": {
                    "id": str(invoice_alpha.business_profile.id),
                    "name": invoice_alpha.business_profile.name,
                    "legal_name": invoice_alpha.business_profile.legal_name,
                    "legal_number": invoice_alpha.business_profile.legal_number,
                    "email": invoice_alpha.business_profile.email,
                    "phone": invoice_alpha.business_profile.phone,
                    "address": {
                        "line1": invoice_alpha.business_profile.address.line1,
                        "line2": invoice_alpha.business_profile.address.line2,
                        "locality": invoice_alpha.business_profile.address.locality,
                        "state": invoice_alpha.business_profile.address.state,
                        "postal_code": invoice_alpha.business_profile.address.postal_code,
                        "country": str(invoice_alpha.business_profile.address.country),
                    },
                    "tax_ids": [],
                    "created_at": ANY,
                    "updated_at": ANY,
                },
                "metadata": invoice_alpha.metadata,
                "delivery_method": invoice_alpha.delivery_method,
                "recipients": invoice_alpha.recipients,
                "subtotal_amount": f"{invoice_alpha.subtotal_amount.amount:.2f}",
                "total_discount_amount": f"{invoice_alpha.total_discount_amount.amount:.2f}",
                "total_excluding_tax_amount": f"{invoice_alpha.total_excluding_tax_amount.amount:.2f}",
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
                "previous_revision_id": None,
                "documents": [
                    {
                        "id": str(document.id),
                        "audience": document.audience,
                        "language": document.language,
                        "footer": document.footer,
                        "memo": document.memo,
                        "custom_fields": document.custom_fields,
                        "url": None,
                        "created_at": ANY,
                        "updated_at": ANY,
                    }
                ],
                "lines": [],
                "coupons": [],
                "discounts": [],
                "total_discounts": [],
                "tax_rates": [],
                "taxes": [],
                "total_taxes": [],
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
    customer = CustomerFactory(
        account=account,
        default_billing_profile=BillingProfileFactory(name="Delta"),
    )
    CustomerFactory(
        account=account,
        default_billing_profile=BillingProfileFactory(name="Epsilon"),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/search", {"search": "Delta"})

    assert [c["id"] for c in response.data["customers"]] == [str(customer.id)]
    assert response.data["products"] == []
    assert response.data["invoices"] == []


def test_search_customers_by_email(api_client, user, account):
    customer = CustomerFactory(
        account=account,
        default_billing_profile=BillingProfileFactory(email="delta@example.com"),
    )
    CustomerFactory(
        account=account,
        default_billing_profile=BillingProfileFactory(email="other@example.com"),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/search", {"search": "delta@example.com"})

    assert [c["id"] for c in response.data["customers"]] == [str(customer.id)]
    assert response.data["products"] == []
    assert response.data["invoices"] == []


def test_search_customers_by_phone(api_client, user, account):
    customer = CustomerFactory(
        account=account,
        default_billing_profile=BillingProfileFactory(phone="555123"),
    )
    CustomerFactory(
        account=account,
        default_billing_profile=BillingProfileFactory(phone="555000"),
    )

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
    customer = CustomerFactory(
        account=account,
        default_billing_profile=BillingProfileFactory(name="Zeta"),
    )
    invoice = InvoiceFactory(account=account, customer=customer)
    InvoiceFactory(
        account=account,
        customer=CustomerFactory(
            account=account,
            default_billing_profile=BillingProfileFactory(name="Eta"),
        ),
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/search", {"search": "Zeta"})

    assert [i["id"] for i in response.data["invoices"]] == [str(invoice.id)]
    assert response.data["products"] == []
    assert [i["id"] for i in response.data["customers"]] == [str(customer.id)]


def test_search_invoices_by_customer_email(api_client, user, account):
    customer = CustomerFactory(
        account=account,
        default_billing_profile=BillingProfileFactory(email="zeta@example.com"),
    )
    invoice = InvoiceFactory(account=account, customer=customer)
    InvoiceFactory(
        account=account,
        customer=CustomerFactory(
            account=account,
            default_billing_profile=BillingProfileFactory(email="eta@example.com"),
        ),
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
            default_billing_profile=BillingProfileFactory(
                name=f"Alpha Customer {i}",
                email=f"alpha{i}@example.com",
            ),
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
    CustomerFactory(
        account=account,
        default_billing_profile=BillingProfileFactory(name="Existing", email="exist@example.com"),
    )
    ProductFactory(account=account, name="Existing")
    InvoiceFactory(
        account=account,
        number="INV-EXISTING",
        customer=CustomerFactory(
            account=account,
            default_billing_profile=BillingProfileFactory(name="Existing", email="exist2@example.com"),
        ),
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
        "type": "client_error",
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
        "type": "client_error",
        "errors": [
            {
                "attr": None,
                "code": "permission_denied",
                "detail": "You do not have permission to perform this action.",
            }
        ],
    }
