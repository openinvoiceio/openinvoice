from __future__ import annotations

from weasyprint import HTML

from common.pdf.exceptions import PdfError

from .base import PdfBackend


class WeasyPrintBackend(PdfBackend):
    """Backend that generates PDFs from HTML using a weasyprint cli."""

    def generate(self, html: str) -> bytes:
        try:
            return HTML(string=html).write_pdf(pdf_variant="pdf/a-2b", zoom=1.28)
        except Exception as e:
            raise PdfError from e
