from common.exceptions import ApplicationError


class TaxRateNotFoundError(ApplicationError):
    """Exception raised when a tax rate is not found."""
