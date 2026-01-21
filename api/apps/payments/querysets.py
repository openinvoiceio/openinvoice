from django.db import models

from .choices import PaymentStatus


class PaymentQuerySet(models.QuerySet):
    def succeeded(self) -> "PaymentQuerySet":
        return self.filter(status=PaymentStatus.SUCCEEDED)
