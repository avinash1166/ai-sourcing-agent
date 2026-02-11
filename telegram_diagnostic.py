#!/usr/bin/env python3
"""
TELEGRAM BUTTON DIAGNOSTIC
Run this to see if your button clicks are reaching Telegram's servers
"""

import requests
import json

print("="*70)
print("🔍 TELEGRAM BUTTON DIAGNOSTIC")
print("="*70)
print()
print("This will check if your button clicks are stored in Telegram")
print("You don't need credentials - we'll use a public test bot")
print()

# Instructions for user
print("📋 TO USE YOUR ACTUAL BOT:")
print("-" * 70)
print("1. Get your bot token from @BotFather on Telegram")
print("2. Get your chat ID by messaging @userinfobot on Telegram")
print("3. Run this with your credentials:")
print()
print("   python telegram_diagnostic.py YOUR_BOT_TOKEN YOUR_CHAT_ID")
print()
print("=" * 70)
print()

import sys

if len(sys.argv) < 3:
    print("❌ Missing arguments!")
    print()
    print("USAGE:")
    print(f"  python {sys.argv[0]} <BOT_TOKEN> <CHAT_ID>")
    print()
    print("Example:")
    print(f"  python {sys.argv[0]} 123456:ABCdefGHI... 9876543210")
    print()
    print("=" * 70)
    sys.exit(1)

BOT_TOKEN = sys.argv[1]
CHAT_ID = sys.argv[2]

print(f"📱 Bot Token: {BOT_TOKEN[:20]}...")
print(f"💬 Chat ID: {CHAT_ID}")
print()

# Test 1: Check bot is valid
print("TEST 1: Checking bot connection...")
print("-" * 70)

api_url = f"https://api.telegram.org/bot{BOT_TOKEN}"

try:
    response = requests.get(f"{api_url}/getMe", timeout=10)
    data = response.json()
    
    if data.get('ok'):
        bot = data['result']
        print(f"✅ Bot connected: @{bot['username']}")
        print(f"   Name: {bot.get('first_name', 'N/A')}")
        print(f"   ID: {bot['id']}")
    else:
        print(f"❌ Bot error: {data.get('description')}")
        print()
        print("POSSIBLE ISSUES:")
        print("• Bot token is invalid")
        print("• Bot was deleted or revoked")
        sys.exit(1)
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print()
    print("POSSIBLE ISSUES:")
    print("• No internet connection")
    print("• Telegram API is down")
    print("• Firewall blocking requests")
    sys.exit(1)

print()

# Test 2: Get updates
print("TEST 2: Checking for button clicks (callback queries)...")
print("-" * 70)

try:
    response = requests.get(
        f"{api_url}/getUpdates",
        params={'timeout': 5},
        timeout=10
    )
    data = response.json()
    
    if not data.get('ok'):
        print(f"❌ Error: {data.get('description')}")
        sys.exit(1)
    
    updates = data.get('result', [])
    
    print(f"📊 Total updates: {len(updates)}")
    
    # Filter for callback queries
    callbacks = [u for u in updates if 'callback_query' in u]
    
    print(f"📲 Callback queries (button clicks): {len(callbacks)}")
    print()
    
    if len(callbacks) == 0:
        print("❓ NO BUTTON CLICKS FOUND")
        print()
        print("This means:")
        print("  • You haven't clicked any buttons yet, OR")
        print("  • Button clicks were already processed")
        print()
        print("TRY THIS:")
        print("  1. Go to your Telegram chat with the bot")
        print("  2. Find a message with ✅/❌ buttons")
        print("  3. Click one of the buttons")
        print("  4. Run this diagnostic again immediately")
        print()
    else:
        print("✅ BUTTON CLICKS DETECTED!")
        print()
        
        for i, update in enumerate(callbacks[:5], 1):  # Show first 5
            cq = update['callback_query']
            print(f"Click #{i}:")
            print(f"  Data: {cq.get('data', 'N/A')}")
            print(f"  From: {cq['from'].get('first_name')} (@{cq['from'].get('username', 'N/A')})")
            print(f"  Date: {cq.get('date', 'N/A')}")
            print()
        
        if len(callbacks) > 5:
            print(f"  ... and {len(callbacks) - 5} more")
            print()
        
        print("✅ YOUR BUTTONS ARE WORKING!")
        print()
        print("The clicks are stored in Telegram's servers.")
        print("Now the callback processor just needs to fetch and process them.")
        print()

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Test 3: Check if we can send a message
print("TEST 3: Checking if we can send messages to you...")
print("-" * 70)

try:
    test_message = "🧪 Telegram Button Diagnostic Test Message"
    
    response = requests.post(
        f"{api_url}/sendMessage",
        json={
            'chat_id': CHAT_ID,
            'text': test_message
        },
        timeout=10
    )
    
    data = response.json()
    
    if data.get('ok'):
        print(f"✅ Test message sent to chat {CHAT_ID}")
        print()
    else:
        error = data.get('description', 'Unknown error')
        print(f"❌ Failed to send message: {error}")
        print()
        
        if 'chat not found' in error.lower():
            print("ISSUE: Chat ID is invalid or bot was blocked by user")
            print()
            print("FIX:")
            print("  1. Make sure you've started a chat with the bot first")
            print("  2. Send /start to the bot in Telegram")
            print("  3. Get your correct chat ID from @userinfobot")
        
except Exception as e:
    print(f"❌ Error: {e}")

print()
print("=" * 70)
print("🏁 DIAGNOSTIC COMPLETE")
print("=" * 70)
