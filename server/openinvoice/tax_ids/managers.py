from django.db import models


class TaxIdManager(models.Manager):
    def create_tax_id(
        self,
        type_: str,
        number: str,
        country: str | None,
    ):
        return self.create(
            type=type_,
            number=number,
            country=country,
        )
