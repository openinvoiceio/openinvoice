from django.apps import AppConfig


class StripeIntegrationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.integrations.stripe"
    label = "stripe_integrations"
