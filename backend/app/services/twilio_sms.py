"""
Twilio SMS service for notifications.
Uses settings from config rather than os.getenv for consistency.
"""

from twilio.rest import Client
from app.core import settings, logger


class TwilioSMS:
    """Send SMS notifications via Twilio."""
    
    def __init__(self):
        self.account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
        self.auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
        self.from_number = getattr(settings, 'TWILIO_PHONE_NUMBER', '')
        self.admin_phone = getattr(settings, 'ADMIN_PHONE_NUMBER', '')
        
        if self.account_sid and self.auth_token and not self.account_sid.startswith("placeholder"):
            self.client = Client(self.account_sid, self.auth_token)
        else:
            self.client = None
            logger.warning("Twilio credentials not configured - SMS disabled (mock mode)")
    
    def send_sms(self, to: str, message: str) -> bool:
        """Send an SMS message."""
        if not self.client:
            logger.info(f"[SMS MOCK] To: {to} | Message: {message}")
            return True
        
        try:
            # Format Indian phone numbers
            if not to.startswith("+"):
                to = f"+91{to}" if len(to) == 10 else f"+{to}"
            
            self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to
            )
            logger.info(f"SMS sent to {to}")
            return True
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return False
    
    def notify_admin_new_order(self, order_number: str, customer_name: str, 
                                customer_phone: str, quantity: int, 
                                total_amount: float) -> bool:
        """Send SMS to admin about new order."""
        if not self.admin_phone:
            logger.warning("Admin phone not configured")
            return False
        
        message = (
            f"🛒 NEW ORDER!\n"
            f"Order: {order_number}\n"
            f"Customer: {customer_name}\n"
            f"Phone: {customer_phone}\n"
            f"Qty: {quantity}\n"
            f"Amount: ₹{total_amount}"
        )
        return self.send_sms(self.admin_phone, message)


# Singleton instance
twilio_sms = TwilioSMS()
