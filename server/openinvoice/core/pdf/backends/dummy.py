from __future__ import annotations

from .base import PdfBackend


class DummyBackend(PdfBackend):
    """Dummy backend that simulates PDF generation for testing purposes."""

    def __init__(self) -> None:
        self.requests: list[str] = []

    def generate(self, html: str) -> bytes:
        self.requests.append(html)
        return b"PDF content"
