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


class InvoiceDiscountSource(models.TextChoices):
    INVOICE = "invoice", "Invoice"
    LINE = "line", "Line"


class InvoiceTaxSource(models.TextChoices):
    INVOICE = "invoice", "Invoice"
    LINE = "line", "Line"
    SHIPPING = "shipping", "Shipping"


class InvoiceTaxBehavior(models.TextChoices):
    INCLUSIVE = "inclusive", "Inclusive"
    EXCLUSIVE = "exclusive", "Exclusive"
    AUTOMATIC = "automatic", "Automatic"
