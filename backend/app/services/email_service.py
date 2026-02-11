"""
Email notification service using aiosmtplib.
Sends transactional emails: order confirmation, shipping updates, payment receipts.
Gracefully degrades if SMTP is not configured (logs instead of sending).
"""

import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime

from app.core import settings, logger
from app.core.retry import async_retry


class EmailService:
    """Async email sending via SMTP."""
    
    def __init__(self):
        self.host = getattr(settings, 'SMTP_HOST', '')
        self.port = getattr(settings, 'SMTP_PORT', 587)
        self.user = getattr(settings, 'SMTP_USER', '')
        self.password = getattr(settings, 'SMTP_PASSWORD', '')
        self.from_email = getattr(settings, 'SMTP_FROM_EMAIL', '')
        self.from_name = getattr(settings, 'SMTP_FROM_NAME', 'Karungali Heritage')
        self.enabled = bool(self.host and self.user and self.password)
        
        if not self.enabled:
            logger.warning("SMTP not configured — emails will be logged only")
    
    @async_retry(max_retries=2, base_delay=1.0, exceptions=(aiosmtplib.SMTPException, ConnectionError, TimeoutError))
    async def _send(self, to: str, subject: str, html_body: str) -> bool:
        """Send an email. Returns True on success. Retries on transient SMTP failures."""
        if not self.enabled:
            logger.info(f"[EMAIL MOCK] To: {to} | Subject: {subject}")
            return True
        
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{self.from_name} <{self.from_email}>"
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(html_body, "html"))
        
        try:
            await aiosmtplib.send(
                msg,
                hostname=self.host,
                port=self.port,
                username=self.user,
                password=self.password,
                start_tls=True,
            )
            logger.info(f"Email sent to {to}: {subject}")
            return True
        except Exception as e:
            logger.error(f"Email send failed to {to}: {e}")
            return False
    
    # ------------------------------------------------------------------
    # Template methods
    # ------------------------------------------------------------------
    
    async def send_order_confirmation(
        self, to: str, order_number: str, total: float, items_count: int
    ) -> bool:
        """Send order confirmation email."""
        html = f"""
        <div style="font-family: 'Segoe UI', sans-serif; max-width: 600px; margin: 0 auto; background: #fafafa; padding: 32px;">
          <h1 style="color: #2d2d2d; border-bottom: 3px solid #c49a6c; padding-bottom: 12px;">
            ✅ Order Confirmed
          </h1>
          <p>Thank you for your order!</p>
          <table style="width: 100%; border-collapse: collapse; margin: 16px 0;">
            <tr><td style="padding: 8px; font-weight: bold;">Order Number</td><td style="padding: 8px;">{order_number}</td></tr>
            <tr><td style="padding: 8px; font-weight: bold;">Items</td><td style="padding: 8px;">{items_count}</td></tr>
            <tr><td style="padding: 8px; font-weight: bold;">Total</td><td style="padding: 8px; color: #c49a6c; font-size: 18px;">₹{total:,.2f}</td></tr>
          </table>
          <p style="color: #666; font-size: 13px;">We'll notify you when your order ships. — Karungali Heritage</p>
        </div>
        """
        return await self._send(to, f"Order Confirmed — {order_number}", html)
    
    async def send_shipping_update(
        self, to: str, order_number: str, status: str,
        courier: Optional[str] = None, tracking_url: Optional[str] = None
    ) -> bool:
        """Send shipping status update email."""
        tracking_link = ""
        if tracking_url:
            tracking_link = f'<p><a href="{tracking_url}" style="color: #c49a6c;">Track your shipment →</a></p>'
        
        courier_info = f"<p>Courier: <strong>{courier}</strong></p>" if courier else ""
        
        html = f"""
        <div style="font-family: 'Segoe UI', sans-serif; max-width: 600px; margin: 0 auto; background: #fafafa; padding: 32px;">
          <h1 style="color: #2d2d2d; border-bottom: 3px solid #c49a6c; padding-bottom: 12px;">
            📦 Shipping Update
          </h1>
          <p>Order <strong>{order_number}</strong> is now: <strong style="color: #c49a6c;">{status.upper()}</strong></p>
          {courier_info}
          {tracking_link}
          <p style="color: #666; font-size: 13px;">— Karungali Heritage</p>
        </div>
        """
        return await self._send(to, f"Shipping Update — {order_number}", html)
    
    async def send_payment_receipt(
        self, to: str, order_number: str, amount: float, 
        payment_id: str, payment_date: Optional[datetime] = None
    ) -> bool:
        """Send payment receipt email."""
        date_str = (payment_date or datetime.utcnow()).strftime("%d %b %Y, %I:%M %p")
        
        html = f"""
        <div style="font-family: 'Segoe UI', sans-serif; max-width: 600px; margin: 0 auto; background: #fafafa; padding: 32px;">
          <h1 style="color: #2d2d2d; border-bottom: 3px solid #c49a6c; padding-bottom: 12px;">
            💳 Payment Receipt
          </h1>
          <table style="width: 100%; border-collapse: collapse; margin: 16px 0;">
            <tr><td style="padding: 8px; font-weight: bold;">Order</td><td style="padding: 8px;">{order_number}</td></tr>
            <tr><td style="padding: 8px; font-weight: bold;">Amount Paid</td><td style="padding: 8px; color: #27ae60; font-size: 18px;">₹{amount:,.2f}</td></tr>
            <tr><td style="padding: 8px; font-weight: bold;">Payment ID</td><td style="padding: 8px; font-family: monospace;">{payment_id}</td></tr>
            <tr><td style="padding: 8px; font-weight: bold;">Date</td><td style="padding: 8px;">{date_str}</td></tr>
          </table>
          <p style="color: #666; font-size: 13px;">This is your official payment receipt. — Karungali Heritage</p>
        </div>
        """
        return await self._send(to, f"Payment Receipt — {order_number}", html)
    
    async def send_refund_notification(
        self, to: str, order_number: str, refund_amount: float
    ) -> bool:
        """Send refund notification email."""
        html = f"""
        <div style="font-family: 'Segoe UI', sans-serif; max-width: 600px; margin: 0 auto; background: #fafafa; padding: 32px;">
          <h1 style="color: #2d2d2d; border-bottom: 3px solid #c49a6c; padding-bottom: 12px;">
            💰 Refund Processed
          </h1>
          <p>A refund of <strong style="color: #27ae60;">₹{refund_amount:,.2f}</strong> has been initiated for order <strong>{order_number}</strong>.</p>
          <p>It will reflect in your account within <strong>5–7 business days</strong>.</p>
          <p style="color: #666; font-size: 13px;">If you have questions, reply to this email. — Karungali Heritage</p>
        </div>
        """
        return await self._send(to, f"Refund Processed — {order_number}", html)


# Singleton
email_service = EmailService()
