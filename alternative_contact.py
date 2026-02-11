"""
Alternative Contact Methods
When email is not found on product page:
1. Search Google for company website
2. Scrape company contact page
3. Use Made-in-China "Chat Now" / "Send Inquiry" buttons
"""

import re
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict
import time

class AlternativeContactFinder:
    """Find vendor contact info through alternative methods"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def find_contact_email(self, vendor_name: str, product_url: str = None) -> Optional[str]:
        """
        Try multiple methods to find vendor email:
        1. Google search for company website
        2. Scrape company contact page
        3. Extract from Made-in-China vendor profile
        
        Returns email or None
        """
        print(f"\n  🔍 Searching for contact email: {vendor_name}")
        
        # Method 1: Google search for company website
        email = self._google_search_for_email(vendor_name)
        if email:
            print(f"  ✅ Found email via Google: {email}")
            return email
        
        # Method 2: Check Made-in-China vendor profile
        if product_url and 'made-in-china.com' in product_url:
            email = self._scrape_made_in_china_profile(product_url)
            if email:
                print(f"  ✅ Found email on Made-in-China profile: {email}")
                return email
        
        print(f"  ⚠️  No email found through alternative methods")
        return None
    
    def _google_search_for_email(self, vendor_name: str) -> Optional[str]:
        """
        Search Google for company website and extract email
        """
        try:
            # Clean vendor name for search
            search_query = f'"{vendor_name}" contact email'
            search_url = f"https://www.google.com/search?q={requests.utils.quote(search_query)}"
            
            response = requests.get(search_url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract search result snippets
            snippets = []
            for result in soup.select('.g'):
                text = result.get_text()
                snippets.append(text)
            
            # Look for emails in snippets
            email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            
            for snippet in snippets:
                emails = re.findall(email_pattern, snippet)
                for email in emails:
                    # Filter out junk emails
                    if not any(x in email.lower() for x in ['example', 'test', 'noreply', 'privacy', 'support@google']):
                        # Check if email domain matches vendor name
                        if self._email_matches_vendor(email, vendor_name):
                            return email
            
            # Try to find company website link
            for link in soup.select('a[href]'):
                href = link.get('href', '')
                if '/url?q=' in href:
                    url = href.split('/url?q=')[1].split('&')[0]
                    if 'contact' in url.lower() or 'about' in url.lower():
                        email = self._scrape_website_for_email(url, vendor_name)
                        if email:
                            return email
            
            return None
            
        except Exception as e:
            print(f"  ⚠️  Google search error: {str(e)[:100]}")
            return None
    
    def _scrape_website_for_email(self, url: str, vendor_name: str) -> Optional[str]:
        """Scrape a website contact page for email"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                return None
            
            # Look for emails in page content
            email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            emails = re.findall(email_pattern, response.text)
            
            for email in emails:
                if not any(x in email.lower() for x in ['example', 'test', 'noreply']):
                    if self._email_matches_vendor(email, vendor_name):
                        return email
            
            return None
            
        except Exception as e:
            return None
    
    def _scrape_made_in_china_profile(self, product_url: str) -> Optional[str]:
        """
        Scrape Made-in-China vendor profile page for contact email
        Product URL: https://vendor.en.made-in-china.com/product/xyz/...
        Profile URL: https://vendor.en.made-in-china.com/
        """
        try:
            # Extract vendor profile URL from product URL
            if '.en.made-in-china.com/product/' in product_url:
                vendor_profile = product_url.split('/product/')[0] + '/company-profile.html'
            else:
                return None
            
            print(f"    → Checking vendor profile: {vendor_profile[:60]}...")
            
            response = requests.get(vendor_profile, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for email in contact section
            email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            
            # Check contact info sections
            for selector in ['.contact-info', '.company-contact', '[class*="email"]', '[class*="contact"]']:
                elements = soup.select(selector)
                for elem in elements:
                    text = elem.get_text()
                    emails = re.findall(email_pattern, text)
                    if emails:
                        # Return first real email found
                        for email in emails:
                            if not any(x in email.lower() for x in ['example', 'test', 'noreply']):
                                return email
            
            # Check entire page as fallback
            emails = re.findall(email_pattern, response.text)
            for email in emails:
                if not any(x in email.lower() for x in ['example', 'test', 'noreply', 'privacy']):
                    # Check if email looks legitimate (not info@ or generic)
                    if '@' in email and '.' in email.split('@')[1]:
                        return email
            
            return None
            
        except Exception as e:
            print(f"    ⚠️  Profile scrape error: {str(e)[:100]}")
            return None
    
    def _email_matches_vendor(self, email: str, vendor_name: str) -> bool:
        """Check if email domain matches vendor name (suggests it's real)"""
        try:
            domain = email.split('@')[1].split('.')[0].lower()
            
            # Extract key parts from vendor name
            vendor_clean = ''.join(c.lower() for c in vendor_name if c.isalnum())
            
            # Extract meaningful words (3+ chars)
            vendor_parts = []
            for word in vendor_name.split():
                word_clean = ''.join(c.lower() for c in word if c.isalnum())
                if len(word_clean) >= 3 and word_clean not in ['shenzhen', 'guangzhou', 'beijing', 'china', 'limited', 'company', 'technology']:
                    vendor_parts.append(word_clean)
            
            # Check if domain contains any vendor part
            for part in vendor_parts:
                if part in domain or domain in part:
                    return True
            
            # Also check full vendor name (alphanumeric only)
            if len(vendor_clean) > 5:
                if vendor_clean[:8] in domain or domain in vendor_clean:
                    return True
            
            return False
            
        except:
            return False
    
    def get_made_in_china_inquiry_data(self, product_url: str) -> Dict:
        """
        Extract data needed to send inquiry via Made-in-China
        Returns dict with: vendor_profile_url, inquiry_form_url, product_id
        """
        try:
            if '.en.made-in-china.com/product/' not in product_url:
                return {}
            
            # Extract vendor and product ID
            parts = product_url.split('/')
            vendor_domain = product_url.split('.en.made-in-china.com')[0].replace('https://', '').replace('http://', '')
            
            # Find product ID (usually in URL)
            product_id = None
            for part in parts:
                if len(part) > 10 and not part.startswith('http'):
                    product_id = part
                    break
            
            return {
                'vendor_domain': vendor_domain,
                'product_id': product_id,
                'inquiry_url': product_url,
                'chat_now_available': True,  # Made-in-China has chat on most products
                'send_inquiry_available': True
            }
            
        except Exception as e:
            print(f"  ⚠️  Error parsing Made-in-China URL: {e}")
            return {}
    
    def send_made_in_china_inquiry(self, product_url: str, message: str = None) -> bool:
        """
        Attempt to send inquiry through Made-in-China
        NOTE: This may require selenium/playwright to click buttons
        Returns True if inquiry form URL found (actual sending would need automation)
        """
        inquiry_data = self.get_made_in_china_inquiry_data(product_url)
        
        if inquiry_data:
            print(f"  📝 Made-in-China inquiry available:")
            print(f"     Vendor: {inquiry_data.get('vendor_domain')}")
            print(f"     Product: {inquiry_data.get('product_id')}")
            print(f"     ℹ️  Manual action: Visit {product_url} and click 'Contact Supplier'")
            return True
        
        return False


# Example usage
if __name__ == "__main__":
    finder = AlternativeContactFinder()
    
    # Test with real vendor
    email = finder.find_contact_email(
        "Shenzhen HYY Technology Co., Ltd.",
        "https://we-signage.en.made-in-china.com/product/XdKtvOkDAGaE/China-Factory-..."
    )
    
    if email:
        print(f"\n✅ Found email: {email}")
    else:
        print(f"\n❌ No email found")
