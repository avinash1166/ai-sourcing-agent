# 🚨 TELEGRAM BUTTONS STILL NOT WORKING? - TROUBLESHOOTING GUIDE

## Quick Check: Are the buttons ACTUALLY not working, or just not responding YET?

### **Scenario A: You clicked a button less than 5 minutes ago**
**Status:** ⏰ **NORMAL** - System polls every 5 minutes  
**Action:** Wait a bit longer, or manually trigger (see below)

### **Scenario B: You clicked over 5 minutes ago, still nothing**
**Status:** ⚠️ **ISSUE** - GitHub Actions might not be running  
**Action:** Follow troubleshooting steps below

---

## INSTANT FIX: Manual Trigger (30 seconds)

**Option 1: Via GitHub Web Interface** (EASIEST)

1. Open: https://github.com/avinash1166/ai-sourcing-agent/actions
2. Click "**Telegram Callback Listener - Continuous**" in the left sidebar
3. Click blue "**Run workflow**" button (top right)
4. Select "Branch: **main**"
5. Click green "**Run workflow**" button
6. Wait 30-60 seconds
7. **Go back to Telegram** - your button should now respond!

**Option 2: Via GitHub CLI** (if installed)

```bash
cd /home/kali/ai_agents_learning
gh workflow run telegram-callback-listener.yml
```

---

## WHY Buttons Aren't Responding

### Problem 1: **GitHub Actions Schedule Hasn't Started Yet**

GitHub Actions cron schedules (`*/5 * * * *`) don't run immediately after pushing code.

**First run might be:** 
- Next 5-minute mark (e.g., if it's 14:23 now, next run is 14:25)
- OR scheduled but in queue (GitHub Actions has delays during peak times)

**Solution:** Manually trigger once (see above)

---

### Problem 2: **Missing GitHub Secrets**

The workflow needs these secrets set in GitHub:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

**Check if secrets are set:**

1. Go to: https://github.com/avinash1166/ai-sourcing-agent/settings/secrets/actions
2. Verify these two secrets exist
3. If missing, add them:
   - Click "New repository secret"
   - Name: `TELEGRAM_BOT_TOKEN`
   - Value: Your bot token from @BotFather
   - Click "Add secret"
   - Repeat for `TELEGRAM_CHAT_ID`

---

### Problem 3: **Workflow is Disabled**

GitHub might auto-disable workflows if repo is inactive.

**Check:**

1. Go to: https://github.com/avinash1166/ai-sourcing-agent/actions
2. Look for yellow banner saying "Workflows have been disabled"
3. If you see it, click "Enable workflows"

---

### Problem 4: **Button Callback Data Format Wrong**

If buttons show but don't do anything when clicked, the callback_data might be malformed.

**Expected format:**
- `relevant_1` (for vendor ID 1)
- `irrelevant_2` (for vendor ID 2)

**Check in code:**
```python
# telegram_feedback.py line 112-113
{"text": "✅ RELEVANT", "callback_data": f"relevant_{vendor_id}"},
{"text": "❌ IRRELEVANT", "callback_data": f"irrelevant_{vendor_id}"}
```

This looks correct in our code ✅

---

## DIAGNOSTIC: Test if Button Clicks Are Being Sent

Run this locally to see if Telegram is receiving your clicks:

```bash
cd /home/kali/ai_agents_learning
python telegram_diagnostic.py YOUR_BOT_TOKEN YOUR_CHAT_ID
```

Replace:
- `YOUR_BOT_TOKEN` with your actual bot token (from GitHub Secrets or @BotFather)
- `YOUR_CHAT_ID` with your actual chat ID (from @userinfobot)

**This will tell you:**
✅ If bot is valid  
✅ If button clicks are stored in Telegram  
✅ If bot can send messages to you  

---

## SOLUTION: Get It Working RIGHT NOW

### Step 1: Get Your Credentials

**Bot Token:**
1. Open Telegram
2. Search for `@BotFather`
3. Send `/mybots`
4. Select your bot
5. Click "API Token"
6. Copy the token (looks like `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

**Chat ID:**
1. Open Telegram
2. Search for `@userinfobot`
3. Send `/start`
4. It will reply with your ID (looks like `123456789`)

### Step 2: Test Locally (INSTANT RESULTS)

Create a file called `.env` in your project folder:

```bash
cd /home/kali/ai_agents_learning
cat > .env << 'EOF'
TELEGRAM_BOT_TOKEN=paste_your_token_here
TELEGRAM_CHAT_ID=paste_your_chat_id_here
EOF
```

Then run:

```bash
python test_telegram_callbacks.py
```

**Expected output:**
```
🔄 Checking for pending Telegram button clicks...
📥 Found 1 pending update(s)
📲 Processing callback: relevant_1
✅ Feedback recorded: relevant for vendor 1
```

### Step 3: Verify GitHub Secrets Are Set

```bash
# Check if secrets exist (won't show values, just names)
gh secret list
```

Should show:
```
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
USER_EMAIL
EMAIL_PASSWORD
```

If missing, set them:

```bash
gh secret set TELEGRAM_BOT_TOKEN
# Paste your token when prompted

gh secret set TELEGRAM_CHAT_ID  
# Paste your chat ID when prompted
```

### Step 4: Manually Trigger GitHub Action

```bash
gh workflow run telegram-callback-listener.yml
```

Wait 30 seconds, then check Telegram - button should respond!

---

## Expected Behavior After Fix

1. **You click ✅ RELEVANT** button in Telegram
2. **Within 5 minutes** (or instantly if manually triggered):
   - Popup appears: "✅ Feedback recorded! Thank you."
   - Button text changes to: "✅ Marked as RELEVANT"
3. **Database updated** with your feedback
4. **Next AI run** uses your feedback to improve vendor selection

---

## Still Not Working?

### Check GitHub Actions Logs

1. Go to: https://github.com/avinash1166/ai-sourcing-agent/actions
2. Click on latest "Telegram Callback Listener" run
3. Click "process-telegram-callbacks" job
4. Expand "Process Telegram callbacks" step
5. Look for errors

**Common errors:**

**Error: "Missing TELEGRAM_BOT_TOKEN"**
→ Secret not set correctly in GitHub

**Error: "Unauthorized"**
→ Bot token is invalid or revoked

**Error: "Chat not found"**
→ Chat ID is wrong or bot was blocked by user

**Error: "No updates found"**
→ No button clicks pending (already processed or none clicked)

---

## Manual Workaround (Until Automation Works)

If GitHub Actions keeps failing, you can process feedback manually:

```bash
# Run this whenever you click buttons
cd /home/kali/ai_agents_learning
export TELEGRAM_BOT_TOKEN="your_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
python telegram_callback_processor.py --once
```

This will:
- Fetch your button clicks
- Process them
- Update database
- Send confirmation

---

## Contact Information

If still stuck, check:
1. GitHub Actions logs (link above)
2. Telegram bot @BotFather (check if bot still active)
3. @userinfobot (verify your chat ID)

---

**Last Updated:** Feb 11, 2026  
**Status:** Awaiting user test results  
**Next Action:** User should manually trigger workflow once to test
