"""
Daily Email Reporter - Sends comprehensive email reports of daily activities
"""

import sqlite3
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List
from config import VENDORS_DB

class DailyEmailReporter:
    """Sends daily email reports with vendor discoveries and activities"""
    
    def __init__(self, recipient_email: str, sender_email: str, sender_password: str):
        self.recipient_email = recipient_email
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.db_path = VENDORS_DB
    
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
            SELECT vendor_name, score, contact_email, product_description
            FROM vendors 
            WHERE discovered_date = ? AND score >= 70
            ORDER BY score DESC
        """, (today,))
        high_score_vendors = cursor.fetchall()
        
        # Medium-scoring vendors (50-69)
        cursor.execute("""
            SELECT vendor_name, score, contact_email
            FROM vendors 
            WHERE discovered_date = ? AND score >= 50 AND score < 70
            ORDER BY score DESC
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
    
    def generate_html_report(self, stats: Dict) -> str:
        """Generate HTML email report"""
        
        high_vendors_html = ""
        if stats["high_score_vendors"]:
            for vendor in stats["high_score_vendors"]:
                name, score, email, desc = vendor
                high_vendors_html += f"""
                <div style="margin: 10px 0; padding: 10px; background: #e8f5e9; border-left: 4px solid #4caf50;">
                    <strong>{name}</strong> - Score: {score}/100<br>
                    <small>Email: {email or 'Not found'}</small><br>
                    <small>Description: {desc[:200] if desc else 'N/A'}...</small>
                </div>
                """
        else:
            high_vendors_html = "<p><em>No high-scoring vendors found today.</em></p>"
        
        medium_vendors_html = ""
        if stats["medium_score_vendors"]:
            for vendor in stats["medium_score_vendors"][:5]:  # Show top 5
                name, score, email = vendor
                medium_vendors_html += f"""
                <div style="margin: 5px 0; padding: 8px; background: #fff3e0; border-left: 3px solid #ff9800;">
                    <strong>{name}</strong> - Score: {score}/100 | Email: {email or 'Not found'}
                </div>
                """
        else:
            medium_vendors_html = "<p><em>No medium-scoring vendors today.</em></p>"
        
        responses_html = ""
        if stats["vendors_with_responses"]:
            for resp in stats["vendors_with_responses"]:
                name, response_text, price, moq, resp_time = resp
                responses_html += f"""
                <div style="margin: 10px 0; padding: 10px; background: #e3f2fd; border-left: 4px solid #2196f3;">
                    <strong>{name}</strong><br>
                    <small>Response time: {resp_time:.1f if resp_time else 'N/A'} hours</small><br>
                    <small>Price: ${price if price else 'Not quoted'} | MOQ: {moq if moq else 'Not quoted'}</small><br>
                    <small>Response: {response_text[:150] if response_text else 'N/A'}...</small>
                </div>
                """
        else:
            responses_html = "<p><em>No responses received today.</em></p>"
        
        keywords_html = ", ".join(stats["keywords_used"][:15]) if stats["keywords_used"] else "None"
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background: #1976d2; color: white; padding: 20px; text-align: center; }}
                .section {{ margin: 20px 0; padding: 15px; background: #f5f5f5; border-radius: 5px; }}
                .stats {{ display: inline-block; margin: 10px; padding: 15px; background: white; border-radius: 5px; }}
                .footer {{ margin-top: 30px; padding: 15px; background: #f5f5f5; text-align: center; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🤖 AI Sourcing Agent - Daily Report</h1>
                <p>{datetime.now().strftime('%B %d, %Y')}</p>
            </div>
            
            <div class="section">
                <h2>📊 Today's Summary</h2>
                <div class="stats">
                    <strong>Vendors Discovered:</strong> {stats["total_discovered"]}
                </div>
                <div class="stats">
                    <strong>Emails Sent:</strong> {stats["emails_sent"]}
                </div>
                <div class="stats">
                    <strong>Replies Received:</strong> {stats["replies_received"]}
                </div>
            </div>
            
            <div class="section">
                <h2>⭐ High-Priority Vendors (Score ≥ 70)</h2>
                {high_vendors_html}
            </div>
            
            <div class="section">
                <h2>📋 Medium-Priority Vendors (Score 50-69)</h2>
                {medium_vendors_html}
            </div>
            
            <div class="section">
                <h2>💬 Vendor Responses Received</h2>
                {responses_html}
            </div>
            
            <div class="section">
                <h2>🔍 Search Keywords Used</h2>
                <p>{keywords_html}</p>
            </div>
            
            <div class="footer">
                <p>This is an automated report from your AI Sourcing Agent.</p>
                <p>Database: {self.db_path}</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def send_report(self) -> bool:
        """Collect stats and send email report"""
        
        try:
            # Collect stats
            stats = self.collect_daily_stats()
            
            # Generate HTML
            html_content = self.generate_html_report(stats)
            
            # Create email
            msg = MIMEMultipart('alternative')
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            msg['Subject'] = f"AI Sourcing Report - {datetime.now().strftime('%b %d, %Y')} - {stats['total_discovered']} Vendors Found"
            
            # Attach HTML
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
            server.quit()
            
            print(f"✅ Daily report sent to {self.recipient_email}")
            return True
            
        except Exception as e:
            print(f"❌ Error sending daily report: {e}")
            return False
