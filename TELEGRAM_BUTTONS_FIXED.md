# Telegram Callback System - Button Click Processing

## Problem Fixed

**BEFORE:** Telegram buttons (✅ RELEVANT / ❌ IRRELEVANT) didn't respond when clicked.

**WHY:** Telegram sends `callback_query` updates when buttons are clicked, but we had **no listener** to receive them!

**NOW:** Full callback processing system with multiple options.

---

## How It Works

### 1. **User clicks button** in Telegram
   - Telegram generates a `callback_query` with data like `relevant_123` or `irrelevant_123`

### 2. **Callback processor fetches updates** from Telegram API
   - Uses `getUpdates` API endpoint
   - Retrieves all pending callbacks since last check

### 3. **Feedback is recorded** in database
   - Updates `vendors` table with `human_feedback` column
   - Stores in `feedback_patterns` table for learning

### 4. **User gets confirmation**
   - Button shows "✅ Marked as RELEVANT" or "❌ Marked as IRRELEVANT"
   - Popup notification appears

---

## Deployment Options

### **Option A: GitHub Actions (Automated) - RECOMMENDED** ✅

Two workflows run automatically:

#### **1. Daily Sourcing Run** (once per day)
- Checks for pending callbacks BEFORE starting search
- File: `.github/workflows/daily-sourcing.yml`
- Schedule: 9 AM UTC daily
- Duration: ~1 hour

#### **2. Continuous Callback Listener** (every 5 minutes)
- Dedicated workflow just for processing button clicks
- File: `.github/workflows/telegram-callback-listener.yml`
- Schedule: Every 5 minutes
- Duration: ~30 seconds

**Result:** Your button clicks are processed within 5 minutes, 24/7!

---

### **Option B: Manual Testing (Local)**

Run the test script manually when you want to process callbacks:

```bash
cd /home/kali/ai_agents_learning
python test_telegram_callbacks.py
```

**Note:** Requires environment variables:
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
python test_telegram_callbacks.py
```

---

### **Option C: Continuous Local Polling** (For Development)

Run a background process that polls every 30 seconds:

```bash
python telegram_callback_processor.py --continuous 30
```

**To run in background:**
```bash
nohup python telegram_callback_processor.py --continuous 30 > telegram_callback.log 2>&1 &
```

**To stop:**
```bash
pkill -f telegram_callback_processor
```

---

## Files Created/Modified

### **New Files:**
1. `telegram_callback_processor.py` - Core callback processing logic
2. `test_telegram_callbacks.py` - Manual testing script
3. `.github/workflows/telegram-callback-listener.yml` - Continuous listener (every 5 min)

### **Modified Files:**
1. `.github/workflows/daily-sourcing.yml` - Added callback processing step
2. `telegram_feedback.py` - Already had `process_callback()` method

---

## Usage Guide

### **For You (User):**

1. **Click buttons in Telegram** whenever you get vendor feedback requests
2. **Wait up to 5 minutes** for processing (GitHub Actions runs every 5 min)
3. **Check confirmation** - Button text changes to "✅ Marked as RELEVANT"
4. **Next AI run learns** from your feedback!

### **What Happens Behind the Scenes:**

```
User clicks ✅ RELEVANT
    ↓
Telegram stores callback_query
    ↓
GitHub Action runs (every 5 min)
    ↓
telegram_callback_processor.py fetches updates
    ↓
Parses: "relevant_123" → vendor_id=123, feedback=relevant
    ↓
Updates database:
   - vendors.human_feedback = 'relevant'
   - feedback_patterns learns: wall_mount=yes → positive
    ↓
Sends confirmation back to Telegram
    ↓
Button changes to "✅ Marked as RELEVANT"
```

---

## Testing Your Buttons

### **Step 1:** Click a button in Telegram
- Go to any vendor feedback message
- Click ✅ RELEVANT or ❌ IRRELEVANT

### **Step 2:** Wait 5 minutes (or manually trigger)

**Option A: Wait for automatic processing**
- GitHub Actions will run within 5 minutes

**Option B: Manual trigger (instant)**
```bash
# On GitHub: Actions → "Telegram Callback Listener" → "Run workflow"
```

### **Step 3:** Verify it worked
- Button should change to show your choice
- You should see a popup: "✅ Feedback recorded! Thank you."

---

## Troubleshooting

### **Buttons still not working after 5 minutes?**

Check GitHub Actions logs:
1. Go to: https://github.com/avinash1166/ai-sourcing-agent/actions
2. Find "Telegram Callback Listener" workflow
3. Check latest run logs

**Common issues:**
- Missing `TELEGRAM_BOT_TOKEN` secret → Add in GitHub Settings → Secrets
- Missing `TELEGRAM_CHAT_ID` secret → Add in GitHub Settings → Secrets
- Workflow disabled → Enable in Actions tab

---

### **Want instant response instead of 5-minute delay?**

**Option 1:** Change GitHub Actions schedule from `*/5` to `*/1` (every minute)
```yaml
# In .github/workflows/telegram-callback-listener.yml
schedule:
  - cron: '* * * * *'  # Every minute (uses more GitHub Actions quota)
```

**Option 2:** Run local polling (see Option C above)

---

## Database Schema

### **vendors table** (feedback columns):
```sql
human_feedback TEXT       -- 'relevant' or 'irrelevant'
feedback_reason TEXT      -- Optional reason (future use)
feedback_date TEXT        -- ISO timestamp when feedback given
```

### **feedback_patterns table** (learning):
```sql
feature_type TEXT         -- 'wall_mount', 'has_battery', 'os', etc.
feature_value TEXT        -- 'yes', 'no', 'Android', '15.6 inch', etc.
sentiment TEXT            -- 'positive' or 'negative'
count INTEGER             -- How many times this pattern seen
last_seen TEXT            -- Most recent occurrence
```

---

## What The AI Learns

When you click **✅ RELEVANT** on a vendor with:
- Wall mount: Yes
- Battery: No
- OS: Android
- Screen: 15.6 inch

**System learns:**
```
✅ wall_mount=yes → positive (+1)
✅ has_battery=no → positive (+1)
✅ os=Android → positive (+1)
✅ screen_size=15.6 inch → positive (+1)
```

**Future scoring adjustment:**
- Vendors matching these patterns get **+5 to +15 bonus points**
- More matches = higher boost

---

## Next Steps

1. **Push this code to GitHub** ✅ (about to do this)
2. **Click buttons in Telegram** to test
3. **Wait 5 minutes** (or manually trigger workflow)
4. **Verify buttons respond** with confirmation
5. **Next daily run** will show improved vendor selection based on your feedback!

---

**Status: READY TO DEPLOY** 🚀

All code is written, tested structure is ready. Just need to push to GitHub and the system will start working!
