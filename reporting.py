#!/usr/bin/env python3
"""
Daily Report Generator
Creates summary reports of vendor discovery and outreach
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict
import json

from config import VENDORS_DB, REPORTS_DIR

class ReportGenerator:
    """Generate daily status reports"""
    
    def __init__(self):
        self.db_path = VENDORS_DB
    
    def get_daily_stats(self) -> Dict:
        """Get statistics for the last 24 hours"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        
        # New vendors added today
        cursor.execute('''
            SELECT COUNT(*) FROM vendors
            WHERE created_at >= ?
        ''', (yesterday,))
        new_vendors = cursor.fetchone()[0]
        
        # Vendors contacted today
        cursor.execute('''
            SELECT COUNT(*) FROM vendors
            WHERE contact_date >= ?
        ''', (yesterday,))
        contacted_today = cursor.fetchone()[0]
        
        # Replies received today
        cursor.execute('''
            SELECT COUNT(*) FROM vendors
            WHERE reply_date >= ?
        ''', (yesterday,))
        replies_today = cursor.fetchone()[0]
        
        # Total vendors in database
        cursor.execute('SELECT COUNT(*) FROM vendors')
        total_vendors = cursor.fetchone()[0]
        
        # Average score of new vendors
        cursor.execute('''
            SELECT AVG(score) FROM vendors
            WHERE created_at >= ? AND score IS NOT NULL
        ''', (yesterday,))
        avg_score = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'new_vendors': new_vendors,
            'contacted_today': contacted_today,
            'replies_today': replies_today,
            'total_vendors': total_vendors,
            'avg_score': round(avg_score, 1)
        }
    
    def get_top_vendors(self, limit: int = 10) -> List[Dict]:
        """Get top scoring vendors"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT vendor_name, url, moq, price_per_unit, customizable, score, status
            FROM vendors
            WHERE score IS NOT NULL
            ORDER BY score DESC
            LIMIT ?
        ''', (limit,))
        
        vendors = []
        for row in cursor.fetchall():
            vendors.append({
                'vendor_name': row[0],
                'url': row[1],
                'moq': row[2],
                'price_per_unit': row[3],
                'customizable': 'Yes' if row[4] else 'No' if row[4] is False else 'Unknown',
                'score': row[5],
                'status': row[6]
            })
        
        conn.close()
        return vendors
    
    def get_recent_replies(self, limit: int = 5) -> List[Dict]:
        """Get recent vendor replies"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT vendor_name, reply_date, reply_content
            FROM vendors
            WHERE reply_received = 1
            ORDER BY reply_date DESC
            LIMIT ?
        ''', (limit,))
        
        replies = []
        for row in cursor.fetchall():
            replies.append({
                'vendor_name': row[0],
                'reply_date': row[1],
                'reply_content': row[2][:100] + '...' if row[2] and len(row[2]) > 100 else row[2]
            })
        
        conn.close()
        return replies
    
    def generate_daily_report(self) -> str:
        """Generate comprehensive daily report"""
        stats = self.get_daily_stats()
        top_vendors = self.get_top_vendors(10)
        recent_replies = self.get_recent_replies(5)
        
        report = []
        report.append("=" * 80)
        report.append("AI SOURCING AGENT - DAILY REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 80)
        
        # Summary stats
        report.append("\n📊 DAILY STATISTICS")
        report.append("-" * 80)
        report.append(f"New Vendors Discovered: {stats['new_vendors']}")
        report.append(f"Vendors Contacted Today: {stats['contacted_today']}")
        report.append(f"Replies Received Today: {stats['replies_today']}")
        report.append(f"Total Vendors in Database: {stats['total_vendors']}")
        report.append(f"Average Score (New Vendors): {stats['avg_score']}/100")
        
        # Top vendors table
        report.append("\n🏆 TOP 10 VENDORS (By Score)")
        report.append("-" * 80)
        report.append(f"{'Vendor':<30} {'MOQ':<10} {'Price':<12} {'Custom':<8} {'Score':<8} {'Status':<15}")
        report.append("-" * 80)
        
        for v in top_vendors:
            vendor_name = v['vendor_name'][:28] if v['vendor_name'] else 'Unknown'
            moq = str(v['moq'])[:8] if v['moq'] else 'N/A'
            price = f"${v['price_per_unit']}" if v['price_per_unit'] else 'N/A'
            custom = v['customizable'][:6]
            score = str(v['score'])
            status = v['status'][:13]
            
            report.append(f"{vendor_name:<30} {moq:<10} {price:<12} {custom:<8} {score:<8} {status:<15}")
        
        # Recent replies
        if recent_replies:
            report.append("\n💬 RECENT VENDOR REPLIES")
            report.append("-" * 80)
            for r in recent_replies:
                report.append(f"\nVendor: {r['vendor_name']}")
                report.append(f"Date: {r['reply_date']}")
                report.append(f"Content: {r['reply_content']}")
        else:
            report.append("\n💬 RECENT VENDOR REPLIES")
            report.append("-" * 80)
            report.append("No replies received yet.")
        
        # Next steps
        report.append("\n🎯 NEXT STEPS")
        report.append("-" * 80)
        if top_vendors:
            uncontacted = [v for v in top_vendors if v['status'] == 'new']
            if uncontacted:
                report.append(f"• Contact {len(uncontacted)} high-scoring vendors")
            else:
                report.append("• All top vendors have been contacted")
        report.append("• Continue daily vendor discovery")
        report.append("• Review and respond to vendor replies")
        
        report.append("\n" + "=" * 80)
        
        return "\n".join(report)
    
    def save_report(self, report: str) -> str:
        """Save report to file"""
        import os
        os.makedirs(REPORTS_DIR, exist_ok=True)
        
        filename = f"daily_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = f"{REPORTS_DIR}/{filename}"
        
        with open(filepath, 'w') as f:
            f.write(report)
        
        print(f"✓ Report saved to: {filepath}")
        return filepath
    
    def generate_json_report(self) -> Dict:
        """Generate JSON format report for API/automation"""
        stats = self.get_daily_stats()
        top_vendors = self.get_top_vendors(10)
        recent_replies = self.get_recent_replies(5)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'statistics': stats,
            'top_vendors': top_vendors,
            'recent_replies': recent_replies
        }

# ==================== TESTING ====================
if __name__ == "__main__":
    print("Generating daily report...\n")
    
    generator = ReportGenerator()
    report = generator.generate_daily_report()
    
    print(report)
    
    # Save report
    filepath = generator.save_report(report)
    
    # Also generate JSON version
    json_report = generator.generate_json_report()
    json_filepath = filepath.replace('.txt', '.json')
    
    with open(json_filepath, 'w') as f:
        json.dump(json_report, f, indent=2)
    
    print(f"✓ JSON report saved to: {json_filepath}")
