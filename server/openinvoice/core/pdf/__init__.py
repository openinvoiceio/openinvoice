from django.conf import settings
from django.utils.module_loading import import_string

from .backends.base import PdfBackend

_BACKEND: PdfBackend | None = None


def get_generator() -> PdfBackend:
    """Return the globally configured PDF backend instance."""
    global _BACKEND
    if _BACKEND is None:
        backend_cls = import_string(settings.PDF_GENERATOR_BACKEND)
        _BACKEND = backend_cls()
    return _BACKEND


def generate_pdf(html: str) -> bytes:
    """Generate PDF bytes from an HTML string using the configured backend."""
    return get_generator().generate(html)


__all__ = ["generate_pdf", "get_generator"]
