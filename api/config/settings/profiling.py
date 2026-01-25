from .development import *  # noqa
from .development import MIDDLEWARE, INSTALLED_APPS

# Applications

INSTALLED_APPS += ["silk"]

# Middlewares

MIDDLEWARE = ["silk.middleware.SilkyMiddleware", *MIDDLEWARE]
