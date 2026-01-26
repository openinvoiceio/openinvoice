class PdfError(Exception):
    """Base class for all PDF-related exceptions."""


class PdfGenerationError(PdfError):
    """Raised when generating a PDF from HTML fails."""
