from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from django.db import models
from django.utils import timezone
from djmoney.money import Money

from .enums import PaymentStatus
from .exceptions import (
    InvoicePaymentAmountExceededError,
    PaymentCheckoutError,
)
from .querysets import PaymentQuerySet

if TYPE_CHECKING:
    from apps.invoices.models import Invoice

    from .models import Payment


class PaymentManager(models.Manager.from_queryset(PaymentQuerySet)):
    def record_payment(
        self,
        invoice: Invoice,
        amount: Money,
        currency: str,
        description: str | None = None,
        transaction_id: str | None = None,
        received_at: datetime | None = None,
    ) -> Payment:
        if amount > invoice.outstanding_amount:
            raise InvoicePaymentAmountExceededError

        payment = self.create(
            account=invoice.account,
            status=PaymentStatus.SUCCEEDED,
            amount=amount,
            currency=currency,
            description=description,
            transaction_id=transaction_id,
            received_at=received_at or timezone.now(),
        )
        payment.invoices.add(invoice)
        invoice.recalculate_paid()

        return payment

    def checkout_invoice(self, invoice: Invoice) -> Payment:
        from .backends import get_payment_backend

        backend = get_payment_backend(account_id=invoice.account, payment_provider=invoice.payment_provider)
        payment = self.create(
            account=invoice.account,
            status=PaymentStatus.PENDING,
            amount=invoice.total_amount,
            currency=invoice.currency,
            description=invoice.number,
            provider=invoice.payment_provider,
        )

        try:
            transaction_id, checkout_url = backend.checkout(invoice=invoice, payment=payment)
        except PaymentCheckoutError as error:
            payment.status = PaymentStatus.FAILED
            payment.message = str(error)
            payment.extra_data = {"error": str(error)}
            payment.save(update_fields=["status", "message", "extra_data"])
            raise

        payment.transaction_id = transaction_id
        payment.url = checkout_url
        payment.save(update_fields=["transaction_id", "url"])
        payment.invoices.add(invoice)

        return payment
