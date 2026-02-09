# AI Sourcing Agent - OEM/ODM Vendor Discovery

A fully automated AI agent for discovering, validating, and engaging with OEM/ODM manufacturers for custom hardware products. Built with **LangChain + LangGraph** and optimized for low-RAM systems (8GB).

## 🎯 Purpose

Automatically find and evaluate Android-based 15.6" touchscreen device manufacturers matching custom specifications:
- 15.6" IPS touchscreen (1080p)
- Android OS (AOSP preferred)
- No battery, front camera, speakers
- eSIM/4G LTE support
- MOQ: 100-500 units
- Target price: $120-$150/unit

## ✨ Key Features

### 🚫 **Zero Hallucinations - Multi-Layer Validation**
Every piece of data goes through **5 validation layers**:
1. **Format Check**: Ensures output matches expected schema
2. **Factual Check**: Verifies extracted data exists in source text (no made-up info)
3. **Constraint Check**: Validates against product requirements & red flags
4. **Consistency Check**: Cross-validates with historical data (detects duplicates/anomalies)
5. **Cross-Validation**: Ensures logical consistency between fields

**Only fact-based, validated data is saved to the database.**

### 🤖 Automated Workflow
- Web scraping (Alibaba, Made-in-China, GlobalSources)
- LLM-based data extraction (Ollama)
- Email outreach (Gmail SMTP)
- Daily reporting
- SQLite database tracking

### 💾 Low-RAM Optimized
- Uses lightweight Ollama model (`qwen2.5:3b`)
- Headless browser scraping
- Minimal memory footprint
- No cloud APIs (100% free)

## 📁 Project Structure

```
ai_agents_learning/
├── config.py              # All configuration & product specs
├── validators.py          # 5-layer validation system
├── oem_search.py         # Main LangGraph agent
├── scraper.py            # Web scraping module
├── email_outreach.py     # Email automation
├── reporting.py          # Daily report generator
├── main.py               # Orchestrator (runs everything)
├── requirements.txt      # Python dependencies
└── data/                 # Created automatically
    ├── vendors.db        # SQLite database
    ├── logs/            # Validation logs
    └── reports/         # Daily reports
```

## 🚀 Installation

### 1. Install Ollama (Lightweight LLM)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull lightweight model (1.9GB - fits in 8GB RAM)
ollama pull qwen2.5:3b
```

### 2. Install Python Dependencies

```bash
cd /home/kali/ai_agents_learning

# Install core dependencies
pip install langchain langchain-ollama langgraph python-dotenv

# Optional: For web scraping (requires ~500MB)
pip install playwright
playwright install chromium
```

### 3. Verify Installation

```bash
# Check Ollama is running
ollama list

# Should show: qwen2.5:3b
```

## 🎮 Usage

### Test Mode (Recommended First)
Run with sample data to verify everything works:

```bash
python main.py --test
```

This will:
- Test 3 sample vendors
- Run full validation pipeline
- Show which vendors pass/fail
- Generate a report

**Expected output**: 2 vendors pass (TechDisplay, Digital Screens), 1 fails (Loop Player - red flags)

### Full Production Mode
Run complete workflow with web scraping:

```bash
python main.py
```

This will:
1. Scrape 30 vendors from Alibaba & Made-in-China
2. Extract & validate each vendor (5 layers)
3. Save valid vendors to database
4. Send outreach emails (placeholder)
5. Generate daily report

### Manual Component Testing

```bash
# Test just the validator
python validators.py

# Test just the scraper
python scraper.py

# Test just the main agent
python oem_search.py

# Generate report only
python reporting.py
```

## ⚙️ Configuration

Edit `config.py` to customize:

```python
# Product specs
PRODUCT_SPECS = {
    "screen_size": "15.6 inch",
    "moq_max_acceptable": 500,
    "target_cogs_max": 150,
    # ... more specs
}

# Search keywords
SEARCH_KEYWORDS = [
    "15.6 inch Android tablet",
    # ... add more
]

# Red flags (auto-reject)
RED_FLAGS = [
    "loop video player only",
    "no customization",
    # ... add more
]
```

## 📊 Validation Example

```
=== VALIDATION RESULTS ===
✓ Layer 1: Format Check: Format valid (confidence: 1.00)
✓ Layer 2: Factual Check: Factual check passed (confidence: 0.95)
✓ Layer 3: Constraint Check: Constraints satisfied (confidence: 1.00)
✓ Layer 4: Consistency Check: Consistency check passed (confidence: 0.90)
✓ Layer 5: Cross-Validation: Cross-validation passed (confidence: 1.00)

✓ ALL VALIDATION LAYERS PASSED - Data is factual and reliable
```

## 📧 Email Setup (Optional)

To enable email outreach:

1. **Enable Gmail App Password**:
   - Go to https://myaccount.google.com/apppasswords
   - Generate app password

2. **Configure in code**:
```python
from email_outreach import EmailOutreach

outreach = EmailOutreach()
outreach.configure('your_email@gmail.com', 'your_app_password')
outreach.batch_send_to_top_vendors(min_score=70)
```

## 📈 Database Schema

**vendors** table:
- vendor_name, url, platform
- moq, price_per_unit, score
- contacted, contact_date
- reply_received, reply_date
- customizable, os, touchscreen, etc.

**validation_logs** table:
- vendor_id, validation_passed
- layer_results (JSON)

## 🔄 Automation (Cron/GitHub Actions)

Run daily at 9 AM:

```bash
# Add to crontab
0 9 * * * cd /home/kali/ai_agents_learning && /usr/bin/python3 main.py >> /tmp/sourcing_agent.log 2>&1
```

Or use GitHub Actions (free):
```yaml
# .github/workflows/daily-sourcing.yml
on:
  schedule:
    - cron: '0 9 * * *'
jobs:
  run-agent:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: pip install -r requirements.txt
      - run: python main.py
```

## 🎯 Validation Philosophy

**Why 5 layers?**
- **LLMs hallucinate** - they make up plausible-sounding information
- **Web scraping is messy** - HTML changes, ads appear, etc.
- **Business decisions are critical** - wrong vendor = wasted money

**How it prevents hallucinations:**
1. Forces LLM to extract only what's in the text
2. Verifies each extracted field exists in source
3. Checks against business constraints
4. Detects duplicates and anomalies
5. Cross-validates for logical consistency

**Result**: Only 100% verified, fact-based data reaches your database.

## 🐛 Troubleshooting

**"No module named 'langchain'"**
```bash
pip install langchain langchain-ollama langgraph
```

**"Ollama connection error"**
```bash
# Start Ollama service
ollama serve

# In another terminal, run agent
python main.py --test
```

**"Playwright not found"**
```bash
pip install playwright
playwright install chromium
```

**Low RAM issues**
- Close other applications
- Use `qwen2.5:3b` (smallest model)
- Reduce `max_vendors_per_day` in config.py

## 📝 Sample Output

```
╔══════════════════════════════════════════════════════════════╗
║                  AI SOURCING AGENT                           ║
║              OEM/ODM Vendor Discovery System                 ║
╚══════════════════════════════════════════════════════════════╝

[STEP 1] Setting up database...
✓ Database initialized

[STEP 2] Discovering vendors from platforms...
>>> Scraping Alibaba for: '15.6 inch Android tablet'...
  ✓ Found: 15.6" Android Tablet PC Industrial Touch Screen...
  → Scraped 5 vendors from Alibaba

[STEP 3] Processing vendors through validation pipeline...
--- Processing vendor 1/5 ---
>>> NODE 1: Extracting vendor information...
✓ Extracted data for: Shenzhen TechDisplay Co.
>>> NODE 2: Validating extracted data...
✓ ALL VALIDATION LAYERS PASSED
>>> NODE 3: Scoring vendor...
✓ Vendor score: 87/100
>>> NODE 4: Saving to database...
✓ Vendor saved to database (ID: 1)

📊 DAILY STATISTICS
--------------------------------------------------------------------------------
New Vendors Discovered: 5
Vendors Contacted Today: 3
Replies Received Today: 0
Total Vendors in Database: 15
Average Score (New Vendors): 78.4/100
```

## 🚀 Next Steps

1. Run test mode: `python main.py --test`
2. Review `data/reports/` folder
3. Check `data/vendors.db` with SQLite browser
4. Customize search keywords in `config.py`
5. Enable web scraping (install playwright)
6. Set up cron job for daily automation
7. Configure email for outreach

## 📄 License

Free to use for personal/commercial projects.

---

**Built with ❤️ for hardware startups**
*No hallucinations. Only facts.*
