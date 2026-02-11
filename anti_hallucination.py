#!/usr/bin/env python3
"""
Anti-Hallucination System with Human Feedback Loop
Prevents dummy data, tracks agent performance with points system
"""

import re
import json
from typing import Dict, Any, Tuple, List
from datetime import datetime

class DataQualityChecker:
    """Detects fake/placeholder/hallucinated data"""
    
    # Known placeholder patterns that LLMs use
    PLACEHOLDER_PATTERNS = {
        'email': [
            r'^sales@company\.com$',
            r'^info@company\.com$',
            r'^contact@company\.com$',
            r'^example@example\.com$',
            r'^vendor@vendor\.com$',
            r'^email@email\.com$',
        ],
        'url': [
            r'^product-page-url',
            r'^company-website$',
            r'^http://example\.com',
            r'^www\.example\.com',
            r'^vendor-website',
            r'^.*placeholder.*',
        ],
        'price': [
            125.5,  # Suspiciously common placeholder
            100.0,
            99.99,
        ],
        'vendor_name': [
            r'^Company Name$',
            r'^Vendor Name$',
            r'^Unknown',
        ]
    }
    
    # Patterns that indicate real data
    REAL_DATA_PATTERNS = {
        'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'url': r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        'chinese_company': r'(Shenzhen|Guangzhou|Dongguan|Foshan|Beijing|Shanghai).+(Co\.|Ltd\.|Technology|Electronics|Display)',
    }
    
    @staticmethod
    def is_placeholder_email(email: str, vendor_name: str = None) -> Tuple[bool, str]:
        """Check if email is a placeholder or fabricated from vendor name"""
        if not email or email == "null" or email == "None":
            return True, "Email is null/None"
        
        # Check known placeholder patterns
        for pattern in DataQualityChecker.PLACEHOLDER_PATTERNS['email']:
            if re.match(pattern, email, re.IGNORECASE):
                return True, f"Placeholder email pattern: {email}"
        
        # NEW: Check if email was fabricated from vendor name
        # Example: "Shenzhen HYY Technology" -> sales@shenzhyy.com or sales@hyytech.com
        if vendor_name and '@' in email:
            email_local = email.split('@')[0].lower()  # "sales", "contact", "info"
            email_domain = email.split('@')[1].split('.')[0].lower()  # "shenzhyy", "hyytech"
            
            # Only flag as fake if email uses generic prefix (sales/info/contact)
            # AND domain was likely derived from vendor name
            if email_local in ['sales', 'info', 'contact', 'inquiry', 'service', 'support']:
                # Extract alphanumeric characters from vendor name
                vendor_clean = ''.join(c.lower() for c in vendor_name if c.isalnum())
                
                # Check if domain contains significant parts of vendor name
                # "shenzhyy" contains "hyy" from "HYY Technology"
                # "hyytech" contains "hyy" and "tech" from "HYY Technology"
                
                # Extract meaningful parts (3+ chars) from vendor name
                vendor_parts = []
                for word in vendor_name.split():
                    word_clean = ''.join(c.lower() for c in word if c.isalnum())
                    if len(word_clean) >= 3 and word_clean not in ['shenzhen', 'guangzhou', 'beijing', 'shanghai', 'china', 'technology', 'electronics', 'limited', 'company']:
                        vendor_parts.append(word_clean)
                
                # If domain contains ANY vendor part AND uses generic prefix, it's likely fake
                for part in vendor_parts:
                    if part in email_domain or email_domain in part:
                        return True, f"Email likely fabricated: generic {email_local}@ + domain '{email_domain}' derived from vendor name part '{part}'"
        
        return False, "Email appears real"
    
    @staticmethod
    def is_placeholder_url(url: str) -> Tuple[bool, str]:
        """Check if URL is a placeholder"""
        if not url or url == "null" or url == "None":
            return True, "URL is null/None"
        
        for pattern in DataQualityChecker.PLACEHOLDER_PATTERNS['url']:
            if re.match(pattern, url, re.IGNORECASE):
                return True, f"Placeholder URL pattern: {url}"
        
        # Check if it's a real URL
        if not re.match(DataQualityChecker.REAL_DATA_PATTERNS['url'], url):
            return True, "URL doesn't match real URL format"
        
        return False, "URL appears real"
    
    @staticmethod
    def is_placeholder_price(price: float) -> Tuple[bool, str]:
        """Check if price is a placeholder"""
        if price is None:
            return True, "Price is None"
        
        # Check for common placeholder prices
        if price in DataQualityChecker.PLACEHOLDER_PATTERNS['price']:
            return True, f"Suspicious placeholder price: ${price}"
        
        # Prices that are too round might be placeholders
        if price > 50 and price % 50 == 0:  # $50, $100, $150, etc.
            return True, f"Suspiciously round price: ${price}"
        
        return False, "Price appears real"
    
    @staticmethod
    def is_generic_vendor_name(name: str) -> Tuple[bool, str]:
        """Check if vendor name is generic/placeholder"""
        if not name or name == "null" or name == "None":
            return True, "Vendor name is null/None"
        
        for pattern in DataQualityChecker.PLACEHOLDER_PATTERNS['vendor_name']:
            if re.match(pattern, name, re.IGNORECASE):
                return True, f"Generic vendor name: {name}"
        
        # Check if it looks like a real Chinese company
        if re.search(DataQualityChecker.REAL_DATA_PATTERNS['chinese_company'], name):
            return False, "Vendor name matches Chinese company pattern"
        
        # Too short names are suspicious
        if len(name) < 10:
            return True, f"Vendor name too short: {name}"
        
        return False, "Vendor name appears real"
    
    @staticmethod
    def check_data_uniqueness(data: Dict[str, Any], historical_data: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """Check if this data is unique (not a duplicate hallucination)"""
        
        # If we see the same email for multiple vendors, it's likely hallucinated
        current_email = data.get('contact_email')
        if current_email:
            email_count = sum(1 for h in historical_data if h.get('contact_email') == current_email)
            if email_count > 3:  # Same email for 3+ vendors = suspicious
                return False, f"Email '{current_email}' appears in {email_count} vendors (likely hallucinated)"
        
        # If we see the same price for multiple vendors, suspicious
        current_price = data.get('price_per_unit')
        if current_price:
            price_count = sum(1 for h in historical_data 
                            if h.get('price_per_unit') == current_price)
            if price_count > 5:  # Same exact price for 5+ vendors = suspicious
                return False, f"Price ${current_price} appears in {price_count} vendors (likely hallucinated)"
        
        # If vendor name + product URL combo exists, it's a duplicate
        vendor_name = data.get('vendor_name')
        product_url = data.get('product_url')
        if vendor_name and product_url:
            for h in historical_data:
                if (h.get('vendor_name') == vendor_name and 
                    h.get('product_url') == product_url):
                    return False, f"Duplicate: {vendor_name} + {product_url}"
        
        return True, "Data appears unique"
    
    @staticmethod
    def validate_extraction_quality(data: Dict[str, Any], 
                                    historical_data: List[Dict[str, Any]] = None) -> Tuple[bool, List[str], float]:
        """
        Comprehensive quality check on extracted data
        
        Returns:
            (passed: bool, issues: List[str], confidence: float)
        """
        issues = []
        confidence = 1.0
        
        # Check email with vendor name context
        is_placeholder, reason = DataQualityChecker.is_placeholder_email(
            data.get('contact_email'),
            data.get('vendor_name')
        )
        if is_placeholder:
            issues.append(f"❌ Email: {reason}")
            confidence -= 0.3
        
        # Check URL
        is_placeholder, reason = DataQualityChecker.is_placeholder_url(data.get('product_url'))
        if is_placeholder:
            issues.append(f"❌ Product URL: {reason}")
            confidence -= 0.3
        
        # Check vendor URL
        is_placeholder, reason = DataQualityChecker.is_placeholder_url(data.get('url'))
        if is_placeholder:
            issues.append(f"❌ Vendor URL: {reason}")
            confidence -= 0.2
        
        # Check price
        is_placeholder, reason = DataQualityChecker.is_placeholder_price(data.get('price_per_unit'))
        if is_placeholder:
            issues.append(f"❌ Price: {reason}")
            confidence -= 0.2
        
        # Check vendor name
        is_generic, reason = DataQualityChecker.is_generic_vendor_name(data.get('vendor_name'))
        if is_generic:
            issues.append(f"❌ Vendor name: {reason}")
            confidence -= 0.3
        
        # Check uniqueness against historical data
        if historical_data:
            is_unique, reason = DataQualityChecker.check_data_uniqueness(data, historical_data)
            if not is_unique:
                issues.append(f"❌ Uniqueness: {reason}")
                confidence -= 0.4
        
        # Confidence can't be negative
        confidence = max(0.0, confidence)
        
        # Pass if confidence > 0.5 (more than half the checks passed)
        passed = confidence > 0.5 and len(issues) < 3
        
        return passed, issues, confidence


class AgentPerformanceTracker:
    """
    Tracks agent performance with points system (dopamine-like reward)
    Agent gains/loses points based on data quality and human feedback
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.current_score = 100  # Start at 100 points
        self.session_stats = {
            'extractions': 0,
            'hallucinations_detected': 0,
            'validations_passed': 0,
            'validations_failed': 0,
            'human_feedback_relevant': 0,
            'human_feedback_irrelevant': 0,
        }
    
    def award_points(self, amount: int, reason: str):
        """Award points for good performance"""
        self.current_score += amount
        print(f"  🎉 +{amount} points: {reason} (Total: {self.current_score})")
    
    def deduct_points(self, amount: int, reason: str):
        """Deduct points for bad performance"""
        self.current_score -= amount
        print(f"  ⚠️  -{amount} points: {reason} (Total: {self.current_score})")
    
    def record_extraction(self, success: bool, quality_score: float):
        """Record an extraction attempt"""
        self.session_stats['extractions'] += 1
        
        if success and quality_score > 0.8:
            self.award_points(10, "High-quality extraction")
            self.session_stats['validations_passed'] += 1
        elif success and quality_score > 0.5:
            self.award_points(5, "Acceptable extraction")
            self.session_stats['validations_passed'] += 1
        else:
            self.deduct_points(5, "Poor quality extraction")
            self.session_stats['validations_failed'] += 1
    
    def record_hallucination(self, severity: str):
        """Record a hallucination detection"""
        self.session_stats['hallucinations_detected'] += 1
        
        penalties = {
            'minor': 3,
            'major': 10,
            'critical': 20
        }
        penalty = penalties.get(severity, 5)
        self.deduct_points(penalty, f"{severity.upper()} hallucination detected")
    
    def record_human_feedback(self, relevant: bool, vendor_name: str):
        """Record human feedback on vendor relevance"""
        if relevant:
            self.session_stats['human_feedback_relevant'] += 1
            self.award_points(15, f"Vendor '{vendor_name}' marked RELEVANT by human")
        else:
            self.session_stats['human_feedback_irrelevant'] += 1
            self.deduct_points(10, f"Vendor '{vendor_name}' marked IRRELEVANT by human")
    
    def get_performance_report(self) -> str:
        """Generate performance report"""
        total_validations = (self.session_stats['validations_passed'] + 
                           self.session_stats['validations_failed'])
        
        if total_validations > 0:
            success_rate = (self.session_stats['validations_passed'] / total_validations) * 100
        else:
            success_rate = 0
        
        report = f"""
╔════════════════════════════════════════╗
║     AGENT PERFORMANCE REPORT           ║
╚════════════════════════════════════════╝

🎯 Current Score: {self.current_score} points
📊 Extraction Success Rate: {success_rate:.1f}%

Session Stats:
  • Total Extractions: {self.session_stats['extractions']}
  • Passed Validation: {self.session_stats['validations_passed']}
  • Failed Validation: {self.session_stats['validations_failed']}
  • Hallucinations Caught: {self.session_stats['hallucinations_detected']}
  • Human Feedback (Relevant): {self.session_stats['human_feedback_relevant']}
  • Human Feedback (Irrelevant): {self.session_stats['human_feedback_irrelevant']}

Performance Grade: {self._get_grade()}
        """
        return report
    
    def _get_grade(self) -> str:
        """Get letter grade based on score"""
        if self.current_score >= 150:
            return "A+ (Excellent) 🌟"
        elif self.current_score >= 120:
            return "A (Great) ⭐"
        elif self.current_score >= 100:
            return "B (Good) ✓"
        elif self.current_score >= 80:
            return "C (Needs Improvement) ⚠️"
        else:
            return "F (Critical Issues) ❌"


def extract_real_email_from_text(text: str, vendor_name: str = None) -> str:
    """
    Aggressively extract email from raw text
    Look for actual emails, not placeholders
    """
    # Find all email patterns
    email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
    emails = re.findall(email_pattern, text)
    
    if not emails:
        return None
    
    # Filter out placeholder emails
    real_emails = []
    for email in emails:
        is_placeholder, _ = DataQualityChecker.is_placeholder_email(email)
        if not is_placeholder:
            real_emails.append(email)
    
    if not real_emails:
        return None
    
    # Prefer emails that match vendor name domain
    if vendor_name:
        vendor_domain = vendor_name.lower().replace(' ', '').replace(',', '')
        for email in real_emails:
            email_domain = email.split('@')[1].split('.')[0]
            if vendor_domain in email_domain or email_domain in vendor_domain:
                return email
    
    # Return first real email found
    return real_emails[0]


def extract_real_urls_from_text(text: str) -> Dict[str, str]:
    """
    Extract real URLs from text (vendor page, product page)
    """
    # Find all URL patterns
    url_pattern = r'https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}[^\s]*'
    urls = re.findall(url_pattern, text)
    
    if not urls:
        return {'vendor_url': None, 'product_url': None}
    
    # Filter out placeholder URLs
    real_urls = []
    for url in urls:
        is_placeholder, _ = DataQualityChecker.is_placeholder_url(url)
        if not is_placeholder:
            real_urls.append(url)
    
    if not real_urls:
        return {'vendor_url': None, 'product_url': None}
    
    # Try to distinguish vendor page from product page
    vendor_url = None
    product_url = None
    
    for url in real_urls:
        # Product pages usually have longer paths or 'product' in URL
        if '/product' in url.lower() or '/item' in url.lower() or len(url.split('/')) > 4:
            product_url = url
        else:
            vendor_url = url
    
    # If we didn't find distinct URLs, use first URL for both
    if not vendor_url and real_urls:
        vendor_url = real_urls[0]
    if not product_url and real_urls:
        product_url = real_urls[-1]  # Use last URL as product
    
    return {
        'vendor_url': vendor_url,
        'product_url': product_url
    }
