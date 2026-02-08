import uuid
from unittest.mock import ANY

import pytest

from tests.factories import CustomerFactory

pytestmark = pytest.mark.django_db


def test_create_billing_profile(api_client, user, account):
    customer = CustomerFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/billing-profiles",
        {
            "customer_id": str(customer.id),
        },
    )

    assert response.status_code == 201
    assert response.data == {
        "id": ANY,
        "legal_name": None,
        "legal_number": None,
        "email": None,
        "phone": None,
        "address": {
            "line1": None,
            "line2": None,
            "locality": None,
            "state": None,
            "postal_code": None,
            "country": None,
        },
        "tax_ids": [],
        "created_at": ANY,
        "updated_at": ANY,
    }


def test_create_billing_profile_customer_not_found(api_client, user, account):
    customer_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/billing-profiles",
        {
            "customer_id": str(customer_id),
        },
    )

    assert response.status_code == 400
    assert response.data == {
        "type": "validation_error",
        "errors": [
            {
                "attr": "customer_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{customer_id}" - object does not exist.',
            }
        ],
    }


def test_create_billing_profile_customer_foreign_account(api_client, user, account):
    customer = CustomerFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/billing-profiles",
        {
            "customer_id": str(customer.id),
        },
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


def test_create_billing_profile_requires_authentication(api_client):
    response = api_client.post(
        "/api/v1/billing-profiles",
        {
            "customer_id": str(uuid.uuid4()),
        },
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


def test_create_billing_profile_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.post(
        "/api/v1/billing-profiles",
        {
            "customer_id": str(uuid.uuid4()),
        },
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
