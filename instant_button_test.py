#!/usr/bin/env python3
"""
IMMEDIATE BUTTON TEST - Run this to process your Telegram button click RIGHT NOW
No need to wait for GitHub Actions!

USAGE:
  1. Set your credentials below (lines 17-18)
  2. Run: python instant_button_test.py
  3. Your button click will be processed immediately!
"""

import requests
import sys

# ============ SET YOUR CREDENTIALS HERE ============
# Get these from GitHub Secrets or your .env file
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Replace with your actual token
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"      # Replace with your actual chat ID
# ===================================================

def test_telegram_api():
    """Test if credentials work"""
    print("🔍 Testing Telegram API connection...")
    
    api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
    
    try:
        response = requests.get(f"{api_url}/getMe", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data.get('result', {})
                print(f"✅ Connected to bot: @{bot_info.get('username')}")
                return True
            else:
                print(f"❌ API Error: {data.get('description')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return False

def get_pending_updates():
    """Get all pending callback queries"""
    print("\n📥 Fetching pending button clicks...")
    
    api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
    
    try:
        response = requests.get(
            f"{api_url}/getUpdates",
            params={
                'timeout': 5,
                'allowed_updates': ['callback_query']
            },
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to get updates: {response.text}")
            return []
        
        data = response.json()
        
        if not data.get('ok'):
            print(f"❌ API Error: {data.get('description')}")
            return []
        
        updates = data.get('result', [])
        callbacks = [u for u in updates if 'callback_query' in u]
        
        print(f"✅ Found {len(callbacks)} pending callback(s)")
        return callbacks
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def show_callback_details(callback_query):
    """Show what button was clicked"""
    callback_data = callback_query.get('data', '')
    message = callback_query.get('message', {})
    user = callback_query.get('from', {})
    
    print(f"\n{'='*60}")
    print(f"📲 BUTTON CLICK DETECTED:")
    print(f"{'='*60}")
    print(f"User: {user.get('first_name')} (@{user.get('username')})")
    print(f"Callback Data: {callback_data}")
    print(f"Message ID: {message.get('message_id')}")
    
    # Parse the callback data
    if '_' in callback_data:
        action, vendor_id = callback_data.split('_', 1)
        print(f"\nParsed:")
        print(f"  Action: {action.upper()}")
        print(f"  Vendor ID: {vendor_id}")
    
    print(f"{'='*60}\n")
    
    return callback_query

def answer_callback(callback_id, text):
    """Send confirmation popup to user"""
    api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
    
    try:
        response = requests.post(
            f"{api_url}/answerCallbackQuery",
            json={
                'callback_query_id': callback_id,
                'text': text,
                'show_alert': False
            },
            timeout=5
        )
        
        if response.status_code == 200:
            print(f"✅ Sent popup to user: '{text}'")
            return True
        else:
            print(f"⚠️  Failed to send popup: {response.text}")
            return False
    except Exception as e:
        print(f"⚠️  Error sending popup: {e}")
        return False

def main():
    print("="*60)
    print("🧪 INSTANT TELEGRAM BUTTON TEST")
    print("="*60)
    
    # Validate credentials
    if TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("\n❌ ERROR: You need to set your TELEGRAM_BOT_TOKEN!")
        print("   Edit this file (line 17) and add your actual bot token")
        print("\n   Or run with environment variables:")
        print("   TELEGRAM_BOT_TOKEN='xxx' TELEGRAM_CHAT_ID='yyy' python instant_button_test.py")
        return
    
    if TELEGRAM_CHAT_ID == "YOUR_CHAT_ID_HERE":
        print("\n❌ ERROR: You need to set your TELEGRAM_CHAT_ID!")
        print("   Edit this file (line 18) and add your actual chat ID")
        return
    
    # Test connection
    if not test_telegram_api():
        print("\n❌ Failed to connect to Telegram. Check your bot token!")
        return
    
    # Get pending updates
    updates = get_pending_updates()
    
    if not updates:
        print("\n📭 No pending button clicks found")
        print("\n   This means:")
        print("   • You haven't clicked any buttons yet, OR")
        print("   • Button clicks were already processed")
        print("\n   Try clicking a ✅/❌ button in Telegram now, then run this again!")
        return
    
    # Process each callback
    print(f"\n🔄 Processing {len(updates)} callback(s)...\n")
    
    for update in updates:
        callback_query = update.get('callback_query')
        if not callback_query:
            continue
        
        callback_id = callback_query.get('id')
        
        # Show details
        show_callback_details(callback_query)
        
        # Send confirmation
        answer_callback(callback_id, "✅ Feedback recorded! (Test mode - not saved to DB yet)")
    
    print("\n" + "="*60)
    print("✅ TEST COMPLETE!")
    print("="*60)
    print("\nYour button clicks are being received by Telegram!")
    print("The full system on GitHub Actions will save them to the database.")
    print("\nNext step: Wait for GitHub Actions to run (every 5 minutes)")
    print("Or manually trigger it at:")
    print("https://github.com/avinash1166/ai-sourcing-agent/actions")
    print("="*60)

if __name__ == "__main__":
    # Allow overriding credentials via environment variables
    import os
    token = os.getenv('TELEGRAM_BOT_TOKEN', TELEGRAM_BOT_TOKEN)
    chat_id = os.getenv('TELEGRAM_CHAT_ID', TELEGRAM_CHAT_ID)
    
    if token != "YOUR_BOT_TOKEN_HERE":
        TELEGRAM_BOT_TOKEN = token
    if chat_id != "YOUR_CHAT_ID_HERE":
        TELEGRAM_CHAT_ID = chat_id
    
    main()
