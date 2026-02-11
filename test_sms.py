
import os
import sys
from dotenv import load_dotenv

# Add backend directory to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

load_dotenv("backend/.env")

from app.services.twilio_sms import TwilioSMS

def test_sms():
    print("Testing Twilio SMS...")
    sms = TwilioSMS()
    
    if not sms.client:
        print("❌ Twilio client not initialized. Check credentials.")
        return

    admin_phone = os.getenv("ADMIN_PHONE_NUMBER")
    if not admin_phone:
        print("❌ ADMIN_PHONE_NUMBER not found.")
        return

    print(f"Attempting to send SMS to {admin_phone}...")
    try:
        success = sms.send_sms(admin_phone, "Test message from Karungali Backend")
        if success:
            print("✅ SMS sent successfully!")
        else:
            print("❌ SMS failed to send. Check logs.")
    except Exception as e:
        print(f"❌ Exception during SMS send: {e}")

if __name__ == "__main__":
    test_sms()
