from django.apps import AppConfig


class StripeIntegrationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "openinvoice.integrations.stripe"
    label = "stripe_integrations"
