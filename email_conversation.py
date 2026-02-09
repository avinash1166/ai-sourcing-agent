"""
Email Conversation Manager - Handles multi-turn conversations with vendors
Monitors inbox, processes replies, and sends intelligent follow-ups
"""

import imaplib
import email
from email.header import decode_header
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import sqlite3
import re
from typing import List, Dict, Optional
from config import VENDORS_DB, OLLAMA_MODEL
from langchain_ollama import OllamaLLM

class EmailConversationManager:
    """Manages ongoing email conversations with vendors"""
    
    def __init__(self, email_address: str, email_password: str, smtp_server: str = "smtp.gmail.com", imap_server: str = "imap.gmail.com"):
        self.email_address = email_address
        self.email_password = email_password
        self.smtp_server = smtp_server
        self.smtp_port = 587
        self.imap_server = imap_server
        self.imap_port = 993
        self.db_path = VENDORS_DB
        self.llm = OllamaLLM(model=OLLAMA_MODEL, temperature=0.4)
    
    def check_for_replies(self, days_back: int = 7) -> List[Dict]:
        """Check email inbox for vendor replies"""
        replies = []
        
        try:
            # Connect to IMAP
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.email_address, self.email_password)
            mail.select("inbox")
            
            # Search for emails from last X days
            since_date = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
            status, messages = mail.search(None, f'(SINCE {since_date})')
            
            if status != "OK":
                return replies
            
            email_ids = messages[0].split()
            
            # Process each email
            for email_id in email_ids[-50:]:  # Process last 50 emails max
                status, msg_data = mail.fetch(email_id, "(RFC822)")
                
                if status != "OK":
                    continue
                
                # Parse email
                msg = email.message_from_bytes(msg_data[0][1])
                
                # Decode subject
                subject = decode_header(msg["Subject"])[0][0]
                if isinstance(subject, bytes):
                    subject = subject.decode()
                
                # Get sender
                from_email = msg.get("From", "")
                
                # Get date
                date_str = msg.get("Date", "")
                
                # Extract body
                body = self._get_email_body(msg)
                
                # Check if this is a reply to our vendor inquiry
                if self._is_vendor_reply(subject, body):
                    replies.append({
                        "from": from_email,
                        "subject": subject,
                        "body": body,
                        "date": date_str,
                        "email_id": email_id.decode()
                    })
            
            mail.close()
            mail.logout()
            
        except Exception as e:
            print(f"Error checking emails: {e}")
        
        return replies
    
    def _get_email_body(self, msg) -> str:
        """Extract email body from email message"""
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    try:
                        body = part.get_payload(decode=True).decode()
                        break
                    except:
                        pass
        else:
            try:
                body = msg.get_payload(decode=True).decode()
            except:
                pass
        
        return body
    
    def _is_vendor_reply(self, subject: str, body: str) -> bool:
        """Check if email is a vendor reply to our inquiry"""
        # Check for keywords that indicate vendor reply
        vendor_keywords = [
            "inquiry", "quote", "quotation", "moq", "price", "specification",
            "product", "manufacturer", "oem", "odm", "tablet", "touchscreen",
            "android", "display"
        ]
        
        text = f"{subject} {body}".lower()
        
        # Must contain at least 2 vendor-related keywords
        keyword_count = sum(1 for kw in vendor_keywords if kw in text)
        
        return keyword_count >= 2
    
    def process_reply(self, reply: Dict) -> Dict:
        """Process vendor reply and extract key information"""
        body = reply["body"]
        from_email = reply["from"]
        
        # Use LLM to extract structured information
        prompt = f"""Analyze this vendor email reply and extract key information in JSON format.

EMAIL FROM: {from_email}
EMAIL BODY:
{body}

Extract the following information (use null if not mentioned):
1. price_quoted: Price per unit (number only, in USD if possible)
2. moq: Minimum Order Quantity (number only)
3. customization_available: Can they customize? (yes/no/unclear)
4. lead_time_days: Production lead time (number of days, or null)
5. interested: Are they interested in our business? (yes/no/unclear)
6. next_steps: What do they want us to do next? (brief text)
7. sentiment: Overall tone (positive/neutral/negative)

Output ONLY valid JSON, nothing else:
"""
        
        try:
            response = self.llm.invoke(prompt)
            
            # Try to parse JSON from response
            import json
            # Clean response - extract JSON if wrapped in markdown
            clean_response = response.strip()
            if "```json" in clean_response:
                clean_response = clean_response.split("```json")[1].split("```")[0]
            elif "```" in clean_response:
                clean_response = clean_response.split("```")[1].split("```")[0]
            
            extracted = json.loads(clean_response)
            
            return {
                "from_email": from_email,
                "extracted_data": extracted,
                "raw_body": body,
                "processed_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error processing reply: {e}")
            return {
                "from_email": from_email,
                "extracted_data": {},
                "raw_body": body,
                "error": str(e)
            }
    
    def generate_follow_up(self, vendor_name: str, previous_conversation: str, extracted_data: Dict) -> str:
        """Generate intelligent follow-up email based on vendor's reply"""
        
        prompt = f"""You are writing a follow-up email to a vendor. Be professional, concise, and focused.

VENDOR: {vendor_name}

THEIR PREVIOUS REPLY DATA:
- Price quoted: {extracted_data.get('price_quoted', 'Not mentioned')}
- MOQ: {extracted_data.get('moq', 'Not mentioned')}
- Customization: {extracted_data.get('customization_available', 'Not mentioned')}
- Lead time: {extracted_data.get('lead_time_days', 'Not mentioned')}
- Their sentiment: {extracted_data.get('sentiment', 'neutral')}

PREVIOUS CONVERSATION:
{previous_conversation[:500]}

TASK: Write a brief follow-up email (3-5 sentences) that:
1. Thanks them for their response
2. Asks for ANY missing critical information (price, MOQ, customization, lead time)
3. If all info is provided and good, express interest in next steps
4. If pricing/MOQ is out of range, politely decline

Output ONLY the email body, no subject line:
"""
        
        try:
            follow_up = self.llm.invoke(prompt)
            return follow_up.strip()
        except Exception as e:
            print(f"Error generating follow-up: {e}")
            return ""
    
    def send_follow_up(self, to_email: str, subject: str, body: str) -> bool:
        """Send follow-up email to vendor"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_address
            msg['To'] = to_email
            msg['Subject'] = f"Re: {subject}"
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_address, self.email_password)
            server.send_message(msg)
            server.quit()
            
            return True
            
        except Exception as e:
            print(f"Error sending follow-up: {e}")
            return False
    
    def update_vendor_with_reply(self, vendor_name: str, reply_data: Dict):
        """Update vendor database with reply information"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        import json
        extracted = reply_data.get('extracted_data', {})
        
        # Calculate response time
        cursor.execute("""
            SELECT last_email_date FROM vendors 
            WHERE vendor_name = ?
            ORDER BY discovered_date DESC LIMIT 1
        """, (vendor_name,))
        
        result = cursor.fetchone()
        response_time_hours = None
        
        if result and result[0]:
            last_email = datetime.strptime(result[0], '%Y-%m-%d')
            response_time_hours = (datetime.now() - last_email).total_seconds() / 3600
        
        # Update vendor record
        cursor.execute("""
            UPDATE vendors 
            SET email_response = ?,
                price_quoted = ?,
                moq_quoted = ?,
                customization_confirmed = ?,
                response_time_hours = ?,
                last_response_date = ?
            WHERE vendor_name = ?
        """, (
            reply_data.get('raw_body', '')[:1000],
            extracted.get('price_quoted'),
            extracted.get('moq'),
            extracted.get('customization_available'),
            response_time_hours,
            datetime.now().strftime('%Y-%m-%d'),
            vendor_name
        ))
        
        conn.commit()
        conn.close()
    
    def run_conversation_loop(self) -> Dict:
        """Main loop: Check for replies, process them, send follow-ups"""
        
        print("Checking for vendor replies...")
        replies = self.check_for_replies(days_back=7)
        
        results = {
            "replies_found": len(replies),
            "processed": 0,
            "follow_ups_sent": 0,
            "errors": []
        }
        
        for reply in replies:
            try:
                # Extract vendor name from email or subject
                vendor_name = self._extract_vendor_name(reply['from'], reply['subject'])
                
                if not vendor_name:
                    continue
                
                # Process the reply
                processed = self.process_reply(reply)
                
                # Update database
                self.update_vendor_with_reply(vendor_name, processed)
                results["processed"] += 1
                
                # Check if we should send follow-up
                extracted = processed.get('extracted_data', {})
                
                # Send follow-up if:
                # 1. They're interested
                # 2. Missing critical info
                # 3. Price/MOQ is acceptable
                
                should_follow_up = (
                    extracted.get('interested') != 'no' and
                    extracted.get('sentiment') != 'negative'
                )
                
                if should_follow_up:
                    follow_up_body = self.generate_follow_up(
                        vendor_name,
                        reply['body'],
                        extracted
                    )
                    
                    if follow_up_body:
                        # Extract email address
                        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', reply['from'])
                        if email_match:
                            to_email = email_match.group(0)
                            
                            sent = self.send_follow_up(
                                to_email,
                                reply['subject'],
                                follow_up_body
                            )
                            
                            if sent:
                                results["follow_ups_sent"] += 1
                                
                                # Update email count in DB
                                self._increment_email_count(vendor_name)
                
            except Exception as e:
                results["errors"].append(str(e))
                print(f"Error processing reply: {e}")
        
        return results
    
    def _extract_vendor_name(self, from_email: str, subject: str) -> Optional[str]:
        """Extract vendor name from email address or subject"""
        # Try to get domain name as vendor name
        email_match = re.search(r'@([\w\.-]+)\.\w+', from_email)
        if email_match:
            domain = email_match.group(1)
            # Clean up common email domains
            if domain not in ['gmail', 'yahoo', 'outlook', 'hotmail']:
                return domain.replace('-', ' ').replace('_', ' ').title()
        
        # Try to extract from subject
        # Look for company names (capitalized words)
        words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', subject)
        if words:
            return words[0]
        
        return None
    
    def _increment_email_count(self, vendor_name: str):
        """Increment email sent count for vendor"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE vendors 
            SET email_sent_count = email_sent_count + 1,
                last_email_date = ?
            WHERE vendor_name = ?
        """, (datetime.now().strftime('%Y-%m-%d'), vendor_name))
        
        conn.commit()
        conn.close()
