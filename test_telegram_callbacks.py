#!/usr/bin/env python3
"""
Test Telegram Callback Processing
Manually check and process any pending button clicks
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from telegram_callback_processor import TelegramCallbackProcessor, get_env_var

def main():
    print("=" * 70)
    print("🧪 TELEGRAM CALLBACK TEST")
    print("=" * 70)
    
    bot_token = get_env_var('TELEGRAM_BOT_TOKEN')
    chat_id = get_env_var('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        print("\n❌ Error: Missing credentials")
        print("   TELEGRAM_BOT_TOKEN:", "✅ Set" if bot_token else "❌ Missing")
        print("   TELEGRAM_CHAT_ID:", "✅ Set" if chat_id else "❌ Missing")
        print("\n   Set them in .env file or as environment variables")
        return
    
    print("\n📋 Configuration:")
    print(f"   Bot Token: {bot_token[:30]}...")
    print(f"   Chat ID: {chat_id}")
    
    processor = TelegramCallbackProcessor(bot_token, chat_id)
    
    print("\n🔍 Checking for pending button clicks from Telegram...")
    print("   (This includes ALL unprocessed callbacks)")
    print()
    
    count = processor.process_pending_callbacks()
    
    print("\n" + "=" * 70)
    if count > 0:
        print(f"✅ SUCCESS: Processed {count} callback(s)")
        print("\n   The vendor database has been updated with your feedback.")
        print("   Next AI run will learn from your preferences!")
    else:
        print("ℹ️  NO CALLBACKS FOUND")
        print("\n   This means:")
        print("   • No buttons have been clicked yet, OR")
        print("   • All button clicks were already processed")
        print("\n   Try clicking a ✅/❌ button in Telegram, then run this again.")
    print("=" * 70)

if __name__ == "__main__":
    main()
