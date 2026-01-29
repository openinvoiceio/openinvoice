import uuid

from django.db import models

from .choices import TaxIdType
from .managers import TaxIdManager
from .querysets import TaxIdQuerySet


class TaxId(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=50, choices=TaxIdType.choices)
    number = models.CharField(max_length=255)
    country = models.CharField(max_length=2, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TaxIdManager.from_queryset(TaxIdQuerySet)()

    @property
    def display_name(self) -> str:
        return self.type.replace("_", " ").upper()
