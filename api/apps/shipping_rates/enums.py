from django.db import models


class ShippingRateTaxPolicy(models.TextChoices):
    MATCH_GOODS = "match_goods", "Match Goods"
    EXEMPT = "exempt", "Exempt"
