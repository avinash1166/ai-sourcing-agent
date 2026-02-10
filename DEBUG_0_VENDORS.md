# 🐛 DEBUG: Why Agent Ran for Only 6 Minutes

## 🔍 PROBLEM YOU REPORTED

```
Telegram Message:
🔍 Vendors Discovered: 0
📧 Emails Sent: 0
💬 Replies Received: 0
⏰ Generated at 21:20 UTC

Agent ran for ~6 minutes only (expected: 60 minutes)
```

---

## ❓ LIKELY CAUSES (In Order of Probability)

### 1. **Playwright Not Installed Properly** (MOST LIKELY)
The workflow installs Playwright, but it might fail silently:

```yaml
# In workflow file:
pip install playwright
playwright install chromium --with-deps
```

**Problem:** If this fails, scraper crashes immediately when trying to use Chromium browser.

**Result:** 
- Scraper setup crashes
- Agent skips all keywords
- Reports 0 vendors
- Exits early (~6 min instead of 60 min)

### 2. **Scraper Import Error**
If `VendorScraper` import fails, the agent would crash in Step 4.

### 3. **Database Migration Failed**
If database schema is wrong, agent might crash when trying to save vendors.

### 4. **Ollama Not Ready**
If Ollama service isn't fully started, LLM calls might fail.

---

## ✅ WHAT I JUST FIXED

### 1. **Added Debug Logging**
Now the agent will print:
```
🌐 STEP 4: Intelligent Web Scraping
✓ Scraper initialized
✓ Validation agent built
✓ Starting keyword loop with 7 keywords...

[1/7] '15.6 inch Android tablet' | ⏱️ 59.5 min left
  📥 Scraped 3 vendors
  🔄 Processing: Shenzhen Tech Co
  ✅ Saved (Score: 75/100)
```

If it crashes, you'll see:
```
❌ CRITICAL ERROR in scraping setup: [error message]
Stack trace: [full error details]
```

### 2. **Added Error Handling**
```python
try:
    scraper = VendorScraper()  # If this fails, you'll see why
    agent = build_agent()
except Exception as e:
    print(f"❌ CRITICAL ERROR: {e}")
    print(f"Stack trace: {traceback.format_exc()}")
```

### 3. **Fixed conversation_results Bug**
If email checking crashed, the variable wasn't defined and caused a crash later.

Now it's initialized:
```python
conversation_results = {"replies_found": 0, ...}  # Default value
```

---

## 🧪 NEXT STEP: Run It Again & Check Logs

### Run in GitHub Actions:
1. Go to: https://github.com/avinash1166/ai-sourcing-agent/actions
2. Click "Run workflow"
3. Wait 10-15 minutes
4. Click on the running job
5. **Click "Run AI Sourcing Agent (1 hour runtime)" step**
6. **Read the output logs**

### What to Look For:

#### ✅ **If It's Working** (you'll see):
```
🌐 STEP 4: Intelligent Web Scraping
✓ Scraper initialized
✓ Validation agent built
✓ Starting keyword loop with 7 keywords...

[1/7] '15.6 inch Android tablet'
  📥 Scraped 3 vendors
  🔄 Processing: Vendor ABC
  ✅ Saved (Score: 72/100)
  🔄 Processing: Vendor XYZ
  ✅ Saved (Score: 85/100)
```

Then it'll run for **60 minutes** finding vendors.

#### ❌ **If Playwright Failed** (you'll see):
```
❌ CRITICAL ERROR in scraping setup: playwright._impl._api_types.Error: 
Executable doesn't exist at /home/runner/.cache/ms-playwright/chromium-1091/chrome-linux/chrome

Stack trace:
  File "scraper.py", line 45, in __init__
    browser = playwright.chromium.launch()
```

**Solution:** Workflow Playwright installation is broken. Need to fix workflow file.

#### ❌ **If Scraper Import Failed** (you'll see):
```
❌ CRITICAL ERROR in scraping setup: No module named 'playwright'

Stack trace:
  File "main_v2.py", line 115
    from scraper import VendorScraper
```

**Solution:** Dependencies not installed properly.

#### ❌ **If Database Migration Failed** (earlier in logs):
```
Running database migration...
Error: no such table: vendors
```

**Solution:** Migration script didn't run. Database schema missing.

---

## 🔧 POSSIBLE FIXES (Based on What You Find)

### Fix 1: Playwright Installation in Workflow
If Playwright is failing, update workflow:

```yaml
- name: Install Playwright
  run: |
    pip install playwright==1.40.0
    python -m playwright install chromium --with-deps
    
    # Verify installation
    python -c "from playwright.sync_api import sync_playwright; print('✓ Playwright OK')"
```

### Fix 2: Use Simpler Scraper (No Playwright)
If Playwright keeps failing, fall back to requests + BeautifulSoup:

```python
# In scraper.py - add fallback method
def scrape_simple(self, url):
    response = requests.get(url, headers=self.headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    # Extract vendor data from HTML
```

### Fix 3: Increase Timeout for Setup
If Ollama/Playwright installation takes too long:

```yaml
# Increase timeout
timeout-minutes: 90  # Was: 70
```

---

## 📊 WHAT SHOULD HAPPEN (Expected Flow)

### Minute 0-15: Setup
```
✓ Install Python
✓ Install Ollama (10 min)
✓ Download qwen2.5-coder:3b model (5 min)
✓ Install pip dependencies
✓ Install Playwright + Chromium (3 min)
✓ Migrate database
```

### Minute 15-75: Main Work
```
Step 1: Check emails (1 min)
Step 2: Learning analysis (1 min)
Step 3: Keywords (30 sec)
Step 4: SCRAPING (55+ minutes) ← This should run!
  [1/7] keyword → scrape → validate → save
  [2/7] keyword → scrape → validate → save
  ...
  25-40 vendors saved
Step 5: Email outreach (2 min)
Step 6: Report (30 sec)
```

### Minute 75: Finish
```
🎉 DAILY RUN COMPLETE
⏱️ Duration: 60.3 minutes
📦 Vendors discovered: 28
📨 Outreach emails sent: 14
📱 Telegram: Report sent!
```

---

## 🎯 ACTION ITEMS

### 1. **Run Workflow Again** (with new debug logging)
   - Go to Actions tab
   - Click "Run workflow"
   - Monitor the logs in real-time

### 2. **Check the "Run AI Sourcing Agent" Step Logs**
   - Look for "✓ Scraper initialized" message
   - Look for "❌ CRITICAL ERROR" messages
   - Copy/paste any errors you see

### 3. **Tell Me What You See**
   - If you see "✓ Scraper initialized" → Agent is working!
   - If you see "❌ CRITICAL ERROR" → Copy the error message
   - If it still runs for only 6 min → Check which step it stops at

---

## 💡 QUICK CHECK: Is It Running Now?

After you trigger the workflow:

**First 5 minutes:** Setup (Ollama install, deps)  
**At minute 10:** Should see "✓ Scraper initialized"  
**At minute 15-60:** Should see vendor processing  
**At minute 60:** Should get Telegram report with 20-40 vendors

**If it stops at minute 6:** Check logs for error messages (I added full stack traces now)

---

## 🆘 If Still Failing After This Run

Send me:
1. **Screenshot** of GitHub Actions logs (the "Run AI Sourcing Agent" step)
2. **The error message** (if any)
3. **Which step it stopped at** (Step 1, 2, 3, or 4?)

I'll fix it immediately! 🔧

---

**TLDR:** Run it again now. The new debug logging will show us EXACTLY where it's crashing. Most likely: Playwright not installing properly in GitHub Actions environment.
