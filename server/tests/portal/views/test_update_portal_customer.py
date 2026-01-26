import pytest

from tests.factories import CustomerFactory, CustomerShippingFactory, PortalTokenFactory

pytestmark = pytest.mark.django_db


def test_update_customer_via_portal(api_client, account):
    customer = CustomerFactory(account=account, name="Old")
    token = PortalTokenFactory(customer=customer)["token"]

    response = api_client.put(
        "/api/v1/portal/customer",
        {
            "name": "New",
            "email": "new@example.com",
            "phone": "123",
            "legal_name": "LN",
            "legal_number": "42",
            "address": {"line1": "New line1"},
            "shipping": {"address": {"country": "US"}},
        },
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert response.status_code == 200
    assert response.data == {
        "id": str(customer.id),
        "name": "New",
        "legal_name": "LN",
        "legal_number": "42",
        "email": "new@example.com",
        "phone": "123",
        "address": {
            "line1": "New line1",
            "line2": customer.address.line2,
            "locality": customer.address.locality,
            "state": customer.address.state,
            "postal_code": customer.address.postal_code,
            "country": customer.address.country,
        },
        "shipping": {
            "name": None,
            "phone": None,
            "address": {
                "line1": None,
                "line2": None,
                "locality": None,
                "state": None,
                "postal_code": None,
                "country": "US",
            },
        },
        "tax_ids": [],
    }


def test_update_customer_requires_authentication(api_client):
    response = api_client.put("/api/v1/portal/customer", {"name": "New"})

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


def test_update_customer_shipping_partial_update(api_client, account):
    shipping = CustomerShippingFactory(name="Portal Ship", phone="222")
    customer = CustomerFactory(account=account, shipping=shipping)
    token = PortalTokenFactory(customer=customer)["token"]

    response = api_client.put(
        "/api/v1/portal/customer",
        {
            "shipping": {
                "phone": "999",
                "address": {"line1": "Portal Line"},
            }
        },
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert response.status_code == 200
    customer.refresh_from_db()
    assert customer.shipping is not None
    assert customer.shipping.name == "Portal Ship"
    assert customer.shipping.phone == "999"
    assert customer.shipping.address.line1 == "Portal Line"
    assert customer.shipping.address.line2 == customer.shipping.address.line2


def test_update_customer_remover_shipping(api_client, account):
    shipping = CustomerShippingFactory()
    customer = CustomerFactory(account=account, shipping=shipping)
    token = PortalTokenFactory(customer=customer)["token"]

    response = api_client.put(
        "/api/v1/portal/customer",
        {"shipping": None},
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert response.status_code == 200
    customer.refresh_from_db()
    assert customer.shipping is None


def test_update_customer_add_shipping(api_client, account):
    customer = CustomerFactory(account=account)
    token = PortalTokenFactory(customer=customer)["token"]

    response = api_client.put(
        "/api/v1/portal/customer",
        {
            "shipping": {
                "name": "Portal New",
                "phone": "333",
                "address": {"line1": "Portal New", "country": "US"},
            }
        },
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert response.status_code == 200
    customer.refresh_from_db()
    assert customer.shipping is not None
    assert customer.shipping.name == "Portal New"
    assert customer.shipping.phone == "333"
    assert customer.shipping.address.line1 == "Portal New"
    assert customer.shipping.address.country == "US"


def test_update_customer_remove_shipping_missing(api_client, account):
    customer = CustomerFactory(account=account)
    token = PortalTokenFactory(customer=customer)["token"]

    response = api_client.put(
        "/api/v1/portal/customer",
        {"shipping": None},
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert response.status_code == 200
    customer.refresh_from_db()
    assert customer.shipping is None
