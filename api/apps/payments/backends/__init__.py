from uuid import UUID

from apps.integrations.enums import PaymentProvider
from apps.integrations.exceptions import PaymentProviderConnectionNotFoundError
from apps.integrations.models import StripeConnection
from apps.payments.exceptions import PaymentBackendNotFoundError

from .base import PaymentBackend
from .stripe import StripeBackend


def get_payment_backend(account_id: UUID, payment_provider: PaymentProvider) -> PaymentBackend:
    match payment_provider:
        case PaymentProvider.STRIPE:
            try:
                connection = StripeConnection.objects.get(account_id=account_id)
            except StripeConnection.DoesNotExist as e:
                raise PaymentProviderConnectionNotFoundError(payment_provider) from e

            return StripeBackend(connection)

        case _:
            raise PaymentBackendNotFoundError(payment_provider)
