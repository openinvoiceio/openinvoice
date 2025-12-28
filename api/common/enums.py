from django.db import models


class FeatureCode(models.TextChoices):
    AUTOMATIC_INVOICE_DELIVERY = "automatic_invoice_delivery"
    AUTOMATIC_CREDIT_NOTE_DELIVERY = "automatic_credit_note_delivery"
    AUTOMATIC_QUOTE_DELIVERY = "automatic_quote_delivery"
    CUSTOM_NUMBERING_SYSTEMS = "custom_numbering_systems"
    CUSTOMER_PORTAL = "customer_portal"
    STRIPE_INTEGRATION = "stripe_integration"


class LimitCode(models.TextChoices):
    MAX_ACCOUNTS = "max_accounts"
    MAX_MEMBERS = "max_members"
    MAX_CUSTOMERS = "max_customers"
    MAX_PRODUCTS = "max_products"
    MAX_COUPONS = "max_coupons"
    MAX_TAX_RATES = "max_tax_rates"
    MAX_INVOICES_PER_MONTH = "max_invoices_per_month"
    MAX_CREDIT_NOTES_PER_MONTH = "max_credit_notes_per_month"
    MAX_QUOTES_PER_MONTH = "max_quotes_per_month"
