class LLMClientError(Exception):
    """Raised when LLM API calls fail, hit rate limits, or return unparseable responses."""
    pass
