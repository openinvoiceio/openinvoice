import logging
from typing import Any

from .base import *  # noqa

# General

DEBUG = True
SECRET_KEY = "django-insecure-a&fp91p%2ybxhoui#s+gm7+mkd(+2*os#e@ncucqz6ra#f%8d4"  # noqa: S105
SALT_KEY = "insecure-salt-key"
ALLOWED_HOSTS = ["localhost"]

# Password

PASSWORD_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)

# Cache

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

# CORS

CORS_ALLOWED_ORIGINS = ["http://localhost:8000"]

# CSRF

CSRF_TRUSTED_ORIGINS = ["http://localhost:8000"]

# Email

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# PDF

PDF_GENERATOR_BACKEND = "common.pdf.backends.dummy.DummyBackend"

# Storage

STORAGE_OPTIONS: dict[str, Any] = {}
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.memory.InMemoryStorage",
        "OPTIONS": STORAGE_OPTIONS,
    },
    "staticfiles": {
        "BACKEND": "django.core.files.storage.memory.InMemoryStorage",
        "OPTIONS": STORAGE_OPTIONS,
    },
}

# Logging

logging.disable()
