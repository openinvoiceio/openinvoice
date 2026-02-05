import pytest

from openinvoice.accounts.choices import MemberRole
from openinvoice.accounts.models import Member
from tests.factories import AccountFactory, BusinessProfileFactory, MemberFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_delete_member(api_client, user, account):
    email = "test@example.com"
    user_2 = UserFactory(email=email, username=email, name="Test User")
    account_2 = AccountFactory(default_business_profile=BusinessProfileFactory(name="Test Account 2"))
    member_1 = MemberFactory(user=user_2, account=account, role=MemberRole.MEMBER)
    MemberFactory(user=user_2, account=account_2, role=MemberRole.OWNER)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/accounts/{account.id}/members/{member_1.id}")

    assert response.status_code == 204

    response = api_client.get(f"/api/v1/accounts/{account.id}/members/{member_1.id}")
    assert response.status_code == 404
    assert Member.objects.filter(user=user_2, account=account_2).exists()
    assert Member.objects.filter(user=user_2, account=account).exists() is False


def test_delete_member_requires_authentication(api_client, user, account):
    member = Member.objects.get(user=user, account=account)

    response = api_client.delete(f"/api/v1/accounts/{account.id}/members/{member.id}")

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


def test_delete_member_requires_account(api_client, user, account):
    member = Member.objects.get(user=user, account=account)
    other_user = UserFactory(email="test@example.com", username="test")

    api_client.force_login(other_user)
    response = api_client.delete(f"/api/v1/accounts/{account.id}/members/{member.id}")

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
