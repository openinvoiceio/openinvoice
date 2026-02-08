import djmoney.settings as djmoney_settings
from django.conf import settings
from django.db import migrations, models


def copy_billing_profile_settings(apps, _schema_editor):
    Customer = apps.get_model("customers", "Customer")

    for customer in Customer.objects.select_related("default_billing_profile").all():
        billing_profile = customer.default_billing_profile
        customer.currency = billing_profile.currency
        customer.language = billing_profile.language
        customer.net_payment_term = billing_profile.net_payment_term
        customer.invoice_numbering_system_id = billing_profile.invoice_numbering_system_id
        customer.credit_note_numbering_system_id = billing_profile.credit_note_numbering_system_id
        customer.save(
            update_fields=[
                "currency",
                "language",
                "net_payment_term",
                "invoice_numbering_system",
                "credit_note_numbering_system",
            ]
        )
        customer.tax_rates.set(billing_profile.tax_rates.all())


class Migration(migrations.Migration):
    dependencies = [
        ("customers", "0004_customer_tax_ids"),
    ]

    operations = [
        migrations.AddField(
            model_name="customer",
            name="currency",
            field=models.CharField(
                choices=djmoney_settings.CURRENCY_CHOICES,
                max_length=3,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="customer",
            name="language",
            field=models.CharField(choices=settings.LANGUAGES, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name="customer",
            name="net_payment_term",
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.AddField(
            model_name="customer",
            name="invoice_numbering_system",
            field=models.ForeignKey(
                null=True,
                on_delete=models.PROTECT,
                related_name="invoice_numbering_customers",
                to="numbering_systems.numberingsystem",
            ),
        ),
        migrations.AddField(
            model_name="customer",
            name="credit_note_numbering_system",
            field=models.ForeignKey(
                null=True,
                on_delete=models.PROTECT,
                related_name="credit_note_numbering_customers",
                to="numbering_systems.numberingsystem",
            ),
        ),
        migrations.AddField(
            model_name="customer",
            name="tax_rates",
            field=models.ManyToManyField(related_name="customers", to="tax_rates.taxrate"),
        ),
        migrations.RunPython(copy_billing_profile_settings, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="billingprofile",
            name="currency",
        ),
        migrations.RemoveField(
            model_name="billingprofile",
            name="language",
        ),
        migrations.RemoveField(
            model_name="billingprofile",
            name="net_payment_term",
        ),
        migrations.RemoveField(
            model_name="billingprofile",
            name="invoice_numbering_system",
        ),
        migrations.RemoveField(
            model_name="billingprofile",
            name="credit_note_numbering_system",
        ),
        migrations.RemoveField(
            model_name="billingprofile",
            name="tax_rates",
        ),
        migrations.DeleteModel(
            name="BillingProfileTaxRate",
        ),
    ]
