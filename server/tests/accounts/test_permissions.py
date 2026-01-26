from unittest.mock import MagicMock

import pytest

from openinvoice.accounts.permissions import IsAccountMember


@pytest.mark.django_db
def test_is_account_member_allows_when_account(account):
    request = MagicMock()
    request.account = account
    assert IsAccountMember().has_permission(request, None) is True


def test_is_account_member_denies_requires_account():
    request = MagicMock()
    request.account = None
    assert IsAccountMember().has_permission(request, None) is False
