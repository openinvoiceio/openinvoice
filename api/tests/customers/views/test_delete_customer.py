import pytest
from drf_standardized_errors.types import ErrorType

from tests.factories import CustomerFactory, InvoiceFactory

pytestmark = pytest.mark.django_db


def test_delete_customer(api_client, user, account):
    customer = CustomerFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/customers/{customer.id}")

    assert response.status_code == 204


def test_delete_customer_with_invoices(api_client, user, account):
    customer = CustomerFactory(account=account)
    InvoiceFactory(customer=customer)

    api_client.force_login(user)
    api_client.force_account(account)

    response = api_client.delete(f"/api/v1/customers/{customer.id}")

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": None,
                "code": "invalid",
                "detail": "Customer with invoices cannot be deleted",
            }
        ],
    }


def test_delete_customer_requires_account(api_client, user):
    customer = CustomerFactory()
    api_client.force_login(user)
    response = api_client.delete(f"/api/v1/customers/{customer.id}")

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


def test_delete_customer_requires_authentication(api_client, account):
    customer = CustomerFactory(account=account)

    response = api_client.delete(f"/api/v1/customers/{customer.id}")

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
