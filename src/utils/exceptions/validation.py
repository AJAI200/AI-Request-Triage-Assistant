class ValidationError(Exception):
    """Raised when classification result values fail allow-list validation."""
    pass

class JSONParseError(Exception):
    """Raised when raw string output fails JSON parsing."""
    pass
