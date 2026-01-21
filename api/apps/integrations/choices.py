from django.db import models


class IntegrationType(models.TextChoices):
    STRIPE = "stripe"


# TODO: move to payments app?
class PaymentProvider(models.TextChoices):
    STRIPE = "stripe"
