from django.db import models

from .enums import PaymentStatus


class PaymentQuerySet(models.QuerySet):
    def succeeded(self) -> "PaymentQuerySet":
        return self.filter(status=PaymentStatus.SUCCEEDED)
