from __future__ import annotations

from django.conf import settings
from gotenberg_client import BaseClientError, GotenbergClient
from gotenberg_client.options import PdfAFormat

from common.pdf.exceptions import PdfError, PdfGenerationError

from .base import PdfBackend


class GotenbergBackend(PdfBackend):
    """Backend that generates PDFs from HTML using a Gotenberg server."""

    def __init__(self) -> None:
        self.client = GotenbergClient(
            host=settings.GOTENBERG_URL,
            timeout=settings.GOTENBERG_TIMEOUT,
        )

    def generate(self, html: str) -> bytes:
        try:
            with self.client.chromium.html_to_pdf() as route:
                response = route.string_index(html).pdf_format(PdfAFormat.A2b).scale(1.28).run_with_retry()
        except BaseClientError as e:
            raise PdfGenerationError from e
        except Exception as e:
            raise PdfError from e
        return response.content
