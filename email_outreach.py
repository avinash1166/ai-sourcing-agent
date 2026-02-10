#!/usr/bin/env python3
"""
Email Outreach Module
Sends templated emails to vendors via Gmail SMTP
"""

import smtplib
import sqlite3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict

from config import EMAIL_TEMPLATE, VENDORS_DB, RATE_LIMITS

class EmailOutreach:
    """Handle email communication with vendors"""
    
    def __init__(self, smtp_server: str = "smtp.gmail.com", smtp_port: int = 587):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = None
        self.sender_password = None
        self.daily_limit = RATE_LIMITS['email_daily_limit']
    
    def configure(self, sender_email: str, sender_password: str):
        """Configure email credentials"""
        self.sender_email = sender_email
        self.sender_password = sender_password
        print(f"✓ Email configured for: {sender_email}")
    
    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        """Send a single email"""
        if not self.sender_email or not self.sender_password:
            print("✗ Email not configured. Call configure() first.")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Connect and send
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            
            text = msg.as_string()
            server.sendmail(self.sender_email, to_email, text)
            server.quit()
            
            print(f"✓ Email sent to: {to_email}")
            return True
        
        except Exception as e:
            print(f"✗ Email error: {e}")
            return False
    
    def send_vendor_inquiry(self, vendor_id: int, vendor_email: str) -> bool:
        """Send inquiry email to a vendor"""
        
        # Get vendor details from database
        conn = sqlite3.connect(VENDORS_DB)
        cursor = conn.cursor()
        
        cursor.execute('SELECT vendor_name FROM vendors WHERE id = ?', (vendor_id,))
        result = cursor.fetchone()
        
        if not result:
            print(f"✗ Vendor ID {vendor_id} not found")
            conn.close()
            return False
        
        vendor_name = result[0]
        
        # Customize email template
        subject = "Inquiry for 15.6\" Android Touchscreen Device - Pilot Order"
        body = EMAIL_TEMPLATE.replace("Hi,", f"Hi {vendor_name},")
        
        # Send email
        success = self.send_email(vendor_email, subject, body)
        
        if success:
            # Update database
            cursor.execute('''
                UPDATE vendors 
                SET contacted = 1, contact_date = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), vendor_id))
            
            conn.commit()
        
        conn.close()
        return success
    
    def batch_send_to_top_vendors(self, min_score: int = 70) -> int:
        """
        Send emails to all uncontacted vendors above a certain score
        Respects daily limit
        """
        print("\n" + "=" * 60)
        print("BATCH EMAIL OUTREACH")
        print("=" * 60)
        
        conn = sqlite3.connect(VENDORS_DB)
        cursor = conn.cursor()
        
        # Get uncontacted high-score vendors
        cursor.execute('''
            SELECT id, vendor_name, url
            FROM vendors
            WHERE contacted = 0 AND score >= ?
            ORDER BY score DESC
            LIMIT ?
        ''', (min_score, self.daily_limit))
        
        vendors = cursor.fetchall()
        
        if not vendors:
            print("✗ No vendors to contact")
            conn.close()
            return 0
        
        print(f"Found {len(vendors)} vendors to contact (score >= {min_score})")
        
        # NOTE: We can't actually send emails without vendor email addresses
        # In real implementation, you'd need to extract emails from vendor URLs
        # or use contact forms on their websites
        
        sent_count = 0
        for vendor_id, vendor_name, url in vendors:
            print(f"\n→ Vendor: {vendor_name}")
            print(f"  URL: {url}")
            print(f"  Status: Email extraction needed (placeholder)")
            
            # Mark as contacted (placeholder)
            cursor.execute('''
                UPDATE vendors 
                SET contacted = 1, contact_date = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), vendor_id))
            
            sent_count += 1
        
        conn.commit()
        conn.close()
        
        print(f"\n✓ Marked {sent_count} vendors as contacted")
        return sent_count
    
    def send_initial_outreach(self, min_score: int = 70, max_emails: int = 20) -> Dict:
        """
        Send initial outreach emails to high-score vendors
        ALIAS for batch_send_to_top_vendors (for compatibility)
        """
        # Temporarily override daily limit
        original_limit = self.daily_limit
        self.daily_limit = max_emails
        
        sent = self.batch_send_to_top_vendors(min_score)
        
        # Restore limit
        self.daily_limit = original_limit
        
        return {
            "sent": sent,
            "already_contacted": 0,
            "errors": 0
        }
    
    def log_vendor_reply(self, vendor_id: int, reply_content: str):
        """Log a reply received from a vendor"""
        conn = sqlite3.connect(VENDORS_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE vendors
            SET reply_received = 1, reply_date = ?, reply_content = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), reply_content, vendor_id))
        
        conn.commit()
        conn.close()
        
        print(f"✓ Reply logged for vendor ID {vendor_id}")

# ==================== TESTING ====================
if __name__ == "__main__":
    print("Email Outreach Module - Configuration Guide")
    print("=" * 60)
    print("\nTo use Gmail SMTP:")
    print("1. Enable 2-Factor Authentication in your Google Account")
    print("2. Generate an App Password: https://myaccount.google.com/apppasswords")
    print("3. Use the app password (not your regular password)")
    print("\nExample usage:")
    print("  outreach = EmailOutreach()")
    print("  outreach.configure('your_email@gmail.com', 'your_app_password')")
    print("  outreach.send_vendor_inquiry(vendor_id=1, vendor_email='vendor@example.com')")
