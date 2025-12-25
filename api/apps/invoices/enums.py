from django.db import models


class InvoiceStatus(models.TextChoices):
    DRAFT = "draft"
    OPEN = "open"
    PAID = "paid"
    VOIDED = "voided"


class InvoicePreviewFormat(models.TextChoices):
    PDF = "pdf"
    EMAIL = "email"


class InvoiceDeliveryMethod(models.TextChoices):
    MANUAL = "manual", "Manual"
    AUTOMATIC = "automatic", "Automatic"
