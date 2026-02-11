"""
SQLAlchemy models for the ecommerce application.
All models use UUID primary keys and include timestamps.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import (
    String, Boolean, DateTime, Numeric, Integer, 
    ForeignKey, Text, JSON, Index, Uuid
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


# ============================================================================
# User Models
# ============================================================================

class User(Base):
    """User model for customers."""
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, 
        primary_key=True, 
        default=uuid.uuid4
    )
    mobile_number: Mapped[str] = mapped_column(
        String(15), 
        unique=True, 
        index=True, 
        nullable=False
    )
    name: Mapped[Optional[str]] = mapped_column(String(100))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    addresses: Mapped[List["Address"]] = relationship(
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    cart_items: Mapped[List["CartItem"]] = relationship(
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    orders: Mapped[List["Order"]] = relationship(
        back_populates="user"
    )


class Address(Base):
    """Delivery address for users."""
    __tablename__ = "addresses"
    
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, 
        primary_key=True, 
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    mobile: Mapped[str] = mapped_column(String(15), nullable=False)
    line1: Mapped[str] = mapped_column(String(255), nullable=False)
    line2: Mapped[Optional[str]] = mapped_column(String(255))
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    pincode: Mapped[str] = mapped_column(String(10), nullable=False)
    country: Mapped[str] = mapped_column(String(100), default="India")
    address_type: Mapped[str] = mapped_column(String(20), default="home")  # home, office, other
    landmark: Mapped[Optional[str]] = mapped_column(String(255))
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow
    )
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="addresses")


class OTPLog(Base):
    """OTP verification logs."""
    __tablename__ = "otp_logs"
    
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, 
        primary_key=True, 
        default=uuid.uuid4
    )
    mobile_number: Mapped[str] = mapped_column(
        String(15), 
        index=True, 
        nullable=False
    )
    otp_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow
    )


# ============================================================================
# Product Models
# ============================================================================

class Product(Base):
    """Product model - single product for the store."""
    __tablename__ = "products"
    
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, 
        primary_key=True, 
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    short_description: Mapped[Optional[str]] = mapped_column(String(500))
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), 
        nullable=False
    )
    mrp: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), 
        nullable=False
    )
    stock: Mapped[int] = mapped_column(Integer, default=0)
    reserved_stock: Mapped[int] = mapped_column(Integer, default=0)
    images: Mapped[dict] = mapped_column(JSON, default=list)
    specifications: Mapped[dict] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )


# ============================================================================
# Cart Models
# ============================================================================

class CartItem(Base):
    """Shopping cart items."""
    __tablename__ = "cart_items"
    
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, 
        primary_key=True, 
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, 
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow
    )
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="cart_items")
    product: Mapped["Product"] = relationship()
    
    # Unique constraint on user + product
    __table_args__ = (
        Index("ix_cart_user_product", "user_id", "product_id", unique=True),
    )


# ============================================================================
# Order Models
# ============================================================================

class Order(Base):
    """Customer orders."""
    __tablename__ = "orders"
    
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, 
        primary_key=True, 
        default=uuid.uuid4
    )
    order_number: Mapped[str] = mapped_column(
        String(20), 
        unique=True, 
        index=True, 
        nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, 
        ForeignKey("users.id"),
        nullable=False
    )
    
    # Snapshot of address at order time
    shipping_name: Mapped[str] = mapped_column(String(100), nullable=False)
    shipping_mobile: Mapped[str] = mapped_column(String(15), nullable=False)
    shipping_line1: Mapped[str] = mapped_column(String(255), nullable=False)
    shipping_line2: Mapped[Optional[str]] = mapped_column(String(255))
    shipping_city: Mapped[str] = mapped_column(String(100), nullable=False)
    shipping_state: Mapped[str] = mapped_column(String(100), nullable=False)
    shipping_pincode: Mapped[str] = mapped_column(String(10), nullable=False)
    shipping_country: Mapped[str] = mapped_column(String(100), default="India")
    shipping_email: Mapped[Optional[str]] = mapped_column(String(255))
    shipping_address_type: Mapped[str] = mapped_column(String(20), default="home")  # home, office, other
    
    # Pricing
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    shipping_fee: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), 
        default=Decimal("0.00")
    )
    tax: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), 
        default=Decimal("0.00")
    )
    discount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), 
        default=Decimal("0.00")
    )
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20), 
        default="pending",
        index=True
    )  # pending, confirmed, processing, shipped, delivered, cancelled, refunded
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow,
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship(
        back_populates="order", 
        cascade="all, delete-orphan"
    )
    payment: Mapped[Optional["Payment"]] = relationship(
        back_populates="order",
        uselist=False
    )
    shipment: Mapped[Optional["Shipment"]] = relationship(
        back_populates="order",
        uselist=False
    )


class OrderItem(Base):
    """Individual items within an order."""
    __tablename__ = "order_items"
    
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, 
        primary_key=True, 
        default=uuid.uuid4
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, 
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, 
        ForeignKey("products.id"),
        nullable=False
    )
    # Snapshot of product at order time
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    product_image: Mapped[Optional[str]] = mapped_column(String(500))
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    # Relationships
    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship()


# ============================================================================
# Payment Models
# ============================================================================

class Payment(Base):
    """Payment records linked to orders."""
    __tablename__ = "payments"
    
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, 
        primary_key=True, 
        default=uuid.uuid4
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, 
        ForeignKey("orders.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )
    gateway: Mapped[str] = mapped_column(
        String(20), 
        default="razorpay"
    )
    gateway_order_id: Mapped[str] = mapped_column(
        String(100), 
        index=True,
        nullable=False
    )
    gateway_payment_id: Mapped[Optional[str]] = mapped_column(String(100))
    gateway_signature: Mapped[Optional[str]] = mapped_column(String(255))
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    status: Mapped[str] = mapped_column(
        String(20), 
        default="pending",
        index=True
    )  # pending, authorized, captured, failed, refunded
    failure_reason: Mapped[Optional[str]] = mapped_column(Text)
    payment_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    order: Mapped["Order"] = relationship(back_populates="payment")


# ============================================================================
# Shipment Models
# ============================================================================

class Shipment(Base):
    """Shipment tracking for orders."""
    __tablename__ = "shipments"
    
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, 
        primary_key=True, 
        default=uuid.uuid4
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, 
        ForeignKey("orders.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )
    shiprocket_order_id: Mapped[Optional[str]] = mapped_column(String(50))
    shiprocket_shipment_id: Mapped[Optional[str]] = mapped_column(String(50))
    awb_number: Mapped[Optional[str]] = mapped_column(
        String(50), 
        index=True
    )
    courier_name: Mapped[Optional[str]] = mapped_column(String(100))
    courier_id: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(
        String(30), 
        default="pending"
    )  # pending, pickup_scheduled, picked_up, in_transit, out_for_delivery, delivered, rto
    tracking_url: Mapped[Optional[str]] = mapped_column(String(500))
    tracking_history: Mapped[dict] = mapped_column(JSON, default=list)
    estimated_delivery: Mapped[Optional[datetime]] = mapped_column(DateTime)
    shipped_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    order: Mapped["Order"] = relationship(back_populates="shipment")


# ============================================================================
# Admin Models
# ============================================================================

class AdminUser(Base):
    """Admin users for the admin panel."""
    __tablename__ = "admin_users"
    
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, 
        primary_key=True, 
        default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), 
        unique=True, 
        index=True, 
        nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(
        String(20), 
        default="admin"
    )  # super_admin, admin, support
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow
    )


# ============================================================================
# Token Blacklist (for logout)
# ============================================================================

class TokenBlacklist(Base):
    """Blacklisted JWT tokens — invalidated on logout."""
    __tablename__ = "token_blacklist"
    
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4
    )
    token_jti: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
