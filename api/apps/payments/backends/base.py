from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import stripe

if TYPE_CHECKING:
    from apps.invoices.models import Invoice
    from apps.payments.models import Payment


class PaymentBackend(ABC):
    @abstractmethod
    def checkout(self, *, invoice: "Invoice", payment: "Payment") -> tuple[str, str | None]:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def process_event(cls, event: stripe.Event) -> None:
        raise NotImplementedError
