from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware  # 改为从 starlette 导入
import time
import uuid
from typing import Callable
import logging
logger = logging.getLogger("api.middleware")
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        logger.info(f"[{request_id}] {request.method} {request.url.path} - Start")
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} - "
            f"Status: {response.status_code} - Time: {process_time:.3f}s"
        )
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        return response
class SessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Add session_id to request state if provided
        session_id = request.headers.get("X-Session-ID")
        if session_id:
            request.state.session_id = session_id
        response = await call_next(request)
        return response
def setup_middleware(app: FastAPI):
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(SessionMiddleware)