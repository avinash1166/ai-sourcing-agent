#!/usr/bin/env python3
"""
Telegram Text-Based Feedback System - MUCH SIMPLER!
User replies to vendor messages with text feedback instead of buttons
Examples:
  - "relevant - good price, wall mount, no battery"
  - "not relevant - has battery which we don't want"
  - "skip - no contact email"
  - "maybe - need to check specifications first"
"""

import sqlite3
import requests
import re
from datetime import datetime
from typing import Dict, Optional, Tuple
from config import VENDORS_DB

class TelegramTextFeedbackCollector:
    """Collect text-based feedback from Telegram replies"""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
        self.db_path = VENDORS_DB
        self._setup_feedback_tables()
    
    def _setup_feedback_tables(self):
        """Create feedback tables if not exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Add feedback columns to vendors table
        cursor.execute("PRAGMA table_info(vendors)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'human_feedback' not in columns:
            cursor.execute("ALTER TABLE vendors ADD COLUMN human_feedback TEXT")
        if 'feedback_reason' not in columns:
            cursor.execute("ALTER TABLE vendors ADD COLUMN feedback_reason TEXT")
        if 'feedback_date' not in columns:
            cursor.execute("ALTER TABLE vendors ADD COLUMN feedback_date TEXT")
        if 'telegram_message_id' not in columns:
            cursor.execute("ALTER TABLE vendors ADD COLUMN telegram_message_id INTEGER")
        
        # Create feedback patterns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feature_type TEXT NOT NULL,
                feature_value TEXT NOT NULL,
                sentiment TEXT NOT NULL,
                count INTEGER DEFAULT 1,
                last_seen TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(feature_type, feature_value, sentiment)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def send_vendor_for_review(self, vendor_id: int) -> Optional[int]:
        """
        Send vendor to Telegram for text-based feedback
        Returns message_id if sent successfully
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT vendor_name, product_name, product_url, contact_email,
                   price_per_unit, moq, score, product_description,
                   wall_mount, has_battery, os, screen_size
            FROM vendors WHERE id = ?
        """, (vendor_id,))
        
        vendor = cursor.fetchone()
        conn.close()
        
        if not vendor:
            return None
        
        (name, product, url, email, price, moq, score, desc,
         wall_mount, has_battery, os, screen_size) = vendor
        
        # Format message
        message = f"""🔔 <b>NEW VENDOR - PLEASE REVIEW</b>

<b>Vendor:</b> {name}
<b>Product:</b> {product or 'N/A'}
<b>Score:</b> {score}/100

<b>Specifications:</b>
• Screen: {screen_size or 'Unknown'}
• OS: {os or 'Unknown'}
• Wall Mount: {'✅ Yes' if wall_mount else '❌ No' if wall_mount is False else '❓ Unknown'}
• Battery: {'⚠️ Yes (we need NO battery)' if has_battery else '✅ No battery' if has_battery is False else '❓ Unknown'}

<b>Pricing:</b>
• Price: ${price}/unit if price else 'Contact vendor'
• MOQ: {moq or 'Unknown'}

<b>Contact:</b>
• Email: {email or '❌ Not found'}
• Product: <a href="{url if url else 'https://www.made-in-china.com'}">{product or 'View product'}</a>

<b>Description:</b>
{desc[:200] if desc else 'No description'}...

━━━━━━━━━━━━━━━━━━
<b>📝 Reply to this message with your feedback:</b>

<code>relevant - [your reason]</code>
<code>not relevant - [your reason]</code>
<code>skip - [your reason]</code>

Example: <code>relevant - good price, wall mount, no battery</code>
"""
        
        try:
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": message,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                message_id = data.get('result', {}).get('message_id')
                
                # Save message_id to database
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE vendors 
                    SET telegram_message_id = ?
                    WHERE id = ?
                """, (message_id, vendor_id))
                conn.commit()
                conn.close()
                
                print(f"  📱 Feedback request sent to Telegram for: {name} (msg_id: {message_id})")
                return message_id
            else:
                print(f"  ⚠️  Telegram send failed: {response.text}")
                return None
                
        except Exception as e:
            print(f"  ❌ Telegram error: {e}")
            return None
    
    def process_text_feedback(self, message_text: str, reply_to_message_id: int) -> bool:
        """
        Process user's text feedback on a vendor
        
        Expected format:
          "relevant - good price and specifications"
          "not relevant - has battery which we don't want"
          "skip - no contact information"
        
        Returns True if processed successfully
        """
        # Find vendor by telegram message ID
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, vendor_name, product_type, wall_mount, has_battery,
                   os, screen_size, price_per_unit, moq
            FROM vendors 
            WHERE telegram_message_id = ?
        """, (reply_to_message_id,))
        
        vendor = cursor.fetchone()
        
        if not vendor:
            conn.close()
            print(f"  ⚠️  No vendor found for message ID {reply_to_message_id}")
            return False
        
        vendor_id, vendor_name = vendor[0], vendor[1]
        vendor_features = vendor[2:]
        
        # Parse feedback text
        feedback_type, reason = self._parse_feedback(message_text)
        
        if not feedback_type:
            conn.close()
            return False
        
        # Map to sentiment
        sentiment_map = {
            'relevant': 'positive',
            'not relevant': 'negative',
            'irrelevant': 'negative',
            'skip': 'neutral',
            'maybe': 'neutral'
        }
        
        sentiment = sentiment_map.get(feedback_type, 'neutral')
        
        # Save feedback
        cursor.execute("""
            UPDATE vendors 
            SET human_feedback = ?,
                feedback_reason = ?,
                feedback_date = ?
            WHERE id = ?
        """, (feedback_type, reason, datetime.now().isoformat(), vendor_id))
        
        # Learn from features (only for positive/negative)
        if sentiment in ['positive', 'negative']:
            self._learn_from_features(cursor, vendor_features, sentiment, reason)
        
        conn.commit()
        conn.close()
        
        print(f"  ✅ Feedback recorded: '{feedback_type}' for vendor {vendor_id} ({vendor_name})")
        print(f"     Reason: {reason}")
        
        return True
    
    def _parse_feedback(self, text: str) -> Tuple[Optional[str], str]:
        """
        Parse feedback text to extract type and reason
        
        Examples:
          "relevant - good price" → ('relevant', 'good price')
          "not relevant - has battery" → ('not relevant', 'has battery')
          "skip - no email" → ('skip', 'no email')
        
        Returns (feedback_type, reason)
        """
        text = text.strip().lower()
        
        # Pattern: "TYPE - REASON" or "TYPE: REASON" or "TYPE REASON"
        patterns = [
            r'^(relevant|not relevant|irrelevant|skip|maybe)\s*[-:]\s*(.+)$',
            r'^(relevant|not relevant|irrelevant|skip|maybe)\s+(.+)$',
        ]
        
        for pattern in patterns:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                feedback_type = match.group(1).lower()
                reason = match.group(2).strip()
                
                # Normalize
                if feedback_type == 'irrelevant':
                    feedback_type = 'not relevant'
                
                return (feedback_type, reason)
        
        # Check if message is just "relevant", "not relevant", etc. without reason
        if text in ['relevant', 'not relevant', 'irrelevant', 'skip', 'maybe']:
            return (text if text != 'irrelevant' else 'not relevant', 'No reason provided')
        
        return (None, '')
    
    def _learn_from_features(self, cursor, vendor_features, sentiment: str, reason: str):
        """
        Extract learnings from vendor features AND user's reason
        """
        product_type, wall_mount, has_battery, os, screen_size, price, moq = vendor_features
        
        # Learn from structured features
        features_to_learn = [
            ('product_type', product_type),
            ('wall_mount', 'yes' if wall_mount else 'no'),
            ('has_battery', 'yes' if has_battery else 'no'),
            ('os', os),
            ('screen_size', screen_size),
        ]
        
        for feature_type, feature_value in features_to_learn:
            if feature_value:
                cursor.execute("""
                    INSERT INTO feedback_patterns (feature_type, feature_value, sentiment, count)
                    VALUES (?, ?, ?, 1)
                    ON CONFLICT(feature_type, feature_value, sentiment) 
                    DO UPDATE SET count = count + 1, last_seen = CURRENT_TIMESTAMP
                """, (feature_type, str(feature_value), sentiment))
        
        # BONUS: Extract keywords from user's reason text
        self._extract_keywords_from_reason(cursor, reason, sentiment)
    
    def _extract_keywords_from_reason(self, cursor, reason: str, sentiment: str):
        """
        Extract and learn from keywords in user's feedback reason
        Examples:
          "good price" → learn that "price" is important
          "has battery which we don't want" → learn "battery" is negative
          "wall mount is perfect" → learn "wall mount" is positive
        """
        # Important keywords to track
        keyword_patterns = {
            'price': ['price', 'pricing', 'cost', 'expensive', 'cheap', 'affordable'],
            'battery': ['battery', 'batteries', 'power'],
            'wall_mount': ['wall mount', 'wall-mount', 'mounting', 'vesa'],
            'email': ['email', 'contact', 'reach'],
            'specifications': ['specs', 'specifications', 'features'],
            'quality': ['quality', 'build', 'premium', 'cheap looking'],
            'customization': ['custom', 'customizable', 'modify', 'oem', 'odm'],
        }
        
        reason_lower = reason.lower()
        
        for feature_type, keywords in keyword_patterns.items():
            for keyword in keywords:
                if keyword in reason_lower:
                    cursor.execute("""
                        INSERT INTO feedback_patterns (feature_type, feature_value, sentiment, count)
                        VALUES (?, ?, ?, 1)
                        ON CONFLICT(feature_type, feature_value, sentiment) 
                        DO UPDATE SET count = count + 1, last_seen = CURRENT_TIMESTAMP
                    """, (f'reason_keyword', keyword, sentiment))
                    break  # Only count once per feature type
    
    def check_for_new_feedback(self, offset: int = 0) -> int:
        """
        Check Telegram for new text messages (user replies)
        Returns number of feedback messages processed
        """
        print("\n🔄 Checking for new text feedback from Telegram...")
        
        try:
            response = requests.get(
                f"{self.api_url}/getUpdates",
                params={
                    'offset': offset,
                    'timeout': 5,
                    'allowed_updates': ['message']
                },
                timeout=10
            )
            
            if response.status_code != 200:
                print(f"  ❌ Failed to get updates: {response.text}")
                return 0
            
            data = response.json()
            
            if not data.get('ok'):
                print(f"  ❌ API Error: {data.get('description')}")
                return 0
            
            updates = data.get('result', [])
            
            if not updates:
                print("  ℹ️  No new messages")
                return 0
            
            print(f"  📥 Found {len(updates)} message(s)")
            
            processed = 0
            
            for update in updates:
                message = update.get('message')
                
                if not message:
                    continue
                
                # Check if this is a reply to our vendor message
                reply_to = message.get('reply_to_message', {})
                reply_to_message_id = reply_to.get('message_id')
                
                if not reply_to_message_id:
                    continue  # Not a reply, skip
                
                message_text = message.get('text', '')
                
                if not message_text:
                    continue  # No text, skip
                
                # Process the feedback
                success = self.process_text_feedback(message_text, reply_to_message_id)
                
                if success:
                    # Send confirmation
                    self._send_confirmation(message.get('chat', {}).get('id'), message_text)
                    processed += 1
            
            print(f"  ✅ Processed {processed} feedback message(s)")
            return processed
            
        except Exception as e:
            print(f"  ❌ Error checking feedback: {e}")
            return 0
    
    def _send_confirmation(self, chat_id: str, feedback_text: str):
        """Send confirmation message to user"""
        try:
            # Parse to show what was understood
            feedback_type, reason = self._parse_feedback(feedback_text)
            
            emoji_map = {
                'relevant': '✅',
                'not relevant': '❌',
                'skip': '⏭️',
                'maybe': '🤔'
            }
            
            emoji = emoji_map.get(feedback_type, '📝')
            
            confirmation = f"{emoji} <b>Feedback recorded!</b>\n\n"
            confirmation += f"<b>Type:</b> {feedback_type.title()}\n"
            confirmation += f"<b>Reason:</b> {reason}\n\n"
            confirmation += "✅ Saved to database. Next AI run will learn from this!"
            
            requests.post(
                f"{self.api_url}/sendMessage",
                json={
                    'chat_id': chat_id,
                    'text': confirmation,
                    'parse_mode': 'HTML'
                },
                timeout=5
            )
        except Exception as e:
            print(f"  ⚠️  Failed to send confirmation: {e}")

    def get_learned_preferences(self) -> Dict:
        """Get patterns learned from text feedback"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get positive patterns
        cursor.execute("""
            SELECT feature_type, feature_value, count 
            FROM feedback_patterns 
            WHERE sentiment = 'positive'
            ORDER BY count DESC
            LIMIT 20
        """)
        positive = cursor.fetchall()
        
        # Get negative patterns
        cursor.execute("""
            SELECT feature_type, feature_value, count 
            FROM feedback_patterns 
            WHERE sentiment = 'negative'
            ORDER BY count DESC
            LIMIT 20
        """)
        negative = cursor.fetchall()
        
        conn.close()
        
        return {
            'positive': positive,
            'negative': negative
        }
    
    def apply_learned_scoring_boost(self, vendor_data: Dict) -> int:
        """
        Apply learned preferences to vendor scoring
        Returns bonus/penalty points based on past feedback
        """
        preferences = self.get_learned_preferences()
        
        bonus = 0
        
        # Check positive patterns (boost score)
        for feature_type, feature_value, count in preferences['positive']:
            vendor_value = vendor_data.get(feature_type)
            
            # Handle special feature types
            if feature_type == 'wall_mount':
                vendor_value = 'yes' if vendor_value else 'no'
            elif feature_type == 'has_battery':
                vendor_value = 'yes' if vendor_value else 'no'
            
            if str(vendor_value).lower() == str(feature_value).lower():
                # More feedback = more boost (capped at +15)
                points = min(count * 3, 15)
                bonus += points
        
        # Check negative patterns (reduce score)
        for feature_type, feature_value, count in preferences['negative']:
            vendor_value = vendor_data.get(feature_type)
            
            if feature_type == 'wall_mount':
                vendor_value = 'yes' if vendor_value else 'no'
            elif feature_type == 'has_battery':
                vendor_value = 'yes' if vendor_value else 'no'
            
            if str(vendor_value).lower() == str(feature_value).lower():
                points = min(count * 3, 15)
                bonus -= points
        
        return bonus
