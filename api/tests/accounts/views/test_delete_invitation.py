import uuid

import pytest

from tests.factories import InvitationFactory

pytestmark = pytest.mark.django_db


def test_delete_invitation(api_client, user, account):
    invitation = InvitationFactory(account=account)

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.delete(f"/api/v1/invitations/{invitation.id}")

    assert response.status_code == 204

    response = api_client.delete(f"/api/v1/invitations/{invitation.id}")
    assert response.status_code == 404


def test_delete_invitation_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.delete(f"/api/v1/invitations/{uuid.uuid4()}")

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


def test_delete_invitation_requires_authentication(api_client, account):
    invitation = InvitationFactory(account=account)

    response = api_client.delete(f"/api/v1/invitations/{invitation.id}")

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
