"""
Shiprocket integration for shipping and delivery.
Handles shipment creation, tracking, and status sync.
"""

import httpx
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

from app.core import settings, logger


class ShiprocketClient:
    """Shiprocket API client."""
    
    def __init__(self):
        self.base_url = settings.SHIPROCKET_API_URL
        self.token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
    
    async def _get_token(self) -> str:
        """Get or refresh authentication token."""
        if self.token and self.token_expiry and datetime.utcnow() < self.token_expiry:
            return self.token
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/external/auth/login",
                json={
                    "email": settings.SHIPROCKET_EMAIL,
                    "password": settings.SHIPROCKET_PASSWORD
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Shiprocket auth failed: {response.text}")
                raise Exception("Shiprocket authentication failed")
            
            data = response.json()
            self.token = data["token"]
            # Token valid for 10 days, refresh at 9
            from datetime import timedelta
            self.token_expiry = datetime.utcnow() + timedelta(days=9)
            
            return self.token
    
    async def _request(
        self, 
        method: str, 
        endpoint: str, 
        data: dict = None
    ) -> dict:
        """Make authenticated request to Shiprocket API."""
        token = await self._get_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            if method == "GET":
                response = await client.get(
                    f"{self.base_url}{endpoint}",
                    headers=headers,
                    params=data
                )
            else:
                response = await client.request(
                    method,
                    f"{self.base_url}{endpoint}",
                    headers=headers,
                    json=data
                )
            
            if response.status_code not in [200, 201]:
                logger.error(f"Shiprocket API error: {response.text}")
                raise Exception(f"Shiprocket API error: {response.status_code}")
            
            return response.json()
    
    async def create_order(
        self,
        order_id: str,
        order_number: str,
        order_date: datetime,
        billing_name: str,
        billing_mobile: str,
        billing_address: str,
        billing_city: str,
        billing_state: str,
        billing_pincode: str,
        items: list,
        subtotal: Decimal,
        shipping_charges: Decimal,
        payment_method: str = "Prepaid",
        length: float = 10,
        breadth: float = 10,
        height: float = 10,
        weight: float = 0.5
    ) -> dict:
        """
        Create a new order in Shiprocket.
        
        Returns:
            Order creation response with order_id and shipment_id
        """
        # Format items for Shiprocket
        order_items = []
        for item in items:
            order_items.append({
                "name": item["product_name"],
                "sku": str(item["product_id"]),
                "units": item["quantity"],
                "selling_price": float(item["price"]),
                "discount": 0,
                "tax": 0,
                "hsn": ""
            })
        
        order_data = {
            "order_id": order_number,
            "order_date": order_date.strftime("%Y-%m-%d %H:%M"),
            "pickup_location": "Primary",
            "billing_customer_name": billing_name,
            "billing_last_name": "",
            "billing_address": billing_address,
            "billing_city": billing_city,
            "billing_pincode": billing_pincode,
            "billing_state": billing_state,
            "billing_country": "India",
            "billing_email": "",
            "billing_phone": billing_mobile.lstrip("+91").lstrip("+"),
            "shipping_is_billing": True,
            "order_items": order_items,
            "payment_method": payment_method,
            "sub_total": float(subtotal),
            "shipping_charges": float(shipping_charges),
            "length": length,
            "breadth": breadth,
            "height": height,
            "weight": weight
        }
        
        result = await self._request("POST", "/external/orders/create/adhoc", order_data)
        logger.info(f"Shiprocket order created: {result.get('order_id')}")
        return result
    
    async def generate_awb(
        self, 
        shipment_id: str, 
        courier_id: int = None
    ) -> dict:
        """
        Generate AWB (Air Waybill) for shipment.
        Auto-selects courier if not specified.
        """
        data = {"shipment_id": shipment_id}
        
        if courier_id:
            data["courier_id"] = courier_id
        
        result = await self._request("POST", "/external/courier/assign/awb", data)
        return result
    
    async def schedule_pickup(self, shipment_id: str) -> dict:
        """Schedule pickup for shipment."""
        result = await self._request(
            "POST",
            "/external/courier/generate/pickup",
            {"shipment_id": [shipment_id]}
        )
        return result
    
    async def track_shipment(self, awb: str) -> dict:
        """Get tracking details for shipment."""
        result = await self._request(
            "GET",
            f"/external/courier/track/awb/{awb}"
        )
        return result
    
    async def get_tracking_url(self, order_id: str) -> str:
        """Get public tracking URL for order."""
        return f"https://shiprocket.co/tracking/{order_id}"
    
    async def cancel_shipment(self, order_ids: list) -> dict:
        """Cancel shipment(s)."""
        result = await self._request(
            "POST",
            "/external/orders/cancel",
            {"ids": order_ids}
        )
        return result
    
    async def check_serviceability(
        self,
        pickup_pincode: str,
        delivery_pincode: str,
        weight: float = 0.5,
        cod: bool = False
    ) -> dict:
        """Check if delivery is serviceable."""
        result = await self._request(
            "GET",
            "/external/courier/serviceability",
            {
                "pickup_postcode": pickup_pincode,
                "delivery_postcode": delivery_pincode,
                "weight": weight,
                "cod": 1 if cod else 0
            }
        )
        return result


# Global client instance
shiprocket_client = ShiprocketClient()


async def create_shipment(
    order_id: str,
    order_number: str,
    order_date: datetime,
    address: dict,
    items: list,
    subtotal: Decimal,
    shipping_charges: Decimal,
    dimensions: dict
) -> Dict[str, Any]:
    """
    Create shipment for an order.
    
    Args:
        order_id: Internal order ID
        order_number: Order reference number
        order_date: Order creation date
        address: Shipping address details
        items: List of order items
        subtotal: Order subtotal
        shipping_charges: Shipping fee
        dimensions: Package dimensions (length, breadth, height, weight)
    
    Returns:
        Shipment creation result with shiprocket IDs
    """
    try:
        # Create order in Shiprocket
        result = await shiprocket_client.create_order(
            order_id=order_id,
            order_number=order_number,
            order_date=order_date,
            billing_name=address["name"],
            billing_mobile=address["mobile"],
            billing_address=f"{address['line1']} {address.get('line2', '')}".strip(),
            billing_city=address["city"],
            billing_state=address["state"],
            billing_pincode=address["pincode"],
            items=items,
            subtotal=subtotal,
            shipping_charges=shipping_charges,
            **dimensions
        )
        
        shiprocket_order_id = result.get("order_id")
        shipment_id = result.get("shipment_id")
        
        # Generate AWB (auto-select courier)
        awb_result = await shiprocket_client.generate_awb(str(shipment_id))
        
        # Schedule pickup
        await shiprocket_client.schedule_pickup(str(shipment_id))
        
        return {
            "shiprocket_order_id": str(shiprocket_order_id),
            "shiprocket_shipment_id": str(shipment_id),
            "awb_number": awb_result.get("response", {}).get("data", {}).get("awb_code"),
            "courier_name": awb_result.get("response", {}).get("data", {}).get("courier_name"),
            "courier_id": awb_result.get("response", {}).get("data", {}).get("courier_company_id"),
            "tracking_url": await shiprocket_client.get_tracking_url(order_number)
        }
        
    except Exception as e:
        logger.error(f"Shipment creation failed: {e}")
        raise


async def get_tracking(awb: str) -> Dict[str, Any]:
    """Get tracking details for AWB."""
    try:
        result = await shiprocket_client.track_shipment(awb)
        tracking_data = result.get("tracking_data", {})
        
        return {
            "status": tracking_data.get("shipment_status_name"),
            "current_location": tracking_data.get("current_location"),
            "delivered_date": tracking_data.get("delivered_date"),
            "activities": tracking_data.get("shipment_track_activities", [])
        }
    except Exception as e:
        logger.error(f"Failed to get tracking for {awb}: {e}")
        return {}
