"""
Main Orchestrator for AI Sourcing Agent - V2 with Learning
FIXED VERSION: 
- Disabled email conversation (was spamming your inbox)
- 1 hour runtime (not 15 minutes)
- Runs once daily (not 4 times)
"""

import time
from datetime import datetime
from scraper import VendorScraper
from oem_search import build_agent, setup_database
from reporting import ReportGenerator
from email_outreach import EmailOutreach
from learning_engine import LearningEngine
from telegram_reporter import TelegramReporter
from config import SEARCH_KEYWORDS, RATE_LIMITS
import os

class SmartDailyOrchestrator:
    """Self-learning orchestrator with Telegram notifications"""
    
    def __init__(self, test_mode=False, runtime_hours=1.0):  # FIXED: 1 hour default
        self.test_mode = test_mode
        self.runtime_hours = runtime_hours
        self.runtime_seconds = runtime_hours * 3600
        self.learning_engine = LearningEngine()
        
        # Telegram configuration from environment
        self.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID', '')
        
        # Email for vendor conversations (Gmail)
        self.user_email = os.getenv('USER_EMAIL', 'avinashlingamop123@gmail.com')
        self.email_password = os.getenv('EMAIL_PASSWORD', '')
        
        # Telegram reporter for notifications to YOU
        self.telegram_reporter = TelegramReporter(
            self.telegram_bot_token,
            self.telegram_chat_id
        ) if (self.telegram_bot_token and self.telegram_chat_id) else None
        
        # Email conversation manager DISABLED for now
        # (was checking YOUR inbox and replying to YOUR emails)
        self.conversation_manager = None
    
    async def run_daily_workflow(self):
        """Run the complete smart daily workflow"""
        
        print("\n" + "="*70)
        print(f"🤖 AI SOURCING AGENT V2 - SELF-LEARNING MODE (FIXED)")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Runtime: {self.runtime_hours * 60:.0f} minutes")
        print(f"Test Mode: {self.test_mode}")
        print("="*70 + "\n")
        
        start_time = time.time()
        vendors_processed = 0
        max_vendors = RATE_LIMITS['max_vendors_per_day']
        
        # Initialize database
        setup_database()
        
        # ============ STEP 1: SKIP EMAIL CHECKING (FIXED) ============
        print("\n🔍 STEP 1: Checking Vendor Responses")
        print("-" * 70)
        print("   ⏭️  DISABLED: Email checking was spamming your inbox")
        print("   💡 Will re-enable later when we actually have vendor replies")
        print("   ℹ️  For now, focus on DISCOVERING new vendors")
        
        # ============ STEP 2: LEARNING ANALYSIS ============
        print("\n📚 STEP 2: Analyzing Past Performance & Learning")
        print("-" * 70)
        learning_report = self.learning_engine.get_learning_report()
        print(learning_report)
        
        # ============ STEP 3: KEYWORD OPTIMIZATION ============
        print("\n🔍 STEP 3: Generating Optimized Keywords")
        print("-" * 70)
        base_keywords = SEARCH_KEYWORDS.copy()
        learned_keywords = self.learning_engine.generate_new_keywords(base_keywords)
        
        all_keywords = base_keywords + learned_keywords
        print(f"✓ Base keywords: {len(base_keywords)}")
        print(f"✓ Learned keywords: {len(learned_keywords)}")
        print(f"✓ Total keywords: {len(all_keywords)}")
        if learned_keywords:
            print(f"  New keywords: {', '.join(learned_keywords[:5])}")
        
        # ============ STEP 4: INTELLIGENT WEB SCRAPING ============
        if not self.test_mode:
            print("\n🌐 STEP 4: Intelligent Web Scraping (Time-boxed to 1 hour)")
            print("-" * 70)
            scraper = VendorScraper()
            agent = build_agent()
            
            for i, keyword in enumerate(all_keywords):
                # Check runtime limit
                elapsed = time.time() - start_time
                if elapsed >= self.runtime_seconds:
                    print(f"\n⏰ Runtime limit reached ({self.runtime_hours}h). Stopping.")
                    break
                
                if vendors_processed >= max_vendors:
                    print(f"\n✋ Max vendors reached ({max_vendors}). Stopping.")
                    break
                
                remaining_time = (self.runtime_seconds - elapsed) / 60
                print(f"\n[{i+1}/{len(all_keywords)}] '{keyword}' | ⏱️  {remaining_time:.1f} min left")
                
                # Scrape vendors
                try:
                    vendors = await scraper.scrape_alibaba(keyword, max_results=3)
                    
                    for vendor_data in vendors:
                        # Check time again
                        if time.time() - start_time >= self.runtime_seconds:
                            print("  ⏰ Time limit reached, stopping.")
                            break
                        
                        vendor_name = vendor_data.get('vendor_name', 'Unknown')
                        
                        # Learning: Should we retry this vendor?
                        if not self.learning_engine.should_retry_vendor(vendor_name):
                            print(f"  ⏭️  Skipping '{vendor_name}' (learned to avoid)")
                            continue
                        
                        # Process through validation agent
                        print(f"  🔄 Processing: {vendor_name}")
                        
                        initial_state = {
                            "task": "extract_and_validate_vendor",
                            "search_query": keyword,
                            "raw_html": vendor_data.get('raw_text', str(vendor_data)),
                            "extracted_data": {},
                            "validation_results": [],
                            "validated_data": {},
                            "historical_vendors": [],
                            "retry_count": 0,
                            "error_log": "",
                            "status": "initialized"
                        }
                        
                        try:
                            final_state = agent.invoke(initial_state)
                            
                            if final_state['status'] == 'saved':
                                vendors_processed += 1
                                score = final_state.get('validated_data', {}).get('score', 0)
                                print(f"  ✅ Saved (Score: {score}/100)")
                            else:
                                print(f"  ⚠️  Status: {final_state['status']}")
                                
                        except Exception as e:
                            print(f"  ❌ Processing error: {str(e)[:100]}")
                        
                        # Rate limiting
                        time.sleep(RATE_LIMITS['search_delay_seconds'])
                    
                except Exception as e:
                    print(f"  ❌ Scraping error: {str(e)[:100]}")
                
                # Delay between keywords
                time.sleep(RATE_LIMITS['search_delay_seconds'] * 2)
            
            print(f"\n✅ Scraping complete. Vendors processed: {vendors_processed}")
        
        else:
            print("\n🌐 STEP 4: Intelligent Web Scraping [SKIPPED - Test Mode]")
            print("   Run without --test flag for actual scraping")
            vendors_processed = 0
        
        # ============ STEP 5: SKIP OUTREACH FOR NOW ============
        print("\n📨 STEP 5: Sending Initial Outreach Emails")
        print("-" * 70)
        print("   ⏭️  SKIPPED for now (focus on discovery first)")
        print("   💡 Will enable later when we have enough vendors")
        
        # ============ STEP 6: REPORTING ============
        print("\n📊 STEP 6: Generating Reports")
        print("-" * 70)
        
        # Text report (always generated)
        try:
            reporter = ReportGenerator()
            report = reporter.generate_daily_report()
            report_path = reporter.save_report(report)
            print(f"✓ Text report saved: {report_path}")
        except Exception as e:
            print(f"⚠️  Text report error: {e}")
            report_path = "N/A"
        
        # Telegram report
        if self.telegram_reporter:
            try:
                telegram_sent = self.telegram_reporter.send_daily_report()
                if telegram_sent:
                    print(f"✅ Telegram report sent!")
                else:
                    print("⚠️  Telegram report failed")
            except Exception as e:
                print(f"❌ Telegram error: {e}")
        else:
            print("⚠️  Telegram not configured (set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)")
        
        # ============ FINAL SUMMARY ============
        total_time = time.time() - start_time
        print("\n" + "="*70)
        print(f"🎉 DAILY RUN COMPLETE")
        print(f"⏱️  Duration: {total_time/60:.1f} minutes")
        print(f"📦 Vendors processed: {vendors_processed}")
        print(f"📄 Report: {report_path}")
        if self.telegram_reporter:
            print(f"📱 Telegram: Report sent!")
        print("="*70 + "\n")
    
    def run_test_mode(self):
        """Quick test with sample data"""
        
        print("\n" + "="*70)
        print("🧪 TEST MODE - Sample Vendor Processing")
        print("="*70 + "\n")
        
        # Setup database
        setup_database()
        agent = build_agent()
        
        # Sample vendor data
        test_vendors = [
            {
                "vendor_name": "Shenzhen Tech Display Co",
                "description": "15.6 inch Android tablet with touchscreen, 1080p, front camera, WiFi, 4G LTE",
                "moq": "100 units",
                "price": "$130/unit",
                "url": "https://example.com/vendor1"
            }
        ]
        
        for vendor in test_vendors:
            print(f"\nTesting: {vendor['vendor_name']}")
            print("-" * 70)
            
            initial_state = {
                "task": "extract_and_validate_vendor",
                "search_query": "test",
                "raw_html": str(vendor),
                "extracted_data": {},
                "validation_results": [],
                "validated_data": {},
                "historical_vendors": [],
                "retry_count": 0,
                "error_log": "",
                "status": "initialized"
            }
            
            try:
                final_state = agent.invoke(initial_state)
                print(f"Status: {final_state['status']}")
                if final_state.get('validated_data'):
                    print(f"Score: {final_state['validated_data'].get('score', 0)}/100")
            except Exception as e:
                print(f"Error: {e}")
        
        print("\n" + "="*70)
        print("🧪 TEST COMPLETE")
        print("="*70 + "\n")


async def main():
    """Main entry point"""
    import sys
    
    mode = sys.argv[1] if len(sys.argv) > 1 else "test"
    
    # 1 FULL HOUR for production
    orchestrator = SmartDailyOrchestrator(
        test_mode=(mode == "test"),
        runtime_hours=0.08 if mode == "test" else 1.0
    )
    
    if mode == "test":
        orchestrator.run_test_mode()
    else:
        orchestrator.run_daily_workflow()


if __name__ == "__main__":
    import sys
    import asyncio
    
    mode = sys.argv[1] if len(sys.argv) > 1 else "test"
    
    # 1 FULL HOUR for production
    orchestrator = SmartDailyOrchestrator(
        test_mode=(mode == "test"),
        runtime_hours=0.08 if mode == "test" else 1.0
    )
    
    if mode == "test":
        orchestrator.run_test_mode()
    else:
        # Run with asyncio for scraper
        asyncio.run(orchestrator.run_daily_workflow())
