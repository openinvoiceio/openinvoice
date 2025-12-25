import uuid

from django.db import models
from django.utils import timezone
from djmoney.models.fields import MoneyField

from apps.integrations.enums import PaymentProvider

from .enums import PaymentStatus
from .managers import PaymentManager


class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey("accounts.Account", related_name="payments", on_delete=models.CASCADE)
    status = models.CharField(max_length=50, choices=PaymentStatus.choices)
    currency = models.CharField(max_length=3)
    amount = MoneyField(max_digits=19, decimal_places=2, currency_field_name="currency")
    description = models.CharField(max_length=255, null=True)
    transaction_id = models.CharField(max_length=255, null=True)
    url = models.URLField(null=True)
    message = models.TextField(null=True)
    extra_data = models.JSONField(default=dict)
    provider = models.CharField(max_length=50, choices=PaymentProvider.choices, null=True)
    invoices = models.ManyToManyField("invoices.Invoice", related_name="payments")
    received_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = PaymentManager()

    class Meta:
        ordering = ["-created_at"]
