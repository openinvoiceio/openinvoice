from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("invoices", "0019_invoice_line_subtotal_amount"),
    ]

    operations = [
        migrations.RenameField(
            model_name="invoiceshipping",
            old_name="tax_amount",
            new_name="total_tax_amount",
        ),
    ]
