from .base import *  # noqa
from .base import MIDDLEWARE

# General

DEBUG = True
SECRET_KEY = "django-insecure-a&fp91p%2ybxhoui#s+gm7+mkd(+2*os#e@ncucqz6ra#f%8d4"  # noqa: S105
SALT_KEY = "insecure-salt-key"
ALLOWED_HOSTS = ["localhost"]

# Middlewares

MIDDLEWARE = ["silk.middleware.SilkyMiddleware", *MIDDLEWARE]

# Vite

DJANGO_VITE = {
    "default": {
        "dev_mode": True,
    }
}

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

# API

HEADLESS_SERVE_SPECIFICATION = True
