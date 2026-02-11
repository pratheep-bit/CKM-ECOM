"""
User profile and address management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.db import get_db, User, Address
from app.schemas import (
    UserResponse,
    UserUpdate,
    AddressCreate,
    AddressUpdate,
    AddressResponse,
    MessageResponse
)
from app.api.deps import get_current_user


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current user's profile."""
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user's profile."""
    if update_data.name:
        current_user.name = update_data.name
    if update_data.email:
        current_user.email = update_data.email
    
    await db.commit()
    await db.refresh(current_user)
    
    return UserResponse.model_validate(current_user)


# Address endpoints
@router.get("/me/addresses", response_model=list[AddressResponse])
async def list_addresses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all addresses for current user."""
    result = await db.execute(
        select(Address)
        .where(Address.user_id == current_user.id)
        .order_by(Address.is_default.desc(), Address.created_at.desc())
    )
    addresses = result.scalars().all()
    return [AddressResponse.model_validate(a) for a in addresses]


@router.post("/me/addresses", response_model=AddressResponse)
async def create_address(
    address_data: AddressCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new address for current user."""
    # If this is default, remove default from others
    if address_data.is_default:
        await db.execute(
            update(Address)
            .where(Address.user_id == current_user.id)
            .values(is_default=False)
        )
    
    address = Address(
        user_id=current_user.id,
        **address_data.model_dump()
    )
    db.add(address)
    await db.commit()
    await db.refresh(address)
    
    return AddressResponse.model_validate(address)


@router.put("/me/addresses/{address_id}", response_model=AddressResponse)
async def update_address(
    address_id: str,
    update_data: AddressUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update an address."""
    result = await db.execute(
        select(Address).where(
            Address.id == address_id,
            Address.user_id == current_user.id
        )
    )
    address = result.scalar_one_or_none()
    
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )
    
    # If setting as default, remove default from others
    if update_data.is_default:
        await db.execute(
            update(Address)
            .where(
                Address.user_id == current_user.id,
                Address.id != address_id
            )
            .values(is_default=False)
        )
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(address, field, value)
    
    await db.commit()
    await db.refresh(address)
    
    return AddressResponse.model_validate(address)


@router.delete("/me/addresses/{address_id}", response_model=MessageResponse)
async def delete_address(
    address_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an address."""
    result = await db.execute(
        select(Address).where(
            Address.id == address_id,
            Address.user_id == current_user.id
        )
    )
    address = result.scalar_one_or_none()
    
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )
    
    await db.delete(address)
    await db.commit()
    
    return MessageResponse(message="Address deleted successfully")
