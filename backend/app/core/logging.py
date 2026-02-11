"""
Logging configuration for the application.
Provides structured logging with JSON format for production.
Includes request ID tracing via contextvars.
"""

import logging
import sys
from typing import Any
import json
from datetime import datetime

from app.core.config import settings


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging with request ID."""
    
    def format(self, record: logging.LogRecord) -> str:
        from app.core.middleware import get_request_id
        
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add request ID if available
        rid = get_request_id()
        if rid:
            log_data["request_id"] = rid
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)
        
        return json.dumps(log_data)


class DevelopmentFormatter(logging.Formatter):
    """Human-readable formatter for development with request ID."""
    
    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"
    
    def format(self, record: logging.LogRecord) -> str:
        from app.core.middleware import get_request_id
        
        color = self.COLORS.get(record.levelname, self.RESET)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        rid = get_request_id()
        rid_str = f" [{rid}]" if rid else ""
        
        formatted = (
            f"{color}[{timestamp}] {record.levelname:8}{self.RESET} |"
            f"{rid_str} "
            f"{record.module}.{record.funcName}:{record.lineno} | "
            f"{record.getMessage()}"
        )
        
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"
        
        return formatted


def setup_logging() -> logging.Logger:
    """
    Configure and return the application logger.
    Uses JSON format in production, colored output in development.
    """
    logger = logging.getLogger("ecommerce")
    logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    
    # Use appropriate formatter based on environment
    if settings.DEBUG:
        handler.setFormatter(DevelopmentFormatter())
    else:
        handler.setFormatter(JSONFormatter())
    
    logger.addHandler(handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


# Create application logger
logger = setup_logging()


def log_with_context(
    level: str, 
    message: str, 
    **extra: Any
) -> None:
    """
    Log a message with additional context data.
    
    Args:
        level: Log level (debug, info, warning, error, critical)
        message: The log message
        **extra: Additional context to include in the log
    """
    log_func = getattr(logger, level.lower(), logger.info)
    
    if extra:
        record = logging.LogRecord(
            name=logger.name,
            level=getattr(logging, level.upper()),
            pathname="",
            lineno=0,
            msg=message,
            args=(),
            exc_info=None
        )
        record.extra_data = extra
        logger.handle(record)
    else:
        log_func(message)
