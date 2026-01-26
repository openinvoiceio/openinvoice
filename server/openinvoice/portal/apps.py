from django.apps import AppConfig


class PortalConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "openinvoice.portal"

    def ready(self) -> None:
        import openinvoice.portal.schema  # noqa: F401
