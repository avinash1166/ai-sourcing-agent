#!/usr/bin/env python3
"""
Main Orchestrator - Daily Automation Script
Runs the complete vendor discovery pipeline
"""

import asyncio
import sys
from datetime import datetime

# Import all modules
from oem_search import setup_database, build_agent
from scraper import VendorScraper
from email_outreach import EmailOutreach
from reporting import ReportGenerator
from config import *

class DailyOrchestrator:
    """Orchestrates the daily vendor discovery workflow"""
    
    def __init__(self):
        self.scraper = VendorScraper()
        self.email_outreach = EmailOutreach()
        self.reporter = ReportGenerator()
        self.agent = None
    
    async def run_daily_workflow(self):
        """
        Complete daily workflow:
        1. Scrape vendors from platforms
        2. Extract and validate each vendor
        3. Send outreach emails
        4. Generate daily report
        """
        print("\n" + "=" * 80)
        print("AI SOURCING AGENT - DAILY WORKFLOW")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Step 1: Setup
        print("\n[STEP 1] Setting up database...")
        setup_database()
        self.agent = build_agent()
        
        # Step 2: Scrape vendors
        print("\n[STEP 2] Discovering vendors from platforms...")
        try:
            vendors = await self.scraper.daily_vendor_discovery()
            print(f"✓ Discovered {len(vendors)} vendors")
        except Exception as e:
            print(f"✗ Scraping failed: {e}")
            print("Note: Install playwright with: pip install playwright && playwright install chromium")
            vendors = []
        
        # Step 3: Process each vendor through validation pipeline
        print("\n[STEP 3] Processing vendors through validation pipeline...")
        processed_count = 0
        validated_count = 0
        
        for i, vendor in enumerate(vendors, 1):
            print(f"\n--- Processing vendor {i}/{len(vendors)} ---")
            
            initial_state = {
                "task": "extract_and_validate_vendor",
                "search_query": "",
                "raw_html": vendor.get('raw_text', ''),
                "extracted_data": {},
                "validation_results": [],
                "validated_data": {},
                "historical_vendors": [],
                "retry_count": 0,
                "error_log": "",
                "status": "initialized"
            }
            
            try:
                final_state = self.agent.invoke(initial_state)
                processed_count += 1
                
                if final_state['status'] == 'saved':
                    validated_count += 1
                    print(f"✓ Vendor validated and saved: {final_state['validated_data'].get('vendor_name', 'Unknown')}")
                else:
                    print(f"✗ Vendor rejected: {final_state.get('error_log', 'Validation failed')}")
            
            except Exception as e:
                print(f"✗ Processing error: {e}")
        
        print(f"\n✓ Processed: {processed_count} vendors")
        print(f"✓ Validated and saved: {validated_count} vendors")
        
        # Step 4: Send outreach emails (placeholder)
        print("\n[STEP 4] Sending outreach emails...")
        sent_count = self.email_outreach.batch_send_to_top_vendors(min_score=70)
        print(f"✓ Contacted {sent_count} vendors")
        
        # Step 5: Generate daily report
        print("\n[STEP 5] Generating daily report...")
        report = self.reporter.generate_daily_report()
        report_path = self.reporter.save_report(report)
        
        print("\n" + "=" * 80)
        print(report)
        print("=" * 80)
        
        print(f"\n✓ Workflow completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"✓ Report saved to: {report_path}")
    
    def run_test_mode(self):
        """
        Test mode: Run with sample data only
        No web scraping, just validation testing
        """
        print("\n" + "=" * 80)
        print("AI SOURCING AGENT - TEST MODE")
        print("=" * 80)
        
        # Setup
        setup_database()
        self.agent = build_agent()
        
        # Sample vendor data
        test_vendors = [
            {
                'vendor_name': 'Shenzhen TechDisplay Co.',
                'raw_text': """
                Company: Shenzhen TechDisplay Co., Ltd.
                Product: 15.6 inch Android Tablet Display
                Display: 15.6" IPS LCD, 1920x1080
                OS: Android 11 (customizable)
                Touch: 10-point capacitive touchscreen
                Camera: 2MP front camera
                Connectivity: WiFi, 4G LTE with eSIM
                Audio: Dual speakers, microphones
                Price: $135 per unit
                MOQ: 100 pieces
                Customization: Yes, ODM services available
                """
            },
            {
                'vendor_name': 'Guangzhou Digital Screens',
                'raw_text': """
                Guangzhou Digital Screens Ltd.
                15.6" Android Display Panel
                Resolution: 1920x1080 FHD
                OS: Android 9.0
                Touchscreen: Yes, capacitive
                Camera: 5MP front
                WiFi + 4G LTE
                Price: $98/unit
                MOQ: 500 units
                Custom firmware available
                """
            },
            {
                'vendor_name': 'Beijing Loop Player Inc.',
                'raw_text': """
                Beijing Loop Player Inc.
                15.6 inch video loop player
                Plays MP4 files on repeat
                No Android, proprietary OS
                Price: $85/unit
                MOQ: 200 units
                Battery required
                No customization available
                """
            }
        ]
        
        print(f"\nTesting with {len(test_vendors)} sample vendors...\n")
        
        for i, vendor in enumerate(test_vendors, 1):
            print(f"\n{'='*60}")
            print(f"TESTING VENDOR {i}: {vendor['vendor_name']}")
            print(f"{'='*60}")
            
            initial_state = {
                "task": "extract_and_validate_vendor",
                "search_query": "",
                "raw_html": vendor['raw_text'],
                "extracted_data": {},
                "validation_results": [],
                "validated_data": {},
                "historical_vendors": [],
                "retry_count": 0,
                "error_log": "",
                "status": "initialized"
            }
            
            final_state = self.agent.invoke(initial_state)
            
            print(f"\nFinal Status: {final_state['status']}")
            if final_state['validated_data']:
                print(f"Score: {final_state['validated_data'].get('score', 'N/A')}/100")
                print("✓ ACCEPTED")
            else:
                print("✗ REJECTED")
        
        # Generate report
        print("\n" + "=" * 80)
        print("GENERATING REPORT")
        print("=" * 80)
        report = self.reporter.generate_daily_report()
        print(report)

async def main():
    """Main entry point"""
    orchestrator = DailyOrchestrator()
    
    # Check if test mode
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        orchestrator.run_test_mode()
    else:
        await orchestrator.run_daily_workflow()

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║                  AI SOURCING AGENT                           ║
║              OEM/ODM Vendor Discovery System                 ║
║                                                              ║
║  Features:                                                   ║
║  ✓ Multi-layer validation (no hallucinations)               ║
║  ✓ Automated web scraping                                   ║
║  ✓ Fact-based extraction only                               ║
║  ✓ Daily reporting                                          ║
║                                                              ║
║  Usage:                                                      ║
║    python main.py          - Run full workflow              ║
║    python main.py --test   - Run test mode (no scraping)    ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n✗ Interrupted by user")
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
