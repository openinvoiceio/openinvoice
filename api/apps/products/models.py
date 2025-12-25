import uuid
from typing import TYPE_CHECKING

from django.db import models
from django.utils import timezone

from apps.files.models import File

from .managers import ProductManager

if TYPE_CHECKING:
    from apps.prices.models import Price


class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=500)
    description = models.TextField(null=True, blank=True)
    url = models.URLField(null=True)
    is_active = models.BooleanField()
    metadata = models.JSONField(default=dict)
    archived_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    account = models.ForeignKey("accounts.Account", on_delete=models.CASCADE, related_name="products")
    image = models.ForeignKey("files.File", on_delete=models.SET_NULL, null=True)
    default_price = models.ForeignKey(
        "prices.Price", on_delete=models.SET_NULL, null=True, related_name="default_product"
    )

    objects = ProductManager()

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
        if not self.is_active:
            return

        self.is_active = False
        self.archived_at = timezone.now()
        self.save(update_fields=["is_active", "archived_at", "updated_at"])

    def unarchive(self) -> None:
        if self.is_active:
            return

        self.is_active = True
        self.archived_at = None
        self.save(update_fields=["is_active", "archived_at", "updated_at"])
