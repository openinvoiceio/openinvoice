from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("invoices", "0009_rename_invoice_customer_fields"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="invoice",
            name="sell_date",
        ),
    ]
