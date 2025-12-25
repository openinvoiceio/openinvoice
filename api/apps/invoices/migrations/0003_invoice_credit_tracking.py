import djmoney.models.fields
from django.db import migrations, models
from django.db.models import F


def initialize_credit_fields(apps, _):
    Invoice = apps.get_model("invoices", "Invoice")
    InvoiceLine = apps.get_model("invoices", "InvoiceLine")

    Invoice.objects.all().update(
        total_credit_amount=0,
        outstanding_amount=F("total_amount"),
    )
    InvoiceLine.objects.all().update(
        total_credit_amount=0,
        credit_quantity=0,
        outstanding_amount=F("total_amount"),
        outstanding_quantity=F("quantity"),
    )


def noop(*_, **__):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("invoices", "0002_alter_invoice_account_alter_invoice_customer_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="invoice",
            name="outstanding_amount",
            field=djmoney.models.fields.MoneyField(
                currency_field_name="currency", decimal_places=2, default=0, max_digits=19
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="invoice",
            name="total_credit_amount",
            field=djmoney.models.fields.MoneyField(
                currency_field_name="currency", decimal_places=2, default=0, max_digits=19
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="invoiceline",
            name="credit_quantity",
            field=models.BigIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="invoiceline",
            name="outstanding_amount",
            field=djmoney.models.fields.MoneyField(
                currency_field_name="currency", decimal_places=2, default=0, max_digits=19
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="invoiceline",
            name="outstanding_quantity",
            field=models.BigIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="invoiceline",
            name="total_credit_amount",
            field=djmoney.models.fields.MoneyField(
                currency_field_name="currency", decimal_places=2, default=0, max_digits=19
            ),
            preserve_default=False,
        ),
        migrations.RunPython(initialize_credit_fields, noop),
    ]
