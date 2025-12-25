from common.exceptions import ApplicationError


class IntegrationConnectionNotFoundError(ApplicationError):
    """Exception raised when integration connection is not found."""


class PaymentProviderConnectionNotFoundError(ApplicationError):
    """Exception raised when payment provider connection is not found."""
