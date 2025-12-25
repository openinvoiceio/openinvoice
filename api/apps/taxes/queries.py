from uuid import UUID

from .models import TaxRate


def get_tax_rate(*, account_id: UUID, tax_rate_id: UUID) -> TaxRate:
    return TaxRate.objects.get(account_id=account_id, id=tax_rate_id)
