import uuid
from unittest.mock import ANY

import pytest

from openinvoice.accounts.choices import MemberRole
from openinvoice.accounts.models import Member
from tests.factories import AccountFactory, BusinessProfileFactory, MemberFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_list_members(api_client, user, account):
    member_1 = Member.objects.get(user=user, account=account)
    email = "test@example.com"
    user_2 = UserFactory(email=email, username=email, name="Test User")
    member_2 = MemberFactory(user=user_2, account=account, role=MemberRole.MEMBER)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/accounts/{account.id}/members")

    assert response.status_code == 200
    assert response.data["count"] == 2
    assert response.data["results"] == [
        {
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
        for member in [member_2, member_1]
    ]


def test_list_members_requires_authentication(api_client):
    response = api_client.get(f"/api/v1/accounts/{uuid.uuid4()}/members")

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


def test_list_members_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.get(f"/api/v1/accounts/{uuid.uuid4()}/members")

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


def test_list_members_from_other_account(api_client, user, account):
    other_user = UserFactory(email="other@example.com", username="other")
    other_account = AccountFactory(default_business_profile=BusinessProfileFactory(name="Other Account"))
    other_member = MemberFactory(account=other_account, user=other_user)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/accounts/{other_member.account_id}/members")

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
