"""
Telegram Reporter - Sends daily reports and notifications via Telegram
Much better than email: instant, saved in chat, no spam folder
"""

import sqlite3
from datetime import datetime, timedelta
import requests
from typing import Dict, List
from config import VENDORS_DB

class TelegramReporter:
    """Sends reports and notifications via Telegram Bot"""
    
    def __init__(self, bot_token: str, chat_id: str):
        """
        Initialize Telegram bot
        
        Args:
            bot_token: Your Telegram Bot Token (from @BotFather)
            chat_id: Your Telegram Chat ID (your user ID)
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
        self.db_path = VENDORS_DB
    
    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Send a message via Telegram"""
        try:
            url = f"{self.api_url}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True
            }
            
            response = requests.post(url, json=data, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            print(f"❌ Telegram send error: {e}")
            return False
    
    def collect_daily_stats(self) -> Dict:
        """Collect statistics from today's activities"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Total vendors discovered today
        cursor.execute("""
            SELECT COUNT(*) FROM vendors 
            WHERE discovered_date = ?
        """, (today,))
        total_discovered = cursor.fetchone()[0]
        
        # High-scoring vendors (>= 70)
        cursor.execute("""
            SELECT vendor_name, score, contact_email, product_description, moq, price_per_unit
            FROM vendors 
            WHERE discovered_date = ? AND score >= 70
            ORDER BY score DESC
            LIMIT 10
        """, (today,))
        high_score_vendors = cursor.fetchall()
        
        # Medium-scoring vendors (50-69)
        cursor.execute("""
            SELECT vendor_name, score, contact_email
            FROM vendors 
            WHERE discovered_date = ? AND score >= 50 AND score < 70
            ORDER BY score DESC
            LIMIT 5
        """, (today,))
        medium_score_vendors = cursor.fetchall()
        
        # Emails sent today
        cursor.execute("""
            SELECT COUNT(*) FROM vendors 
            WHERE last_email_date = ? AND email_sent_count > 0
        """, (today,))
        emails_sent = cursor.fetchone()[0]
        
        # Replies received today
        cursor.execute("""
            SELECT COUNT(*) FROM vendors 
            WHERE last_response_date = ?
        """, (today,))
        replies_received = cursor.fetchone()[0]
        
        # Vendors with responses
        cursor.execute("""
            SELECT vendor_name, email_response, price_quoted, moq_quoted, response_time_hours
            FROM vendors 
            WHERE last_response_date = ?
            ORDER BY response_time_hours ASC
            LIMIT 5
        """, (today,))
        vendors_with_responses = cursor.fetchall()
        
        # Keywords used today
        cursor.execute("""
            SELECT DISTINCT keywords_used FROM vendors 
            WHERE discovered_date = ?
        """, (today,))
        keywords_results = cursor.fetchall()
        
        conn.close()
        
        # Parse keywords
        import json
        all_keywords = set()
        for kr in keywords_results:
            if kr[0]:
                try:
                    kws = json.loads(kr[0]) if isinstance(kr[0], str) else kr[0]
                    all_keywords.update(kws)
                except:
                    pass
        
        return {
            "total_discovered": total_discovered,
            "high_score_vendors": high_score_vendors,
            "medium_score_vendors": medium_score_vendors,
            "emails_sent": emails_sent,
            "replies_received": replies_received,
            "vendors_with_responses": vendors_with_responses,
            "keywords_used": list(all_keywords)
        }
    
    def generate_report_message(self, stats: Dict) -> str:
        """Generate formatted Telegram message"""
        
        # Header
        message = f"""🤖 <b>AI Sourcing Agent - Daily Report</b>
📅 {datetime.now().strftime('%B %d, %Y')}

━━━━━━━━━━━━━━━━━━━━━━━━
📊 <b>TODAY'S SUMMARY</b>
━━━━━━━━━━━━━━━━━━━━━━━━

🔍 Vendors Discovered: <b>{stats["total_discovered"]}</b>
📧 Emails Sent: <b>{stats["emails_sent"]}</b>
💬 Replies Received: <b>{stats["replies_received"]}</b>

"""
        
        # High-priority vendors
        if stats["high_score_vendors"]:
            message += "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            message += "⭐ <b>HIGH-PRIORITY VENDORS</b> (Score ≥ 70)\n"
            message += "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            for vendor in stats["high_score_vendors"]:
                name, score, email, desc, moq, price = vendor
                message += f"✅ <b>{name}</b> - Score: {score}/100\n"
                if email:
                    message += f"   📧 {email}\n"
                if price:
                    message += f"   💰 ${price}/unit"
                if moq:
                    message += f" | MOQ: {moq}\n"
                else:
                    message += "\n"
                if desc:
                    message += f"   📝 {desc[:100]}...\n"
                message += "\n"
        else:
            message += "ℹ️ No high-scoring vendors found today.\n\n"
        
        # Vendor responses
        if stats["vendors_with_responses"]:
            message += "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            message += "💬 <b>VENDOR RESPONSES</b>\n"
            message += "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            for resp in stats["vendors_with_responses"]:
                name, response_text, price, moq, resp_time = resp
                message += f"💬 <b>{name}</b>\n"
                if resp_time:
                    message += f"   ⏱️ Responded in {resp_time:.1f} hours\n"
                if price:
                    message += f"   💰 Price: ${price}"
                if moq:
                    message += f" | MOQ: {moq}"
                if price or moq:
                    message += "\n"
                if response_text:
                    message += f"   📄 {response_text[:100]}...\n"
                message += "\n"
        
        # Medium-priority vendors (compact)
        if stats["medium_score_vendors"]:
            message += "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            message += "📋 <b>MEDIUM-PRIORITY</b> (Score 50-69)\n"
            message += "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            for vendor in stats["medium_score_vendors"]:
                name, score, email = vendor
                message += f"• {name} ({score}/100)\n"
        
        # Keywords used
        if stats["keywords_used"]:
            message += "\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
            message += "🔍 <b>KEYWORDS USED TODAY</b>\n"
            message += "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            keywords_text = ", ".join(stats["keywords_used"][:10])
            message += f"{keywords_text}\n"
        
        # Footer
        message += f"\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
        message += f"🤖 Automated by AI Sourcing Agent\n"
        message += f"⏰ Generated at {datetime.now().strftime('%H:%M UTC')}"
        
        return message
    
    def send_daily_report(self) -> bool:
        """Collect stats and send Telegram report"""
        
        try:
            # Collect stats
            stats = self.collect_daily_stats()
            
            # Generate message
            message = self.generate_report_message(stats)
            
            # Send message
            success = self.send_message(message)
            
            if success:
                print(f"✅ Telegram report sent!")
            else:
                print(f"⚠️ Telegram report failed")
            
            return success
            
        except Exception as e:
            print(f"❌ Error generating Telegram report: {e}")
            return False
    
    def send_vendor_alert(self, vendor_name: str, score: int, email: str = None, price: str = None, moq: str = None):
        """Send instant alert for high-scoring vendor"""
        
        message = f"""🚨 <b>HIGH-SCORE VENDOR FOUND!</b>

⭐ <b>{vendor_name}</b>
📊 Score: <b>{score}/100</b>
"""
        
        if email:
            message += f"📧 {email}\n"
        if price:
            message += f"💰 ${price}/unit\n"
        if moq:
            message += f"📦 MOQ: {moq}\n"
        
        message += f"\n⏰ {datetime.now().strftime('%H:%M UTC')}"
        
        return self.send_message(message)
    
    def send_response_alert(self, vendor_name: str, response_preview: str):
        """Send instant alert when vendor responds"""
        
        message = f"""💬 <b>VENDOR RESPONDED!</b>

📧 <b>{vendor_name}</b> replied:

"{response_preview[:200]}..."

⏰ {datetime.now().strftime('%H:%M UTC')}
"""
        
        return self.send_message(message)
    
    def send_learning_update(self, new_keywords_count: int, success_rate: float):
        """Send learning progress update"""
        
        message = f"""🧠 <b>LEARNING UPDATE</b>

✨ Generated {new_keywords_count} new keywords
📈 Success rate: {success_rate:.1%}

Agent is getting smarter! 🚀

⏰ {datetime.now().strftime('%H:%M UTC')}
"""
        
        return self.send_message(message)
    
    def test_connection(self) -> bool:
        """Test Telegram bot connection"""
        
        try:
            url = f"{self.api_url}/getMe"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                bot_info = response.json()
                bot_name = bot_info.get('result', {}).get('first_name', 'Unknown')
                print(f"✅ Telegram bot connected: {bot_name}")
                
                # Send test message
                test_msg = f"✅ AI Sourcing Agent connected!\n\n🤖 Bot is ready to send reports.\n\n⏰ {datetime.now().strftime('%H:%M UTC')}"
                self.send_message(test_msg)
                
                return True
            else:
                print(f"❌ Telegram bot connection failed")
                return False
                
        except Exception as e:
            print(f"❌ Telegram test error: {e}")
            return False
