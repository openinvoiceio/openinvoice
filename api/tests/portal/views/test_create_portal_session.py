import uuid

import pytest
from drf_standardized_errors.types import ErrorType

from apps.portal.crypto import sign_portal_token
from tests.factories import CustomerFactory

pytestmark = pytest.mark.django_db


def test_create_portal_session(api_client, user, account, settings):
    customer = CustomerFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post("/api/v1/portal/sessions", {"customer_id": str(customer.id)})

    assert response.status_code == 200
    expected_token = sign_portal_token(customer)
    assert response.data == {"portal_url": f"{settings.BASE_URL}/customer-portal/{expected_token}"}


def test_create_portal_session_requires_authentication(api_client):
    response = api_client.post("/api/v1/portal/sessions", {"customer_id": str(uuid.uuid4())})

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


def test_create_portal_session_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.post("/api/v1/portal/sessions", {"customer_id": str(uuid.uuid4())})

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


def test_create_portal_session_rejects_foreign_account(api_client, user, account):
    other_customer = CustomerFactory()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post("/api/v1/portal/sessions", {"customer_id": str(other_customer.id)})

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "customer_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{other_customer.id}" - object does not exist.',
            }
        ],
    }


def test_create_portal_session_customer_not_found(api_client, user, account):
    non_existent_customer_id = uuid.uuid4()

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post("/api/v1/portal/sessions", {"customer_id": str(non_existent_customer_id)})

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "customer_id",
                "code": "does_not_exist",
                "detail": f'Invalid pk "{non_existent_customer_id}" - object does not exist.',
            }
        ],
    }
