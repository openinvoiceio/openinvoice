import uuid
from decimal import Decimal
from unittest.mock import ANY

import pytest

from common.choices import FeatureCode, LimitCode
from openinvoice.integrations.choices import PaymentProvider
from openinvoice.invoices.choices import InvoiceDeliveryMethod, InvoiceDocumentRole, InvoiceStatus
from openinvoice.invoices.models import Invoice
from openinvoice.tax_rates.choices import TaxRateStatus
from tests.factories import (
    CouponFactory,
    CustomerFactory,
    ShippingRateFactory,
    StripeConnectionFactory,
    TaxRateFactory,
)

pytestmark = pytest.mark.django_db


def test_create_invoice(api_client, user, account):
    customer = CustomerFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoices",
        {"customer_id": str(customer.id)},
    )

    assert response.status_code == 201
    invoice = Invoice.objects.get(id=response.data["id"])
    document = invoice.documents.get(role=InvoiceDocumentRole.PRIMARY)
    assert response.data == {
        "id": response.data["id"],
        "status": InvoiceStatus.DRAFT,
        "number": None,
        "numbering_system_id": None,
        "currency": customer.currency,
        "tax_behavior": "automatic",
        "issue_date": None,
        "due_date": None,
        "net_payment_term": 0,
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
        "metadata": {},
        "delivery_method": InvoiceDeliveryMethod.MANUAL,
        "recipients": [customer.email],
        "subtotal_amount": "0.00",
        "total_discount_amount": "0.00",
        "total_excluding_tax_amount": "0.00",
        "shipping_amount": "0.00",
        "total_tax_amount": "0.00",
        "total_amount": "0.00",
        "total_credit_amount": "0.00",
        "total_paid_amount": "0.00",
        "outstanding_amount": "0.00",
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
                "role": document.role,
                "language": document.language,
                "footer": document.footer,
                "memo": document.memo,
                "custom_fields": document.custom_fields,
                "file_id": None,
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

    assert invoice.customer_id == customer.id
    assert invoice.head is not None
    assert invoice.head.root_id == invoice.id
    assert invoice.head.current_id is None


def test_create_invoice_with_customer_tax_rates(api_client, user, account):
    tax_rate = TaxRateFactory(account=account)
    customer = CustomerFactory(account=account)
    customer.tax_rates.add(tax_rate)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoices",
        {"customer_id": str(customer.id)},
    )

    assert response.status_code == 201
    assert [r["id"] for r in response.data["tax_rates"]] == [str(tax_rate.id)]


def test_create_invoice_ignores_archived_customer_tax_rates(api_client, user, account):
    active_rate = TaxRateFactory(account=account, status=TaxRateStatus.ACTIVE)
    archived_rate = TaxRateFactory(account=account, status=TaxRateStatus.ARCHIVED)
    customer = CustomerFactory(account=account)
    customer.tax_rates.add(active_rate, archived_rate)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoices",
        {"customer_id": str(customer.id)},
    )

    assert response.status_code == 201
    assert [r["id"] for r in response.data["tax_rates"]] == [str(active_rate.id)]


def test_create_invoice_with_shipping(api_client, user, account):
    customer = CustomerFactory(account=account)
    shipping_rate = ShippingRateFactory(account=account, amount=Decimal("10.00"))
    tax_rate = TaxRateFactory(account=account, percentage=Decimal("10.00"))

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoices",
        {
            "customer_id": str(customer.id),
            "shipping": {
                "shipping_rate_id": str(shipping_rate.id),
                "tax_rates": [str(tax_rate.id)],
            },
        },
    )

    assert response.status_code == 201
    assert response.data["shipping"] == {
        "name": customer.name,
        "phone": customer.phone,
        "address": {
            "line1": customer.address.line1,
            "line2": customer.address.line2,
            "locality": customer.address.locality,
            "state": customer.address.state,
            "postal_code": customer.address.postal_code,
            "country": customer.address.country,
        },
        "amount": "10.00",
        "total_excluding_tax_amount": "10.00",
        "total_tax_amount": "1.00",
        "total_tax_rate": "10.00",
        "total_amount": "11.00",
        "shipping_rate_id": str(shipping_rate.id),
        "tax_rates": [
            {
                "id": str(tax_rate.id),
                "account_id": str(account.id),
                "name": tax_rate.name,
                "description": tax_rate.description,
                "country": tax_rate.country,
                "percentage": f"{tax_rate.percentage:.2f}",
                "status": tax_rate.status,
                "archived_at": tax_rate.archived_at,
                "updated_at": ANY,
                "created_at": ANY,
            }
        ],
        "total_taxes": [
            {
                "tax_rate_id": str(tax_rate.id),
                "name": tax_rate.name,
                "percentage": "10.00",
                "amount": "1.00",
            }
        ],
    }
    assert response.data["shipping_amount"] == "10.00"
    assert response.data["total_tax_amount"] == "1.00"
    assert response.data["total_amount"] == "11.00"


def test_create_invoice_with_invalid_shipping_rate(api_client, user, account):
    customer = CustomerFactory(account=account)
    shipping_rate_id = str(uuid.uuid4())

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoices",
        {
            "customer_id": str(customer.id),
            "shipping": {
                "shipping_rate_id": shipping_rate_id,
            },
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "shipping.shipping_rate_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{shipping_rate_id}" - object does not exist.',
            }
        ],
    }


def test_create_invoice_with_foreign_shipping_rate(api_client, user, account):
    customer = CustomerFactory(account=account)
    shipping_rate = ShippingRateFactory()  # Not linked to the account

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoices",
        {
            "customer_id": str(customer.id),
            "shipping": {
                "shipping_rate_id": str(shipping_rate.id),
            },
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "shipping.shipping_rate_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{shipping_rate.id}" - object does not exist.',
            },
        ],
    }


def test_create_invoice_with_invalid_shipping_tax_rate(api_client, user, account):
    customer = CustomerFactory(account=account)
    shipping_rate = ShippingRateFactory(account=account)
    tax_rate_id_1 = str(uuid.uuid4())
    tax_rate_id_2 = str(uuid.uuid4())

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoices",
        {
            "customer_id": str(customer.id),
            "shipping": {
                "shipping_rate_id": str(shipping_rate.id),
                "tax_rates": [tax_rate_id_1, tax_rate_id_2],
            },
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "shipping.tax_rates",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{tax_rate_id_1}" - object does not exist.',
            },
        ],
    }


def test_create_invoice_with_foreign_shipping_tax_rate(api_client, user, account):
    customer = CustomerFactory(account=account)
    shipping_rate = ShippingRateFactory(account=account)
    foreign_tax_rate = TaxRateFactory()  # Not linked to the account

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoices",
        {
            "customer_id": str(customer.id),
            "shipping": {
                "shipping_rate_id": str(shipping_rate.id),
                "tax_rates": [str(foreign_tax_rate.id)],
            },
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "shipping.tax_rates",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{foreign_tax_rate.id}" - object does not exist.',
            },
        ],
    }


def test_create_invoice_overflow_returns_validation_error(api_client, user, account):
    customer = CustomerFactory(account=account)
    shipping_rate = ShippingRateFactory(account=account, amount=Decimal("50000000000000000.00"))
    tax_rate = TaxRateFactory(account=account, percentage=Decimal("100"))

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoices",
        {
            "customer_id": str(customer.id),
            "shipping": {
                "shipping_rate_id": str(shipping_rate.id),
                "tax_rates": [str(tax_rate.id)],
            },
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Amount exceeds the maximum allowed value",
            }
        ],
    }


def test_create_invoice_with_duplicate_shipping_tax_rates(api_client, user, account):
    customer = CustomerFactory(account=account)
    shipping_rate = ShippingRateFactory(account=account)
    tax_rate = TaxRateFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoices",
        {
            "customer_id": str(customer.id),
            "shipping": {
                "shipping_rate_id": str(shipping_rate.id),
                "tax_rates": [str(tax_rate.id), str(tax_rate.id)],
            },
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "shipping.tax_rates",
                "code": "duplicate",
                "detail": "Duplicate values are not allowed.",
            }
        ],
    }


def test_create_invoice_shipping_tax_rates_limit_exceeded(api_client, user, account, settings):
    settings.MAX_INVOICE_TAX_RATES = 1
    tax_rate1 = TaxRateFactory(account=account)
    tax_rate2 = TaxRateFactory(account=account)
    customer = CustomerFactory(account=account)
    shipping_rate = ShippingRateFactory(account=account, currency=customer.currency)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoices",
        {
            "customer_id": str(customer.id),
            "shipping": {
                "shipping_rate_id": str(shipping_rate.id),
                "tax_rates": [str(tax_rate1.id), str(tax_rate2.id)],
            },
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "shipping.tax_rates",
                "code": "invalid",
                "detail": "Ensure this list contains at most 1 items.",
            }
        ],
    }


def test_create_invoice_with_automatic_delivery_and_without_entitlement(api_client, user, account, settings):
    settings.DEFAULT_PLAN = "test"
    settings.PLANS = {"test": {"features": {FeatureCode.AUTOMATIC_INVOICE_DELIVERY: False}}}
    customer = CustomerFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoices",
        {
            "customer_id": str(customer.id),
            "delivery_method": InvoiceDeliveryMethod.AUTOMATIC,
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "delivery_method",
                "code": "invalid",
                "detail": "Automatic delivery is forbidden for your account.",
            }
        ],
    }


def test_create_invoice_customer_not_found(api_client, user, account):
    customer = CustomerFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoices",
        {"customer_id": str(customer.id)},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "customer_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{customer.id}" - object does not exist.',
            }
        ],
    }


def test_create_invoice_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.post(
        "/api/v1/invoices",
        {"customer_id": str(uuid.uuid4())},
    )

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


def test_create_invoice_requires_authentication(api_client, account):
    customer = CustomerFactory(account=account)

    response = api_client.post(
        "/api/v1/invoices",
        {"customer_id": str(customer.id)},
    )

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


def test_create_invoice_numbering_system_not_found(api_client, user, account):
    customer = CustomerFactory(account=account)
    numbering_system_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoices",
        {
            "customer_id": str(customer.id),
            "numbering_system_id": str(numbering_system_id),
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "numbering_system_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{numbering_system_id}" - object does not exist.',
            }
        ],
    }


def test_create_invoice_with_payment_provider(api_client, user, account):
    customer = CustomerFactory(account=account)
    connection = StripeConnectionFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoices",
        {
            "customer_id": str(customer.id),
            "payment_provider": PaymentProvider.STRIPE,
            "payment_connection_id": str(connection.id),
        },
    )

    assert response.status_code == 201
    assert response.data["payment_provider"] == PaymentProvider.STRIPE
    assert response.data["payment_connection_id"] == str(connection.id)


def test_create_invoice_with_unknown_payment_connection(api_client, user, account):
    connection_id = str(uuid.uuid4())
    customer = CustomerFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoices",
        {
            "customer_id": str(customer.id),
            "payment_provider": PaymentProvider.STRIPE,
            "payment_connection_id": connection_id,
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "payment_connection_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{connection_id}" - object does not exist.',
            }
        ],
    }


def test_create_invoice_payment_provider_without_connection(api_client, user, account):
    customer = CustomerFactory(account=account)
    StripeConnectionFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoices",
        {
            "customer_id": str(customer.id),
            "payment_provider": PaymentProvider.STRIPE,
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "non_field_errors",
                "code": "invalid",
                "detail": "Fields payment_provider, payment_connection_id must be provided together.",
            }
        ],
    }


def test_create_invoice_requires_customer(api_client, user, account):
    api_client.force_login(user)
    api_client.force_account(account)

    response = api_client.post("/api/v1/invoices")

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "customer_id",
                "code": "required",
                "detail": "This field is required.",
            }
        ],
    }


def test_create_invoice_limit_exceeded(api_client, user, account, settings):
    settings.DEFAULT_PLAN = "test"
    settings.PLANS = {"test": {"limits": {LimitCode.MAX_INVOICES_PER_MONTH: 0}}}

    customer = CustomerFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoices",
        {"customer_id": str(customer.id)},
    )

    assert response.status_code == 403
    assert response.data == {
        "type": "client_error",
        "errors": [
            {
                "attr": None,
                "code": "limit_exceeded",
                "detail": "Limit has been exceeded for your account.",
            }
        ],
    }


def test_create_invoice_with_coupons(api_client, user, account):
    customer = CustomerFactory(account=account)
    coupon1 = CouponFactory(account=account, currency=customer.currency)
    coupon2 = CouponFactory(account=account, currency=customer.currency)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoices",
        {
            "customer_id": str(customer.id),
            "coupons": [str(coupon1.id), str(coupon2.id)],
        },
    )

    assert response.status_code == 201
    assert [r["id"] for r in response.data["coupons"]] == [str(coupon1.id), str(coupon2.id)]


def test_create_invoice_with_coupons_invalid_currency(api_client, user, account):
    coupon1 = CouponFactory(account=account, currency="USD")
    coupon2 = CouponFactory(account=account, currency="EUR")
    customer = CustomerFactory(account=account, currency="USD")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoices",
        {
            "customer_id": str(customer.id),
            "coupons": [str(coupon1.id), str(coupon2.id)],
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "coupons.1",
                "code": "invalid",
                "detail": "Invalid coupon currency for this invoice.",
            }
        ],
    }


def test_create_invoice_with_duplicate_coupons(api_client, user, account):
    coupon = CouponFactory(account=account, currency="USD")
    customer = CustomerFactory(account=account, currency="USD")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoices",
        {
            "customer_id": str(customer.id),
            "coupons": [str(coupon.id), str(coupon.id)],
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "coupons",
                "code": "duplicate",
                "detail": "Duplicate values are not allowed.",
            }
        ],
    }


def test_create_invoice_with_foreign_coupon(api_client, user, account):
    currency = "USD"
    coupon1 = CouponFactory(account=account, currency=currency)
    coupon2 = CouponFactory(currency=currency)  # Not linked to the account
    customer = CustomerFactory(account=account, currency=currency)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoices",
        {
            "customer_id": str(customer.id),
            "coupons": [str(coupon1.id), str(coupon2.id)],
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "coupons",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{coupon2.id}" - object does not exist.',
            }
        ],
    }


def test_create_invoice_coupons_limit_exceeded(api_client, user, account, settings):
    settings.MAX_INVOICE_COUPONS = 1
    currency = "USD"
    coupon1 = CouponFactory(account=account, currency=currency)
    coupon2 = CouponFactory(account=account, currency=currency)
    customer = CustomerFactory(account=account, currency=currency)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoices",
        {
            "customer_id": str(customer.id),
            "coupons": [str(coupon1.id), str(coupon2.id)],
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "coupons",
                "code": "invalid",
                "detail": "Ensure this list contains at most 1 items.",
            }
        ],
    }


def test_create_invoice_with_tax_rates(api_client, user, account):
    tax_rate1 = TaxRateFactory(account=account)
    tax_rate2 = TaxRateFactory(account=account)
    customer = CustomerFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoices",
        {
            "customer_id": str(customer.id),
            "tax_rates": [str(tax_rate1.id), str(tax_rate2.id)],
        },
    )

    assert response.status_code == 201
    assert [r["id"] for r in response.data["tax_rates"]] == [str(tax_rate1.id), str(tax_rate2.id)]


def test_create_invoice_with_duplicate_tax_rates(api_client, user, account):
    tax_rate = TaxRateFactory(account=account)
    customer = CustomerFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoices",
        {
            "customer_id": str(customer.id),
            "tax_rates": [str(tax_rate.id), str(tax_rate.id)],
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "tax_rates",
                "code": "duplicate",
                "detail": "Duplicate values are not allowed.",
            }
        ],
    }


def test_create_invoice_with_foreign_tax_rate(api_client, user, account):
    tax_rate1 = TaxRateFactory(account=account)
    tax_rate2 = TaxRateFactory()  # Not linked to the account
    customer = CustomerFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoices",
        {
            "customer_id": str(customer.id),
            "tax_rates": [str(tax_rate1.id), str(tax_rate2.id)],
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "tax_rates",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{tax_rate2.id}" - object does not exist.',
            }
        ],
    }


def test_create_invoice_tax_rates_limit_exceeded(api_client, user, account, settings):
    settings.MAX_INVOICE_TAX_RATES = 1
    tax_rate1 = TaxRateFactory(account=account)
    tax_rate2 = TaxRateFactory(account=account)
    customer = CustomerFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invoices",
        {
            "customer_id": str(customer.id),
            "tax_rates": [str(tax_rate1.id), str(tax_rate2.id)],
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "tax_rates",
                "code": "invalid",
                "detail": "Ensure this list contains at most 1 items.",
            }
        ],
    }
