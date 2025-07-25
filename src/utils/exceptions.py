# utils/exceptions.py

class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""

class ProjectNotFoundError(Exception):
    """Raised when the GitLab project is not found."""

class AuthError(Exception):
    """Raised when authentication with GitLab or services fails."""

class NetworkError(Exception):
    """Raised when a network error occurs while calling external APIs."""

class LLMServiceError(Exception):
    """Raised when the LLM service returns an error."""

class GRPCServiceError(Exception):
    """Raised when the gRPC service returns an error."""

class RetryLimitExceeded(Exception):
    """Raised when the maximum retry limit is reached."""

class TimeoutError(Exception):
    """Raised when an operation times out."""

class ManualInterventionRequired(Exception):
    """Raised when manual intervention is required for a job."""

class InvalidAPIResponse(Exception):
    """Raised when an API response is invalid or incomplete."""