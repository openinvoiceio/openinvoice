from unittest.mock import ANY

import pytest

from openinvoice.accounts.choices import InvitationStatus
from tests.factories import AccountFactory, BusinessProfileFactory, InvitationFactory

pytestmark = pytest.mark.django_db


def test_list_invitations(api_client, user, account):
    other_account = AccountFactory(default_business_profile=BusinessProfileFactory(name="Test Account"))
    invitation_1 = InvitationFactory(
        code="invitation_code_1",
        account=account,
    )
    invitation_2 = InvitationFactory(
        code="invitation_code_2",
        account=account,
        status=InvitationStatus.ACCEPTED,
    )
    InvitationFactory(
        code="invitation_code_3",
        account=other_account,
    )

    api_client.force_login(user)
    api_client.force_account(account)
    response = api_client.get("/api/v1/invitations")

    assert response.status_code == 200
    assert response.data["count"] == 2
    assert response.data["results"] == [
        {
            "id": str(invitation.id),
            "email": invitation.email,
            "status": invitation.status,
            "created_at": ANY,
            "accepted_at": invitation.accepted_at,
        }
        for invitation in [invitation_2, invitation_1]
    ]


def test_list_invitations_requires_account(api_client, user):
    api_client.force_login(user)
    response = api_client.get("/api/v1/invitations")

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


def test_list_invitations_requires_authentication(api_client, account):
    InvitationFactory(account=account)

    response = api_client.get("/api/v1/invitations")

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
