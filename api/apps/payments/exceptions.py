from common.exceptions import ApplicationError


class InvoicePaymentAmountExceededError(ApplicationError):
    """Exception raised when payment amount exceeds the invoice total."""


class PaymentBackendNotFoundError(ApplicationError):
    """Exception raised when payment backend is not configured."""


class PaymentCheckoutError(ApplicationError):
    """Exception raised when payment checkout session creation fails."""
