import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("addresses", "0001_initial"),
        ("customers", "0004_alter_customer_net_payment_term"),
    ]

    operations = [
        migrations.CreateModel(
            name="CustomerShipping",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=255, null=True)),
                ("phone", models.CharField(max_length=255, null=True)),
                (
                    "address",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="customer_shipping_address",
                        to="addresses.address",
                    ),
                ),
            ],
        ),
        migrations.RenameField(
            model_name="customer",
            old_name="billing_address",
            new_name="address",
        ),
        migrations.RemoveField(
            model_name="customer",
            name="shipping_address",
        ),
        migrations.AddField(
            model_name="customer",
            name="shipping",
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="customer",
                to="customers.customershipping",
            ),
        ),
        migrations.AlterField(
            model_name="customer",
            name="address",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="customer_address",
                to="addresses.address",
            ),
        ),
    ]
