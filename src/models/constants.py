# models/constants.py

# GitLab Pipeline/Job Statuses
PIPELINE_SUCCESS_STATES = {"success", "skipped", "completed"}
PIPELINE_FAILURE_STATES = {"failed"}
PIPELINE_WAITING_STATES = {"manual"}
PIPELINE_RUNNING_STATES = {"running", "pending"}

# Default Exponential Backoff Parameters
DEFAULT_BACKOFF_INITIAL = 90  # seconds
DEFAULT_BACKOFF_MAX = 900     # seconds

# LLM Model
DEFAULT_LLM_MODEL = "GPT-4.1"

# Logging
LOGGING_FORMAT = "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"

# API Rate Limits
GITLAB_API_RATE_LIMIT = 300  # requests per minute (example)

# Error Messages
ERROR_PROJECT_NOT_FOUND = "GitLab project not found."
ERROR_AUTH_FAILED = "Authentication failed."
ERROR_NETWORK = "Network error occurred."
ERROR_LLM_FAILURE = "LLM service unavailable."
ERROR_GRPC_FAILURE = "gRPC communication failed."

# Config keys
CONFIG_PATHS = "paths"
CONFIG_SERVICES = "services"
CONFIG_AUTH = "authentication"
CONFIG_RETRY = "retry_config"
CONFIG_TEMPLATES = "templates"