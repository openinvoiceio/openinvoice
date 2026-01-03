from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from uuid import UUID

from django.conf import settings
from django.utils.module_loading import import_string

if TYPE_CHECKING:
    from apps.invoices.models import Invoice


class Integration(ABC):
    name: str
    slug: str
    description: str

    @abstractmethod
    def is_enabled(self, account_id: UUID) -> bool: ...


class PaymentProviderIntegration(Integration, ABC):
    @abstractmethod
    def checkout(self, invoice: Invoice, payment_id: UUID) -> tuple[str, str | None]: ...


def get_integration(slug: str) -> Integration:
    try:
        backend_string = settings.INTEGRATIONS[slug]
    except KeyError as e:
        raise RuntimeError(f"Integration '{slug}' not found.") from e

    return import_string(backend_string)()


def get_payment_integration(slug: str) -> PaymentProviderIntegration:
    integration = get_integration(slug)
    if not isinstance(integration, PaymentProviderIntegration):
        raise RuntimeError(f"Integration '{slug}' is not a payment provider integration.")
    return integration
