"""
Admin API endpoints.
Handles order management, shipments, refunds, and analytics.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.db import get_db, Order, OrderItem, Payment, Shipment, User, AdminUser, Product
from app.schemas import (
    AdminLoginRequest,
    AdminOrderUpdate,
    AdminCreateShipmentRequest,
    AdminRefundRequest,
    OrderResponse,
    OrderListResponse,
    PaymentResponse,
    AnalyticsResponse,
    TokenResponse,
    MessageResponse,
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse
)
from app.api.deps import get_current_admin
from app.core import (
    create_access_token,
    create_refresh_token,
    verify_password,
    settings,
    logger
)
from app.core.order_state import validate_transition, get_allowed_transitions
from app.integrations import create_shipment
from app.services.razorpay_service import razorpay_service
from app.api.deps import admin_login_rate_limiter


router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[Depends(admin_login_rate_limiter)]
)
async def admin_login(
    request: AdminLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Admin login with email/password."""
    result = await db.execute(
        select(AdminUser).where(AdminUser.email == request.email)
    )
    admin = result.scalar_one_or_none()
    
    if not admin or not verify_password(request.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )
    
    # Update last login
    admin.last_login = datetime.utcnow()
    await db.commit()
    
    # Generate tokens with admin flag
    access_token = create_access_token(
        str(admin.id),
        additional_claims={"is_admin": True, "role": admin.role}
    )
    refresh_token = create_refresh_token(str(admin.id))
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/orders", response_model=OrderListResponse)
async def list_all_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str = None,
    date_from: datetime = None,
    date_to: datetime = None,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all orders with filtering options."""
    offset = (page - 1) * page_size
    
    # Build query conditions
    conditions = []
    if status:
        conditions.append(Order.status == status)
    if date_from:
        conditions.append(Order.created_at >= date_from)
    if date_to:
        conditions.append(Order.created_at <= date_to)
    
    # Count total
    count_query = select(func.count(Order.id))
    if conditions:
        count_query = count_query.where(and_(*conditions))
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()
    
    # Get orders
    query = (
        select(Order)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    if conditions:
        query = query.where(and_(*conditions))
    
    result = await db.execute(query)
    orders = result.scalars().all()
    
    return OrderListResponse(
        items=[OrderResponse.model_validate(o) for o in orders],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order_admin(
    order_id: str,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get order details for admin."""
    query = (
        select(Order)
        .options(
            selectinload(Order.items),
            selectinload(Order.payment),
            selectinload(Order.shipment)
        )
        .where((Order.id == order_id) | (Order.order_number == order_id))
    )
    result = await db.execute(query)
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return OrderResponse.model_validate(order)


@router.put("/orders/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: str,
    update: AdminOrderUpdate,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update order status."""
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where((Order.id == order_id) | (Order.order_number == order_id))
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if update.status:
        if not validate_transition(order.status, update.status):
            allowed = get_allowed_transitions(order.status)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot change from '{order.status}' to '{update.status}'. "
                       f"Allowed transitions: {allowed or 'none (terminal state)'}"
            )
        order.status = update.status
    
    await db.commit()
    logger.info(f"Admin {admin.email} updated order {order.order_number}")
    
    return OrderResponse.model_validate(order)


@router.post("/orders/{order_id}/ship", response_model=MessageResponse)
async def create_order_shipment(
    order_id: str,
    request: AdminCreateShipmentRequest,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create shipment for order via Shiprocket."""
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where((Order.id == order_id) | (Order.order_number == order_id))
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.status not in ["confirmed", "processing"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot ship order with status: {order.status}"
        )
    
    # Check if shipment already exists
    existing = await db.execute(
        select(Shipment).where(Shipment.order_id == order.id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Shipment already exists for this order"
        )
    
    try:
        # Create shipment via Shiprocket
        shipment_data = await create_shipment(
            order_id=str(order.id),
            order_number=order.order_number,
            order_date=order.created_at,
            address={
                "name": order.shipping_name,
                "mobile": order.shipping_mobile,
                "line1": order.shipping_line1,
                "line2": order.shipping_line2,
                "city": order.shipping_city,
                "state": order.shipping_state,
                "pincode": order.shipping_pincode
            },
            items=[{
                "product_id": str(item.product_id),
                "product_name": item.product_name,
                "quantity": item.quantity,
                "price": item.price
            } for item in order.items],
            subtotal=order.subtotal,
            shipping_charges=order.shipping_fee,
            dimensions={
                "length": request.length,
                "breadth": request.breadth,
                "height": request.height,
                "weight": request.weight
            }
        )
        
        # Create shipment record
        shipment = Shipment(
            order_id=order.id,
            shiprocket_order_id=shipment_data["shiprocket_order_id"],
            shiprocket_shipment_id=shipment_data["shiprocket_shipment_id"],
            awb_number=shipment_data.get("awb_number"),
            courier_name=shipment_data.get("courier_name"),
            courier_id=shipment_data.get("courier_id"),
            tracking_url=shipment_data.get("tracking_url"),
            status="pickup_scheduled"
        )
        db.add(shipment)
        
        # Update order status
        order.status = "shipped"
        
        await db.commit()
        
        logger.info(f"Shipment created for order {order.order_number} by {admin.email}")
        
        return MessageResponse(
            message=f"Shipment created. AWB: {shipment_data.get('awb_number')}"
        )
        
    except Exception as e:
        logger.error(f"Shipment creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create shipment: {str(e)}"
        )


@router.post("/orders/{order_id}/refund", response_model=MessageResponse)
async def process_order_refund(
    order_id: str,
    request: AdminRefundRequest,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Process refund for an order."""
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.payment))
        .where((Order.id == order_id) | (Order.order_number == order_id))
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if not order.payment or order.payment.status != "captured":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No captured payment found for this order"
        )
    
    refund_amount = request.amount or order.total
    
    try:
        refund_result = razorpay_service.process_refund(
            order.payment.gateway_payment_id,
            refund_amount,
            {"reason": request.reason, "admin": admin.email}
        )
        
        if refund_result:
            order.payment.status = "refunded"
            order.status = "refunded"
            await db.commit()
            
            logger.info(
                f"Refund of {refund_amount} processed for order {order.order_number} "
                f"by {admin.email}"
            )
            
            return MessageResponse(
                message=f"Refund of ₹{refund_amount} processed successfully"
            )
        else:
            raise Exception("Refund API returned no result")
            
    except Exception as e:
        logger.error(f"Refund failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Refund failed: {str(e)}"
        )


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard analytics."""
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    
    # Total orders and revenue
    total_result = await db.execute(
        select(
            func.count(Order.id),
            func.coalesce(func.sum(Order.total), 0)
        ).where(Order.status.notin_(["cancelled", "refunded"]))
    )
    total_orders, total_revenue = total_result.one()
    
    # Today's orders and revenue
    today_result = await db.execute(
        select(
            func.count(Order.id),
            func.coalesce(func.sum(Order.total), 0)
        ).where(
            Order.created_at >= today_start,
            Order.status.notin_(["cancelled", "refunded"])
        )
    )
    orders_today, revenue_today = today_result.one()
    
    # Orders by status
    status_result = await db.execute(
        select(Order.status, func.count(Order.id))
        .group_by(Order.status)
    )
    orders_by_status = dict(status_result.all())
    
    # Revenue by day (last 7 days)
    week_ago = today_start - timedelta(days=7)
    daily_result = await db.execute(
        select(
            func.date(Order.created_at).label("date"),
            func.coalesce(func.sum(Order.total), 0).label("revenue")
        )
        .where(
            Order.created_at >= week_ago,
            Order.status.notin_(["cancelled", "refunded"])
        )
        .group_by(func.date(Order.created_at))
        .order_by(func.date(Order.created_at))
    )
    revenue_by_day = [
        {"date": str(row.date), "revenue": float(row.revenue)}
        for row in daily_result.all()
    ]
    
    return AnalyticsResponse(
        total_orders=total_orders,
        total_revenue=Decimal(str(total_revenue)),
        orders_today=orders_today,
        revenue_today=Decimal(str(revenue_today)),
        pending_orders=orders_by_status.get("pending", 0),
        shipped_orders=orders_by_status.get("shipped", 0),
        delivered_orders=orders_by_status.get("delivered", 0),
        orders_by_status=orders_by_status,
        revenue_by_day=revenue_by_day
    )


# ============================================================================
# Product CRUD
# ============================================================================

@router.get("/products", response_model=ProductListResponse)
async def admin_list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    include_inactive: bool = Query(True),
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """List all products (including inactive) for admin."""
    query = select(Product)
    if not include_inactive:
        query = query.where(Product.is_active == True)
    
    # Count total
    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar()
    
    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    products = result.scalars().all()
    
    return ProductListResponse(
        items=[ProductResponse.model_validate(p) for p in products],
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_product(
    product_data: ProductCreate,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new product."""
    # Check slug uniqueness
    existing = await db.execute(
        select(Product).where(Product.slug == product_data.slug)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product with slug '{product_data.slug}' already exists"
        )
    
    product = Product(**product_data.model_dump())
    db.add(product)
    await db.commit()
    await db.refresh(product)
    
    logger.info(f"Admin {admin.email} created product: {product.name}")
    return ProductResponse.model_validate(product)


@router.put("/products/{product_id}", response_model=ProductResponse)
async def admin_update_product(
    product_id: str,
    product_data: ProductUpdate,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update an existing product."""
    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Apply only provided fields
    update_data = product_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    product.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(product)
    
    logger.info(f"Admin {admin.email} updated product: {product.name}")
    return ProductResponse.model_validate(product)


@router.delete("/products/{product_id}", response_model=MessageResponse)
async def admin_delete_product(
    product_id: str,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Soft-delete a product (set inactive)."""
    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    product.is_active = False
    product.updated_at = datetime.utcnow()
    await db.commit()
    
    logger.info(f"Admin {admin.email} deactivated product: {product.name}")
    return MessageResponse(message=f"Product '{product.name}' deactivated")
