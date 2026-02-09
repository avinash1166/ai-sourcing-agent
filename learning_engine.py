"""
Learning Engine - Self-improving AI that learns from past vendor interactions
Analyzes historical data to improve keyword generation and search strategies
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Set
from collections import Counter
import re
from config import VENDORS_DB, DATA_DIR, OLLAMA_MODEL
from langchain_ollama import OllamaLLM

class LearningEngine:
    """Self-learning system that improves search strategies over time"""
    
    def __init__(self):
        self.db_path = VENDORS_DB
        self.llm = OllamaLLM(model=OLLAMA_MODEL, temperature=0.3)
        
    def analyze_successful_vendors(self, days_back: int = 30) -> Dict:
        """Analyze vendors that scored well to learn patterns"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get high-scoring vendors from past X days
        cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        cursor.execute("""
            SELECT vendor_name, product_description, keywords_used, score, 
                   email_response, response_time_hours
            FROM vendors 
            WHERE score >= 70 
            AND discovered_date >= ?
            ORDER BY score DESC
        """, (cutoff_date,))
        
        successful_vendors = cursor.fetchall()
        conn.close()
        
        if not successful_vendors:
            return {
                "keywords": set(),
                "description_patterns": [],
                "avg_response_time": 0,
                "success_count": 0
            }
        
        # Extract patterns
        all_keywords = []
        descriptions = []
        response_times = []
        
        for vendor in successful_vendors:
            name, desc, keywords, score, response, response_time = vendor
            
            if keywords:
                all_keywords.extend(json.loads(keywords) if isinstance(keywords, str) else keywords)
            
            if desc:
                descriptions.append(desc)
            
            if response_time:
                response_times.append(response_time)
        
        # Find common keywords in successful searches
        keyword_freq = Counter(all_keywords)
        top_keywords = set([kw for kw, count in keyword_freq.most_common(20)])
        
        # Extract description patterns (common words/phrases)
        description_patterns = self._extract_patterns_from_descriptions(descriptions)
        
        return {
            "keywords": top_keywords,
            "description_patterns": description_patterns,
            "avg_response_time": sum(response_times) / len(response_times) if response_times else 0,
            "success_count": len(successful_vendors)
        }
    
    def analyze_failed_vendors(self, days_back: int = 30) -> Dict:
        """Analyze vendors that scored poorly to learn what to avoid"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        cursor.execute("""
            SELECT vendor_name, product_description, keywords_used, score, rejection_reason
            FROM vendors 
            WHERE score < 40 OR validation_status = 'rejected'
            AND discovered_date >= ?
        """, (cutoff_date,))
        
        failed_vendors = cursor.fetchall()
        conn.close()
        
        if not failed_vendors:
            return {
                "avoid_keywords": set(),
                "red_flag_patterns": [],
                "failure_count": 0
            }
        
        # Extract anti-patterns
        avoid_keywords = []
        rejection_reasons = []
        
        for vendor in failed_vendors:
            name, desc, keywords, score, rejection = vendor
            
            if keywords:
                avoid_keywords.extend(json.loads(keywords) if isinstance(keywords, str) else keywords)
            
            if rejection:
                rejection_reasons.append(rejection)
        
        keyword_freq = Counter(avoid_keywords)
        avoid_kw_set = set([kw for kw, count in keyword_freq.most_common(10)])
        
        return {
            "avoid_keywords": avoid_kw_set,
            "red_flag_patterns": rejection_reasons,
            "failure_count": len(failed_vendors)
        }
    
    def _extract_patterns_from_descriptions(self, descriptions: List[str]) -> List[str]:
        """Extract common phrases/terms from successful vendor descriptions"""
        if not descriptions:
            return []
        
        # Combine all descriptions
        combined = " ".join(descriptions).lower()
        
        # Extract common 2-3 word phrases
        words = re.findall(r'\b[a-z]{3,}\b', combined)
        
        # Find bigrams and trigrams
        bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words)-1)]
        trigrams = [f"{words[i]} {words[i+1]} {words[i+2]}" for i in range(len(words)-2)]
        
        # Get most common patterns
        bigram_freq = Counter(bigrams)
        trigram_freq = Counter(trigrams)
        
        patterns = []
        patterns.extend([bg for bg, count in bigram_freq.most_common(10) if count >= 2])
        patterns.extend([tg for tg, count in trigram_freq.most_common(5) if count >= 2])
        
        return patterns
    
    def generate_new_keywords(self, base_keywords: List[str]) -> List[str]:
        """Use LLM to generate new search keywords based on learning"""
        
        # Get historical data
        success_data = self.analyze_successful_vendors(days_back=30)
        failure_data = self.analyze_failed_vendors(days_back=30)
        
        # Build learning context
        prompt = f"""You are a search keyword optimization expert. Based on historical vendor search data, generate NEW search keywords for finding OEM/ODM manufacturers.

SUCCESSFUL KEYWORDS (led to good vendors):
{', '.join(list(success_data['keywords'])[:15]) if success_data['keywords'] else 'None yet'}

DESCRIPTION PATTERNS (found in successful vendors):
{', '.join(success_data['description_patterns'][:10]) if success_data['description_patterns'] else 'None yet'}

AVOID KEYWORDS (led to poor vendors):
{', '.join(list(failure_data['avoid_keywords'])[:10]) if failure_data['avoid_keywords'] else 'None yet'}

BASE KEYWORDS:
{', '.join(base_keywords)}

TASK: Generate 10 NEW search keywords that:
1. Build on successful patterns
2. Avoid failed keyword patterns  
3. Are variations/combinations of what worked
4. Target 15.6" Android touchscreen manufacturers

Output ONLY the keywords as a comma-separated list, nothing else.
"""
        
        try:
            response = self.llm.invoke(prompt)
            
            # Parse keywords from response
            new_keywords = [kw.strip() for kw in response.split(',') if kw.strip()]
            
            # Clean and validate
            new_keywords = [kw for kw in new_keywords if len(kw) > 5 and len(kw) < 100]
            
            return new_keywords[:10]  # Return max 10
            
        except Exception as e:
            print(f"Error generating keywords: {e}")
            return []
    
    def should_retry_vendor(self, vendor_name: str) -> bool:
        """Decide if we should retry contacting a vendor based on past interactions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT email_sent_count, last_email_date, score, email_response
            FROM vendors 
            WHERE vendor_name = ?
            ORDER BY discovered_date DESC
            LIMIT 1
        """, (vendor_name,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return True  # New vendor, try it
        
        email_count, last_email, score, response = result
        
        # Don't retry if:
        # - Already sent 3+ emails
        # - Last email was < 7 days ago
        # - Score was very low (< 30)
        # - Got a rejection response
        
        if email_count >= 3:
            return False
        
        if last_email:
            days_since = (datetime.now() - datetime.strptime(last_email, '%Y-%m-%d')).days
            if days_since < 7:
                return False
        
        if score and score < 30:
            return False
        
        if response and any(word in response.lower() for word in ['no', 'not interested', 'cannot', 'unable']):
            return False
        
        return True
    
    def get_learning_report(self) -> str:
        """Generate a report on what the system has learned"""
        success_data = self.analyze_successful_vendors(days_back=30)
        failure_data = self.analyze_failed_vendors(days_back=30)
        
        report = f"""
=== LEARNING ENGINE REPORT ===
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SUCCESSFUL PATTERNS (Last 30 days):
- Total successful vendors: {success_data['success_count']}
- Top performing keywords: {', '.join(list(success_data['keywords'])[:10]) if success_data['keywords'] else 'None yet'}
- Common description patterns: {', '.join(success_data['description_patterns'][:5]) if success_data['description_patterns'] else 'None yet'}
- Average response time: {success_data['avg_response_time']:.1f} hours

FAILURE PATTERNS (Last 30 days):
- Total failed vendors: {failure_data['failure_count']}
- Keywords to avoid: {', '.join(list(failure_data['avoid_keywords'])[:10]) if failure_data['avoid_keywords'] else 'None yet'}
- Common rejection reasons: {len(failure_data['red_flag_patterns'])} unique patterns identified

LEARNING STATUS:
- System is {'actively learning' if success_data['success_count'] > 0 else 'in initial learning phase'}
- Keyword evolution: {'Enabled' if success_data['success_count'] >= 5 else 'Needs more data (5+ successful vendors)'}

===========================
"""
        return report
    
    def optimize_search_strategy(self) -> Dict:
        """Generate optimized search strategy based on learning"""
        success_data = self.analyze_successful_vendors(days_back=30)
        
        # Adjust search priorities based on what worked
        strategy = {
            "priority_keywords": list(success_data['keywords'])[:15] if success_data['keywords'] else [],
            "platforms_to_focus": ["alibaba.com", "made-in-china.com"],  # Can be dynamic later
            "optimal_search_time": "morning",  # Can learn from response patterns
            "retry_interval_days": 7,
            "min_score_threshold": 60
        }
        
        return strategy
