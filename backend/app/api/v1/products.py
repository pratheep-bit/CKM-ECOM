"""
Product API endpoints.
Read-only endpoints for product catalog.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db import get_db, Product
from app.schemas import ProductResponse, ProductListResponse


router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=ProductListResponse)
async def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    is_active: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """Get paginated list of products."""
    offset = (page - 1) * page_size
    
    # Count total
    count_query = select(func.count(Product.id)).where(
        Product.is_active == is_active
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()
    
    # Get products
    query = (
        select(Product)
        .where(Product.is_active == is_active)
        .offset(offset)
        .limit(page_size)
        .order_by(Product.created_at.desc())
    )
    result = await db.execute(query)
    products = result.scalars().all()
    
    return ProductListResponse(
        items=[ProductResponse.model_validate(p) for p in products],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get product by ID or slug."""
    # Try to find by slug first, then by ID
    query = select(Product).where(
        (Product.slug == product_id) | (Product.id == product_id)
    )
    result = await db.execute(query)
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    if not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not available"
        )
    
    return ProductResponse.model_validate(product)
