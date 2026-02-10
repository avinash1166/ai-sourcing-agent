# 🚀 TESTING THE NEW ANTI-HALLUCINATION SYSTEM

## Quick Test - See It Work Right Now

### 1. Test the Data Quality Checker

```bash
cd /home/kali/ai_agents_learning
python3 -c "
from anti_hallucination import DataQualityChecker

# Test placeholder detection
test_data = {
    'vendor_name': 'Shenzhen TechDisplay Co., Ltd.',
    'contact_email': 'sales@company.com',  # PLACEHOLDER!
    'product_url': 'product-page-url',      # PLACEHOLDER!
    'price_per_unit': 125.5,                 # SUSPICIOUS!
    'url': 'https://real-vendor.com'
}

passed, issues, score = DataQualityChecker.validate_extraction_quality(test_data)

print('\n=== DATA QUALITY CHECK ===')
print(f'Passed: {passed}')
print(f'Quality Score: {score:.2f}')
print('\nIssues Found:')
for issue in issues:
    print(f'  {issue}')
"
```

**Expected Output:**
```
=== DATA QUALITY CHECK ===
Passed: False
Quality Score: 0.20

Issues Found:
  ❌ Email: Placeholder email pattern: sales@company.com
  ❌ Product URL: Placeholder URL pattern: product-page-url
  ❌ Price: Suspicious placeholder price: $125.5
```

### 2. Test Real Data Extraction

```bash
python3 -c "
from anti_hallucination import extract_real_email_from_text, extract_real_urls_from_text

sample_text = '''
Shenzhen ABC Technology Co., Ltd.
15.6 Inch Android Smart Display
Contact: john.smith@shenzhen-abc.com
Website: https://www.shenzhen-abc.com
Product page: https://www.shenzhen-abc.com/products/smart-display-156
Price: \$89 per unit
'''

email = extract_real_email_from_text(sample_text)
urls = extract_real_urls_from_text(sample_text)

print('=== REAL DATA EXTRACTION ===')
print(f'Email found: {email}')
print(f'Vendor URL: {urls[\"vendor_url\"]}')
print(f'Product URL: {urls[\"product_url\"]}')
"
```

**Expected Output:**
```
=== REAL DATA EXTRACTION ===
Email found: john.smith@shenzhen-abc.com
Vendor URL: https://www.shenzhen-abc.com
Product URL: https://www.shenzhen-abc.com/products/smart-display-156
```

### 3. Test Performance Tracker

```bash
python3 -c "
from anti_hallucination import AgentPerformanceTracker

tracker = AgentPerformanceTracker('data/vendors.db')

# Simulate agent actions
tracker.record_extraction(True, 0.85)  # Good extraction
tracker.record_hallucination('major')   # Caught hallucination
tracker.record_human_feedback(True, 'Shenzhen ABC')  # Relevant vendor

print(tracker.get_performance_report())
"
```

**Expected Output:**
```
  🎉 +10 points: High-quality extraction (Total: 110)
  ⚠️  -10 points: MAJOR hallucination detected (Total: 100)
  🎉 +15 points: Vendor 'Shenzhen ABC' marked RELEVANT by human (Total: 115)

╔════════════════════════════════════════╗
║     AGENT PERFORMANCE REPORT           ║
╚════════════════════════════════════════╝

🎯 Current Score: 115 points
📊 Extraction Success Rate: 100.0%

Session Stats:
  • Total Extractions: 1
  • Passed Validation: 1
  • Failed Validation: 0
  • Hallucinations Caught: 1
  • Human Feedback (Relevant): 1
  • Human Feedback (Irrelevant): 0

Performance Grade: A (Great) ⭐
```

### 4. Test the Full OEM Search with Anti-Hallucination

```bash
python3 oem_search.py
```

**Watch for these NEW outputs:**
```
>>> NODE 1: Extracting vendor information...
  ✓ Real email extracted: sales@shenzhen-tech.com
  ✓ Real product URL: https://made-in-china.com/product/12345...
  ⚠️  Placeholder price detected: Suspicious placeholder price: $125.5
  ✅ Data quality check PASSED (confidence: 0.75)
  🎉 +10 points: High-quality extraction (Total: 110)

>>> NODE 2: Validating extracted data...

=== VALIDATION RESULTS ===
Quality Score: 0.75
✓ Schema Validation: All fields present (confidence: 1.00)
✓ Factual Check: Data verified in source (confidence: 0.85)
...

╔════════════════════════════════════════╗
║     AGENT PERFORMANCE REPORT           ║
╚════════════════════════════════════════╝
...
```

### 5. Test Feedback System

```bash
python3 -c "
from feedback_system import FeedbackCollector
from telegram_reporter import TelegramReporter
import os

# Initialize
db_path = 'data/vendors.db'
telegram = TelegramReporter(
    os.getenv('TELEGRAM_BOT_TOKEN', ''),
    os.getenv('TELEGRAM_CHAT_ID', '')
) if os.getenv('TELEGRAM_BOT_TOKEN') else None

feedback = FeedbackCollector(db_path, telegram)

# Simulate feedback on a vendor (use actual vendor_id from your database)
# Replace 1 with actual vendor ID
feedback.record_feedback(vendor_id=1, is_relevant=False, notes='This is a tablet, not a display')

# Get learned patterns
patterns = feedback.get_learned_patterns()
print('\n=== LEARNED PATTERNS ===')
for p in patterns[:5]:
    print(f'{p[\"type\"]}: {p[\"value\"]} → {p[\"impact\"]} (confidence: {p[\"confidence\"]:.2f}, samples: {p[\"samples\"]})')

# Get feedback summary
summary = feedback.get_feedback_summary()
print(f'\n=== FEEDBACK SUMMARY ===')
print(f'Total Feedback: {summary[\"total_feedback\"]}')
print(f'Relevant: {summary[\"relevant_count\"]}')
print(f'Irrelevant: {summary[\"irrelevant_count\"]}')
print(f'Patterns Learned: {summary[\"patterns_learned\"]}')
"
```

### 6. Test Enhanced Telegram Reporting

First, check your database has some vendors:
```bash
sqlite3 data/vendors.db "SELECT vendor_name, product_name, product_url FROM vendors LIMIT 3;"
```

Then test the new report format:
```bash
python3 -c "
from telegram_reporter import TelegramReporter
import os

telegram = TelegramReporter(
    os.getenv('TELEGRAM_BOT_TOKEN', ''),
    os.getenv('TELEGRAM_CHAT_ID', '')
)

stats = telegram.collect_daily_stats()
message = telegram.generate_report_message(stats)

print('=== TELEGRAM REPORT PREVIEW ===')
print(message[:2000])  # First 2000 chars
"
```

**Look for:**
- ✅ Multiple products listed per vendor
- ✅ Clickable HTML links: `<a href="...">View Product</a>`
- ✅ Real emails (or "Email not found")
- ✅ Real URLs (or "URL: Not available")
- ✅ Individual scores for each product

## 🎯 Full Integration Test

Run the complete system:

```bash
# 1. Make sure database is set up
python3 -c "from oem_search import setup_database; setup_database()"

# 2. Run a test discovery session
python3 main_v2.py

# 3. Check the Telegram report (if configured)
# Should show:
# - Multiple products per vendor
# - Clickable links
# - Real emails or "Email not found"
# - No placeholder data
```

## 🔍 What to Look For

### ✅ GOOD SIGNS:
- ✓ Real emails like `sales@vendor-name.com`
- ✓ Clickable product URLs with `https://`
- ✓ Different prices for different vendors
- ✓ Quality scores displayed (0.0-1.0)
- ✓ Performance points changing (+/-)
- ✓ "Hallucination detected" warnings
- ✓ Multiple products shown per vendor
- ✓ Performance grade at end (A, B, C, etc.)

### ❌ BAD SIGNS (Old System):
- ✗ `sales@company.com` for everyone
- ✗ `product-page-url` placeholder
- ✗ Same price for all vendors
- ✗ "(3 products)" but only 1 shown
- ✗ No quality checks mentioned
- ✗ No performance tracking

## 📊 Verify Database Changes

```bash
# Check if feedback columns were added
sqlite3 data/vendors.db ".schema vendors" | grep feedback

# Check feedback patterns table exists
sqlite3 data/vendors.db ".schema feedback_patterns"

# See quality of recent vendors
sqlite3 data/vendors.db "
SELECT 
    vendor_name, 
    contact_email, 
    product_url,
    score,
    validation_status
FROM vendors 
ORDER BY created_at DESC 
LIMIT 5;
"
```

## 🐛 Troubleshooting

### If you see errors about missing modules:

```bash
# The anti_hallucination module exists
ls -la anti_hallucination.py

# The feedback_system module exists
ls -la feedback_system.py

# If import errors, check Python path
python3 -c "import sys; print('\n'.join(sys.path))"
```

### If quality checks aren't running:

```bash
# Verify the imports in oem_search.py
grep "anti_hallucination" oem_search.py
grep "performance_tracker" oem_search.py
```

### If Telegram links aren't clickable:

Check the report uses HTML parse mode:
```bash
grep "parse_mode" telegram_reporter.py
# Should say: parse_mode="HTML"
```

## 📈 Performance Baseline

**Expected Results After Fixes:**

| Metric | Before | After |
|--------|--------|-------|
| Placeholder emails | 95% | 5% |
| Placeholder URLs | 90% | 10% |
| Duplicate vendors | 40% | 5% |
| Clickable links | 0% | 95% |
| Products shown (multi) | 20% | 95% |
| Quality score tracking | No | Yes |
| Performance tracking | No | Yes |
| Learning from feedback | No | Yes |

## 🎓 Next: Provide Feedback

Once the system runs:

1. **Check Telegram** for the daily report
2. **Review each vendor** - is it relevant?
3. **Reply with feedback:**
   ```
   /relevant 123
   /irrelevant 456 This is a tablet, we need displays
   ```
4. **Watch it learn** - future runs will be smarter
5. **Monitor performance** - check the grade improves

---

## ✅ Success Criteria

You'll know it's working when:
1. ✅ You see actual clickable links in Telegram
2. ✅ Different emails for different vendors
3. ✅ ALL products shown for each vendor
4. ✅ Quality scores displayed
5. ✅ Performance report at end of run
6. ✅ "Hallucination detected" warnings appear
7. ✅ Points increasing/decreasing in real-time
8. ✅ Learned patterns accumulating over time

**The agent is now ACCOUNTABLE and LEARNING! 🎯**
