import uuid

from django.db import models
from django.utils.functional import empty
from django_countries.fields import CountryField

from .managers import AddressManager

UnsetType = type(empty)


class Address(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    line1 = models.CharField(max_length=255, null=True)
    line2 = models.CharField(max_length=255, null=True)
    locality = models.CharField(max_length=255, null=True)
    state = models.CharField(max_length=255, null=True)
    postal_code = models.CharField(max_length=255, null=True)
    country = CountryField(null=True)

    objects = AddressManager()

    def __str__(self) -> str:
        return f"{self.line1 or ''}, {self.locality or ''} ({self.country or ''})"

    def update(
        self,
        *,
        line1: str | None | UnsetType = empty,
        line2: str | None | UnsetType = empty,
        locality: str | None | UnsetType = empty,
        state: str | None | UnsetType = empty,
        postal_code: str | None | UnsetType = empty,
        country: str | None | UnsetType = empty,
    ) -> None:
        if line1 is not empty:
            self.line1 = line1

        if line2 is not empty:
            self.line2 = line2

        if locality is not empty:
            self.locality = locality

        if state is not empty:
            self.state = state

        if postal_code is not empty:
            self.postal_code = postal_code

        if country is not empty:
            self.country = country

        self.save()
