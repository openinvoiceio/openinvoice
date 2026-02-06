from django.db import migrations, models


def migrate_account_tax_ids(apps, _schema_editor):
    Account = apps.get_model("accounts", "Account")
    TaxId = apps.get_model("tax_ids", "TaxId")

    for account in Account.objects.all():
        tax_id_ids = list(
            TaxId.objects.filter(business_profiles__accounts=account).values_list("id", flat=True).distinct()
        )
        if tax_id_ids:
            account.tax_ids.add(*tax_id_ids)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_account_name_email"),
        ("tax_ids", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="account",
            name="tax_ids",
            field=models.ManyToManyField(related_name="accounts", to="tax_ids.taxid"),
        ),
        migrations.RunPython(migrate_account_tax_ids, migrations.RunPython.noop),
    ]
