from django.db import models


class ProductQuerySet(models.QuerySet):
    def for_account(self, account_id):
        return self.filter(account_id=account_id)

    def with_prices(self):
        return (
            self.prefetch_related("prices")
            .select_related("default_price")
            .annotate(prices_count=models.Count("prices"))
        )
