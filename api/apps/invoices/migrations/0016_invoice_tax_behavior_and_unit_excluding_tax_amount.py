import djmoney.models.fields
from django.db import migrations, models


def backfill_tax_behavior_and_unit_excluding_tax_amount(apps, _):
    Invoice = apps.get_model("invoices", "Invoice")
    InvoiceLine = apps.get_model("invoices", "InvoiceLine")

    Invoice.objects.all().update(tax_behavior="exclusive")
    InvoiceLine.objects.all().update(unit_excluding_tax_amount=models.F("unit_amount"))


class Migration(migrations.Migration):
    dependencies = [
        ("invoices", "0015_alter_invoicecoupon_coupon_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="invoice",
            name="tax_behavior",
            field=models.CharField(
                choices=[
                    ("inclusive", "Inclusive"),
                    ("exclusive", "Exclusive"),
                    ("automatic", "Automatic"),
                ],
                default="automatic",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="invoiceline",
            name="unit_excluding_tax_amount",
            field=djmoney.models.fields.MoneyField(
                currency_field_name="currency",
                decimal_places=2,
                default=0,
                max_digits=19,
            ),
            preserve_default=False,
        ),
        migrations.RunPython(backfill_tax_behavior_and_unit_excluding_tax_amount),
    ]
