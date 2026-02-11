import asyncio
import logging
from uuid import uuid4

from app.db import async_session_maker, Product
from app.core import settings
from sqlalchemy import select
from sqlalchemy import select, text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

    async with async_session_maker() as session:
        # Check existing product by slug
        result = await session.execute(
            select(Product).where(Product.slug == "karungali-mala-108")
        )
        existing = result.scalar_one_or_none()
        
        if not existing:
            product = Product(
                id=uuid4(),
                name="Karungali Mala",
                slug="karungali-mala-108",
                description="Handcrafted using authentic Karungali wood, blessed across 108 sacred temples in India.",
                short_description="A Sacred Gift of Nature",
                price=25000,
                mrp=30000,
                stock=100,
                images=["https://images.unsplash.com/photo-1603201667141-5a2d4c673378?q=80&w=2070"],
                is_active=True,
                specifications={
                    "Material": "Karungali Wood",
                    "Beads": "108",
                    "Origin": "India"
                }
            )
            session.add(product)
            await session.commit()
            logger.info(f"Product created: {product.name} (ID: {product.id})")
        else:
            logger.info(f"Product already exists: {existing.name} (ID: {existing.id})")
        return

if __name__ == "__main__":
    asyncio.run(seed_data())
