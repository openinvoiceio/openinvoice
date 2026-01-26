from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:
    from .models import Address


class AddressManager(models.Manager):
    def create_address(
        self,
        line1: str | None = None,
        line2: str | None = None,
        locality: str | None = None,
        state: str | None = None,
        postal_code: str | None = None,
        country: str | None = None,
    ) -> Address:
        return self.create(
            line1=line1,
            line2=line2,
            locality=locality,
            state=state,
            postal_code=postal_code,
            country=country,
        )

    def from_address(self, address: Address | None) -> Address | None:
        if address is None:
            return None

        return self.create(
            line1=address.line1,
            line2=address.line2,
            locality=address.locality,
            state=address.state,
            postal_code=address.postal_code,
            country=address.country,
        )
