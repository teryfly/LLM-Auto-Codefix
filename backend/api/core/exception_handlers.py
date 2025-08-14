from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from utils.exceptions import (
    ProjectNotFoundError,
    AuthError,
    NetworkError,
    LLMServiceError,
    GRPCServiceError,
    RetryLimitExceeded,
    TimeoutError,
    ManualInterventionRequired
)

logger = logging.getLogger("api.exceptions")

async def project_not_found_handler(request: Request, exc: ProjectNotFoundError):
    logger.error(f"Project not found: {exc}")
    return JSONResponse(
        status_code=404,
        content={"error": "project_not_found", "message": str(exc)}
    )

async def auth_error_handler(request: Request, exc: AuthError):
    logger.error(f"Authentication error: {exc}")
    return JSONResponse(
        status_code=401,
        content={"error": "authentication_failed", "message": str(exc)}
    )

async def network_error_handler(request: Request, exc: NetworkError):
    logger.error(f"Network error: {exc}")
    return JSONResponse(
        status_code=503,
        content={"error": "network_error", "message": str(exc)}
    )

async def llm_service_error_handler(request: Request, exc: LLMServiceError):
    logger.error(f"LLM service error: {exc}")
    return JSONResponse(
        status_code=502,
        content={"error": "llm_service_error", "message": str(exc)}
    )

async def timeout_error_handler(request: Request, exc: TimeoutError):
    logger.error(f"Timeout error: {exc}")
    return JSONResponse(
        status_code=408,
        content={"error": "timeout", "message": str(exc)}
    )

async def validation_error_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content={"error": "validation_error", "message": str(exc)}
    )

async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_server_error", "message": "An unexpected error occurred"}
    )

def setup_exception_handlers(app: FastAPI):
    app.add_exception_handler(ProjectNotFoundError, project_not_found_handler)
    app.add_exception_handler(AuthError, auth_error_handler)
    app.add_exception_handler(NetworkError, network_error_handler)
    app.add_exception_handler(LLMServiceError, llm_service_error_handler)
    app.add_exception_handler(TimeoutError, timeout_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, general_exception_handler)