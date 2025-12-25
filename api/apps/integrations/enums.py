from django.db import models


class IntegrationType(models.TextChoices):
    STRIPE = "stripe"


class PaymentProvider(models.TextChoices):
    STRIPE = "stripe"
