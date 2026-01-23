from __future__ import annotations

from decimal import Decimal

import djmoney.models.fields
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("invoices", "0018_invoice_shipping_taxable_amount_and_rate"),
    ]

    operations = [
        migrations.AddField(
            model_name="invoiceline",
            name="subtotal_amount",
            field=djmoney.models.fields.MoneyField(
                currency_field_name="currency",
                decimal_places=2,
                default=Decimal("0"),
                max_digits=19,
            ),
            preserve_default=False,
        ),
    ]
