import uuid

from django.db import migrations, models


def create_business_profiles(apps, _schema_editor):
    Account = apps.get_model("accounts", "Account")
    BusinessProfile = apps.get_model("accounts", "BusinessProfile")

    for account in Account.objects.all():
        profile = BusinessProfile.objects.create(
            name=account.name,
            legal_name=account.legal_name,
            legal_number=account.legal_number,
            email=account.email,
            phone=account.phone,
            address=account.address,
        )
        profile.tax_ids.set(account.tax_ids.all())
        account.default_business_profile = profile
        account.save(update_fields=["default_business_profile"])
        account.business_profiles.add(profile)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0007_account_language"),
        ("addresses", "0001_initial"),
        ("tax_ids", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="BusinessProfile",
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
                        related_name="business_profile_address",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.AddField(
            model_name="businessprofile",
            name="tax_ids",
            field=models.ManyToManyField(related_name="business_profiles", to="tax_ids.taxid"),
        ),
        migrations.AddField(
            model_name="account",
            name="default_business_profile",
            field=models.OneToOneField(
                to="accounts.businessprofile",
                on_delete=models.PROTECT,
                related_name="+",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="account",
            name="business_profiles",
            field=models.ManyToManyField(related_name="accounts", to="accounts.businessprofile"),
        ),
        migrations.RunPython(create_business_profiles, migrations.RunPython.noop),
        migrations.RemoveField(model_name="account", name="name"),
        migrations.RemoveField(model_name="account", name="legal_name"),
        migrations.RemoveField(model_name="account", name="legal_number"),
        migrations.RemoveField(model_name="account", name="email"),
        migrations.RemoveField(model_name="account", name="phone"),
        migrations.RemoveField(model_name="account", name="address"),
        migrations.RemoveField(model_name="account", name="tax_ids"),
        migrations.AlterField(
            model_name="account",
            name="default_business_profile",
            field=models.OneToOneField(
                to="accounts.businessprofile",
                on_delete=models.PROTECT,
                related_name="+",
            ),
        ),
    ]
