import pytest

from apps.accounts.session import ACTIVE_ACCOUNT_SESSION_KEY
from tests.factories import AccountFactory, MemberFactory

pytestmark = pytest.mark.django_db


def test_switch_account(api_client, user):
    account = AccountFactory()
    MemberFactory(user=user, account=account)

    api_client.force_login(user)
    assert ACTIVE_ACCOUNT_SESSION_KEY not in api_client.session
    response = api_client.post(f"/api/v1/accounts/{account.id}/switch")

    assert response.status_code == 204
    assert api_client.session[ACTIVE_ACCOUNT_SESSION_KEY] == str(account.id)


def test_switch_account_requires_authentication(api_client, account):
    response = api_client.post(f"/api/v1/accounts/{account.id}/switch")

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
