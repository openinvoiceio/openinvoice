import uuid

import djmoney.settings
from django.conf import settings
from django.db import migrations, models


def create_customer_profiles(apps, _schema_editor):
    Customer = apps.get_model("customers", "Customer")
    BillingProfile = apps.get_model("customers", "BillingProfile")
    ShippingProfile = apps.get_model("customers", "ShippingProfile")

    for customer in Customer.objects.all():
        billing_profile = BillingProfile.objects.create(
            name=customer.name,
            legal_name=customer.legal_name,
            legal_number=customer.legal_number,
            email=customer.email,
            phone=customer.phone,
            address=customer.address,
            currency=customer.currency,
            language=customer.language,
            net_payment_term=customer.net_payment_term,
            invoice_numbering_system=customer.invoice_numbering_system,
            credit_note_numbering_system=customer.credit_note_numbering_system,
        )
        billing_profile.tax_ids.set(customer.tax_ids.all())
        billing_profile.tax_rates.set(customer.tax_rates.all())

        customer.default_billing_profile = billing_profile
        customer.save(update_fields=["default_billing_profile"])
        customer.billing_profiles.add(billing_profile)

        if customer.shipping_id:
            shipping_profile = ShippingProfile.objects.create(
                name=customer.shipping.name,
                phone=customer.shipping.phone,
                address=customer.shipping.address,
            )
            customer.default_shipping_profile = shipping_profile
            customer.save(update_fields=["default_shipping_profile"])
            customer.shipping_profiles.add(shipping_profile)


class Migration(migrations.Migration):
    dependencies = [
        ("customers", "0007_customer_language"),
        ("addresses", "0001_initial"),
        ("numbering_systems", "0001_initial"),
        ("tax_rates", "0001_initial"),
        ("tax_ids", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="BillingProfile",
            fields=[
                ("id", models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)),
                ("name", models.CharField(max_length=255)),
                ("legal_name", models.CharField(max_length=255, null=True)),
                ("legal_number", models.CharField(max_length=255, null=True)),
                ("email", models.EmailField(max_length=255, null=True)),
                ("phone", models.CharField(max_length=255, null=True)),
                (
                    "address",
                    models.OneToOneField(
                        to="addresses.address",
                        on_delete=models.PROTECT,
                        related_name="billing_profile_address",
                    ),
                ),
                (
                    "currency",
                    models.CharField(
                        max_length=3,
                        choices=djmoney.settings.CURRENCY_CHOICES,
                        null=True,
                    ),
                ),
                ("language", models.CharField(max_length=10, null=True, choices=settings.LANGUAGES)),
                ("net_payment_term", models.PositiveIntegerField(null=True)),
                (
                    "invoice_numbering_system",
                    models.ForeignKey(
                        to="numbering_systems.numberingsystem",
                        on_delete=models.PROTECT,
                        related_name="invoice_numbering_billing_profiles",
                        null=True,
                    ),
                ),
                (
                    "credit_note_numbering_system",
                    models.ForeignKey(
                        to="numbering_systems.numberingsystem",
                        on_delete=models.PROTECT,
                        related_name="credit_note_numbering_billing_profiles",
                        null=True,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="BillingProfileTaxRate",
            fields=[
                ("id", models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)),
                (
                    "billing_profile",
                    models.ForeignKey(
                        to="customers.billingprofile",
                        on_delete=models.CASCADE,
                        related_name="billing_profile_tax_rates",
                    ),
                ),
                (
                    "tax_rate",
                    models.ForeignKey(
                        to="tax_rates.taxrate",
                        on_delete=models.PROTECT,
                        related_name="billing_profile_tax_rates",
                    ),
                ),
            ],
            options={"unique_together": {("billing_profile", "tax_rate")}},
        ),
        migrations.CreateModel(
            name="ShippingProfile",
            fields=[
                ("id", models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)),
                ("name", models.CharField(max_length=255, null=True)),
                ("phone", models.CharField(max_length=255, null=True)),
                (
                    "address",
                    models.OneToOneField(
                        to="addresses.address",
                        on_delete=models.PROTECT,
                        related_name="shipping_profile_address",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.AddField(
            model_name="billingprofile",
            name="tax_ids",
            field=models.ManyToManyField(related_name="billing_profiles", to="tax_ids.taxid"),
        ),
        migrations.AddField(
            model_name="billingprofile",
            name="tax_rates",
            field=models.ManyToManyField(
                related_name="billing_profiles",
                through="customers.billingprofiletaxrate",
                to="tax_rates.taxrate",
            ),
        ),
        migrations.AddField(
            model_name="customer",
            name="default_billing_profile",
            field=models.OneToOneField(
                to="customers.billingprofile",
                on_delete=models.PROTECT,
                related_name="+",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="customer",
            name="default_shipping_profile",
            field=models.OneToOneField(
                to="customers.shippingprofile",
                on_delete=models.PROTECT,
                related_name="+",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="customer",
            name="billing_profiles",
            field=models.ManyToManyField(related_name="customers", to="customers.billingprofile"),
        ),
        migrations.AddField(
            model_name="customer",
            name="shipping_profiles",
            field=models.ManyToManyField(related_name="customers", to="customers.shippingprofile"),
        ),
        migrations.RunPython(create_customer_profiles, migrations.RunPython.noop),
        migrations.RemoveField(model_name="customer", name="name"),
        migrations.RemoveField(model_name="customer", name="legal_name"),
        migrations.RemoveField(model_name="customer", name="legal_number"),
        migrations.RemoveField(model_name="customer", name="email"),
        migrations.RemoveField(model_name="customer", name="phone"),
        migrations.RemoveField(model_name="customer", name="currency"),
        migrations.RemoveField(model_name="customer", name="language"),
        migrations.RemoveField(model_name="customer", name="net_payment_term"),
        migrations.RemoveField(model_name="customer", name="invoice_numbering_system"),
        migrations.RemoveField(model_name="customer", name="credit_note_numbering_system"),
        migrations.RemoveField(model_name="customer", name="address"),
        migrations.RemoveField(model_name="customer", name="shipping"),
        migrations.RemoveField(model_name="customer", name="tax_rates"),
        migrations.RemoveField(model_name="customer", name="tax_ids"),
        migrations.DeleteModel(name="CustomerTaxRate"),
        migrations.DeleteModel(name="CustomerShipping"),
        migrations.AlterField(
            model_name="customer",
            name="default_billing_profile",
            field=models.OneToOneField(
                to="customers.billingprofile",
                on_delete=models.PROTECT,
                related_name="+",
            ),
        ),
    ]
