class AuthenticationError(Exception):
    """Raised when authentication credentials or tokens are invalid/missing."""
    pass

class PermissionError(Exception):
    """Raised when an authenticated user lacks permission for an operation."""
    pass
