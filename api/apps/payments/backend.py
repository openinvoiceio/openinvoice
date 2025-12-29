from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from uuid import UUID

from django.conf import settings
from django.utils.module_loading import import_string

from apps.integrations.enums import PaymentProvider

if TYPE_CHECKING:
    from apps.invoices.models import Invoice

    from .models import Payment


class PaymentBackend(ABC):
    @classmethod
    @abstractmethod
    def from_account(cls, account_id: UUID, connection_id: UUID) -> "PaymentBackend": ...

    @abstractmethod
    def checkout(self, invoice: "Invoice", payment: "Payment") -> tuple[str, str | None]: ...


def get_payment_backend(account_id: UUID, connection_id: UUID, payment_provider: PaymentProvider) -> PaymentBackend:
    try:
        backend_string = settings.PAYMENT_BACKENDS[payment_provider]
    except KeyError as e:
        raise RuntimeError(f"Payment provider '{payment_provider}' not found.") from e

    backend_cls: PaymentBackend = import_string(backend_string)

    return backend_cls.from_account(account_id, connection_id)
