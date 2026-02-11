"""
SMS integration for customer notifications.
Consolidated on Twilio for OTP delivery and order notifications.
"""

from app.core import settings, logger
from app.services.twilio_sms import twilio_sms


async def send_otp_sms(mobile: str, otp: str) -> bool:
    """
    Send OTP via SMS using Twilio.
    
    Args:
        mobile: Mobile number with country code
        otp: The OTP to send
    
    Returns:
        True if SMS sent successfully
    """
    message = f"Your Karungali Heritage verification code is: {otp}. Valid for 10 minutes."
    return twilio_sms.send_sms(mobile, message)


async def send_order_notification_sms(
    mobile: str, 
    order_number: str, 
    status: str
) -> bool:
    """
    Send order status notification via SMS using Twilio.
    
    Args:
        mobile: Customer mobile number
        order_number: Order reference number
        status: Current order status
    """
    status_messages = {
        "confirmed": f"Your order {order_number} is confirmed! We'll process it shortly. — Karungali Heritage",
        "shipped": f"Your order {order_number} has been shipped! You'll receive tracking details soon. — Karungali Heritage",
        "delivered": f"Your order {order_number} has been delivered! Thank you for shopping with Karungali Heritage.",
        "cancelled": f"Your order {order_number} has been cancelled. If this was a mistake, please contact us. — Karungali Heritage",
        "refunded": f"Refund for order {order_number} has been initiated. It will reflect in 5-7 business days. — Karungali Heritage",
    }
    
    message = status_messages.get(
        status,
        f"Order {order_number} status update: {status}. — Karungali Heritage"
    )
    
    return twilio_sms.send_sms(mobile, message)
