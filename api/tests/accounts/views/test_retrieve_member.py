from unittest.mock import ANY

import pytest
from drf_standardized_errors.types import ErrorType

from apps.accounts.models import Member
from tests.factories import AccountFactory, MemberFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_retrieve_member(api_client, user, account):
    member = Member.objects.get(user=user, account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/accounts/{account.id}/members/{member.id}")

    assert response.status_code == 200
    assert response.data == {
        "id": member.id,
        "user": {
            "id": member.user.id,
            "name": member.user.name,
            "email": member.user.email,
            "avatar_url": None,
            "avatar_id": None,
            "active_account_id": str(account.id),
            "joined_at": ANY,
            "has_usable_password": True,
        },
        "account_id": str(account.id),
        "role": member.role,
        "joined_at": ANY,
    }


def test_retrieve_member_requires_authentication(api_client, account):
    member = Member.objects.filter(account=account).first()

    response = api_client.get(f"/api/v1/accounts/{account.id}/members/{member.id}")

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


def test_retrieve_member_requires_account(api_client, user):
    account = AccountFactory()
    other_user = UserFactory(email="test@example.com", username="test")
    member = MemberFactory(account=account, user=other_user)

    api_client.force_login(user)
    response = api_client.get(f"/api/v1/accounts/{account.id}/members/{member.id}")

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
