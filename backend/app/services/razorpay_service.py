"""
Razorpay payment service — single source of truth for all Razorpay interactions.
Handles order creation, payment verification, refunds, and webhook signature verification.
"""

import hmac
import hashlib
import razorpay
from typing import Optional
from decimal import Decimal
from fastapi import HTTPException, status

from app.core import settings, logger


class RazorpayService:
    """Consolidated Razorpay service."""

    def __init__(self):
        if not settings.RAZORPAY_KEY_ID or settings.RAZORPAY_KEY_ID.startswith("placeholder"):
            logger.warning("Razorpay credentials not configured")
            self.client = None
        else:
            self.client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )

    # ------------------------------------------------------------------
    # Order creation
    # ------------------------------------------------------------------

    def create_order(self, amount: int, currency: str = "INR", receipt: str = None) -> dict:
        """
        Create an order in Razorpay.
        Amount should be in paise (e.g., 10000 = ₹100).
        """
        if not self.client:
            if settings.DEBUG:
                logger.info("Mocking Razorpay Create Order")
                return {
                    "id": f"order_mock_{receipt}",
                    "entity": "order",
                    "amount": amount,
                    "amount_paid": 0,
                    "amount_due": amount,
                    "currency": currency,
                    "receipt": receipt,
                    "status": "created",
                    "attempts": 0,
                    "notes": [],
                    "created_at": 1234567890
                }
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Payment gateway not configured"
            )

        try:
            data = {
                "amount": amount,
                "currency": currency,
                "receipt": receipt,
                "payment_capture": 1  # Auto capture
            }
            order = self.client.order.create(data=data)
            logger.info(f"Razorpay order created: {order['id']}")
            return order
        except Exception as e:
            logger.error(f"Razorpay Create Order Failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create payment order"
            )

    # ------------------------------------------------------------------
    # Payment verification (client callback)
    # ------------------------------------------------------------------

    def verify_payment_signature(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str
    ) -> bool:
        """Verify the HMAC signature returned by Razorpay after payment."""
        if not self.client:
            if settings.DEBUG:
                return True
            return False

        try:
            params_dict = {
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            }
            self.client.utility.verify_payment_signature(params_dict)
            return True
        except razorpay.errors.SignatureVerificationError:
            return False
        except Exception as e:
            logger.error(f"Payment Verification Failed: {e}")
            return False

    # ------------------------------------------------------------------
    # Webhook signature verification
    # ------------------------------------------------------------------

    def verify_webhook_signature(self, body: bytes, signature: str) -> bool:
        """
        Verify Razorpay webhook signature.
        Uses RAZORPAY_WEBHOOK_SECRET to compute HMAC-SHA256.
        Fails closed in production — rejects if secret is not configured.
        """
        webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET
        if not webhook_secret or webhook_secret.startswith("placeholder"):
            if settings.DEBUG:
                logger.warning("Webhook secret not configured — accepting in DEBUG mode")
                return True
            logger.error("Webhook secret not configured — rejecting in production")
            return False

        expected = hmac.new(
            webhook_secret.encode("utf-8"),
            body,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected, signature)

    # ------------------------------------------------------------------
    # Fetch payment details
    # ------------------------------------------------------------------

    def fetch_payment(self, payment_id: str) -> Optional[dict]:
        """Fetch payment details from Razorpay."""
        if not self.client:
            return None
        try:
            return self.client.payment.fetch(payment_id)
        except Exception as e:
            logger.error(f"Failed to fetch payment {payment_id}: {e}")
            return None

    # ------------------------------------------------------------------
    # Refunds
    # ------------------------------------------------------------------

    def process_refund(
        self,
        payment_id: str,
        amount: Optional[Decimal] = None,
        notes: dict = None
    ) -> Optional[dict]:
        """
        Process refund for a payment.

        Args:
            payment_id: Razorpay payment ID
            amount: Refund amount in rupees (None for full refund)
            notes: Additional refund notes

        Returns:
            Refund object if successful, None on failure.
        """
        if not self.client:
            if settings.DEBUG:
                logger.info(f"Mock refund for payment {payment_id}")
                return {"id": f"rfnd_mock_{payment_id}", "status": "processed"}
            return None

        refund_data = {}
        if amount:
            refund_data["amount"] = int(amount * 100)
        if notes:
            refund_data["notes"] = notes

        try:
            refund = self.client.payment.refund(payment_id, refund_data)
            logger.info(f"Refund processed: {refund['id']} for payment {payment_id}")
            return refund
        except Exception as e:
            logger.error(f"Failed to process refund for {payment_id}: {e}")
            return None


# Singleton instance
razorpay_service = RazorpayService()
