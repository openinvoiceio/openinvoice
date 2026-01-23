import uuid

from django.db import models
from encrypted_fields import EncryptedTextField

from apps.integrations.stripe.managers import StripeConnectionManager
from apps.integrations.stripe.querysets import StripeConnectionQuerySet


class StripeConnection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    account = models.ForeignKey("accounts.Account", on_delete=models.CASCADE, related_name="stripe_connections")
    api_key = EncryptedTextField()
    webhook_endpoint_id = models.CharField(max_length=255)
    webhook_secret = EncryptedTextField()
    redirect_url = models.URLField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = StripeConnectionManager.from_queryset(StripeConnectionQuerySet)()

    class Meta:
        ordering = ["created_at"]

    def update(self, name: str, redirect_url: str | None) -> None:
        self.name = name
        self.redirect_url = redirect_url
        self.save()
