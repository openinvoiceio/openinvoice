import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("addresses", "0001_initial"),
        ("invoices", "0004_alter_invoice_net_payment_term"),
    ]

    operations = [
        migrations.RenameField(
            model_name="invoicecustomer",
            old_name="billing_address",
            new_name="address",
        ),
        migrations.RemoveField(
            model_name="invoicecustomer",
            name="shipping_address",
        ),
        migrations.AddField(
            model_name="invoiceshipping",
            name="name",
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="invoiceshipping",
            name="phone",
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="invoiceshipping",
            name="address",
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="invoice_shipping_address",
                to="addresses.address",
            ),
        ),
        migrations.AlterField(
            model_name="invoicecustomer",
            name="address",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="invoice_customer_address",
                to="addresses.address",
            ),
        ),
    ]
