from django.db import models


class PaymentStatus(models.TextChoices):
    SUCCEEDED = "succeeded", "Succeeded"
    PENDING = "pending", "Pending"
    FAILED = "failed", "Failed"
    REJECTED = "rejected", "Rejected"
