from .development import *  # noqa
from .development import MIDDLEWARE

# Middlewares

MIDDLEWARE = ["silk.middleware.SilkyMiddleware", *MIDDLEWARE]
