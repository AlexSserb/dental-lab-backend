class LlmError(Exception):
    """Base class for LLM failures."""


class LlmNotConfigured(LlmError):
    pass


class LlmUnavailable(LlmError):
    """Provider unreachable, timed out or returned an HTTP error."""


class LlmValidationFailed(LlmError):
    """The model kept returning output that failed validation after all attempts."""
