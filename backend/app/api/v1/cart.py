"""
Cart API endpoints.
Manages shopping cart for authenticated users.
"""

from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from app.db import get_db, CartItem, Product, User
from app.schemas import (
    CartItemCreate,
    CartItemUpdate,
    CartItemResponse,
    CartResponse,
    MessageResponse
)
from app.api.deps import get_current_user


router = APIRouter(prefix="/cart", tags=["Cart"])


@router.get("", response_model=CartResponse)
async def get_cart(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's cart with all items."""
    query = (
        select(CartItem)
        .options(selectinload(CartItem.product))
        .where(CartItem.user_id == current_user.id)
        .order_by(CartItem.created_at.desc())
    )
    result = await db.execute(query)
    cart_items = result.scalars().all()
    
    # Calculate subtotal
    subtotal = Decimal("0.00")
    item_count = 0
    
    for item in cart_items:
        if item.product and item.product.is_active:
            subtotal += item.product.price * item.quantity
            item_count += item.quantity
    
    return CartResponse(
        items=[CartItemResponse.model_validate(item) for item in cart_items],
        subtotal=subtotal,
        item_count=item_count
    )


@router.post("/add", response_model=CartItemResponse)
async def add_to_cart(
    item: CartItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add item to cart or update quantity if exists."""
    # Check product exists and is in stock
    product_result = await db.execute(
        select(Product).where(Product.id == item.product_id)
    )
    product = product_result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    if not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product not available"
        )
    
    if product.stock < item.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only {product.stock} items available"
        )
    
    # Check if item already in cart
    existing_result = await db.execute(
        select(CartItem)
        .options(selectinload(CartItem.product))
        .where(
            CartItem.user_id == current_user.id,
            CartItem.product_id == item.product_id
        )
    )
    existing = existing_result.scalar_one_or_none()
    
    if existing:
        # Update quantity
        new_quantity = existing.quantity + item.quantity
        if new_quantity > product.stock:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot add more. Only {product.stock} items available"
            )
        existing.quantity = min(new_quantity, 10)  # Max 10 per item
        await db.flush()
        await db.commit()
        return CartItemResponse.model_validate(existing)
    
    # Create new cart item
    cart_item = CartItem(
        user_id=current_user.id,
        product_id=item.product_id,
        quantity=item.quantity
    )
    db.add(cart_item)
    await db.flush()
    
    # Load product relationship
    await db.refresh(cart_item, ["product"])
    await db.commit()
    
    return CartItemResponse.model_validate(cart_item)


@router.put("/{cart_item_id}", response_model=CartItemResponse)
async def update_cart_item(
    cart_item_id: str,
    item: CartItemUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update cart item quantity."""
    result = await db.execute(
        select(CartItem)
        .options(selectinload(CartItem.product))
        .where(
            CartItem.id == cart_item_id,
            CartItem.user_id == current_user.id
        )
    )
    cart_item = result.scalar_one_or_none()
    
    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )
    
    # Check stock
    if cart_item.product.stock < item.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only {cart_item.product.stock} items available"
        )
    
    cart_item.quantity = item.quantity
    await db.flush()
    await db.commit()
    
    return CartItemResponse.model_validate(cart_item)


@router.delete("/{cart_item_id}", response_model=MessageResponse)
async def remove_from_cart(
    cart_item_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove item from cart."""
    result = await db.execute(
        select(CartItem).where(
            CartItem.id == cart_item_id,
            CartItem.user_id == current_user.id
        )
    )
    cart_item = result.scalar_one_or_none()
    
    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )
    
    await db.delete(cart_item)
    await db.commit()
    
    return MessageResponse(message="Item removed from cart")


@router.post("/clear", response_model=MessageResponse)
async def clear_cart(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Clear all items from cart."""
    await db.execute(
        delete(CartItem).where(CartItem.user_id == current_user.id)
    )
    await db.commit()
    return MessageResponse(message="Cart cleared")


@router.post("/merge", response_model=CartResponse)
async def merge_cart(
    items: list[CartItemCreate],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Merge guest cart items into user's cart after login.
    """
    if not items:
        # Just return current cart if no items to merge
        # Need to call get_cart logic manually or redirect
        # For simplicity, returning empty response or calling get_cart logic here
        
        # Load current cart
        query = (
            select(CartItem)
            .options(selectinload(CartItem.product))
            .where(CartItem.user_id == current_user.id)
            .order_by(CartItem.created_at.desc())
        )
        result = await db.execute(query)
        cart_items = result.scalars().all()
        
        subtotal = Decimal("0.00")
        item_count = 0
        for item in cart_items:
            if item.product and item.product.is_active:
                subtotal += item.product.price * item.quantity
                item_count += item.quantity
        
        return CartResponse(
            items=[CartItemResponse.model_validate(item) for item in cart_items],
            subtotal=subtotal,
            item_count=item_count
        )
        
    for item in items:
        # Check product
        product_result = await db.execute(
            select(Product).where(Product.id == item.product_id)
        )
        product = product_result.scalar_one_or_none()
        
        if not product or not product.is_active:
            continue
            
        # Check existing item
        existing_result = await db.execute(
            select(CartItem).where(
                CartItem.user_id == current_user.id,
                CartItem.product_id == item.product_id
            )
        )
        existing = existing_result.scalar_one_or_none()
        
        if existing:
            # Update quantity (max 10 or stock)
            new_quantity = existing.quantity + item.quantity
            existing.quantity = min(new_quantity, 10)
            if existing.quantity > product.stock:
                 existing.quantity = product.stock
        else:
            # Create new item
            qty = min(item.quantity, 10)
            if qty > product.stock:
                qty = product.stock
            
            if qty > 0:
                new_item = CartItem(
                    user_id=current_user.id,
                    product_id=item.product_id,
                    quantity=qty
                )
                db.add(new_item)
                
    await db.commit()
    
    # Return updated cart logic duplicated from GET
    query = (
        select(CartItem)
        .options(selectinload(CartItem.product))
        .where(CartItem.user_id == current_user.id)
        .order_by(CartItem.created_at.desc())
    )
    result = await db.execute(query)
    cart_items = result.scalars().all()
    
    subtotal = Decimal("0.00")
    item_count = 0
    for item in cart_items:
        if item.product and item.product.is_active:
            subtotal += item.product.price * item.quantity
            item_count += item.quantity
    
    return CartResponse(
        items=[CartItemResponse.model_validate(item) for item in cart_items],
        subtotal=subtotal,
        item_count=item_count
    )

