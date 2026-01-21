from unittest.mock import ANY

import pytest
from drf_standardized_errors.types import ErrorType

from apps.accounts.choices import InvitationStatus, MemberRole
from apps.accounts.models import Member
from tests.factories import InvitationFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_accept_invitation(api_client, account):
    email = "invitee@example.com"
    invitation = InvitationFactory(account=account, email=email)
    new_user = UserFactory(email=email, username=email, name="invitee")
    assert invitation.status == InvitationStatus.PENDING

    api_client.force_login(new_user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invitations/accept",
        data={"code": invitation.code},
    )

    assert response.status_code == 200
    assert response.data == {
        "id": ANY,
        "user": {
            "id": new_user.id,
            "name": "invitee",
            "email": new_user.email,
            "avatar_url": None,
            "avatar_id": None,
            "active_account_id": str(account.id),
            "joined_at": ANY,
            "has_usable_password": True,
        },
        "account_id": str(account.id),
        "role": MemberRole.MEMBER,
        "joined_at": ANY,
    }
    invitation.refresh_from_db()
    assert invitation.status == InvitationStatus.ACCEPTED
    assert Member.objects.filter(user=new_user, account=account, role=MemberRole.MEMBER).exists()


def test_accept_invitation_requires_authentication(api_client):
    response = api_client.post(
        "/api/v1/invitations/accept",
        data={"code": "code"},
    )

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


def test_accept_invitation_not_requires_account(api_client, account):
    invitation = InvitationFactory(account=account)
    user = UserFactory(email=invitation.email, username=invitation.email, name="invitee")

    api_client.force_login(user)
    response = api_client.post(
        "/api/v1/invitations/accept",
        data={"code": invitation.code},
    )

    assert response.status_code == 200
    assert response.data == {
        "id": ANY,
        "user": {
            "id": user.id,
            "name": "invitee",
            "email": user.email,
            "avatar_url": None,
            "avatar_id": None,
            "active_account_id": str(account.id),
            "joined_at": ANY,
            "has_usable_password": True,
        },
        "account_id": str(account.id),
        "role": MemberRole.MEMBER,
        "joined_at": ANY,
    }


def test_accept_invitation_invalid_code(api_client, account):
    email = "invitee@example.com"
    invitation = InvitationFactory(account=account, email=email)
    new_user = UserFactory(email=email, username=email, name="invitee")
    assert invitation.status == InvitationStatus.PENDING

    api_client.force_login(new_user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invitations/accept",
        data={"code": "invalid_code"},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "non_field_errors",
                "code": "invalid",
                "detail": "Invalid invitation code.",
            }
        ],
    }


def test_accept_invitation_expired(api_client, account, monkeypatch):
    email = "invitee@example.com"
    invitation = InvitationFactory(account=account, email=email)
    new_user = UserFactory(email=email, username=email, name="invitee")
    assert invitation.status == InvitationStatus.PENDING

    # Patch the is_expired property to return True
    monkeypatch.setattr(
        "apps.accounts.models.Invitation.is_expired",
        True,
    )

    api_client.force_login(new_user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invitations/accept",
        data={"code": invitation.code},
    )

    assert response.status_code == 400
    assert response.data == {
        "type": ErrorType.VALIDATION_ERROR,
        "errors": [
            {
                "attr": "non_field_errors",
                "code": "invalid",
                "detail": "This invitation has expired.",
            }
        ],
    }
