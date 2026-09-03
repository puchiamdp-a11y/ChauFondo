import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests and responses."""

    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Start timing
        start_time = time.time()

        # Get user info from token if available
        user_id = "anonymous"
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            user_id = f"token_user"  # Simplified, full extraction in routes

        # Log request
        logger.info(
            f"{request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "endpoint": f"{request.method} {request.url.path}",
                "user_id": user_id,
            }
        )

        try:
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Log response
            log_level = "info"
            if response.status_code >= 500:
                log_level = "error"
            elif response.status_code >= 400:
                log_level = "warning"

            getattr(logger, log_level)(
                f"{request.method} {request.url.path} - {response.status_code}",
                extra={
                    "request_id": request_id,
                    "endpoint": f"{request.method} {request.url.path}",
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                    "user_id": user_id,
                }
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            return response

        except Exception as e:
            # Log error
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"{request.method} {request.url.path} - {type(e).__name__}: {str(e)}",
                exc_info=True,
                extra={
                    "request_id": request_id,
                    "endpoint": f"{request.method} {request.url.path}",
                    "duration_ms": round(duration_ms, 2),
                    "user_id": user_id,
                }
            )
            raise
