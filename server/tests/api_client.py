from rest_framework.test import APIClient as DRFAPIClient

from openinvoice.accounts.session import ACTIVE_ACCOUNT_SESSION_KEY


class APIClient(DRFAPIClient):
    """Test client with account-awareness."""

    def force_account(self, account):
        session = self.session
        session[ACTIVE_ACCOUNT_SESSION_KEY] = str(account.id)
        session.save()
