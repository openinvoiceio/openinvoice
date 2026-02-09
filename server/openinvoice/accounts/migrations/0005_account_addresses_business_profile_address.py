import django.db.models.deletion
from django.db import migrations, models


def migrate_account_addresses(apps, _schema_editor):
    Account = apps.get_model("accounts", "Account")
    BusinessProfile = apps.get_model("accounts", "BusinessProfile")

    for account in Account.objects.all():
        address_ids = list(
            BusinessProfile.objects.filter(accounts=account, address__isnull=False)
            .values_list("address_id", flat=True)
            .distinct()
        )
        if address_ids:
            account.addresses.add(*address_ids)


class Migration(migrations.Migration):
    dependencies = [
        ("addresses", "0002_address_timestamps"),
        ("accounts", "0004_account_tax_ids"),
    ]

    operations = [
        migrations.AddField(
            model_name="account",
            name="addresses",
            field=models.ManyToManyField(related_name="accounts", to="addresses.address"),
        ),
        migrations.RunSQL(
            sql=(
                "ALTER TABLE accounts_businessprofile "
                "DROP CONSTRAINT IF EXISTS accounts_businessprofile_address_id_848f941d_uniq;"
                "DROP INDEX IF EXISTS accounts_businessprofile_address_id_848f941d;"
            ),
            reverse_sql=(
                "ALTER TABLE accounts_businessprofile "
                "ADD CONSTRAINT accounts_businessprofile_address_id_848f941d_uniq "
                "UNIQUE (address_id);"
            ),
        ),
        migrations.AlterField(
            model_name="businessprofile",
            name="address",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="business_profiles",
                to="addresses.address",
            ),
        ),
        migrations.RunPython(migrate_account_addresses, migrations.RunPython.noop),
    ]
