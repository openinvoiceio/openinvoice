from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("addresses", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="address",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name="address",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AlterField(
            model_name="address",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name="address",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
    ]
