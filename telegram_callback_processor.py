#!/usr/bin/env python3
"""
Telegram Callback Processor - Process button clicks from Telegram
Can run standalone or be called from main workflow
"""

import os
import requests
import time
from telegram_feedback import TelegramFeedbackCollector

# Load from environment variables
def get_env_var(name: str) -> str:
    """Get environment variable with .env fallback"""
    value = os.getenv(name)
    if not value:
        # Try loading from .env file
        try:
            from dotenv import load_dotenv
            load_dotenv()
            value = os.getenv(name)
        except ImportError:
            pass
    return value or ""

class TelegramCallbackProcessor:
    """Process Telegram inline button callbacks"""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
        self.feedback_collector = TelegramFeedbackCollector(bot_token, chat_id)
        self.last_update_id = self._load_last_update_id()
    
    def _load_last_update_id(self) -> int:
        """Load last processed update ID from file"""
        try:
            with open('data/.telegram_last_update', 'r') as f:
                return int(f.read().strip())
        except:
            return 0
    
    def _save_last_update_id(self, update_id: int):
        """Save last processed update ID to file"""
        try:
            os.makedirs('data', exist_ok=True)
            with open('data/.telegram_last_update', 'w') as f:
                f.write(str(update_id))
        except Exception as e:
            print(f"⚠️  Failed to save update ID: {e}")
    
    def process_pending_callbacks(self) -> int:
        """
        Fetch and process all pending callback queries from Telegram
        Returns number of callbacks processed
        """
        print("\n🔄 Checking for pending Telegram button clicks...")
        
        try:
            # Get updates from Telegram
            response = requests.get(
                f"{self.api_url}/getUpdates",
                params={
                    'offset': self.last_update_id + 1,
                    'timeout': 5,
                    'allowed_updates': ['callback_query']
                },
                timeout=10
            )
            
            if response.status_code != 200:
                print(f"❌ Failed to get updates: {response.text}")
                return 0
            
            data = response.json()
            
            if not data.get('ok'):
                print(f"❌ Telegram API error: {data.get('description')}")
                return 0
            
            updates = data.get('result', [])
            
            if not updates:
                print("  ℹ️  No pending callbacks")
                return 0
            
            print(f"  📥 Found {len(updates)} pending update(s)")
            
            processed = 0
            
            for update in updates:
                update_id = update.get('update_id')
                callback_query = update.get('callback_query')
                
                if not callback_query:
                    continue
                
                callback_id = callback_query.get('id')
                callback_data = callback_query.get('data')
                message = callback_query.get('message', {})
                user = callback_query.get('from', {})
                
                print(f"\n  📲 Processing callback: {callback_data}")
                print(f"     User: {user.get('first_name')} (@{user.get('username')})")
                
                # Process the feedback
                success = self.feedback_collector.process_callback(callback_data)
                
                if success:
                    # Answer the callback query (removes loading state from button)
                    self._answer_callback_query(
                        callback_id,
                        text="✅ Feedback recorded! Thank you."
                    )
                    
                    # Edit the message to show it was processed
                    self._mark_message_processed(message.get('message_id'), callback_data)
                    
                    processed += 1
                else:
                    self._answer_callback_query(
                        callback_id,
                        text="❌ Failed to process feedback. Please try again."
                    )
                
                # Update last processed update ID
                if update_id > self.last_update_id:
                    self.last_update_id = update_id
                    self._save_last_update_id(update_id)
            
            print(f"\n✅ Processed {processed}/{len(updates)} callbacks")
            return processed
            
        except Exception as e:
            print(f"❌ Error processing callbacks: {e}")
            return 0
    
    def _answer_callback_query(self, callback_id: str, text: str):
        """Send answer to callback query (shows popup to user)"""
        try:
            requests.post(
                f"{self.api_url}/answerCallbackQuery",
                json={
                    'callback_query_id': callback_id,
                    'text': text,
                    'show_alert': False
                },
                timeout=5
            )
        except Exception as e:
            print(f"  ⚠️  Failed to answer callback: {e}")
    
    def _mark_message_processed(self, message_id: int, callback_data: str):
        """Edit the original message to show feedback was processed"""
        try:
            feedback_type = callback_data.split('_')[0].upper()
            emoji = "✅" if feedback_type == "RELEVANT" else "❌"
            
            requests.post(
                f"{self.api_url}/editMessageReplyMarkup",
                json={
                    'chat_id': self.chat_id,
                    'message_id': message_id,
                    'reply_markup': {
                        'inline_keyboard': [[
                            {'text': f'{emoji} Marked as {feedback_type}', 'callback_data': 'processed'}
                        ]]
                    }
                },
                timeout=5
            )
        except Exception as e:
            print(f"  ⚠️  Failed to update message: {e}")
    
    def run_continuous(self, interval: int = 30):
        """
        Run continuous polling loop
        interval: seconds between checks (default 30s)
        """
        print(f"🤖 Starting Telegram callback processor (polling every {interval}s)")
        print(f"   Bot: {self.bot_token[:20]}...")
        print(f"   Chat: {self.chat_id}")
        print("\n   Press Ctrl+C to stop\n")
        
        try:
            while True:
                self.process_pending_callbacks()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n\n👋 Callback processor stopped")

def main():
    """Run callback processor"""
    
    # Load credentials from environment
    bot_token = get_env_var('TELEGRAM_BOT_TOKEN')
    chat_id = get_env_var('TELEGRAM_CHAT_ID')
    
    # Check for required environment variables
    if not bot_token or not chat_id:
        print("❌ Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")
        print("   Set them in .env file or environment variables")
        return
    
    processor = TelegramCallbackProcessor(bot_token, chat_id)
    
    # Check command line argument
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == '--once':
            # Process once and exit (for GitHub Actions)
            processor.process_pending_callbacks()
        elif sys.argv[1] == '--continuous':
            # Run continuously (for local/server deployment)
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            processor.run_continuous(interval)
        else:
            print("Usage:")
            print("  python telegram_callback_processor.py --once         # Process once and exit")
            print("  python telegram_callback_processor.py --continuous [interval]  # Run continuously")
    else:
        # Default: process once
        processor.process_pending_callbacks()

if __name__ == "__main__":
    main()
