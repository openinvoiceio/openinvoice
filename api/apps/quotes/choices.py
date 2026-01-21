from django.db import models


class QuoteStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    OPEN = "open", "Open"
    ACCEPTED = "accepted", "Accepted"
    CANCELED = "canceled", "Canceled"


class QuotePreviewFormat(models.TextChoices):
    PDF = "pdf", "PDF"
    EMAIL = "email", "Email"


class QuoteDeliveryMethod(models.TextChoices):
    MANUAL = "manual", "Manual"
    AUTOMATIC = "automatic", "Automatic"
