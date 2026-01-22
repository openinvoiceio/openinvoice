from django.db import models

from .choices import TaxRateStatus


class TaxRateQuerySet(models.QuerySet):
    def for_account(self, account_id):
        return self.filter(account_id=account_id)

    def active(self):
        return self.filter(status=TaxRateStatus.ACTIVE)
