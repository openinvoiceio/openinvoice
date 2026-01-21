from django.db import models


class PriceModel(models.TextChoices):
    FLAT = "flat", "Flat"
    GRADUATED = "graduated", "Graduated"
    VOLUME = "volume", "Volume"
