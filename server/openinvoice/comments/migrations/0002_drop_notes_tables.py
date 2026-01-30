from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("comments", "0001_initial"),
        ("credit_notes", "0007_creditnote_comments"),
        ("invoices", "0012_invoice_comments"),
        ("quotes", "0006_quote_comments"),
    ]

    operations = [
        migrations.RunSQL(
            "\n".join(
                [
                    "DROP TABLE IF EXISTS credit_notes_creditnote_notes CASCADE;",
                    "DROP TABLE IF EXISTS invoices_invoice_notes CASCADE;",
                    "DROP TABLE IF EXISTS quotes_quote_notes CASCADE;",
                    "DROP TABLE IF EXISTS notes_note CASCADE;",
                ]
            ),
            reverse_sql=migrations.RunSQL.noop,
        )
    ]
