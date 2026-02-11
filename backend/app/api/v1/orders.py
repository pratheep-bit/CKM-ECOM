"""
Order API endpoints.
Handles order creation, listing, tracking, and cancellation.
Stock is RESERVED on order creation and COMMITTED on payment verification.
"""

from datetime import datetime, timedelta
from decimal import Decimal
import random
import string
import uuid as uuid_module
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.db import get_db, Order, OrderItem, CartItem, Product, Address, User, async_session_maker
from app.schemas import (
    OrderCreate,
    OrderResponse,
    OrderListResponse,
    OrderTrackingResponse,
    MessageResponse
)
from app.api.deps import get_current_user
from app.core import logger
from app.core.order_state import is_cancellable


router = APIRouter(prefix="/orders", tags=["Orders"])


def _order_id_filter(order_id: str, user_id):
    """Build a filter that matches an order by UUID id or order_number string.
    Safely handles the case where order_id is not a valid UUID."""
    from sqlalchemy import or_
    try:
        parsed_uuid = uuid_module.UUID(order_id)
        return Order.user_id == user_id, or_(Order.id == parsed_uuid, Order.order_number == order_id)
    except ValueError:
        # Not a valid UUID — only match by order_number
        return Order.user_id == user_id, Order.order_number == order_id


def generate_order_number() -> str:
    """Generate unique order number."""
    timestamp = datetime.utcnow().strftime("%y%m%d%H%M%S")
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"ORD{timestamp}{random_part}"


@router.post("", response_model=OrderResponse)
async def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new order from cart items.
    RESERVES stock (does not deduct). Stock is committed on payment verification.
    """
    # Get user's cart items
    cart_result = await db.execute(
        select(CartItem)
        .options(selectinload(CartItem.product))
        .where(CartItem.user_id == current_user.id)
    )
    cart_items = cart_result.scalars().all()
    
    if not cart_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty"
        )
    
    # Get delivery address
    address_result = await db.execute(
        select(Address).where(
            Address.id == order_data.address_id,
            Address.user_id == current_user.id
        )
    )
    address = address_result.scalar_one_or_none()
    
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery address not found"
        )
    
    # Validate stock and calculate totals
    subtotal = Decimal("0.00")
    order_items = []
    
    for cart_item in cart_items:
        # Re-fetch product with row lock to prevent concurrent overselling
        product_result = await db.execute(
            select(Product).where(Product.id == cart_item.product_id).with_for_update()
        )
        product = product_result.scalar_one_or_none()
        
        if not product or not product.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product not available"
            )
        
        # Check AVAILABLE stock (total stock minus already reserved)
        available_stock = product.stock - product.reserved_stock
        if available_stock < cart_item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for {product.name}. Available: {available_stock}"
            )
        
        item_total = product.price * cart_item.quantity
        subtotal += item_total
        
        order_items.append({
            "product_id": product.id,
            "product_name": product.name,
            "product_image": product.images[0] if product.images else None,
            "quantity": cart_item.quantity,
            "price": product.price,
            "total": item_total
        })
        
        # RESERVE stock (not deduct) — committed on payment success
        product.reserved_stock += cart_item.quantity
    
    # Calculate fees
    shipping_fee = Decimal("0.00") if subtotal >= 500 else Decimal("50.00")
    tax = (subtotal * Decimal("0.18")).quantize(Decimal("0.01"))  # 18% GST
    total = subtotal + shipping_fee + tax
    
    # Create order
    order = Order(
        order_number=generate_order_number(),
        user_id=current_user.id,
        shipping_name=address.name,
        shipping_mobile=address.mobile,
        shipping_line1=address.line1,
        shipping_line2=address.line2,
        shipping_city=address.city,
        shipping_state=address.state,
        shipping_pincode=address.pincode,
        shipping_country=address.country,
        shipping_address_type=address.address_type,
        shipping_email=current_user.email,
        subtotal=subtotal,
        shipping_fee=shipping_fee,
        tax=tax,
        total=total,
        status="pending"
    )
    db.add(order)
    await db.flush()
    
    # Create order items
    for item_data in order_items:
        order_item = OrderItem(
            order_id=order.id,
            **item_data
        )
        db.add(order_item)
    
    # NOTE: Cart is NOT cleared here.
    # Cart is cleared after payment is verified (in webhooks.py / payment verification).
    # This ensures items remain in cart if the user cancels or dismisses payment.
    
    await db.flush()
    await db.refresh(order, ["items"])
    await db.commit()
    
    logger.info(f"Order created: {order.order_number} for user {current_user.id} (stock reserved)")
    
    return OrderResponse.model_validate(order)



@router.get("", response_model=OrderListResponse)
async def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's order history."""
    offset = (page - 1) * page_size
    
    # Count total
    count_result = await db.execute(
        select(func.count(Order.id)).where(Order.user_id == current_user.id)
    )
    total = count_result.scalar_one()
    
    # Get orders
    query = (
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    orders = result.scalars().all()
    
    return OrderListResponse(
        items=[OrderResponse.model_validate(o) for o in orders],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get order details by ID or order number."""
    user_filter, id_filter = _order_id_filter(order_id, current_user.id)
    query = (
        select(Order)
        .options(selectinload(Order.items))
        .where(user_filter, id_filter)
    )
    result = await db.execute(query)
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return OrderResponse.model_validate(order)


@router.get("/{order_id}/track", response_model=OrderTrackingResponse)
async def track_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get order tracking information."""
    user_filter, id_filter = _order_id_filter(order_id, current_user.id)
    query = (
        select(Order)
        .options(selectinload(Order.shipment))
        .where(user_filter, id_filter)
    )
    result = await db.execute(query)
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    shipment = order.shipment
    
    return OrderTrackingResponse(
        order_number=order.order_number,
        order_status=order.status,
        shipment_status=shipment.status if shipment else None,
        courier_name=shipment.courier_name if shipment else None,
        awb_number=shipment.awb_number if shipment else None,
        tracking_url=shipment.tracking_url if shipment else None,
        tracking_history=shipment.tracking_history if shipment else [],
        estimated_delivery=shipment.estimated_delivery if shipment else None
    )


# ============================================================================
# Customer Order Cancellation
# ============================================================================


@router.post("/{order_id}/cancel", response_model=MessageResponse)
async def cancel_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel an order and release reserved stock.
    Auto-triggers refund if payment was captured.
    Only works for orders in cancellable statuses (pending, confirmed, processing).
    """
    from app.db import Payment
    
    # Find order
    user_filter, id_filter = _order_id_filter(order_id, current_user.id)
    result = await db.execute(
        select(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.payment)
        )
        .where(user_filter, id_filter)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Order not found"
        )
    
    if not is_cancellable(order.status):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel order in '{order.status}' status"
        )
    
    # Release reserved stock
    for item in order.items:
        product_result = await db.execute(
            select(Product).where(Product.id == item.product_id)
        )
        product = product_result.scalar_one_or_none()
        if product:
            if order.status in ("confirmed", "processing"):
                # Stock was already committed — restore it
                product.stock += item.quantity
            else:
                # Stock was only reserved — release reservation
                product.reserved_stock = max(0, product.reserved_stock - item.quantity)
    
    # Mark cancelled
    order.status = "cancelled"
    order.updated_at = datetime.utcnow()
    
    # Auto-refund if payment was captured
    refund_initiated = False
    if order.payment and order.payment.status == "captured":
        try:
            from app.services.razorpay_service import razorpay_service
            razorpay_service.process_refund(
                order.payment.gateway_payment_id,
                amount=order.total
            )
            order.payment.status = "refunded"
            refund_initiated = True
            logger.info(f"Auto-refund initiated for order {order.order_number}")
        except Exception as e:
            logger.error(f"Auto-refund failed for {order.order_number}: {e}")
            # Cancellation still proceeds, admin can process refund manually
    
    await db.commit()
    logger.info(f"Order {order.order_number} cancelled by user {current_user.id}")
    
    # Send email notifications (fire-and-forget)
    if refund_initiated:
        try:
            from app.services.email_service import email_service
            user_email = getattr(order, 'shipping_email', None)
            if user_email:
                await email_service.send_refund_notification(
                    to=user_email,
                    order_number=order.order_number,
                    refund_amount=float(order.total)
                )
        except Exception as e:
            logger.warning(f"Refund notification email failed for {order.order_number}: {e}")
    
    msg = "Order cancelled successfully"
    if refund_initiated:
        msg += ". Refund has been initiated and will reflect in 5-7 business days."
    
    return MessageResponse(message=msg, success=True)


# ============================================================================
# Background Task: Auto-cancel expired orders
# ============================================================================

async def cancel_expired_orders(max_age_minutes: int = 30):
    """
    Cancel orders that have been pending for longer than max_age_minutes.
    Releases reserved stock back to available inventory.
    
    This runs as a background task, so it creates its own DB session.
    """
    cutoff = datetime.utcnow() - timedelta(minutes=max_age_minutes)
    
    async with async_session_maker() as session:
        # Find expired pending orders
        result = await session.execute(
            select(Order)
            .options(selectinload(Order.items).selectinload(OrderItem.product))
            .where(
                Order.status == "pending",
                Order.created_at < cutoff
            )
        )
        expired_orders = result.scalars().all()
        
        if not expired_orders:
            return 0
        
        cancelled_count = 0
        for order in expired_orders:
            # Release reserved stock
            for item in order.items:
                product_result = await session.execute(
                    select(Product).where(Product.id == item.product_id)
                )
                product = product_result.scalar_one_or_none()
                if product:
                    product.reserved_stock = max(0, product.reserved_stock - item.quantity)
            
            order.status = "cancelled"
            cancelled_count += 1
            logger.info(f"Auto-cancelled expired order {order.order_number}")
        
        await session.commit()
        logger.info(f"Auto-cancel: {cancelled_count} expired orders cancelled")
        return cancelled_count

