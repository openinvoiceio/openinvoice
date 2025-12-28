from django.db import models


class FeatureCode(models.TextChoices):
    AUTOMATIC_INVOICE_DELIVERY = "automatic-invoice-delivery"
    AUTOMATIC_CREDIT_NOTE_DELIVERY = "automatic-credit-note-delivery"
    AUTOMATIC_QUOTE_DELIVERY = "automatic-quote-delivery"
    CUSTOM_NUMBERING_SYSTEMS = "custom-numbering-systems"
    CUSTOMER_PORTAL = "customer-portal"
    STRIPE_INTEGRATION = "stripe-integration"


class LimitCode(models.TextChoices):
    MAX_MEMBERS = "max-members"
    MAX_CUSTOMERS = "max-customers"
    MAX_PRODUCTS = "max-products"
    MAX_COUPONS = "max-coupons"
    MAX_TAX_RATES = "max-tax-rates"
    MAX_INVOICES_PER_MONTH = "max-invoices-per-month"
    MAX_CREDIT_NOTES_PER_MONTH = "max-credit-notes-per-month"
    MAX_QUOTES_PER_MONTH = "max-quotes-per-month"
