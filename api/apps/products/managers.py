from __future__ import annotations

from django.db import models

from apps.files.models import File

from .choices import ProductStatus
from .querysets import ProductQuerySet


class ProductManager(models.Manager.from_queryset(ProductQuerySet)):  # type: ignore[misc]
    def create_product(
        self,
        account,
        name: str,
        description: str | None = None,
        metadata: dict | None = None,
        url: str | None = None,
        image: File | None = None,
    ):
        return self.create(
            account=account,
            name=name,
            description=description,
            status=ProductStatus.ACTIVE,
            metadata=metadata or {},
            url=url,
            image=image,
        )
