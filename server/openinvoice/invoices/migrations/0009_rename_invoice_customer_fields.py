from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("invoices", "0008_remove_invoiceshipping_total_taxable_amount"),
    ]

    operations = [
        migrations.RenameField(
            model_name="invoice",
            old_name="customer_on_invoice",
            new_name="invoice_customer",
        ),
        migrations.RenameField(
            model_name="invoice",
            old_name="account_on_invoice",
            new_name="invoice_account",
        ),
    ]
