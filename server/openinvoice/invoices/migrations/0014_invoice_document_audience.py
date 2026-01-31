from django.contrib.postgres.fields import ArrayField
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("invoices", "0013_remove_invoice_custom_fields_remove_invoice_footer_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="invoicedocument",
            name="audience",
            field=ArrayField(
                base_field=models.CharField(
                    choices=[("customer", "Customer"), ("internal", "Internal"), ("legal", "Legal")],
                    max_length=20,
                ),
                default=list,
                size=None,
            ),
        ),
        migrations.RemoveConstraint(
            model_name="invoicedocument",
            name="uniq_primary_invoice_document",
        ),
        migrations.RemoveConstraint(
            model_name="invoicedocument",
            name="uniq_legal_invoice_document",
        ),
        migrations.RemoveIndex(
            model_name="invoicedocument",
            name="invoices_in_invoice_35a518_idx",
        ),
    ]
