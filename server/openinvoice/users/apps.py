from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "openinvoice.users"

    def ready(self):
        import openinvoice.users.schema  # noqa
