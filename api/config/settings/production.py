import logging

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from .base import *  # noqa
from .base import LOG_LEVEL, env

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
