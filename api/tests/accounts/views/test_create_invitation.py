from unittest.mock import ANY

import pytest
from drf_standardized_errors.types import ErrorType

from apps.accounts.choices import InvitationStatus

pytestmark = pytest.mark.django_db


def test_create_invitation(api_client, user, account, mailoutbox):
    assert len(mailoutbox) == 0
    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.post(
        "/api/v1/invitations",
        data={
            "email": "invitee@example.com",
        },
    )

    assert response.status_code == 201
    assert response.data == {
        "id": ANY,
        "email": "invitee@example.com",
        "status": InvitationStatus.PENDING,
        "created_at": ANY,
        "accepted_at": None,
        "rejected_at": None,
    }
    assert len(mailoutbox) == 1


def test_create_invitation_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.post(
        "/api/v1/invitations",
        data={"email": "invitee@example.com"},
    )

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


def test_create_invitation_requires_authentication(api_client):
    response = api_client.post(
        "/api/v1/invitations",
        data={"email": "invitee@example.com"},
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
