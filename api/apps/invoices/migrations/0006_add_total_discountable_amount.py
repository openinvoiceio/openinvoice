import djmoney.models.fields
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("invoices", "0005_invoice_shipping_contact_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="invoiceline",
            name="total_discountable_amount",
            field=djmoney.models.fields.MoneyField(
                currency_field_name="currency",
                decimal_places=2,
                max_digits=19,
                default=0,
            ),
            preserve_default=False,
        ),
    ]
