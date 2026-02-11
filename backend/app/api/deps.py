"""
API Dependencies for authentication, database, and rate limiting.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis.asyncio as redis
from uuid import UUID

from app.db import get_db, User, AdminUser, TokenBlacklist
from app.core import verify_token, settings


# Security scheme
security = HTTPBearer()


# Redis client (lazy initialization)
_redis_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """Get Redis client instance."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    return _redis_client


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Validate JWT token and return current user.
    Raises 401 if token is invalid or user not found.
    """
    token = credentials.credentials
    
    payload = verify_token(token, token_type="access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Check if token is blacklisted
    token_jti = payload.get("jti")
    if token_jti:
        blacklisted = await db.execute(
            select(TokenBlacklist).where(TokenBlacklist.token_jti == token_jti)
        )
        if blacklisted.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    result = await db.execute(
        select(User).where(User.id == UUID(user_id))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    return user


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> AdminUser:
    """
    Validate JWT token and return current admin user.
    Raises 401 if token is invalid or admin not found.
    """
    token = credentials.credentials
    
    payload = verify_token(token, token_type="access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    admin_id = payload.get("sub")
    is_admin = payload.get("is_admin", False)
    
    if not admin_id or not is_admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin access required"
        )
    
    result = await db.execute(
        select(AdminUser).where(AdminUser.id == UUID(admin_id))
    )
    admin = result.scalar_one_or_none()
    
    if not admin or not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin not found or disabled"
        )
    
    return admin


class RateLimiter:
    """Rate limiter using Redis sliding window."""
    
    def __init__(self, requests: int, window: int):
        """
        Initialize rate limiter.
        
        Args:
            requests: Maximum requests allowed
            window: Time window in seconds
        """
        self.requests = requests
        self.window = window
    
    async def __call__(self, request: Request) -> None:
        """Check rate limit for request."""
        try:
            redis_client = await get_redis()
            
            # Use IP address and path as key
            client_ip = request.client.host if request.client else "unknown"
            key = f"rate_limit:{client_ip}:{request.url.path}"
            
            # Get current count
            current = await redis_client.get(key)
            
            if current is None:
                # First request, set with expiry
                await redis_client.setex(key, self.window, 1)
            elif int(current) >= self.requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Try again in {self.window} seconds."
                )
            else:
                # Increment counter
                await redis_client.incr(key)
        except HTTPException:
            raise
        except Exception as e:
            # Fallback to in-memory if Redis fails
            import logging
            import time
            logging.error(f"Redis rate limit error: {e}. Falling back to in-memory.")
            
            # Simple in-memory fallback
            # Note: This is per-process and will not work perfectly across workers,
            # but it prevents a complete fail-open or fail-close.
            try:
                if not hasattr(self, "_memory_store"):
                    self._memory_store = {}
                
                now = time.time()
                # Clean old entries
                self._memory_store = {k: v for k, v in self._memory_store.items() 
                                    if now - v[1] < self.window}
                
                key = f"mem:{client_ip}:{request.url.path}"
                count, start_time = self._memory_store.get(key, (0, now))
                
                if count >= self.requests:
                     raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Rate limit exceeded (fallback). Try again in {self.window} seconds."
                    )
                
                self._memory_store[key] = (count + 1, start_time)
            except Exception as fallback_error:
                 logging.error(f"Rate limit fallback error: {fallback_error}")
                 # Last resort: fail open to keep service alive
                 pass


# Pre-configured rate limiters
default_rate_limiter = RateLimiter(
    requests=settings.RATE_LIMIT_PER_MINUTE, 
    window=60
)
otp_rate_limiter = RateLimiter(
    requests=settings.OTP_RATE_LIMIT_PER_HOUR, 
    window=3600
)
admin_login_rate_limiter = RateLimiter(
    requests=settings.ADMIN_LOGIN_RATE_LIMIT_PER_MINUTE,
    window=60
)


async def get_optional_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise.
    Useful for endpoints that work with or without auth.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.split(" ")[1]
    payload = verify_token(token, token_type="access")
    
    if not payload:
        return None
    
    user_id = payload.get("sub")
    if not user_id:
        return None
    
    result = await db.execute(
        select(User).where(User.id == UUID(user_id))
    )
    return result.scalar_one_or_none()
