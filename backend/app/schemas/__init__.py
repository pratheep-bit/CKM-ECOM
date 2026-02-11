"""
Pydantic schemas for request/response validation.
Organized by domain.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID


# ============================================================================
# Base Schemas
# ============================================================================

class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Auth Schemas
# ============================================================================

class SendOTPRequest(BaseModel):
    """Request to send OTP."""
    mobile_number: str = Field(
        ..., 
        pattern=r"^\+?[1-9]\d{9,14}$",
        description="Mobile number with country code"
    )


class VerifyOTPRequest(BaseModel):
    """Request to verify OTP."""
    mobile_number: str = Field(
        ..., 
        pattern=r"^\+?[1-9]\d{9,14}$"
    )
    otp: str = Field(..., min_length=6, max_length=6)


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Request to refresh access token."""
    refresh_token: str


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
    success: bool = True


# ============================================================================
# User Schemas
# ============================================================================

class UserBase(BaseSchema):
    """Base user fields."""
    name: Optional[str] = None
    email: Optional[str] = None


class UserUpdate(UserBase):
    """Schema for updating user profile."""
    pass


class UserResponse(UserBase):
    """User response schema."""
    id: UUID
    mobile_number: str
    is_verified: bool
    created_at: datetime


# ============================================================================
# Address Schemas
# ============================================================================

class AddressBase(BaseModel):
    """Base address fields."""
    name: str = Field(..., max_length=100)
    mobile: str = Field(..., pattern=r"^\+?[1-9]\d{9,14}$")
    line1: str = Field(..., max_length=255)
    line2: Optional[str] = Field(None, max_length=255)
    city: str = Field(..., max_length=100)
    state: str = Field(..., max_length=100)
    pincode: str = Field(..., pattern=r"^\d{6}$")
    country: str = Field("India", max_length=100)
    address_type: str = Field("home", pattern="^(home|office|other)$")
    landmark: Optional[str] = Field(None, max_length=255)
    is_default: bool = False


class AddressCreate(AddressBase):
    """Schema for creating address."""
    pass


class AddressUpdate(BaseModel):
    """Schema for updating address."""
    name: Optional[str] = Field(None, max_length=100)
    mobile: Optional[str] = Field(None, pattern=r"^\+?[1-9]\d{9,14}$")
    line1: Optional[str] = Field(None, max_length=255)
    line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    pincode: Optional[str] = Field(None, pattern=r"^\d{6}$")
    country: Optional[str] = Field(None, max_length=100)
    address_type: Optional[str] = Field(None, pattern="^(home|office|other)$")
    landmark: Optional[str] = Field(None, max_length=255)
    is_default: Optional[bool] = None


class AddressResponse(AddressBase, BaseSchema):
    """Address response schema."""
    id: UUID
    created_at: datetime


# ============================================================================
# Product Schemas
# ============================================================================

class ProductBase(BaseSchema):
    """Base product fields."""
    name: str
    slug: str
    description: str
    short_description: Optional[str] = None
    price: Decimal
    mrp: Decimal
    stock: int
    images: List[str] = []
    specifications: dict = {}
    is_active: bool = True


class ProductResponse(ProductBase):
    """Product response schema."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    @property
    def discount_percentage(self) -> int:
        """Calculate discount percentage."""
        if self.mrp > 0:
            return int(((self.mrp - self.price) / self.mrp) * 100)
        return 0


class ProductListResponse(BaseSchema):
    """Paginated product list."""
    items: List[ProductResponse]
    total: int
    page: int
    page_size: int


class ProductCreate(ProductBase):
    """Schema for creating a product (admin)."""
    pass


class ProductUpdate(BaseSchema):
    """Schema for updating a product (admin). All fields optional."""
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    price: Optional[Decimal] = None
    mrp: Optional[Decimal] = None
    stock: Optional[int] = None
    images: Optional[List[str]] = None
    specifications: Optional[dict] = None
    is_active: Optional[bool] = None


# ============================================================================
# Cart Schemas
# ============================================================================

class CartItemBase(BaseModel):
    """Base cart item fields."""
    product_id: UUID
    quantity: int = Field(..., ge=1, le=10)


class CartItemCreate(CartItemBase):
    """Schema for adding to cart."""
    pass


class CartItemUpdate(BaseModel):
    """Schema for updating cart item."""
    quantity: int = Field(..., ge=1, le=10)


class CartItemResponse(BaseSchema):
    """Cart item response."""
    id: UUID
    product_id: UUID
    quantity: int
    product: ProductResponse
    created_at: datetime


class CartResponse(BaseModel):
    """Full cart response."""
    items: List[CartItemResponse]
    subtotal: Decimal
    item_count: int


# ============================================================================
# Order Schemas
# ============================================================================

class OrderItemResponse(BaseSchema):
    """Order item response."""
    id: UUID
    product_id: UUID
    product_name: str
    product_image: Optional[str]
    quantity: int
    price: Decimal
    total: Decimal


class OrderCreate(BaseModel):
    """Schema for creating order."""
    address_id: UUID


class OrderResponse(BaseSchema):
    """Order response schema."""
    id: UUID
    order_number: str
    status: str
    subtotal: Decimal
    shipping_fee: Decimal
    tax: Decimal
    discount: Decimal
    total: Decimal
    shipping_name: str
    shipping_mobile: str
    shipping_line1: str
    shipping_line2: Optional[str]
    shipping_city: str
    shipping_state: str
    shipping_pincode: str
    shipping_country: str
    shipping_email: Optional[str]
    shipping_address_type: str
    items: List[OrderItemResponse]
    created_at: datetime
    updated_at: datetime


class OrderListResponse(BaseModel):
    """Paginated order list."""
    items: List[OrderResponse]
    total: int
    page: int
    page_size: int


class OrderTrackingResponse(BaseModel):
    """Order tracking response."""
    order_number: str
    order_status: str
    shipment_status: Optional[str]
    courier_name: Optional[str]
    awb_number: Optional[str]
    tracking_url: Optional[str]
    tracking_history: List[dict]
    estimated_delivery: Optional[datetime]


# ============================================================================
# Payment Schemas
# ============================================================================

class PaymentCreateRequest(BaseModel):
    """Request to create payment for order."""
    order_id: UUID


class PaymentCreateResponse(BaseModel):
    """Response with Razorpay order details."""
    razorpay_order_id: str
    razorpay_key_id: str
    amount: int  # In paise
    currency: str
    order_id: str


class PaymentVerifyRequest(BaseModel):
    """Request to verify payment."""
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class PaymentResponse(BaseSchema):
    """Payment response schema."""
    id: UUID
    order_id: UUID
    gateway: str
    gateway_order_id: str
    gateway_payment_id: Optional[str]
    amount: Decimal
    currency: str
    status: str
    created_at: datetime


# ============================================================================
# Admin Schemas
# ============================================================================

class AdminLoginRequest(BaseModel):
    """Admin login request."""
    email: str
    password: str


class AdminOrderUpdate(BaseModel):
    """Admin order update schema."""
    status: Optional[str] = None


class AdminCreateShipmentRequest(BaseModel):
    """Request to create shipment for order."""
    length: float  # cm
    breadth: float  # cm
    height: float  # cm
    weight: float  # kg


class AdminRefundRequest(BaseModel):
    """Request to process refund."""
    amount: Optional[Decimal] = None  # Partial refund amount, None for full
    reason: str


class AnalyticsResponse(BaseModel):
    """Analytics dashboard data."""
    total_orders: int
    total_revenue: Decimal
    orders_today: int
    revenue_today: Decimal
    pending_orders: int
    shipped_orders: int
    delivered_orders: int
    orders_by_status: dict
    revenue_by_day: List[dict]
