from common.exceptions import ApplicationError


class InvoiceNotFoundError(ApplicationError):
    """Exception raised when an invoice is not found."""
