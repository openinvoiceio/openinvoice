from django.db import models


class CreditNoteStatus(models.TextChoices):
    DRAFT = "draft"
    ISSUED = "issued"
    VOIDED = "voided"


class CreditNoteReason(models.TextChoices):
    DUPLICATED_CHARGE = "duplicated_charge"
    PRODUCT_UNSATISFACTORY = "product_unsatisfactory"
    ORDER_CHANGE = "order_change"
    ORDER_CANCELLATION = "order_cancellation"
    FRAUDULENT_CHARGE = "fraudulent_charge"
    OTHER = "other"


class CreditNotePreviewFormat(models.TextChoices):
    EMAIL = "email"
    PDF = "pdf"


class CreditNoteDeliveryMethod(models.TextChoices):
    MANUAL = "manual", "Manual"
    AUTOMATIC = "automatic", "Automatic"
