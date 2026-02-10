# 🎮 QUICK COMMAND REFERENCE

## Run the System

```bash
# Normal run (with all new features)
python3 main_v2.py

# Test mode (quick test)
python3 oem_search.py
```

## Check What's Working

```bash
# Test anti-hallucination detection
python3 -c "from anti_hallucination import DataQualityChecker; test_data = {'contact_email': 'sales@company.com', 'product_url': 'product-page-url', 'price_per_unit': 125.5}; passed, issues, score = DataQualityChecker.validate_extraction_quality(test_data); print(f'Quality: {score:.2f}'); [print(i) for i in issues]"

# Test real data extraction
python3 -c "from anti_hallucination import extract_real_email_from_text; email = extract_real_email_from_text('Contact: john@example.com for inquiries'); print(f'Found: {email}')"

# Test performance tracker
python3 -c "from anti_hallucination import AgentPerformanceTracker; t = AgentPerformanceTracker('data/vendors.db'); t.record_extraction(True, 0.85); print(t.get_performance_report())"
```

## Database Queries

```bash
# See recent vendors with quality info
sqlite3 data/vendors.db "SELECT vendor_name, contact_email, product_url, score FROM vendors ORDER BY created_at DESC LIMIT 5;"

# Check for placeholders (should be minimal now)
sqlite3 data/vendors.db "SELECT COUNT(*) FROM vendors WHERE contact_email LIKE '%@company.com';"

# See vendors with feedback
sqlite3 data/vendors.db "SELECT vendor_name, human_feedback, feedback_notes FROM vendors WHERE human_feedback IS NOT NULL;"

# See learned patterns
sqlite3 data/vendors.db "SELECT pattern_type, pattern_value, relevance_impact, confidence FROM feedback_patterns ORDER BY confidence DESC LIMIT 10;"

# Count unique vendors vs total products
sqlite3 data/vendors.db "SELECT COUNT(DISTINCT vendor_name) as unique_vendors, COUNT(*) as total_products FROM vendors;"
```

## Provide Feedback

```bash
# Via Python (replace vendor_id)
python3 -c "from feedback_system import FeedbackCollector; f = FeedbackCollector('data/vendors.db'); f.record_feedback(1, is_relevant=True, notes='Good vendor')"

# Via Telegram (reply to bot)
# /relevant 123
# /irrelevant 456 Reason here
```

## View Reports

```bash
# Generate and view Telegram report
python3 -c "from telegram_reporter import TelegramReporter; import os; t = TelegramReporter(os.getenv('TELEGRAM_BOT_TOKEN', ''), os.getenv('TELEGRAM_CHAT_ID', '')); stats = t.collect_daily_stats(); print(t.generate_report_message(stats)[:2000])"

# View performance stats
python3 -c "from anti_hallucination import AgentPerformanceTracker; t = AgentPerformanceTracker('data/vendors.db'); t.session_stats['extractions'] = 10; t.session_stats['validations_passed'] = 8; print(t.get_performance_report())"

# View learning summary
python3 -c "from feedback_system import FeedbackCollector; f = FeedbackCollector('data/vendors.db'); summary = f.get_feedback_summary(); print(f'Total Feedback: {summary[\"total_feedback\"]}'); print(f'Patterns Learned: {summary[\"patterns_learned\"]}')"
```

## Troubleshooting

```bash
# Check if new modules are importable
python3 -c "import anti_hallucination; import feedback_system; print('✅ All modules working!')"

# Check if database has new tables
sqlite3 data/vendors.db ".tables" | grep feedback

# Check if database has new columns
sqlite3 data/vendors.db "PRAGMA table_info(vendors);" | grep feedback

# View recent errors in logs
tail -n 50 data/logs/*.log

# Check Telegram connectivity
python3 -c "from telegram_reporter import TelegramReporter; import os; t = TelegramReporter(os.getenv('TELEGRAM_BOT_TOKEN'), os.getenv('TELEGRAM_CHAT_ID')); print('✅ Connected!' if t.send_message('Test') else '❌ Failed')"
```

## Reset/Clean Data

```bash
# Clear all vendors (start fresh)
sqlite3 data/vendors.db "DELETE FROM vendors; DELETE FROM validation_logs;"

# Clear feedback data only
sqlite3 data/vendors.db "UPDATE vendors SET human_feedback = NULL, feedback_date = NULL; DELETE FROM feedback_patterns;"

# Backup before clearing
cp data/vendors.db data/vendors_backup_$(date +%Y%m%d).db
```

## Monitor Performance

```bash
# Watch logs in real-time
tail -f data/logs/*.log

# Count hallucinations caught today
grep "hallucination detected" data/logs/*.log | wc -l

# Count quality checks passed today  
grep "quality check PASSED" data/logs/*.log | wc -l

# See performance grades
grep "Performance Grade" data/logs/*.log | tail -n 5
```

## Export Data

```bash
# Export all vendors to CSV
sqlite3 -header -csv data/vendors.db "SELECT * FROM vendors;" > vendors_export.csv

# Export high-scoring vendors only
sqlite3 -header -csv data/vendors.db "SELECT vendor_name, product_name, contact_email, product_url, price_per_unit, moq, score FROM vendors WHERE score >= 70 ORDER BY score DESC;" > high_score_vendors.csv

# Export learned patterns
sqlite3 -header -csv data/vendors.db "SELECT * FROM feedback_patterns ORDER BY confidence DESC;" > learned_patterns.csv
```

## Quick Stats

```bash
# Overall statistics
python3 -c "
import sqlite3
conn = sqlite3.connect('data/vendors.db')
c = conn.cursor()
print('=== SYSTEM STATISTICS ===')
print(f'Total vendors: {c.execute(\"SELECT COUNT(DISTINCT vendor_name) FROM vendors\").fetchone()[0]}')
print(f'Total products: {c.execute(\"SELECT COUNT(*) FROM vendors\").fetchone()[0]}')
print(f'With feedback: {c.execute(\"SELECT COUNT(*) FROM vendors WHERE human_feedback IS NOT NULL\").fetchone()[0]}')
print(f'Patterns learned: {c.execute(\"SELECT COUNT(*) FROM feedback_patterns\").fetchone()[0]}')
print(f'Avg score: {c.execute(\"SELECT AVG(score) FROM vendors\").fetchone()[0]:.1f}')
conn.close()
"
```

## Environment Setup

```bash
# Check environment variables
echo "Telegram Bot Token: ${TELEGRAM_BOT_TOKEN:0:10}..."
echo "Telegram Chat ID: $TELEGRAM_CHAT_ID"
echo "User Email: $USER_EMAIL"

# Set environment variables (if needed)
export TELEGRAM_BOT_TOKEN="your-token-here"
export TELEGRAM_CHAT_ID="your-chat-id-here"
export USER_EMAIL="your-email@gmail.com"
export EMAIL_PASSWORD="your-app-password-here"
```

## Daily Workflow

```bash
# Morning: Run discovery
python3 main_v2.py

# Check Telegram for results
# Provide feedback on vendors

# Evening: Check what was learned
python3 -c "from feedback_system import FeedbackCollector; f = FeedbackCollector('data/vendors.db'); print('Patterns learned:', f.get_feedback_summary()['patterns_learned'])"

# Weekly: Export high-scoring vendors for review
sqlite3 -header -csv data/vendors.db "SELECT * FROM vendors WHERE score >= 70 AND discovered_date >= date('now', '-7 days');" > weekly_vendors.csv
```

## Debugging

```bash
# Verbose run with all logs
python3 -u main_v2.py 2>&1 | tee run_log_$(date +%Y%m%d_%H%M%S).log

# Test single vendor extraction
python3 oem_search.py | grep -A 20 "VALIDATION RESULTS"

# Check if quality checks are running
python3 oem_search.py | grep "quality check"

# Check if performance tracking is running
python3 oem_search.py | grep "points:"
```

---

## 🎯 Most Common Commands

### Daily Use:
```bash
# 1. Run the system
python3 main_v2.py

# 2. Check results
sqlite3 data/vendors.db "SELECT vendor_name, score FROM vendors WHERE discovered_date = date('now') ORDER BY score DESC LIMIT 10;"

# 3. Provide feedback (via Telegram or Python)
# Telegram: /relevant 123 or /irrelevant 456
```

### Weekly Review:
```bash
# Export week's best vendors
sqlite3 -header -csv data/vendors.db "SELECT vendor_name, contact_email, product_url, price_per_unit, moq, score FROM vendors WHERE score >= 70 AND discovered_date >= date('now', '-7 days') ORDER BY score DESC;" > weekly_export.csv

# Check learning progress
python3 -c "from feedback_system import FeedbackCollector; f = FeedbackCollector('data/vendors.db'); print(f.get_feedback_summary())"
```

### Troubleshooting:
```bash
# Test all systems
python3 -c "import anti_hallucination, feedback_system; print('✅ All systems operational!')"

# Check database health
sqlite3 data/vendors.db "PRAGMA integrity_check;"
```

---

**💡 Tip:** Bookmark this file for quick reference!
