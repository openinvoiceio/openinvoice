from django.contrib.postgres.fields import ArrayField
from django.db import migrations, models


def migrate_audience(apps, _schema_editor):
    InvoiceDocument = apps.get_model("invoices", "InvoiceDocument")

    documents = []
    for document in InvoiceDocument.objects.all().iterator():
        if document.role == "primary":
            document.audience = ["customer"]
        elif document.role == "secondary":
            document.audience = ["internal"]
        elif document.role == "legal":
            document.audience = ["legal"]
        else:
            document.audience = []
        documents.append(document)

    if documents:
        InvoiceDocument.objects.bulk_update(documents, ["audience"])


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
        migrations.RunPython(migrate_audience, migrations.RunPython.noop),
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
        migrations.RemoveField(
            model_name="invoicedocument",
            name="role",
        ),
    ]
