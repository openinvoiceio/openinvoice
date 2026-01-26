from django.db import models


class NumberingSystemAppliesTo(models.TextChoices):
    INVOICE = "invoice"
    CREDIT_NOTE = "credit_note"
    QUOTE = "quote"


class NumberingSystemResetInterval(models.TextChoices):
    NEVER = "never"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class NumberingSystemStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    ARCHIVED = "archived", "Archived"
