import json
from fastapi import APIRouter, Request, HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from app.db import async_session_maker, Payment, Order, Product, Shipment, CartItem
from app.services.razorpay_service import razorpay_service
from app.core import logger


router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/razorpay")
async def razorpay_webhook(request: Request):
    """
    Handle Razorpay webhook events.
    
    This is the server-side safety net: even if the client callback fails
    (user closes browser, network error), this webhook ensures the payment
    outcome is always recorded.
    
    Supported events:
    - payment.captured → confirm order, commit stock
    - payment.failed → release reserved stock
    """
    # Read raw body for signature verification
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")
    
    # Verify webhook signature
    if not razorpay_service.verify_webhook_signature(body, signature):
        logger.warning("Razorpay webhook: invalid signature")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature"
        )
    
    # Parse event
    try:
        event_data = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON body"
        )
    
    event_type = event_data.get("event")
    payload = event_data.get("payload", {})
    
    logger.info(f"Razorpay webhook received: {event_type}")
    
    if event_type == "payment.captured":
        await _handle_payment_captured(payload)
    elif event_type == "payment.failed":
        await _handle_payment_failed(payload)
    else:
        logger.info(f"Razorpay webhook: ignoring event type '{event_type}'")
    
    # Always return 200 to acknowledge receipt
    return {"status": "ok"}


async def _handle_payment_captured(payload: dict):
    """Handle successful payment capture from Razorpay."""
    payment_entity = payload.get("payment", {}).get("entity", {})
    razorpay_order_id = payment_entity.get("order_id")
    razorpay_payment_id = payment_entity.get("id")
    
    if not razorpay_order_id:
        logger.warning("Webhook payment.captured: missing order_id")
        return
    
    async with async_session_maker() as session:
        # Find payment record
        result = await session.execute(
            select(Payment).where(
                Payment.gateway_order_id == razorpay_order_id
            )
        )
        payment = result.scalar_one_or_none()
        
        if not payment:
            logger.warning(f"Webhook: no payment record for Razorpay order {razorpay_order_id}")
            return
        
        # Idempotency: skip if already captured
        if payment.status == "captured":
            logger.info(f"Webhook: payment {razorpay_order_id} already captured, skipping")
            return
        
        # Update payment
        payment.status = "captured"
        payment.gateway_payment_id = razorpay_payment_id
        
        # Fetch order with items
        order_result = await session.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == payment.order_id)
        )
        order = order_result.scalar_one_or_none()
        
        if order and order.status == "pending":
            order.status = "confirmed"
            
            # Commit reserved stock
            for item in order.items:
                product_result = await session.execute(
                    select(Product).where(Product.id == item.product_id)
                )
                product = product_result.scalar_one_or_none()
                if product:
                    product.stock -= item.quantity
                    product.reserved_stock = max(0, product.reserved_stock - item.quantity)
            
            logger.info(f"Webhook: order {order.order_number} confirmed, stock committed")
            
            # Clear user's cart (safety net — may already be cleared by verify endpoint)
            await session.execute(
                delete(CartItem).where(CartItem.user_id == order.user_id)
            )
        
        await session.commit()


async def _handle_payment_failed(payload: dict):
    """Handle payment failure from Razorpay."""
    payment_entity = payload.get("payment", {}).get("entity", {})
    razorpay_order_id = payment_entity.get("order_id")
    
    if not razorpay_order_id:
        logger.warning("Webhook payment.failed: missing order_id")
        return
    
    async with async_session_maker() as session:
        # Find payment record
        result = await session.execute(
            select(Payment).where(
                Payment.gateway_order_id == razorpay_order_id
            )
        )
        payment = result.scalar_one_or_none()
        
        if not payment:
            logger.warning(f"Webhook: no payment record for Razorpay order {razorpay_order_id}")
            return
        
        # Skip if already processed
        if payment.status in ["captured", "failed"]:
            logger.info(f"Webhook: payment {razorpay_order_id} already {payment.status}, skipping")
            return
        
        # Update payment status
        payment.status = "failed"
        error_desc = payload.get("payment", {}).get("entity", {}).get("error_description", "Unknown")
        payment.failure_reason = f"Webhook: {error_desc}"
        
        # Release reserved stock
        order_result = await session.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == payment.order_id)
        )
        order = order_result.scalar_one_or_none()
        
        if order and order.status == "pending":
            for item in order.items:
                product_result = await session.execute(
                    select(Product).where(Product.id == item.product_id)
                )
                product = product_result.scalar_one_or_none()
                if product:
                    product.reserved_stock = max(0, product.reserved_stock - item.quantity)
            
            logger.info(f"Webhook: released reserved stock for order {order.order_number}")
        
        await session.commit()


# ============================================================================
# Shiprocket Webhook
# ============================================================================

# Shiprocket status code → internal status mapping
SHIPROCKET_STATUS_MAP = {
    1: "pickup_scheduled",     # AWB Assigned
    2: "pickup_scheduled",     # Ready to Pick
    3: "picked_up",            # Picked Up
    4: "picked_up",            # Pickup Queued
    5: "in_transit",           # Shipped / In Transit
    6: "in_transit",           # Out for Delivery
    7: "delivered",            # Delivered
    8: "rto",                  # RTO Initiated
    9: "rto",                  # RTO Delivered
    10: "rto",                 # RTO Acknowledged
    17: "pickup_scheduled",    # Pickup Scheduled
    18: "in_transit",          # Reached Destination Hub
    38: "in_transit",          # Reached Warehouse
}

# Which Shiprocket statuses correspond to order-level status changes
SHIPROCKET_TO_ORDER_STATUS = {
    "picked_up": "shipped",
    "in_transit": "shipped",
    "delivered": "delivered",
}


@router.post("/shiprocket")
async def shiprocket_webhook(request: Request):
    """
    Handle Shiprocket shipment tracking webhooks.
    
    Updates shipment status and order status based on tracking events.
    Shiprocket sends POST requests with tracking data when shipment status changes.
    """
    try:
        event_data = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON body"
        )
    
    awb = event_data.get("awb")
    current_status_id = event_data.get("current_status_id")
    current_status = event_data.get("current_status", "")
    
    if not awb:
        logger.warning("Shiprocket webhook: missing AWB")
        return {"status": "ok"}
    
    logger.info(f"Shiprocket webhook: AWB={awb}, status_id={current_status_id}, status={current_status}")
    
    # Map Shiprocket status to internal status
    internal_status = SHIPROCKET_STATUS_MAP.get(current_status_id)
    if not internal_status:
        logger.info(f"Shiprocket webhook: unknown status_id {current_status_id}, ignoring")
        return {"status": "ok"}
    
    async with async_session_maker() as session:
        # Find shipment by AWB
        result = await session.execute(
            select(Shipment).where(Shipment.awb_number == awb)
        )
        shipment = result.scalar_one_or_none()
        
        if not shipment:
            logger.warning(f"Shiprocket webhook: no shipment for AWB {awb}")
            return {"status": "ok"}
        
        # Update shipment status
        shipment.status = internal_status
        
        # Add to tracking history
        from datetime import datetime
        history_entry = {
            "status": current_status,
            "status_id": current_status_id,
            "timestamp": datetime.utcnow().isoformat(),
            "location": event_data.get("current_city", "")
        }
        if isinstance(shipment.tracking_history, list):
            shipment.tracking_history = shipment.tracking_history + [history_entry]
        else:
            shipment.tracking_history = [history_entry]
        
        # Update delivery timestamps
        if internal_status == "picked_up" and not shipment.shipped_at:
            shipment.shipped_at = datetime.utcnow()
        elif internal_status == "delivered":
            shipment.delivered_at = datetime.utcnow()
        
        # Update estimated delivery if provided
        etd = event_data.get("etd")
        if etd:
            try:
                shipment.estimated_delivery = datetime.fromisoformat(etd)
            except (ValueError, TypeError):
                pass
        
        # Update order status if applicable
        order_status = SHIPROCKET_TO_ORDER_STATUS.get(internal_status)
        if order_status:
            order_result = await session.execute(
                select(Order).where(Order.id == shipment.order_id)
            )
            order = order_result.scalar_one_or_none()
            if order and order.status not in ["delivered", "cancelled", "refunded"]:
                order.status = order_status
                logger.info(f"Shiprocket webhook: order status → {order_status}")
        
        await session.commit()
        logger.info(f"Shiprocket webhook: shipment {awb} → {internal_status}")
    
    return {"status": "ok"}

