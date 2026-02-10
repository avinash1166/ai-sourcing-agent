#!/usr/bin/env python3
"""
Human Feedback Loop System
Allows users to mark vendors as relevant/irrelevant via Telegram
Improves agent learning over time
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Tuple
from telegram_reporter import TelegramReporter

class FeedbackCollector:
    """Collects and processes human feedback on vendor relevance"""
    
    def __init__(self, db_path: str, telegram_reporter: TelegramReporter = None):
        self.db_path = db_path
        self.telegram = telegram_reporter
        self._setup_feedback_tables()
    
    def _setup_feedback_tables(self):
        """Create feedback tracking tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Add feedback columns to vendors table if they don't exist
        cursor.execute("PRAGMA table_info(vendors)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'human_feedback' not in columns:
            cursor.execute("""
                ALTER TABLE vendors 
                ADD COLUMN human_feedback TEXT DEFAULT NULL
            """)
        
        if 'feedback_date' not in columns:
            cursor.execute("""
                ALTER TABLE vendors 
                ADD COLUMN feedback_date TEXT DEFAULT NULL
            """)
        
        if 'feedback_notes' not in columns:
            cursor.execute("""
                ALTER TABLE vendors 
                ADD COLUMN feedback_notes TEXT DEFAULT NULL
            """)
        
        # Create feedback learning table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                pattern_value TEXT NOT NULL,
                relevance_impact TEXT NOT NULL,
                confidence REAL DEFAULT 0.5,
                sample_count INTEGER DEFAULT 1,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(pattern_type, pattern_value)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def request_feedback_for_vendor(self, vendor_id: int) -> bool:
        """Send Telegram message requesting feedback for a specific vendor"""
        if not self.telegram:
            print("⚠️  Telegram not configured, skipping feedback request")
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT vendor_name, product_name, product_url, contact_email, 
                   price_per_unit, moq, score, product_description
            FROM vendors WHERE id = ?
        """, (vendor_id,))
        
        vendor = cursor.fetchone()
        conn.close()
        
        if not vendor:
            return False
        
        name, product, url, email, price, moq, score, desc = vendor
        
        # Format feedback request message
        message = f"""
🔔 <b>FEEDBACK REQUEST</b>

Is this vendor relevant for our product?

<b>Vendor:</b> {name}
<b>Product:</b> {product or 'N/A'}
<b>Score:</b> {score}/100
<b>Price:</b> ${price}/unit | MOQ: {moq}
<b>Email:</b> {email or 'Not found'}
<b>URL:</b> {url[:100] if url else 'Not found'}...

<b>Description:</b> {desc[:200] if desc else 'N/A'}...

━━━━━━━━━━━━━━━━━━━━━━━━
Reply with:
✅ <code>/relevant {vendor_id}</code> - This is relevant
❌ <code>/irrelevant {vendor_id}</code> - Not relevant
💬 <code>/notes {vendor_id} Your notes here</code>
"""
        
        return self.telegram.send_message(message)
    
    def record_feedback(self, vendor_id: int, is_relevant: bool, notes: str = None) -> bool:
        """Record human feedback for a vendor"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        feedback = 'relevant' if is_relevant else 'irrelevant'
        today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute("""
            UPDATE vendors 
            SET human_feedback = ?,
                feedback_date = ?,
                feedback_notes = ?
            WHERE id = ?
        """, (feedback, today, notes, vendor_id))
        
        # Learn from the feedback
        self._learn_from_feedback(vendor_id, is_relevant)
        
        conn.commit()
        conn.close()
        
        print(f"✓ Feedback recorded for vendor {vendor_id}: {feedback}")
        return True
    
    def _learn_from_feedback(self, vendor_id: int, is_relevant: bool):
        """Extract patterns from feedback to improve future detection"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get vendor details
        cursor.execute("""
            SELECT vendor_name, product_type, os, wall_mount, has_battery,
                   price_per_unit, moq, platform, raw_data
            FROM vendors WHERE id = ?
        """, (vendor_id,))
        
        vendor = cursor.fetchone()
        if not vendor:
            conn.close()
            return
        
        name, prod_type, os, wall_mount, has_battery, price, moq, platform, raw_data = vendor
        
        # Extract learnable patterns
        impact = 'positive' if is_relevant else 'negative'
        
        patterns_to_learn = []
        
        # Product type patterns
        if prod_type:
            patterns_to_learn.append(('product_type', prod_type.lower(), impact))
        
        # OS patterns
        if os:
            patterns_to_learn.append(('os', os.lower(), impact))
        
        # Wall mount preference
        if wall_mount is not None:
            patterns_to_learn.append(('wall_mount', str(wall_mount), impact))
        
        # Battery preference (we don't want battery)
        if has_battery is not None:
            # Invert logic: if has_battery=True and irrelevant, that's expected
            # if has_battery=False and relevant, that's good
            if has_battery and not is_relevant:
                patterns_to_learn.append(('has_battery', 'True', 'negative'))
            elif not has_battery and is_relevant:
                patterns_to_learn.append(('has_battery', 'False', 'positive'))
        
        # Platform patterns
        if platform:
            patterns_to_learn.append(('platform', platform.lower(), impact))
        
        # Price range patterns
        if price:
            price_range = self._categorize_price(price)
            patterns_to_learn.append(('price_range', price_range, impact))
        
        # MOQ patterns
        if moq:
            moq_range = self._categorize_moq(moq)
            patterns_to_learn.append(('moq_range', moq_range, impact))
        
        # Vendor name patterns (city, company type)
        if name:
            city_pattern = self._extract_city(name)
            if city_pattern:
                patterns_to_learn.append(('vendor_city', city_pattern, impact))
        
        # Update or insert patterns
        for pattern_type, pattern_value, relevance_impact in patterns_to_learn:
            cursor.execute("""
                INSERT INTO feedback_patterns (pattern_type, pattern_value, relevance_impact, confidence, sample_count)
                VALUES (?, ?, ?, 0.6, 1)
                ON CONFLICT(pattern_type, pattern_value) DO UPDATE SET
                    confidence = MIN(1.0, confidence + 0.1),
                    sample_count = sample_count + 1,
                    relevance_impact = ?,
                    last_updated = CURRENT_TIMESTAMP
            """, (pattern_type, pattern_value, relevance_impact, relevance_impact))
        
        conn.commit()
        conn.close()
        
        print(f"  📚 Learned {len(patterns_to_learn)} patterns from feedback")
    
    def _categorize_price(self, price: float) -> str:
        """Categorize price into ranges"""
        if price < 70:
            return 'under_70'
        elif price <= 90:
            return '70_to_90'
        elif price <= 130:
            return '90_to_130'
        else:
            return 'over_130'
    
    def _categorize_moq(self, moq: int) -> str:
        """Categorize MOQ into ranges"""
        if moq <= 100:
            return 'under_100'
        elif moq <= 500:
            return '100_to_500'
        elif moq <= 1000:
            return '500_to_1000'
        else:
            return 'over_1000'
    
    def _extract_city(self, vendor_name: str) -> str:
        """Extract city from vendor name"""
        cities = ['Shenzhen', 'Guangzhou', 'Dongguan', 'Foshan', 'Beijing', 
                 'Shanghai', 'Hangzhou', 'Ningbo', 'Xiamen']
        
        for city in cities:
            if city.lower() in vendor_name.lower():
                return city.lower()
        return None
    
    def get_learned_patterns(self) -> List[Dict]:
        """Get all learned patterns with confidence scores"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT pattern_type, pattern_value, relevance_impact, confidence, sample_count
            FROM feedback_patterns
            WHERE confidence > 0.5
            ORDER BY confidence DESC, sample_count DESC
        """)
        
        patterns = []
        for row in cursor.fetchall():
            patterns.append({
                'type': row[0],
                'value': row[1],
                'impact': row[2],
                'confidence': row[3],
                'samples': row[4]
            })
        
        conn.close()
        return patterns
    
    def predict_relevance(self, vendor_data: Dict) -> Tuple[float, List[str]]:
        """
        Predict if vendor is relevant based on learned patterns
        
        Returns:
            (relevance_score: float, matching_patterns: List[str])
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        relevance_score = 0.5  # Start neutral
        matching_patterns = []
        
        # Check each field against learned patterns
        checks = [
            ('product_type', vendor_data.get('product_type', '').lower()),
            ('os', vendor_data.get('os', '').lower()),
            ('wall_mount', str(vendor_data.get('wall_mount', ''))),
            ('has_battery', str(vendor_data.get('has_battery', ''))),
            ('platform', vendor_data.get('platform', '').lower()),
        ]
        
        # Add price and MOQ ranges
        if vendor_data.get('price_per_unit'):
            price_range = self._categorize_price(vendor_data['price_per_unit'])
            checks.append(('price_range', price_range))
        
        if vendor_data.get('moq'):
            moq_range = self._categorize_moq(vendor_data['moq'])
            checks.append(('moq_range', moq_range))
        
        if vendor_data.get('vendor_name'):
            city = self._extract_city(vendor_data['vendor_name'])
            if city:
                checks.append(('vendor_city', city))
        
        # Query patterns
        for pattern_type, pattern_value in checks:
            if not pattern_value:
                continue
            
            cursor.execute("""
                SELECT relevance_impact, confidence
                FROM feedback_patterns
                WHERE pattern_type = ? AND pattern_value = ?
            """, (pattern_type, pattern_value))
            
            result = cursor.fetchone()
            if result:
                impact, confidence = result
                weight = confidence * 0.1  # Each pattern contributes up to 0.1
                
                if impact == 'positive':
                    relevance_score += weight
                    matching_patterns.append(f"✓ {pattern_type}={pattern_value}")
                else:
                    relevance_score -= weight
                    matching_patterns.append(f"✗ {pattern_type}={pattern_value}")
        
        conn.close()
        
        # Clamp score to 0-1
        relevance_score = max(0.0, min(1.0, relevance_score))
        
        return relevance_score, matching_patterns
    
    def get_feedback_summary(self) -> Dict:
        """Get summary of all feedback"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN human_feedback = 'relevant' THEN 1 ELSE 0 END) as relevant,
                SUM(CASE WHEN human_feedback = 'irrelevant' THEN 1 ELSE 0 END) as irrelevant
            FROM vendors
            WHERE human_feedback IS NOT NULL
        """)
        
        row = cursor.fetchone()
        total, relevant, irrelevant = row if row else (0, 0, 0)
        
        # Get pattern count
        cursor.execute("SELECT COUNT(*) FROM feedback_patterns")
        pattern_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_feedback': total,
            'relevant_count': relevant,
            'irrelevant_count': irrelevant,
            'patterns_learned': pattern_count,
            'accuracy': (relevant / total * 100) if total > 0 else 0
        }
