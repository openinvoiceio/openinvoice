import uuid
from unittest.mock import ANY

import pytest
from drf_standardized_errors.types import ErrorType

from tests.factories import InvitationFactory

pytestmark = pytest.mark.django_db


def test_retrieve_invitation(api_client, user, account):
    invitation = InvitationFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get(f"/api/v1/invitations/{invitation.id}")

    assert response.status_code == 200
    assert response.data == {
        "id": str(invitation.id),
        "email": invitation.email,
        "status": invitation.status,
        "created_at": ANY,
        "accepted_at": invitation.accepted_at,
        "rejected_at": invitation.rejected_at,
    }


def test_retrieve_invitation_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.get(f"/api/v1/invitations/{uuid.uuid4()}")

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


def test_retrieve_invitation_requires_authentication(api_client, account):
    invitation = InvitationFactory(account=account)

    response = api_client.get(f"/api/v1/invitations/{invitation.id}")

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
