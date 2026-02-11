"""
Security utilities for authentication, password hashing, and JWT handling.
"""

from datetime import datetime, timedelta
from typing import Optional, Any
from jose import jwt, JWTError
from passlib.context import CryptContext
import hashlib
import secrets
import uuid

from app.core.config import settings


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
    additional_claims: dict = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        subject: The subject (usually user ID) to encode in the token
        expires_delta: Optional custom expiration time
        additional_claims: Additional claims to include in the token
    
    Returns:
        Encoded JWT token string
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access",
        "iat": datetime.utcnow(),
        "jti": str(uuid.uuid4())
    }
    
    if additional_claims:
        to_encode.update(additional_claims)
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(subject: str) -> str:
    """
    Create a JWT refresh token with longer expiration.
    
    Args:
        subject: The subject (usually user ID) to encode in the token
    
    Returns:
        Encoded JWT refresh token string
    """
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh",
        "iat": datetime.utcnow(),
        "jti": str(uuid.uuid4())
    }
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: The JWT token to verify
        token_type: Expected token type ("access" or "refresh")
    
    Returns:
        Decoded token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("type") != token_type:
            return None
        return payload
    except JWTError:
        return None


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def generate_otp(length: int = 6) -> str:
    """Generate a random numeric OTP."""
    return ''.join([str(secrets.randbelow(10)) for _ in range(length)])


def hash_otp(otp: str, mobile: str) -> str:
    """
    Hash OTP with mobile number for secure storage.
    Uses SHA256 for fast verification while still being secure.
    """
    combined = f"{mobile}:{otp}:{settings.SECRET_KEY}"
    return hashlib.sha256(combined.encode()).hexdigest()


def verify_otp_hash(otp: str, mobile: str, otp_hash: str) -> bool:
    """Verify OTP against stored hash."""
    expected_hash = hash_otp(otp, mobile)
    return secrets.compare_digest(expected_hash, otp_hash)
