"""
Request ID middleware for distributed tracing.
Generates a unique ID per request, makes it available via contextvars,
and injects it into response headers.
"""

import uuid
from contextvars import ContextVar
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Context variable — accessible from any async code in the request lifecycle
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    """Get the current request ID from context."""
    return request_id_var.get()


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that assigns a unique request ID to every incoming request.
    - Reads X-Request-ID header if provided (from upstream proxy/LB)
    - Otherwise generates a new UUID
    - Stores in contextvars for access by loggers
    - Injects into response headers
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Use existing header or generate new
        rid = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
        request_id_var.set(rid)
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        
        return response
