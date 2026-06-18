class Customer360Error(Exception):
    """Base domain error."""


class DataValidationError(Customer360Error):
    """Raised when incoming data fails validation."""


class InsufficientDataError(Customer360Error):
    """Raised when an analytical model cannot be fitted safely."""
