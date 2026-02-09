# Quick Start Guide - AI Sourcing Agent

## ⚡ Super Quick Start (5 minutes)

### Step 1: Install Ollama
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:3b
```

### Step 2: Install Dependencies
```bash
cd /home/kali/ai_agents_learning
pip install langchain langchain-ollama langgraph
```

### Step 3: Run Test
```bash
python3 main.py --test
```

**Done!** You should see 3 vendors being processed with validation results.

---

## 📋 Command Cheat Sheet

```bash
# Full setup (automated)
./setup.sh

# Test mode (no web scraping, uses sample data)
python3 main.py --test

# Production mode (scrapes real vendors)
python3 main.py

# Test individual components
python3 oem_search.py      # Test agent only
python3 scraper.py         # Test scraper only
python3 reporting.py       # Generate report only
python3 validators.py      # Test validators only

# Check database
sqlite3 data/vendors.db "SELECT vendor_name, score FROM vendors ORDER BY score DESC LIMIT 10;"

# View latest report
cat data/reports/daily_report_*.txt | tail -100

# Check Ollama models
ollama list

# Start Ollama service (if not running)
ollama serve
```

---

## 🎯 What Each File Does

| File | Purpose | Edit This? |
|------|---------|------------|
| `config.py` | All settings & product specs | ✅ YES - Customize for your product |
| `validators.py` | 5-layer validation system | ⚠️ MAYBE - Only if changing validation logic |
| `oem_search.py` | Main LangGraph agent | ❌ NO - Core logic |
| `scraper.py` | Web scraping module | ⚠️ MAYBE - To add new platforms |
| `email_outreach.py` | Email automation | ⚠️ MAYBE - To customize templates |
| `reporting.py` | Daily reports | ⚠️ MAYBE - To customize format |
| `main.py` | Orchestrator (runs everything) | ❌ NO - Entry point |
| `setup.sh` | Installation script | ❌ NO - One-time use |

---

## 🔧 Common Customizations

### Change Product Specs
Edit `config.py`:
```python
PRODUCT_SPECS = {
    "display": "10.1 inch",  # Changed from 15.6
    "moq_max_acceptable": 1000,  # Changed from 500
    # ... etc
}
```

### Add Search Keywords
Edit `config.py`:
```python
SEARCH_KEYWORDS = [
    "15.6 inch Android tablet",
    "YOUR NEW KEYWORD HERE",
]
```

### Add Red Flags
Edit `config.py`:
```python
RED_FLAGS = [
    "loop video player only",
    "YOUR NEW RED FLAG",
]
```

### Change Validation Strictness
Edit `validators.py` - line ~75:
```python
# Current: 60% confidence required
if confidence < 0.6:
    return ValidationResult(passed=False, ...)

# Make stricter (80%):
if confidence < 0.8:
    return ValidationResult(passed=False, ...)

# Make looser (40%):
if confidence < 0.4:
    return ValidationResult(passed=False, ...)
```

### Adjust Scoring Weights
Edit `config.py`:
```python
SCORING_WEIGHTS = {
    "android_os": 30,  # Increased from 20 (more important)
    "price_in_range": 10,  # Decreased from 20 (less important)
    # ... etc
}
```

---

## 📊 Understanding the Output

### Test Mode Output
```
>>> NODE 1: Extracting vendor information...
✓ Extracted data for: Shenzhen TechDisplay Co.
```
**Meaning**: LLM successfully extracted structured data from raw text.

```
>>> NODE 2: Validating extracted data...
✓ Layer 1: Format Check: Format valid (confidence: 1.00)
✓ Layer 2: Factual Check: Factual check passed (confidence: 0.95)
```
**Meaning**: All validation layers passed. Data is fact-based.

```
>>> NODE 3: Scoring vendor...
✓ Vendor score: 87/100 (87/100 points)
```
**Meaning**: Vendor scored 87/100 based on product fit.

```
>>> NODE 4: Saving to database...
✓ Vendor saved to database (ID: 1)
```
**Meaning**: Vendor passed all checks and was saved.

### Validation Failure Example
```
✗ Layer 3: Constraint Check: MOQ too high: 1000 > 500
✗ VALIDATION FAILED - Data rejected
```
**Meaning**: Vendor requires MOQ of 1000, exceeds our limit of 500. Auto-rejected.

---

## 🚨 Troubleshooting

### Problem: "ModuleNotFoundError: No module named 'langchain'"
**Solution**:
```bash
pip install langchain langchain-ollama langgraph
```

### Problem: "Connection error: Ollama not running"
**Solution**:
```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Run agent
python3 main.py --test
```

### Problem: "Out of memory" / System freezes
**Solution**:
```bash
# Use even smaller model
ollama pull qwen2.5:1.5b

# Edit config.py
OLLAMA_MODEL = "qwen2.5:1.5b"
```

### Problem: "No vendors scraped"
**Solution**:
1. Check internet connection
2. Run test mode instead: `python3 main.py --test`
3. Install Playwright: `pip install playwright && playwright install chromium`

### Problem: "All vendors rejected by validation"
**Solution**:
This is actually GOOD - it means validation is working!
- Check `data/reports/` to see why vendors were rejected
- If validation is too strict, adjust thresholds in `validators.py`
- Add more search keywords to find better matches

---

## 📈 Expected Results

### Test Mode (3 sample vendors)
- ✅ Vendor 1 (TechDisplay): **PASS** - Score ~85-90
- ✅ Vendor 2 (Digital Screens): **PASS** - Score ~70-75  
- ❌ Vendor 3 (Loop Player): **FAIL** - Red flags detected

### Production Mode (30 real vendors)
- Typical pass rate: **40-60%** (12-18 vendors saved)
- Average score: **70-80**
- Time: **12-15 minutes**

### After 7 Days
- Total vendors in DB: ~100-120
- High-scoring (80+): ~20-30
- Ready for outreach: ~10-15

---

## 🎓 Learning Resources

### Understanding LangGraph
- State machines for AI agents
- Each "node" = a function
- "Edges" = flow control
- Great for multi-step workflows

### Understanding Validation Layers
1. **Format**: "Is this JSON valid?"
2. **Factual**: "Is this data in the source text?"
3. **Constraint**: "Does this meet our requirements?"
4. **Consistency**: "Is this similar to past data?"
5. **Cross-validation**: "Does this make logical sense?"

### Why This Matters
Without validation, LLMs will:
- Make up plausible-sounding company names
- Invent prices that "seem reasonable"
- Claim features that aren't mentioned
- Hallucinate contact information

With 5-layer validation:
- ✅ Only facts from source text
- ✅ Only vendors meeting requirements  
- ✅ No duplicates
- ✅ No anomalies

---

## 🔄 Daily Workflow

### Morning (Automated)
1. **9:00 AM**: Agent runs automatically (cron job)
2. **9:15 AM**: Email report arrives
3. **9:30 AM**: Check high-scoring vendors

### Afternoon (Manual)
4. **2:00 PM**: Review vendor replies
5. **3:00 PM**: Research top 3 vendors
6. **4:00 PM**: Schedule calls/meetings

### Weekly
- Monday: Adjust search keywords based on results
- Friday: Review week's vendors, shortlist top 10

---

## 📧 Email Setup (Optional)

### Gmail Setup
1. Go to: https://myaccount.google.com/apppasswords
2. Generate app password
3. Create `.env` file:
```bash
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password_here
```

4. Use in code:
```python
from email_outreach import EmailOutreach
import os
from dotenv import load_dotenv

load_dotenv()
outreach = EmailOutreach()
outreach.configure(
    os.getenv('EMAIL_ADDRESS'),
    os.getenv('EMAIL_PASSWORD')
)
outreach.batch_send_to_top_vendors(min_score=70)
```

---

## 🎯 Next Steps

### After Your First Successful Run:
1. ✅ Check `data/vendors.db` with a SQLite browser
2. ✅ Read the generated report in `data/reports/`
3. ✅ Customize `config.py` for your product
4. ✅ Run in production mode (if Playwright installed)
5. ✅ Set up daily cron job

### Cron Job Setup (Daily 9 AM):
```bash
crontab -e

# Add this line:
0 9 * * * cd /home/kali/ai_agents_learning && /usr/bin/python3 main.py >> /tmp/sourcing_agent.log 2>&1
```

### Advanced Usage:
- Integrate with Notion for vendor pipeline
- Add Telegram bot for instant notifications  
- Create Streamlit dashboard for visualization
- Set up email auto-responder for vendor replies

---

## 💡 Pro Tips

1. **Start with test mode** - Don't scrape real vendors until you understand the output
2. **Review rejections** - Failed validations teach you what to avoid
3. **Adjust gradually** - Change one thing at a time (keywords, thresholds, etc.)
4. **Trust the validation** - If it rejects 60% of vendors, that's good! Quality > quantity
5. **Monitor RAM usage** - Use `htop` to ensure you're not maxing out
6. **Back up the database** - `cp data/vendors.db data/vendors_backup.db`

---

## 📞 Support

### Logs Location
- Agent logs: Terminal output
- Validation logs: Inside `validation_logs` table
- Reports: `data/reports/`
- Database: `data/vendors.db`

### Debug Mode
```python
# Add to top of main.py for verbose output
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check System
```bash
# Python version
python3 --version  # Need 3.8+

# Ollama status
ollama list

# Disk space
df -h

# RAM usage
free -h
```

---

**Ready to find your perfect OEM/ODM partner! 🚀**
