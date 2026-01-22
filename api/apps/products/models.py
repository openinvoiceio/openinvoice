import uuid
from typing import TYPE_CHECKING

from django.db import models
from django.utils import timezone

from apps.files.models import File

from .choices import ProductStatus
from .managers import ProductManager
from .querysets import ProductQuerySet

if TYPE_CHECKING:
    from apps.prices.models import Price


class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=500)
    description = models.TextField(null=True, blank=True)
    url = models.URLField(null=True)
    status = models.CharField(max_length=20, choices=ProductStatus.choices, default=ProductStatus.ACTIVE)
    metadata = models.JSONField(default=dict)
    archived_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    account = models.ForeignKey("accounts.Account", on_delete=models.CASCADE, related_name="products")
    image = models.ForeignKey("files.File", on_delete=models.SET_NULL, null=True)
    default_price = models.ForeignKey(
        "prices.Price", on_delete=models.SET_NULL, null=True, related_name="default_product"
    )

    objects = ProductManager.from_queryset(ProductQuerySet)()

    class Meta:
        ordering = ["-created_at"]

    def update(
        self,
        name: str,
        description: str | None,
        default_price: "Price | None",
        url: str | None,
        image: File | None,
        metadata: dict,
    ) -> None:
        self.name = name
        self.description = description
        self.default_price = default_price
        self.url = url
        self.image = image
        self.metadata = metadata

        self.save()

    def archive(self) -> None:
        if self.status == ProductStatus.ARCHIVED:
            return

        self.status = ProductStatus.ARCHIVED
        self.archived_at = timezone.now()
        self.save()

    def restore(self) -> None:
        if self.status == ProductStatus.ACTIVE:
            return

        self.status = ProductStatus.ACTIVE
        self.archived_at = None
        self.save()
