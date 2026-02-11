
import asyncio
import os
import sys
from sqlalchemy import text
from dotenv import load_dotenv

# Add backend directory to path
sys.path.append(os.path.join(os.getcwd(), "backend"))
load_dotenv("backend/.env")

from app.db.database import async_session_maker

async def clear_otps():
    mobile = os.getenv("ADMIN_PHONE_NUMBER").replace(" ", "")
    print(f"Clearing OTPs for {mobile}...")
    
    # Ensure usage of correct DB path
    from app.core.config import settings
    # Override DATABASE_URL to be absolutepath if needed, but it should pick up from .env
    # The issue is likely that "sqlite:///./karungali.db" refers to CWD.
    if "sqlite" in settings.DATABASE_URL:
       # Verify file exists
       if not os.path.exists("./karungali.db") and os.path.exists("backend/karungali.db"):
           # We are in root, db is in backend
           # We should chdir to backend or update URL... 
           # Easier to just chdir
           os.chdir("backend")
           print(f"Changed working directory to {os.getcwd()}")
           
    async with async_session_maker() as session:
        await session.execute(
            text("DELETE FROM otp_logs WHERE mobile_number = :mobile"),
            {"mobile": mobile}
        )
        await session.commit()
    print("✅ OTPs cleared.")

if __name__ == "__main__":
    asyncio.run(clear_otps())
