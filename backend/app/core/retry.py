"""
Retry decorator for external API calls.
Provides exponential backoff with configurable retries and jitter.
"""

import asyncio
import functools
import random
from typing import Tuple, Type

from app.core import logger


def async_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry_log: bool = True,
):
    """
    Decorator that retries an async function with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds (doubles each attempt)
        max_delay: Maximum delay cap in seconds
        exceptions: Tuple of exception types to catch and retry
        on_retry_log: Whether to log retry attempts
    
    Usage:
        @async_retry(max_retries=3, exceptions=(httpx.HTTPError,))
        async def call_external_api():
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        if on_retry_log:
                            logger.error(
                                f"{func.__name__}: all {max_retries} retries exhausted. "
                                f"Last error: {e}"
                            )
                        raise
                    
                    # Exponential backoff with jitter
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    jitter = random.uniform(0, delay * 0.1)
                    wait = delay + jitter
                    
                    if on_retry_log:
                        logger.warning(
                            f"{func.__name__}: attempt {attempt + 1}/{max_retries} "
                            f"failed ({type(e).__name__}: {e}). "
                            f"Retrying in {wait:.1f}s..."
                        )
                    
                    await asyncio.sleep(wait)
            
            raise last_exception  # Should never reach here
        
        return wrapper
    return decorator
