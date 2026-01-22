from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import models
from stripe import StripeClient

if TYPE_CHECKING:
    from apps.accounts.models import Account

    from .models import StripeConnection


class StripeConnectionManager(models.Manager):
    def create_connection(
        self,
        account: Account,
        name: str,
        code: str,
        api_key: str,
        redirect_url: str | None = None,
    ) -> StripeConnection:
        connection_id = uuid.uuid4()
        client = StripeClient(api_key)
        webhook_endpoint = client.webhook_endpoints.create(
            url=settings.BASE_URL + f"/api/v1/integrations/stripe/connections/{connection_id}/webhook",
            description=f"OpenInvoice connection - {code}",
            enabled_events=[
                "checkout.session.completed",
                "checkout.session.async_payment_succeeded",
                "checkout.session.async_payment_failed",
                "checkout.session.expired",
            ],
        )
        return self.create(
            id=connection_id,
            account=account,
            name=name,
            code=code,
            api_key=api_key,
            webhook_endpoint_id=webhook_endpoint.id,
            webhook_secret=webhook_endpoint.secret,
            redirect_url=redirect_url,
        )
