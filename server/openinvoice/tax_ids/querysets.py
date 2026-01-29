from __future__ import annotations

from django.db import models


class TaxIdQuerySet(models.QuerySet):
    def clone(self):
        return self.model.objects.bulk_create(
            [
                self.model(
                    type=tax_id.type,
                    number=tax_id.number,
                    country=tax_id.country,
                )
                for tax_id in self
            ]
        )
