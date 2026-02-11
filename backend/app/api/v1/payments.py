"""
Payment API endpoints.
Handles Razorpay order creation and payment verification.
On successful verification: commits reserved stock (deducts from stock, clears reservation).
On failure: releases reserved stock.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from app.db import get_db, Order, OrderItem, Payment, Product, User, CartItem
from app.schemas import (
    PaymentCreateRequest,
    PaymentCreateResponse,
    PaymentVerifyRequest,
    PaymentResponse,
    MessageResponse
)
from app.api.deps import get_current_user
from app.services.razorpay_service import razorpay_service
from app.core import settings, logger

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/create", response_model=PaymentCreateResponse)
async def create_payment_order(
    request: PaymentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Initiate payment for an order.
    Creates a Razorpay order and returns details for frontend to open checkout.
    """
    # Get order
    order_result = await db.execute(
        select(Order).where(
            Order.id == request.order_id,
            Order.user_id == current_user.id
        )
    )
    order = order_result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
        
    if order.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order is already {order.status}"
        )
        
    # Check if payment already exists and is captured
    payment_result = await db.execute(
        select(Payment).where(Payment.order_id == order.id)
    )
    existing_payment = payment_result.scalar_one_or_none()
    
    if existing_payment and existing_payment.status == "captured":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment already completed for this order"
        )
        
    # Create Razorpay Order — amount in paise
    amount_paise = int(order.total * 100)
    
    try:
        razorpay_order = razorpay_service.create_order(
            amount=amount_paise,
            currency="INR",
            receipt=str(order.order_number)
        )
        
        # Save payment record (initially pending)
        if not existing_payment:
            payment = Payment(
                order_id=order.id,
                gateway="razorpay",
                gateway_order_id=razorpay_order["id"],
                amount=order.total,
                status="pending"
            )
            db.add(payment)
        else:
            # Update existing failed/pending payment attempt
            existing_payment.gateway_order_id = razorpay_order["id"]
            existing_payment.status = "pending"
            
        await db.commit()
        
        return PaymentCreateResponse(
            razorpay_order_id=razorpay_order["id"],
            razorpay_key_id=settings.RAZORPAY_KEY_ID,
            amount=amount_paise,
            currency="INR",
            order_id=str(order.id)
        )
        
    except Exception as e:
        logger.error(f"Payment Creation Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate payment"
        )


@router.post("/verify", response_model=PaymentResponse)
async def verify_payment(
    request: PaymentVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Verify payment signature from Razorpay.
    On success: commits reserved stock and confirms order.
    On failure: releases reserved stock.
    """
    # Find payment record by gateway order id
    result = await db.execute(
        select(Payment).where(
            Payment.gateway_order_id == request.razorpay_order_id
        )
    )
    payment = result.scalar_one_or_none()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment record not found"
        )
    
    # Idempotency: if already captured, return existing payment
    if payment.status == "captured":
        return PaymentResponse.model_validate(payment)
        
    # Verify signature
    is_valid = razorpay_service.verify_payment_signature(
        request.razorpay_order_id,
        request.razorpay_payment_id,
        request.razorpay_signature
    )
    
    # Fetch order with items for stock management
    order_result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == payment.order_id)
    )
    order = order_result.scalar_one()
    
    if not is_valid:
        # Payment failed — release reserved stock
        payment.status = "failed"
        payment.failure_reason = "Signature verification failed"
        
        await _release_reserved_stock(db, order.items)
        
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payment signature"
        )
    
    # Payment successful — commit reserved stock
    payment.status = "captured"
    payment.gateway_payment_id = request.razorpay_payment_id
    payment.gateway_signature = request.razorpay_signature
    
    # Commit stock: deduct from stock, clear reservation
    await _commit_reserved_stock(db, order.items)
    
    # Confirm order
    order.status = "confirmed"
    
    # Clear user's cart now that payment is confirmed
    await db.execute(
        delete(CartItem).where(CartItem.user_id == order.user_id)
    )
    
    await db.commit()
    await db.refresh(payment)
    
    logger.info(f"Payment verified for order {order.order_number} — stock committed")
    
    # Send email notifications (fire-and-forget)
    try:
        from app.services.email_service import email_service
        user_email = getattr(order, 'shipping_email', None)
        if user_email:
            await email_service.send_payment_receipt(
                to=user_email,
                order_number=order.order_number,
                amount=float(order.total),
                payment_id=request.razorpay_payment_id
            )
            await email_service.send_order_confirmation(
                to=user_email,
                order_number=order.order_number,
                total=float(order.total),
                items_count=len(order.items)
            )
    except Exception as e:
        logger.warning(f"Email notification failed for {order.order_number}: {e}")
    
    return PaymentResponse.model_validate(payment)


# ------------------------------------------------------------------
# Stock management helpers
# ------------------------------------------------------------------

async def _commit_reserved_stock(db: AsyncSession, order_items):
    """
    Commit reserved stock after successful payment.
    Moves stock from reserved to sold (stock -= qty, reserved_stock -= qty).
    """
    for item in order_items:
        product_result = await db.execute(
            select(Product).where(Product.id == item.product_id).with_for_update()
        )
        product = product_result.scalar_one_or_none()
        if product:
            product.stock -= item.quantity
            product.reserved_stock = max(0, product.reserved_stock - item.quantity)


async def _release_reserved_stock(db: AsyncSession, order_items):
    """
    Release reserved stock after payment failure.
    Returns reserved units back to available pool (reserved_stock -= qty).
    """
    for item in order_items:
        product_result = await db.execute(
            select(Product).where(Product.id == item.product_id).with_for_update()
        )
        product = product_result.scalar_one_or_none()
        if product:
            product.reserved_stock = max(0, product.reserved_stock - item.quantity)
