class IntegrationError(Exception):
    """Base exception for integration-related errors."""


class IntegrationConnectionError(IntegrationError):
    """Exception raised for errors during integration connection process."""
