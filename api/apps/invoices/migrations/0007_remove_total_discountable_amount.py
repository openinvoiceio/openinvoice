from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("invoices", "0006_add_total_discountable_amount"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="invoiceline",
            name="total_discountable_amount",
        ),
    ]
