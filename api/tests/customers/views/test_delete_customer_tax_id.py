import uuid

import pytest

from tests.factories import CustomerFactory, TaxIdFactory

pytestmark = pytest.mark.django_db


def test_delete_customer_tax_id(api_client, user, account):
    customer = CustomerFactory(account=account)
    tax_id = TaxIdFactory()
    customer.tax_ids.add(tax_id)
    api_client.force_login(user)
    api_client.force_account(account)

    response = api_client.delete(f"/api/v1/customers/{customer.id}/tax-ids/{tax_id.id}")

    assert response.status_code == 204
    assert customer.tax_ids.count() == 0


def test_delete_customer_tax_id_not_found(api_client, user, account):
    customer = CustomerFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)

    response = api_client.delete(f"/api/v1/customers/{customer.id}/tax-ids/{uuid.uuid4()}")

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


def test_delete_customer_tax_id_requires_authentication(api_client):
    response = api_client.delete(f"/api/v1/customers/{uuid.uuid4()}/tax-ids/{uuid.uuid4()}")

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


def test_delete_customer_tax_id_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.delete(f"/api/v1/customers/{uuid.uuid4()}/tax-ids/{uuid.uuid4()}")

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
