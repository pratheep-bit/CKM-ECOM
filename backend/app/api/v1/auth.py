"""
Authentication API endpoints.
Handles OTP-based mobile login.
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from uuid import UUID

from app.db import get_db, User, OTPLog
from app.schemas import (
    SendOTPRequest,
    VerifyOTPRequest,
    TokenResponse,
    RefreshTokenRequest,
    MessageResponse
)
from app.core import (
    generate_otp,
    hash_otp,
    verify_otp_hash,
    create_access_token,
    create_refresh_token,
    verify_token,
    settings,
    logger
)
from app.api.deps import otp_rate_limiter
from app.integrations.sms import send_otp_sms


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/send-otp",
    response_model=MessageResponse,
    dependencies=[Depends(otp_rate_limiter)]
)
async def send_otp(
    request: SendOTPRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Send OTP to the provided mobile number.
    Creates user if not exists.
    """
    mobile = request.mobile_number
    
    # Check for existing unexpired OTP
    existing_otp = await db.execute(
        select(OTPLog).where(
            and_(
                OTPLog.mobile_number == mobile,
                OTPLog.expires_at > datetime.utcnow(),
                OTPLog.is_used == False
            )
        )
    )
    existing = existing_otp.scalar_one_or_none()
    
    if existing:
        # Invalidate existing OTP to allow generating a new one
        existing.is_used = True
        await db.commit()
    
    # Generate new OTP
    otp = generate_otp()
    otp_hashed = hash_otp(otp, mobile)
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    
    # Create OTP log entry
    otp_log = OTPLog(
        mobile_number=mobile,
        otp_hash=otp_hashed,
        expires_at=expires_at
    )
    db.add(otp_log)
    
    # Send OTP via SMS
    try:
        await send_otp_sms(mobile, otp)
        logger.info(f"OTP sent to {mobile[:4]}****")
    except Exception as e:
        logger.error(f"Failed to send OTP: {e}")
    
    # In development, always log OTP for testing
    if settings.DEBUG:
        logger.info(f"DEV OTP for {mobile}: {otp}")
    
    await db.commit()
    
    return MessageResponse(
        message="OTP sent successfully",
        success=True
    )


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp_endpoint(
    request: VerifyOTPRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify OTP and return JWT tokens.
    Creates user if first-time login.
    """
    mobile = request.mobile_number
    otp = request.otp
    
    # Find valid OTP
    result = await db.execute(
        select(OTPLog).where(
            and_(
                OTPLog.mobile_number == mobile,
                OTPLog.expires_at > datetime.utcnow(),
                OTPLog.is_used == False
            )
        ).order_by(OTPLog.created_at.desc())
    )
    otp_log = result.scalar_one_or_none()
    
    if not otp_log:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid OTP found. Please request a new one."
        )
    
    # Increment attempts
    otp_log.attempts += 1
    
    if otp_log.attempts > 5:
        otp_log.is_used = True  # Invalidate after too many attempts
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Too many attempts. Please request a new OTP."
        )
    
    # Verify OTP
    if settings.ALLOW_MASTER_OTP and otp == "123456":
        # Allow master OTP only when explicitly enabled (NEVER in production)
        pass
    elif not verify_otp_hash(otp, mobile, otp_log.otp_hash):
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP"
        )
    
    # Mark OTP as used
    otp_log.is_used = True
    
    # Get or create user
    user_result = await db.execute(
        select(User).where(User.mobile_number == mobile)
    )
    user = user_result.scalar_one_or_none()
    
    if not user:
        # Create new user
        user = User(
            mobile_number=mobile,
            is_verified=True
        )
        db.add(user)
        await db.flush()  # Get user ID
        logger.info(f"New user created: {mobile[:4]}****")
    else:
        user.is_verified = True
    
    await db.commit()
    
    # Generate tokens
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token."""
    payload = verify_token(request.refresh_token, token_type="refresh")
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    user_id = payload.get("sub")
    
    # Verify user still exists and is active
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or disabled"
        )
    
    # Blacklist the old refresh token to prevent reuse
    old_jti = payload.get("jti")
    if old_jti:
        from app.db import TokenBlacklist
        blacklisted = TokenBlacklist(
            token_jti=old_jti,
            user_id=UUID(user_id),
            expires_at=datetime.utcfromtimestamp(payload["exp"])
        )
        db.add(blacklisted)
        try:
            await db.commit()
        except Exception:
            pass  # Already blacklisted
    
    # Generate new tokens
    access_token = create_access_token(str(user.id))
    new_refresh_token = create_refresh_token(str(user.id))
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: AsyncSession = Depends(get_db)
):
    """
    Logout user by blacklisting their current token.
    The token's JTI is stored so it's rejected on future requests.
    """
    token = credentials.credentials
    payload = verify_token(token, token_type="access")
    
    if payload and payload.get("jti"):
        from app.db import TokenBlacklist
        blacklisted = TokenBlacklist(
            token_jti=payload["jti"],
            user_id=UUID(payload["sub"]),
            expires_at=datetime.utcfromtimestamp(payload["exp"])
        )
        db.add(blacklisted)
        try:
            await db.commit()
        except Exception:
            pass  # Already blacklisted (duplicate jti)
    
    return MessageResponse(
        message="Logged out successfully",
        success=True
    )
