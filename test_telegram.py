#!/usr/bin/env python3
"""
Quick test to verify Telegram bot is working
"""

import os
import requests

# Your credentials
TELEGRAM_BOT_TOKEN = "8559218509:AAFs_qYImadj_xHISB_aHq27TQnJVmABi2w"
TELEGRAM_CHAT_ID = "7846267215"

def test_telegram():
    """Send a test message to Telegram"""
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    message = """🧪 <b>TEST MESSAGE</b>

This is a test from your AI Sourcing Agent!

If you're seeing this, Telegram integration is working! ✅

Your actual reports will look like this but with vendor data.

⏰ Testing at """ + requests.get("http://worldtimeapi.org/api/timezone/UTC").json().get("datetime", "unknown")
    
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print("✅ SUCCESS! Check your Telegram (@my_sourcing001_bot)")
            print(f"   Message sent successfully!")
            return True
        else:
            print(f"❌ FAILED: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    print("Testing Telegram bot integration...")
    print(f"Bot Token: {TELEGRAM_BOT_TOKEN[:20]}...")
    print(f"Chat ID: {TELEGRAM_CHAT_ID}")
    print()
    test_telegram()
