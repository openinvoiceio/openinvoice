from django.db import models


class PriceModel(models.TextChoices):
    FLAT = "flat", "Flat"
    GRADUATED = "graduated", "Graduated"
    VOLUME = "volume", "Volume"


class PriceStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    ARCHIVED = "archived", "Archived"
