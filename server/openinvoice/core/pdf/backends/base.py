from __future__ import annotations

from abc import ABC, abstractmethod


class PdfBackend(ABC):
    """Base class for PDF generator backends."""

    @abstractmethod
    def generate(self, html: str) -> bytes:
        """Generate PDF bytes from an HTML string."""
        raise NotImplementedError
