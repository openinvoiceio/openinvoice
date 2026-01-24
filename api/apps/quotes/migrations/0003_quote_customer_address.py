import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("addresses", "0001_initial"),
        ("quotes", "0002_alter_quote_currency_alter_quotediscount_currency_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="quotecustomer",
            old_name="billing_address",
            new_name="address",
        ),
        migrations.RemoveField(
            model_name="quotecustomer",
            name="shipping_address",
        ),
        migrations.AlterField(
            model_name="quotecustomer",
            name="address",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="quote_customer_address",
                to="addresses.address",
            ),
        ),
    ]
