"""
Main FastAPI application entry point.
Configures middleware, routes, and startup/shutdown events.
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import time

from app.core import settings, logger
from app.core.middleware import RequestIDMiddleware
from app.api import api_router
from app.db import init_db


async def _run_order_cleanup_loop():
    """Background loop that cancels expired unpaid orders every 5 minutes."""
    from app.api.v1.orders import cancel_expired_orders
    
    while True:
        try:
            cancelled = await cancel_expired_orders(max_age_minutes=30)
            if cancelled:
                logger.info(f"Order cleanup: cancelled {cancelled} expired orders")
        except Exception as e:
            logger.error(f"Order cleanup error: {e}")
        
        await asyncio.sleep(300)  # Run every 5 minutes


async def _cleanup_expired_tokens_loop():
    """Background loop that cleans up expired blacklisted tokens (daily)."""
    from datetime import datetime
    from sqlalchemy import delete
    from app.db import async_session_maker, TokenBlacklist
    
    while True:
        try:
            async with async_session_maker() as session:
                result = await session.execute(
                    delete(TokenBlacklist).where(
                        TokenBlacklist.expires_at < datetime.utcnow()
                    )
                )
                await session.commit()
                if result.rowcount:
                    logger.info(f"Token cleanup: removed {result.rowcount} expired entries")
        except Exception as e:
            logger.error(f"Token cleanup error: {e}")
        
        await asyncio.sleep(86400)  # Run daily


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} ({settings.ENVIRONMENT})...")
    
    # Initialize database tables (in production, use Alembic migrations)
    if settings.DEBUG:
        await init_db()
        logger.info("Database tables initialized (Dev Mode)")
    else:
        logger.info("Skipping auto-init of DB tables (Production Mode)")
    
    # Initialize Sentry if configured
    if settings.SENTRY_DSN:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
            sentry_sdk.init(
                dsn=settings.SENTRY_DSN,
                environment=settings.ENVIRONMENT,
                traces_sample_rate=0.1,
                integrations=[FastApiIntegration(), SqlalchemyIntegration()],
            )
            logger.info("Sentry initialized")
        except ImportError:
            logger.warning("sentry-sdk not installed, skipping Sentry init")
    
    # Check Redis connectivity
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.REDIS_URL)
        await r.ping()
        logger.info("Redis connected ✓")
        await r.close()
    except Exception:
        logger.warning("Redis not available — rate limiting will use in-memory fallback")
    
    # Start background tasks
    cleanup_task = asyncio.create_task(_run_order_cleanup_loop())
    token_cleanup_task = asyncio.create_task(_cleanup_expired_tokens_loop())
    logger.info("Background tasks started (order cleanup 5m, token cleanup 24h)")
    
    yield
    
    # Shutdown
    cleanup_task.cancel()
    token_cleanup_task.cancel()
    try:
        await asyncio.gather(cleanup_task, token_cleanup_task, return_exceptions=True)
    except asyncio.CancelledError:
        pass
    logger.info("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.API_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)


# Request ID middleware (must be first — before CORS)
app.add_middleware(RequestIDMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing and request ID."""
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    
    logger.info(
        f"{request.method} {request.url.path} - "
        f"{response.status_code} - {process_time:.2f}ms"
    )
    
    return response


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, 
    exc: RequestValidationError
):
    """Handle validation errors with detailed response."""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": errors
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred" if not settings.DEBUG 
                     else str(exc)
        }
    )


# Include API routes
app.include_router(api_router)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.API_VERSION,
        "environment": settings.ENVIRONMENT
    }


# Root redirect
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "docs": "/docs" if settings.DEBUG else None,
        "health": "/health"
    }
