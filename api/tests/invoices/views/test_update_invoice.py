import uuid
from decimal import Decimal
from unittest.mock import ANY

import pytest
from django.utils import timezone
from drf_standardized_errors.types import ErrorType

from apps.integrations.choices import PaymentProvider
from apps.invoices.choices import InvoiceDeliveryMethod, InvoiceStatus
from apps.invoices.models import InvoiceCoupon, InvoiceTaxRate
from common.choices import FeatureCode
from tests.factories import (
    CouponFactory,
    CustomerFactory,
    InvoiceCouponFactory,
    InvoiceFactory,
    InvoiceShippingFactory,
    InvoiceTaxRateFactory,
    NumberingSystemFactory,
    ShippingRateFactory,
    StripeConnectionFactory,
    TaxRateFactory,
)

pytestmark = pytest.mark.django_db


def test_update_invoice(api_client, user, account):
    invoice = InvoiceFactory(account=account, currency="PLN")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {
            "customer_id": str(invoice.customer.id),
            "number": "INV-10",
            "numbering_system_id": None,
            "currency": "USD",
            "issue_date": None,
            "sell_date": None,
            "due_date": invoice.due_date.isoformat(),
            "metadata": {},
            "custom_fields": {},
            "footer": None,
            "description": None,
        },
    )

    assert response.status_code == 200
    invoice.refresh_from_db()
    assert response.data == {
        "id": str(invoice.id),
        "status": invoice.status,
        "number": invoice.effective_number,
        "numbering_system_id": None,
        "currency": invoice.currency,
        "tax_behavior": invoice.tax_behavior,
        "issue_date": None,
        "sell_date": None,
        "due_date": invoice.due_date.isoformat(),
        "net_payment_term": invoice.net_payment_term,
        "customer": {
            "id": str(invoice.customer.id),
            "name": invoice.customer.name,
            "legal_name": invoice.customer.legal_name,
            "legal_number": invoice.customer.legal_number,
            "email": invoice.customer.email,
            "phone": invoice.customer.phone,
            "description": invoice.customer.description,
            "billing_address": {
                "line1": invoice.customer.billing_address.line1,
                "line2": invoice.customer.billing_address.line2,
                "locality": invoice.customer.billing_address.locality,
                "state": invoice.customer.billing_address.state,
                "postal_code": invoice.customer.billing_address.postal_code,
                "country": invoice.customer.billing_address.country,
            },
            "shipping_address": {
                "line1": invoice.customer.shipping_address.line1,
                "line2": invoice.customer.shipping_address.line2,
                "locality": invoice.customer.shipping_address.locality,
                "state": invoice.customer.shipping_address.state,
                "postal_code": invoice.customer.shipping_address.postal_code,
                "country": invoice.customer.shipping_address.country,
            },
            "logo_id": None,
        },
        "account": {
            "id": str(invoice.account.id),
            "name": invoice.account.name,
            "legal_name": invoice.account.legal_name,
            "legal_number": invoice.account.legal_number,
            "email": invoice.account.email,
            "phone": invoice.account.phone,
            "address": {
                "line1": invoice.account.address.line1,
                "line2": invoice.account.address.line2,
                "locality": invoice.account.address.locality,
                "state": invoice.account.address.state,
                "postal_code": invoice.account.address.postal_code,
                "country": invoice.account.address.country,
            },
            "logo_id": None,
        },
        "metadata": {},
        "custom_fields": {},
        "footer": None,
        "description": None,
        "delivery_method": InvoiceDeliveryMethod.MANUAL,
        "recipients": [],
        "subtotal_amount": f"{invoice.subtotal_amount.amount:.2f}",
        "total_discount_amount": f"{invoice.total_discount_amount.amount:.2f}",
        "total_excluding_tax_amount": f"{invoice.total_excluding_tax_amount.amount:.2f}",
        "shipping_amount": f"{invoice.shipping_amount.amount:.2f}",
        "total_tax_amount": f"{invoice.total_tax_amount.amount:.2f}",
        "total_amount": f"{invoice.total_amount.amount:.2f}",
        "total_credit_amount": f"{invoice.total_credit_amount.amount:.2f}",
        "total_paid_amount": f"{invoice.total_paid_amount.amount:.2f}",
        "outstanding_amount": f"{invoice.outstanding_amount.amount:.2f}",
        "payment_provider": None,
        "payment_connection_id": None,
        "created_at": ANY,
        "updated_at": ANY,
        "opened_at": None,
        "paid_at": None,
        "voided_at": None,
        "pdf_id": None,
        "lines": [],
        "coupons": [],
        "discounts": [],
        "total_discounts": [],
        "tax_rates": [],
        "taxes": [],
        "total_taxes": [],
        "shipping": None,
    }


def test_update_invoice_change_customer(api_client, user, account):
    customer1 = CustomerFactory(account=account)
    invoice = InvoiceFactory(account=account, customer=customer1)
    customer2 = CustomerFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {
            "customer_id": str(customer2.id),
            "number": invoice.effective_number,
            "numbering_system_id": None,
            "currency": invoice.currency,
            "issue_date": None,
            "sell_date": None,
            "due_date": invoice.due_date.isoformat(),
            "metadata": {},
            "custom_fields": {},
            "footer": None,
            "description": None,
        },
    )

    assert response.status_code == 200
    invoice.refresh_from_db()
    assert invoice.customer_id == customer2.id
    assert response.data["customer"]["id"] == str(customer2.id)


def test_update_invoice_add_shipping(api_client, user, account):
    invoice = InvoiceFactory(account=account, currency="PLN")
    shipping_rate = ShippingRateFactory(account=account, amount=Decimal(20))
    tax_rate = TaxRateFactory(account=account, percentage=Decimal(10))

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {
            "shipping": {
                "shipping_rate_id": str(shipping_rate.id),
                "tax_rates": [str(tax_rate.id)],
            },
        },
    )

    assert response.status_code == 200
    assert response.data["shipping"] == {
        "amount": "20.00",
        "total_excluding_tax_amount": "18.18",
        "total_tax_amount": "1.82",
        "total_tax_rate": "10.00",
        "total_amount": "20.00",
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
                "updated_at": ANY,
                "created_at": ANY,
                "archived_at": tax_rate.archived_at,
            }
        ],
        "total_taxes": [
            {
                "tax_rate_id": str(tax_rate.id),
                "amount": "1.82",
            }
        ],
    }
    assert response.data["shipping_amount"] == "20.00"
    assert response.data["total_tax_amount"] == "1.82"
    assert response.data["total_amount"] == "20.00"


def test_update_invoice_existing_shipping(api_client, user, account):
    shipping_rate = ShippingRateFactory(account=account, amount=Decimal(20))
    tax_rate = TaxRateFactory(account=account, percentage=Decimal(10))
    invoice = InvoiceFactory(
        account=account,
        currency="PLN",
        shipping_amount=Decimal(20),
        total_tax_amount=Decimal(2),
        total_amount=Decimal(22),
    )
    shipping = InvoiceShippingFactory(
        amount=shipping_rate.amount, total_tax_amount=Decimal(2), total_amount=Decimal(22), shipping_rate=shipping_rate
    )
    shipping.set_tax_rates([tax_rate])
    invoice.shipping = shipping
    invoice.save()

    new_shipping_rate = ShippingRateFactory(account=account, amount=Decimal(30))
    new_tax_rate = TaxRateFactory(account=account, percentage=Decimal(15))

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {
            "shipping": {
                "shipping_rate_id": str(new_shipping_rate.id),
                "tax_rates": [str(new_tax_rate.id)],
            },
        },
    )

    assert response.status_code == 200
    assert response.data["shipping"] == {
        "amount": "30.00",
        "total_excluding_tax_amount": "26.09",
        "total_tax_amount": "3.91",
        "total_tax_rate": "15.00",
        "total_amount": "30.00",
        "shipping_rate_id": str(new_shipping_rate.id),
        "tax_rates": [
            {
                "id": str(new_tax_rate.id),
                "account_id": str(account.id),
                "name": new_tax_rate.name,
                "description": new_tax_rate.description,
                "country": new_tax_rate.country,
                "percentage": f"{new_tax_rate.percentage:.2f}",
                "status": new_tax_rate.status,
                "updated_at": ANY,
                "created_at": ANY,
                "archived_at": new_tax_rate.archived_at,
            }
        ],
        "total_taxes": [
            {
                "tax_rate_id": str(new_tax_rate.id),
                "amount": "3.91",
            }
        ],
    }
    assert response.data["shipping_amount"] == "30.00"
    assert response.data["total_tax_amount"] == "3.91"
    assert response.data["total_amount"] == "30.00"


def test_update_invoice_remove_shipping(api_client, user, account):
    shipping_rate = ShippingRateFactory(account=account, amount=Decimal(20))
    tax_rate = TaxRateFactory(account=account, percentage=Decimal(10))
    invoice = InvoiceFactory(
        account=account,
        currency="PLN",
        shipping_amount=Decimal(20),
        total_tax_amount=Decimal(2),
        total_amount=Decimal(22),
    )
    shipping = InvoiceShippingFactory(
        amount=shipping_rate.amount, total_tax_amount=Decimal(2), total_amount=Decimal(22), shipping_rate=shipping_rate
    )
    shipping.set_tax_rates([tax_rate])
    invoice.shipping = shipping
    invoice.save()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {"shipping": None},
    )

    assert response.status_code == 200
    assert response.data["shipping"] is None
    assert response.data["shipping_amount"] == "0.00"
    assert response.data["total_tax_amount"] == "0.00"
    assert response.data["total_amount"] == "0.00"


def test_update_invoice_remove_shipping_without_existing_shipping(api_client, user, account):
    invoice = InvoiceFactory(account=account, currency="PLN")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {"shipping": None},
    )

    assert response.status_code == 200
    assert response.data["shipping"] is None
    assert response.data["shipping_amount"] == "0.00"
    assert response.data["total_tax_amount"] == "0.00"
    assert response.data["total_amount"] == "0.00"


def test_update_invoice_invalid_shipping_rate(api_client, user, account):
    invoice = InvoiceFactory(account=account, currency="PLN")
    shipping_rate_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {
            "shipping": {
                "shipping_rate_id": str(shipping_rate_id),
            },
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "shipping.shipping_rate_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{shipping_rate_id}" - object does not exist.',
            }
        ],
    }


def test_update_invoice_foreign_shipping_rate(api_client, user, account):
    invoice = InvoiceFactory(account=account, currency="PLN")
    shipping_rate = ShippingRateFactory()  # Different account

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {
            "shipping": {
                "shipping_rate_id": str(shipping_rate.id),
            },
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "shipping.shipping_rate_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{shipping_rate.id}" - object does not exist.',
            }
        ],
    }


def test_update_invoice_shipping_invalid_tax_rate(api_client, user, account):
    invoice = InvoiceFactory(account=account, currency="PLN")
    shipping_rate = ShippingRateFactory(account=account)
    tax_rate_id_1 = uuid.uuid4()
    tax_rate_id_2 = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {
            "shipping": {
                "shipping_rate_id": str(shipping_rate.id),
                "tax_rates": [str(tax_rate_id_1), str(tax_rate_id_2)],
            },
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "shipping.tax_rates",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{tax_rate_id_1}" - object does not exist.',
            }
        ],
    }


def test_update_invoice_shipping_foreign_tax_rate(api_client, user, account):
    invoice = InvoiceFactory(account=account, currency="PLN")
    shipping_rate = ShippingRateFactory(account=account)
    tax_rate = TaxRateFactory(account=account)
    foreign_tax_rate = TaxRateFactory()  # Different account

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {
            "shipping": {
                "shipping_rate_id": str(shipping_rate.id),
                "tax_rates": [str(tax_rate.id), str(foreign_tax_rate.id)],
            },
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "shipping.tax_rates",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{foreign_tax_rate.id}" - object does not exist.',
            }
        ],
    }


def test_update_invoice_shipping_duplicate_tax_rates(api_client, user, account):
    invoice = InvoiceFactory(account=account, currency="PLN")
    shipping_rate = ShippingRateFactory(account=account)
    tax_rate = TaxRateFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {
            "shipping": {
                "shipping_rate_id": str(shipping_rate.id),
                "tax_rates": [str(tax_rate.id), str(tax_rate.id)],
            },
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "shipping.tax_rates",
                "code": "duplicate",
                "detail": "Duplicate values are not allowed.",
            }
        ],
    }


def test_update_invoice_shipping_tax_rates_limit_exceeded(api_client, user, account, settings):
    settings.MAX_INVOICE_TAX_RATES = 1
    invoice = InvoiceFactory(account=account, currency="PLN")
    shipping_rate = ShippingRateFactory(account=account, currency=invoice.currency)
    tax_rate1 = TaxRateFactory(account=account)
    tax_rate2 = TaxRateFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {
            "shipping": {
                "shipping_rate_id": str(shipping_rate.id),
                "tax_rates": [str(tax_rate1.id), str(tax_rate2.id)],
            }
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "shipping.tax_rates",
                "code": "invalid",
                "detail": "Ensure this list contains at most 1 items.",
            }
        ],
    }


def test_update_invoice_payment_provider(api_client, user, account):
    invoice = InvoiceFactory(account=account, currency="PLN")
    connection = StripeConnectionFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {"payment_provider": PaymentProvider.STRIPE, "payment_connection_id": str(connection.id)},
    )

    assert response.status_code == 200
    assert response.data["payment_provider"] == PaymentProvider.STRIPE
    assert response.data["payment_connection_id"] == str(connection.id)


def test_update_invoice_with_unknown_payment_connection(api_client, user, account):
    connection_id = uuid.uuid4()
    invoice = InvoiceFactory(account=account, currency="PLN")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {"payment_provider": PaymentProvider.STRIPE, "payment_connection_id": str(connection_id)},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "payment_connection_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{connection_id}" - object does not exist.',
            }
        ],
    }


def test_update_invoice_payment_provider_without_connection(api_client, user, account):
    connection = StripeConnectionFactory(account=account)
    invoice = InvoiceFactory(
        account=account, currency="PLN", payment_provider=PaymentProvider.STRIPE, payment_connection_id=connection.id
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {"payment_provider": PaymentProvider.STRIPE, "payment_connection_id": None},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "non_field_errors",
                "code": "invalid",
                "detail": "Fields payment_provider, payment_connection_id must be provided together.",
            }
        ],
    }


def test_update_invoice_revision_requires_same_customer(api_client, user, account):
    invoice = InvoiceFactory(account=account, status=InvoiceStatus.OPEN)
    revision = InvoiceFactory(head=invoice.head, account=account, customer=invoice.customer, previous_revision=invoice)
    other_customer = CustomerFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{revision.id}",
        {
            "customer_id": str(other_customer.id),
            "number": revision.number,
            "numbering_system_id": None,
            "currency": revision.currency,
            "issue_date": None,
            "sell_date": None,
            "due_date": revision.due_date.isoformat(),
            "metadata": {},
            "custom_fields": {},
            "footer": revision.footer,
            "description": revision.description,
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "customer_id",
                "code": "invalid",
                "detail": "Revision must use the same customer",
            }
        ],
    }


def test_update_invoice_customer_not_found(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    customer_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {
            "customer_id": str(customer_id),
            "number": invoice.effective_number,
            "numbering_system_id": None,
            "currency": invoice.currency,
            "issue_date": None,
            "sell_date": None,
            "due_date": invoice.due_date.isoformat(),
            "metadata": {},
            "custom_fields": {},
            "footer": None,
            "description": None,
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "customer_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{customer_id}" - object does not exist.',
            }
        ],
    }


def test_update_invoice_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.put(
        f"/api/v1/invoices/{uuid.uuid4()}",
        {
            "customer_id": str(uuid.uuid4()),
            "number": "INV-1",
            "numbering_system_id": None,
            "currency": "PLN",
            "issue_date": None,
            "sell_date": None,
            "due_date": None,
            "metadata": {},
            "custom_fields": {},
            "footer": None,
            "description": None,
        },
    )

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


def test_update_invoice_rejects_foreign_account(api_client, user, account):
    other_invoice = InvoiceFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{other_invoice.id}",
        {
            "customer_id": str(other_invoice.customer.id),
            "number": other_invoice.number,
            "numbering_system_id": None,
            "currency": other_invoice.currency,
            "issue_date": None,
            "sell_date": None,
            "due_date": other_invoice.due_date.isoformat(),
            "metadata": {},
            "custom_fields": {},
            "footer": None,
            "description": None,
        },
    )

    assert response.status_code == 404
    assert response.data == {
        "type": ErrorType.CLIENT_ERROR,
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
        InvoiceStatus.OPEN,
        InvoiceStatus.PAID,
        InvoiceStatus.VOIDED,
    ],
)
def test_update_invoice_non_draft(api_client, user, account, status):
    invoice = InvoiceFactory(account=account, status=status)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {
            "customer_id": str(invoice.customer.id),
            "number": invoice.effective_number,
            "numbering_system_id": None,
            "currency": invoice.currency,
            "issue_date": None,
            "sell_date": None,
            "due_date": invoice.due_date.isoformat(),
            "metadata": {},
            "custom_fields": {},
            "footer": None,
            "description": None,
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Only draft invoices can be updated",
            }
        ],
    }


def test_update_invoice_numbering_system_not_found(api_client, user, account):
    invoice = InvoiceFactory(account=account)
    numbering_system_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {
            "customer_id": str(invoice.customer.id),
            "number": None,
            "numbering_system_id": str(numbering_system_id),
            "currency": invoice.currency,
            "issue_date": None,
            "sell_date": None,
            "due_date": invoice.due_date.isoformat(),
            "metadata": {},
            "custom_fields": {},
            "footer": None,
            "description": None,
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "numbering_system_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{numbering_system_id}" - object does not exist.',
            }
        ],
    }


def test_update_invoice_assign_numbering_system(api_client, user, account):
    numbering_system = NumberingSystemFactory(account=account)
    invoice = InvoiceFactory(account=account, number="MANUAL", numbering_system=None)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {
            "customer_id": str(invoice.customer_id),
            "number": None,
            "numbering_system_id": str(numbering_system.id),
            "currency": invoice.currency,
            "issue_date": None,
            "sell_date": None,
            "due_date": invoice.due_date.isoformat(),
            "metadata": {},
            "custom_fields": {},
            "footer": None,
            "description": None,
        },
    )

    assert response.status_code == 200
    invoice.refresh_from_db()
    assert invoice.number is None
    assert invoice.effective_number == "INV-1"
    assert invoice.numbering_system_id == numbering_system.id
    assert response.data["number"] == "INV-1"
    assert response.data["numbering_system_id"] == str(numbering_system.id)


def test_update_invoice_assign_numbering_system_existing_invoices(api_client, user, account):
    numbering_system = NumberingSystemFactory(account=account)
    InvoiceFactory(
        account=account,
        numbering_system=numbering_system,
        number="INV-1",
        status=InvoiceStatus.OPEN,
        opened_at=timezone.now(),
    )
    invoice = InvoiceFactory(account=account, number="MANUAL", numbering_system=None)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {
            "customer_id": str(invoice.customer_id),
            "number": None,
            "numbering_system_id": str(numbering_system.id),
            "currency": invoice.currency,
            "issue_date": None,
            "sell_date": None,
            "due_date": invoice.due_date.isoformat(),
            "metadata": {},
            "custom_fields": {},
            "footer": None,
            "description": None,
        },
    )

    assert response.status_code == 200
    invoice.refresh_from_db()
    assert invoice.number is None
    assert invoice.effective_number == "INV-2"
    assert invoice.numbering_system_id == numbering_system.id
    assert response.data["number"] == "INV-2"
    assert response.data["numbering_system_id"] == str(numbering_system.id)


def test_update_invoice_switch_to_manual_number(api_client, user, account):
    numbering_system = NumberingSystemFactory(account=account)
    invoice = InvoiceFactory(account=account, numbering_system=numbering_system, number="INV-1")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {
            "customer_id": str(invoice.customer_id),
            "number": "MAN-1",
            "numbering_system_id": None,
            "currency": invoice.currency,
            "issue_date": None,
            "sell_date": None,
            "due_date": invoice.due_date.isoformat(),
            "metadata": {},
            "custom_fields": {},
            "footer": None,
            "description": None,
        },
    )

    assert response.status_code == 200
    invoice.refresh_from_db()
    assert invoice.number == "MAN-1"
    assert invoice.numbering_system_id is None
    assert response.data["number"] == "MAN-1"
    assert response.data["numbering_system_id"] is None


def test_update_invoice_with_automatic_delivery_and_without_entitlement(api_client, user, account, settings):
    settings.DEFAULT_PLAN = "test"
    settings.PLANS = {"test": {"features": {FeatureCode.AUTOMATIC_INVOICE_DELIVERY: False}}}
    invoice = InvoiceFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {"delivery_method": InvoiceDeliveryMethod.AUTOMATIC},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "delivery_method",
                "code": "invalid",
                "detail": "Automatic delivery is forbidden for your account.",
            }
        ],
    }


def test_update_invoice_requires_authentication(api_client, account):
    invoice = InvoiceFactory(account=account)

    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {
            "customer_id": str(invoice.customer_id),
            "number": invoice.effective_number,
        },
    )

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


def test_update_invoice_with_coupons(api_client, user, account):
    customer = CustomerFactory(account=account)
    invoice = InvoiceFactory(account=account, customer=customer)
    coupon1 = CouponFactory(account=account, currency=invoice.currency)
    coupon2 = CouponFactory(account=account, currency=invoice.currency)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {"coupons": [str(coupon1.id), str(coupon2.id)]},
    )

    assert response.status_code == 200
    assert [r["id"] for r in response.data["coupons"]] == [str(coupon1.id), str(coupon2.id)]


def test_update_invoice_coupons_change_position(api_client, user, account):
    customer = CustomerFactory(account=account)
    invoice = InvoiceFactory(account=account, customer=customer)
    coupon1 = CouponFactory(account=account, currency=invoice.currency)
    coupon2 = CouponFactory(account=account, currency=invoice.currency)
    invoice_coupon1 = InvoiceCouponFactory(invoice=invoice, coupon=coupon1, position=1)
    invoice_coupon2 = InvoiceCouponFactory(invoice=invoice, coupon=coupon2, position=2)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {"coupons": [str(coupon2.id), str(coupon1.id)]},
    )

    assert response.status_code == 200
    assert [r["id"] for r in response.data["coupons"]] == [str(coupon2.id), str(coupon1.id)]
    assert InvoiceCoupon.objects.filter(id__in=[invoice_coupon1.id, invoice_coupon2.id]).exists() is False
    assert invoice.coupons.count() == 2
    assert invoice.invoice_coupons.get(coupon_id=coupon1.id).position == 1
    assert invoice.invoice_coupons.get(coupon_id=coupon2.id).position == 0


def test_update_invoice_remove_coupons(api_client, user, account):
    customer = CustomerFactory(account=account)
    invoice = InvoiceFactory(account=account, customer=customer)
    coupon1 = CouponFactory(account=account, currency=invoice.currency)
    coupon2 = CouponFactory(account=account, currency=invoice.currency)
    InvoiceCouponFactory(invoice=invoice, coupon=coupon1, position=1)
    InvoiceCouponFactory(invoice=invoice, coupon=coupon2, position=2)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {"coupons": []},
    )

    assert response.status_code == 200
    assert response.data["coupons"] == []
    assert invoice.coupons.count() == 0


def test_update_invoice_with_coupons_invalid_currency(api_client, user, account):
    customer = CustomerFactory(account=account)
    invoice = InvoiceFactory(account=account, customer=customer)
    coupon1 = CouponFactory(account=account, currency=invoice.currency)
    coupon2 = CouponFactory(account=account, currency="EUR")

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {"coupons": [str(coupon1.id), str(coupon2.id)]},
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


def test_update_invoice_with_duplicate_coupons(api_client, user, account):
    customer = CustomerFactory(account=account)
    invoice = InvoiceFactory(account=account, customer=customer)
    coupon = CouponFactory(account=account, currency=invoice.currency)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {"coupons": [str(coupon.id), str(coupon.id)]},
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


def test_update_invoice_with_foreign_coupon(api_client, user, account):
    customer = CustomerFactory(account=account)
    invoice = InvoiceFactory(account=account, customer=customer)
    coupon1 = CouponFactory(account=account, currency=invoice.currency)
    coupon2 = CouponFactory(currency=invoice.currency)  # Not linked to the account

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {"coupons": [str(coupon1.id), str(coupon2.id)]},
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


def test_update_invoice_coupons_limit_exceeded(api_client, user, account, settings):
    settings.MAX_INVOICE_COUPONS = 1
    customer = CustomerFactory(account=account)
    invoice = InvoiceFactory(account=account, customer=customer)
    coupon1 = CouponFactory(account=account, currency=invoice.currency)
    coupon2 = CouponFactory(account=account, currency=invoice.currency)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {"coupons": [str(coupon1.id), str(coupon2.id)]},
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


def test_update_invoice_with_tax_rates(api_client, user, account):
    customer = CustomerFactory(account=account)
    invoice = InvoiceFactory(account=account, customer=customer)
    tax_rate1 = TaxRateFactory(account=account)
    tax_rate2 = TaxRateFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {"tax_rates": [str(tax_rate1.id), str(tax_rate2.id)]},
    )

    assert response.status_code == 200
    assert [r["id"] for r in response.data["tax_rates"]] == [str(tax_rate1.id), str(tax_rate2.id)]


def test_update_invoice_tax_rates_change_position(api_client, user, account):
    customer = CustomerFactory(account=account)
    invoice = InvoiceFactory(account=account, customer=customer)
    tax_rate1 = TaxRateFactory(account=account)
    tax_rate2 = TaxRateFactory(account=account)
    invoice_tax_rate1 = InvoiceTaxRateFactory(invoice=invoice, tax_rate=tax_rate1, position=1)
    invoice_tax_rate2 = InvoiceTaxRateFactory(invoice=invoice, tax_rate=tax_rate2, position=2)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {"tax_rates": [str(tax_rate2.id), str(tax_rate1.id)]},
    )

    assert response.status_code == 200
    assert [r["id"] for r in response.data["tax_rates"]] == [str(tax_rate2.id), str(tax_rate1.id)]
    assert InvoiceTaxRate.objects.filter(id__in=[invoice_tax_rate1.id, invoice_tax_rate2.id]).exists() is False
    assert invoice.tax_rates.count() == 2
    assert invoice.invoice_tax_rates.get(tax_rate_id=tax_rate1.id).position == 1
    assert invoice.invoice_tax_rates.get(tax_rate_id=tax_rate2.id).position == 0


def test_update_invoice_remove_tax_rates(api_client, user, account):
    customer = CustomerFactory(account=account)
    invoice = InvoiceFactory(account=account, customer=customer)
    tax_rate1 = TaxRateFactory(account=account)
    tax_rate2 = TaxRateFactory(account=account)
    InvoiceTaxRateFactory(invoice=invoice, tax_rate=tax_rate1, position=1)
    InvoiceTaxRateFactory(invoice=invoice, tax_rate=tax_rate2, position=2)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {"tax_rates": []},
    )

    assert response.status_code == 200
    assert response.data["tax_rates"] == []
    assert invoice.tax_rates.count() == 0


def test_update_invoice_with_duplicate_tax_rates(api_client, user, account):
    customer = CustomerFactory(account=account)
    invoice = InvoiceFactory(account=account, customer=customer)
    tax_rate = TaxRateFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {"tax_rates": [str(tax_rate.id), str(tax_rate.id)]},
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


def test_update_invoice_with_foreign_tax_rate(api_client, user, account):
    customer = CustomerFactory(account=account)
    invoice = InvoiceFactory(account=account, customer=customer)
    tax_rate1 = TaxRateFactory(account=account)
    tax_rate2 = TaxRateFactory()  # Not linked to the account

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {"tax_rates": [str(tax_rate1.id), str(tax_rate2.id)]},
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


def test_update_invoice_tax_rates_limit_exceeded(api_client, user, account, settings):
    settings.MAX_INVOICE_TAX_RATES = 1
    customer = CustomerFactory(account=account)
    invoice = InvoiceFactory(account=account, customer=customer)
    tax_rate1 = TaxRateFactory(account=account)
    tax_rate2 = TaxRateFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.put(
        f"/api/v1/invoices/{invoice.id}",
        {"tax_rates": [str(tax_rate1.id), str(tax_rate2.id)]},
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
