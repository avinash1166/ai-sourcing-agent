#!/usr/bin/env python3
"""
Process Text Feedback from Telegram
Checks for user replies to vendor messages and processes them
Much simpler than button callbacks!
"""

import os
import sys

# Get credentials from environment
def get_env_var(name: str) -> str:
    """Get environment variable with .env fallback"""
    value = os.getenv(name)
    if not value:
        try:
            from dotenv import load_dotenv
            load_dotenv()
            value = os.getenv(name)
        except ImportError:
            pass
    return value or ""

from telegram_text_feedback import TelegramTextFeedbackCollector

def main():
    """Process text feedback from Telegram"""
    
    bot_token = get_env_var('TELEGRAM_BOT_TOKEN')
    chat_id = get_env_var('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        print("❌ Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")
        print("   Set them in .env file or environment variables")
        return
    
    print("="*70)
    print("📝 TELEGRAM TEXT FEEDBACK PROCESSOR")
    print("="*70)
    print()
    
    collector = TelegramTextFeedbackCollector(bot_token, chat_id)
    
    # Check for new feedback
    count = collector.check_for_new_feedback()
    
    print()
    print("="*70)
    if count > 0:
        print(f"✅ Processed {count} feedback message(s)")
        print()
        print("Your feedback has been saved and the AI will learn from it!")
    else:
        print("ℹ️  No new feedback found")
        print()
        print("Reply to a vendor message in Telegram with:")
        print("  'relevant - [your reason]'")
        print("  'not relevant - [your reason]'")
        print("  'skip - [your reason]'")
    print("="*70)

if __name__ == "__main__":
    main()
