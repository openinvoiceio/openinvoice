import uuid

import pytest
from drf_standardized_errors.types import ErrorType

from tests.factories import TaxIdFactory

pytestmark = pytest.mark.django_db


def test_delete_account_tax_id(api_client, user, account):
    tax_id = TaxIdFactory()
    account.tax_ids.add(tax_id)
    api_client.force_login(user)
    api_client.force_account(account)

    response = api_client.delete(f"/api/v1/accounts/{account.id}/tax-ids/{tax_id.id}")

    assert response.status_code == 204
    assert account.tax_ids.count() == 0


def test_delete_account_tax_id_not_found(api_client, user, account):
    api_client.force_login(user)
    api_client.force_account(account)

    response = api_client.delete(f"/api/v1/accounts/{account.id}/tax-ids/{uuid.uuid4()}")

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


def test_delete_account_tax_id_requires_authentication(api_client):
    response = api_client.delete(f"/api/v1/accounts/{uuid.uuid4()}/tax-ids/{uuid.uuid4()}")

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


def test_delete_account_tax_id_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.delete(f"/api/v1/accounts/{uuid.uuid4()}/tax-ids/{uuid.uuid4()}")

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
