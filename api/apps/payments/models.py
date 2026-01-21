import uuid
from datetime import datetime

from django.db import models
from django.utils import timezone
from djmoney.models.fields import MoneyField

from apps.integrations.choices import PaymentProvider

from .choices import PaymentStatus
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
    connection_id = models.UUIDField(null=True)
    invoices = models.ManyToManyField("invoices.Invoice", related_name="payments")
    received_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = PaymentManager()

    class Meta:
        ordering = ["-created_at"]

    def complete(self, extra_data: dict, received_at: datetime) -> None:
        self.status = PaymentStatus.SUCCEEDED
        self.message = None
        self.extra_data = extra_data
        self.received_at = received_at

        self.save()

        for invoice in self.invoices.all():
            invoice.recalculate_paid()

    def fail(self, message: str, extra_data: dict, received_at: datetime) -> None:
        self.status = PaymentStatus.FAILED
        self.message = message
        self.extra_data = extra_data
        self.received_at = received_at

        self.save()

    def reject(self, message: str, extra_data: dict, received_at: datetime) -> None:
        self.status = PaymentStatus.REJECTED
        self.message = message
        self.extra_data = extra_data
        self.received_at = received_at

        self.save()
