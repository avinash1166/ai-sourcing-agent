"""
Telegram Feedback System - Interactive vendor review via Telegram
Sends each discovered vendor for human approval/rejection
Learns from feedback to improve future searches
"""

import sqlite3
import requests
import json
from datetime import datetime
from typing import Dict, Optional
from config import VENDORS_DB

class TelegramFeedbackCollector:
    """Collect human feedback on vendors via Telegram with inline buttons"""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
        self.db_path = VENDORS_DB
        self._setup_feedback_table()
    
    def _setup_feedback_table(self):
        """Create feedback table if not exists"""
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
        
        # Create feedback patterns table (for learning)
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
    
    def request_feedback(self, vendor_id: int) -> bool:
        """
        Send vendor to Telegram with inline buttons for feedback
        Returns True if message sent successfully
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
            return False
        
        (name, product, url, email, price, moq, score, desc,
         wall_mount, has_battery, os, screen_size) = vendor
        
        # Format message
        message = f"""🔔 <b>NEW VENDOR FOUND - FEEDBACK REQUESTED</b>

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
<b>Is this vendor relevant for our product?</b>
"""
        
        # Create inline keyboard with buttons
        inline_keyboard = {
            "inline_keyboard": [
                [
                    {"text": "✅ RELEVANT", "callback_data": f"relevant_{vendor_id}"},
                    {"text": "❌ IRRELEVANT", "callback_data": f"irrelevant_{vendor_id}"}
                ],
                [
                    {"text": "🔗 View Product", "url": url if url and url.startswith('http') else "https://www.made-in-china.com"}
                ]
            ]
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": message,
                    "parse_mode": "HTML",
                    "reply_markup": inline_keyboard,
                    "disable_web_page_preview": True
                },
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"  📱 Feedback request sent to Telegram for: {name}")
                return True
            else:
                print(f"  ⚠️  Telegram send failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"  ❌ Telegram error: {e}")
            return False
    
    def process_callback(self, callback_data: str, vendor_id: int = None, reason: str = None) -> bool:
        """
        Process feedback from Telegram button clicks
        callback_data format: "relevant_123" or "irrelevant_123"
        """
        # Parse callback
        if '_' in callback_data:
            feedback_type, vid = callback_data.split('_', 1)
            vendor_id = int(vid)
        else:
            feedback_type = callback_data
        
        if feedback_type not in ['relevant', 'irrelevant']:
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Save feedback to vendors table
        cursor.execute("""
            UPDATE vendors 
            SET human_feedback = ?, 
                feedback_reason = ?,
                feedback_date = ?
            WHERE id = ?
        """, (feedback_type, reason, datetime.now().isoformat(), vendor_id))
        
        # Extract vendor features for learning
        cursor.execute("""
            SELECT vendor_name, product_type, wall_mount, has_battery, 
                   os, screen_size, price_per_unit, moq
            FROM vendors WHERE id = ?
        """, (vendor_id,))
        
        vendor = cursor.fetchone()
        if vendor:
            sentiment = 'positive' if feedback_type == 'relevant' else 'negative'
            
            # Learn from features
            features_to_learn = [
                ('product_type', vendor[1]),
                ('wall_mount', 'yes' if vendor[2] else 'no'),
                ('has_battery', 'yes' if vendor[3] else 'no'),
                ('os', vendor[4]),
                ('screen_size', vendor[5]),
            ]
            
            for feature_type, feature_value in features_to_learn:
                if feature_value:
                    cursor.execute("""
                        INSERT INTO feedback_patterns (feature_type, feature_value, sentiment, count)
                        VALUES (?, ?, ?, 1)
                        ON CONFLICT(feature_type, feature_value, sentiment) 
                        DO UPDATE SET count = count + 1, last_seen = CURRENT_TIMESTAMP
                    """, (feature_type, str(feature_value), sentiment))
        
        conn.commit()
        conn.close()
        
        print(f"  ✅ Feedback recorded: {feedback_type} for vendor {vendor_id}")
        return True
    
    def get_learned_preferences(self) -> Dict:
        """Get patterns learned from feedback"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get positive patterns (what user likes)
        cursor.execute("""
            SELECT feature_type, feature_value, count 
            FROM feedback_patterns 
            WHERE sentiment = 'positive'
            ORDER BY count DESC
            LIMIT 20
        """)
        positive = cursor.fetchall()
        
        # Get negative patterns (what user dislikes)
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
            'positive_patterns': [
                {'type': p[0], 'value': p[1], 'count': p[2]} 
                for p in positive
            ],
            'negative_patterns': [
                {'type': n[0], 'value': n[1], 'count': n[2]} 
                for n in negative
            ]
        }
    
    def apply_learned_scoring_boost(self, vendor_data: Dict) -> int:
        """
        Apply scoring boost based on learned preferences
        Returns bonus points (0-30) to add to vendor score
        """
        patterns = self.get_learned_preferences()
        bonus = 0
        
        # Check against positive patterns
        for pattern in patterns['positive_patterns']:
            feature_type = pattern['type']
            feature_value = str(pattern['value'])
            weight = pattern['count']
            
            vendor_value = str(vendor_data.get(feature_type, ''))
            
            if feature_value.lower() in vendor_value.lower():
                bonus += min(weight * 2, 10)  # Max 10 points per feature
        
        # Check against negative patterns (penalty)
        for pattern in patterns['negative_patterns']:
            feature_type = pattern['type']
            feature_value = str(pattern['value'])
            weight = pattern['count']
            
            vendor_value = str(vendor_data.get(feature_type, ''))
            
            if feature_value.lower() in vendor_value.lower():
                bonus -= min(weight * 2, 10)  # Max -10 points per feature
        
        # Cap bonus at +30 / -30
        return max(-30, min(30, bonus))
