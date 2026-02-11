import asyncio
import httpx
import sys
from app.db import async_session_maker, Product
from app.core import settings
from app.core.security import create_access_token

import uuid

async def seed_product():
    product_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    async with async_session_maker() as session:
        # Check if product exists
        if not (await session.get(Product, product_id)):
            product = Product(
                id=product_id,
                name="Karungali Mala",
                description="Original Ebony Wood Mala",
                price=25000.0,
                stock=100,
                category="Mala",
                is_active=True,
                images=["https://placeholder.com/image.jpg"]
            )
            session.add(product)
            await session.commit()
            print(f"Stock seeded: Karungali Mala ({product_id})")
            return str(product_id)
        return str(product_id)

async def test_flow():
    base_url = "http://localhost:8000/api/v1"
    
    # 1. Seed Product
    product_id = await seed_product()
    
    async with httpx.AsyncClient(base_url=base_url) as client:
        # 2. Login / Register
        mobile = "+919999999999"
        # Send OTP
        resp = await client.post("/auth/send-otp", json={"mobile_number": mobile})
        print(f"Send OTP: {resp.status_code}")
        
        # Verify OTP (assuming fixed OTP "123456" for test or we need to extract from logs, but for now lets assume debug mode bypass or similar. Wait, backend uses random. Let's hijack verify with a known user token or use the backdoor if exists.
        # Actually, since I can read logs, I could parse it, but that's complex.
        # Let's use the existing admin token if possible or just create a user directly in DB?
        # Creating user directly is easier for backend test script.
        
        # Mock user creation/token generation

        async with async_session_maker() as session:
            # Check user
            from sqlalchemy import select
            from app.db import User
            result = await session.execute(select(User).where(User.mobile_number == mobile))
            user = result.scalar_one_or_none()
            if not user:
                user = User(mobile_number=mobile, full_name="Test User", role="user")
                session.add(user)
                await session.commit()
                await session.refresh(user)
            
            token = create_access_token(user.id)
            headers = {"Authorization": f"Bearer {token}"}
            print(f"Logged in as {user.mobile_number}")

        # 3. Add to Cart
        cart_resp = await client.post(
            "/cart/add", 
            json={"product_id": product_id, "quantity": 1},
            headers=headers
        )
        print(f"Add to Cart: {cart_resp.status_code} - {cart_resp.text}")
        assert cart_resp.status_code == 200

        # 4. Create Address
        addr_resp = await client.post(
            "/users/addresses",
            json={
                "name": "Test User",
                "mobile": "9999999999",
                "line1": "123 Test St",
                "city": "Chennai",
                "state": "TN",
                "pincode": "600001",
                "is_default": True
            },
            headers=headers
        )
        print(f"Create Addr: {addr_resp.status_code} - {addr_resp.text}")
        assert addr_resp.status_code == 200
        address_id = addr_resp.json()["id"]

        # 5. Create Order
        order_resp = await client.post(
            "/orders",
            json={"address_id": address_id},
            headers=headers
        )
        print(f"Create Order: {order_resp.status_code} - {order_resp.text}")
        
        if order_resp.status_code == 200:
            order_data = order_resp.json()
            print(f"✅ Order Created: {order_data['order_number']}")
            print(f"   Total: {order_data['total_amount']}")
            print(f"   Status: {order_data['status']}")
        else:
            print("❌ Order Creation Failed")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_flow())
