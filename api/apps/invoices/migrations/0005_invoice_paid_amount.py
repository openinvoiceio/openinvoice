import djmoney.models.fields
from django.db import migrations
from django.db.models import DecimalField, Sum, Value
from django.db.models.functions import Coalesce
from djmoney.money import Money

from apps.payments.choices import PaymentStatus


def initialize_paid_amounts(apps, _schema_editor):
    Invoice = apps.get_model("invoices", "Invoice")
    Payment = apps.get_model("payments", "Payment")

    for invoice in Invoice.objects.all():
        total_paid_amount = Payment.objects.filter(
            invoices=invoice,
            status=PaymentStatus.SUCCEEDED,
        ).aggregate(
            total=Coalesce(
                Sum("amount"),
                Value(0),
                output_field=DecimalField(max_digits=19, decimal_places=2),
            )
        )["total"]

        invoice.total_paid_amount = Money(total_paid_amount or 0, invoice.currency)
        outstanding_amount = invoice.total_amount - invoice.total_credit_amount - invoice.total_paid_amount
        invoice.outstanding_amount = max(outstanding_amount, Money(0, invoice.currency))
        invoice.save(update_fields=["total_paid_amount", "outstanding_amount"])


class Migration(migrations.Migration):
    dependencies = [
        ("invoices", "0004_invoice_delivery_method_invoice_recipients"),
        ("payments", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="invoice",
            name="total_paid_amount",
            field=djmoney.models.fields.MoneyField(
                currency_field_name="currency", decimal_places=2, default=0, max_digits=19
            ),
            preserve_default=False,
        ),
        migrations.RunPython(initialize_paid_amounts, migrations.RunPython.noop),
    ]
