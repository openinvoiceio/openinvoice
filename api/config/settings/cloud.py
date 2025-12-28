import logging
from typing import Final

import sentry_sdk
import stripe
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from .base import *  # noqa
from .base import LOG_LEVEL, PRIVACY_URL, TERMS_URL, FeatureCode, LimitCode, env

# Production checklist https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# General

DEBUG = env.bool("DJANGO_DEBUG", default=False)
SECRET_KEY = env.str("DJANGO_SECRET_KEY")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[])

# CORS

CORS_ALLOW_ALL_ORIGINS = False
CORS_ORIGIN_WHITELIST = env.list("DJANGO_CORS_ORIGIN_WHITELIST", default=[])

# CSRF

CSRF_COOKIE_DOMAIN = env.str("DJANGO_CSRF_COOKIE_DOMAIN")
CSRF_COOKIE_SECURE = env.bool("DJANGO_CSRF_COOKIE_SECURE", default=True)
CSRF_TRUSTED_ORIGINS = CORS_ORIGIN_WHITELIST

# Session

SESSION_COOKIE_SECURE = env.bool("DJANGO_SESSION_COOKIE_SECURE", default=True)

# Security

# https://docs.djangoproject.com/en/5.1/ref/settings/#secure-proxy-ssl-header
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# https://docs.djangoproject.com/en/5.1/ref/settings/#secure-ssl-redirect
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
# https://docs.djangoproject.com/en/5.1/ref/middleware/#x-content-type-options-nosniff
SECURE_CONTENT_TYPE_NOSNIFF = env.bool("DJANGO_SECURE_CONTENT_TYPE_NOSNIFF", default=True)
SECURE_BROWSER_XSS_FILTER = True

# Storage

STORAGE_OPTIONS = {
    "access_key": env.str("DJANGO_AWS_ACCESS_KEY_ID"),
    "secret_key": env.str("DJANGO_AWS_SECRET_ACCESS_KEY"),
    "bucket_name": env.str("DJANGO_AWS_STORAGE_BUCKET_NAME"),
    "region_name": env.str("DJANGO_AWS_S3_REGION_NAME"),
    "default_acl": "private",
}

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": STORAGE_OPTIONS,
    },
    "staticfiles": {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": STORAGE_OPTIONS,
    },
}

# Sentry

SENTRY_DSN = env.str("DJANGO_SENTRY_DSN", default=None)
SENTRY_LOG_LEVEL = env.str("DJANGO_SENTRY_LOG_LEVEL", LOG_LEVEL)

sentry_sdk.init(
    dsn=SENTRY_DSN,
    integrations=[
        LoggingIntegration(level=SENTRY_LOG_LEVEL, event_level=logging.CRITICAL),
        DjangoIntegration(),
    ],
    environment="production",
    traces_sample_rate=env.float("DJANGO_SENTRY_TRACES_SAMPLE_RATE", default=0.1),
)

# Stripe

STRIPE_API_KEY = env.str("DJANGO_STRIPE_API_KEY", default=None)
stripe.api_key = STRIPE_API_KEY
stripe.api_version = "2025-03-31.basil"
STRIPE_STANDARD_PRICE_ID = env.str("DJANGO_STRIPE_STANDARD_PRICE_ID", default="")
STRIPE_ENTERPRISE_PRICE_ID = env.str("DJANGO_STRIPE_ENTERPRISE_PRICE_ID", default="")
STRIPE_WEBHOOK_SECRET = env.str("DJANGO_STRIPE_WEBHOOK_SECRET", default="")
STRIPE_TRIAL_DAYS = env.int("DJANGO_STRIPE_TRIAL_DAYS", default=14)
STRIPE_PAYMENT_METHOD_TYPES: Final = ["card"]
STRIPE_BILLING_PORTAL_CONFIGURATION: stripe.billing_portal.Configuration.CreateParams = {
    "business_profile": {
        "headline": "Manage your subscription",
        "privacy_policy_url": PRIVACY_URL,
        "terms_of_service_url": TERMS_URL,
    },
    "features": {
        "invoice_history": {
            "enabled": True,
        },
        "subscription_update": {
            "enabled": True,
            "default_allowed_updates": ["price", "quantity", "promotion_code"],
            "proration_behavior": "create_prorations",
        },
        "subscription_cancel": {
            "enabled": True,
            "mode": "at_period_end",
            "cancellation_reason": {
                "enabled": True,
                "options": [
                    "too_expensive",
                    "missing_features",
                    "switched_service",
                    "unused",
                    "other",
                ],
            },
        },
    },
}

# Entitlements

DEFAULT_PLAN = "free"
STANDARD_PLAN = "standard"
ENTERPRISE_PLAN = "enterprise"
PLANS = {
    DEFAULT_PLAN: {
        "name": "Free",
        "features": {
            FeatureCode.AUTOMATIC_INVOICE_DELIVERY: False,
            FeatureCode.AUTOMATIC_CREDIT_NOTE_DELIVERY: False,
            FeatureCode.AUTOMATIC_QUOTE_DELIVERY: False,
            FeatureCode.CUSTOM_NUMBERING_SYSTEMS: False,
            FeatureCode.CUSTOMER_PORTAL: True,
            FeatureCode.STRIPE_INTEGRATION: False,
        },
        "limits": {
            LimitCode.MAX_ACCOUNTS: 1,
            LimitCode.MAX_MEMBERS: 1,
            LimitCode.MAX_CUSTOMERS: 10,
            LimitCode.MAX_PRODUCTS: 20,
            LimitCode.MAX_COUPONS: 5,
            LimitCode.MAX_TAX_RATES: 5,
            LimitCode.MAX_INVOICES_PER_MONTH: 10,
            LimitCode.MAX_CREDIT_NOTES_PER_MONTH: 10,
            LimitCode.MAX_QUOTES_PER_MONTH: 10,
        },
        "price_id": None,
    },
    STANDARD_PLAN: {
        "name": "Standard",
        "features": {
            FeatureCode.AUTOMATIC_INVOICE_DELIVERY: True,
            FeatureCode.AUTOMATIC_CREDIT_NOTE_DELIVERY: True,
            FeatureCode.AUTOMATIC_QUOTE_DELIVERY: True,
            FeatureCode.CUSTOM_NUMBERING_SYSTEMS: True,
            FeatureCode.CUSTOMER_PORTAL: True,
            FeatureCode.STRIPE_INTEGRATION: True,
        },
        "limits": {
            LimitCode.MAX_ACCOUNTS: 5,
            LimitCode.MAX_MEMBERS: 5,
            LimitCode.MAX_CUSTOMERS: None,
            LimitCode.MAX_PRODUCTS: None,
            LimitCode.MAX_COUPONS: None,
            LimitCode.MAX_TAX_RATES: None,
            LimitCode.MAX_INVOICES_PER_MONTH: 200,
            LimitCode.MAX_CREDIT_NOTES_PER_MONTH: 200,
            LimitCode.MAX_QUOTES_PER_MONTH: 200,
        },
        "price_id": STRIPE_STANDARD_PRICE_ID,
    },
    ENTERPRISE_PLAN: {
        "name": "Enterprise",
        "features": {
            FeatureCode.AUTOMATIC_INVOICE_DELIVERY: True,
            FeatureCode.AUTOMATIC_CREDIT_NOTE_DELIVERY: True,
            FeatureCode.AUTOMATIC_QUOTE_DELIVERY: True,
            FeatureCode.CUSTOM_NUMBERING_SYSTEMS: True,
            FeatureCode.CUSTOMER_PORTAL: True,
            FeatureCode.STRIPE_INTEGRATION: True,
        },
        "limits": {
            LimitCode.MAX_ACCOUNTS: None,
            LimitCode.MAX_MEMBERS: None,
            LimitCode.MAX_CUSTOMERS: None,
            LimitCode.MAX_PRODUCTS: None,
            LimitCode.MAX_COUPONS: None,
            LimitCode.MAX_TAX_RATES: None,
            LimitCode.MAX_INVOICES_PER_MONTH: None,
            LimitCode.MAX_CREDIT_NOTES_PER_MONTH: None,
            LimitCode.MAX_QUOTES_PER_MONTH: None,
        },
        "price_id": STRIPE_ENTERPRISE_PRICE_ID,
    },
}
