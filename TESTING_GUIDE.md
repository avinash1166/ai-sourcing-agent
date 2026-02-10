# 🚀 TESTING GUIDE - GitHub Actions

## ✅ Changes Pushed Successfully!

Commit: `🔥 CRITICAL FIX: Target smart screens/digital signage instead of tablets`

---

## 📋 HOW TO TEST ON GITHUB ACTIONS

### **Step 1: Go to GitHub Actions**
1. Open: https://github.com/avinash1166/ai-sourcing-agent/actions
2. You should see: `AI Sourcing Agent - Self-Learning Mode` workflow

### **Step 2: Manually Trigger the Workflow**
1. Click on "AI Sourcing Agent - Self-Learning Mode"
2. Click the **"Run workflow"** button (top right)
3. Select branch: `main` 
4. Click green **"Run workflow"** button
5. Wait ~10 seconds, then refresh the page

### **Step 3: Monitor the Run**
You'll see a new workflow run starting. It will take **~60-70 minutes** total:

**Timeline:**
- 0-10 min: Setup (Python, Ollama, dependencies)
- 10-60 min: **Smart screen discovery & validation** ⭐
- 60-65 min: Email outreach
- 65-70 min: Telegram reporting

### **Step 4: Check Telegram for Results**
Around **60-70 minutes** after starting, you'll receive a Telegram message showing:

**Expected Good Results:**
```
🔍 Vendors Discovered: 5-12
📧 Emails Sent: 3-8
💬 Replies Received: 0-2

⭐ HIGH-PRIORITY VENDORS (Score ≥ 70)
━━━━━━━━━━━━━━━━━━━━━━━━

✅ Shenzhen HYY Technology Co., Ltd. (85/100)
   📧 sales@hyy-tech.com
   💰 $125/unit | MOQ: 100
   📝 15.6" wall mount Android smart display...

✅ Smart Display Solutions Ltd. (78/100)
   📧 info@smartdisplay.com
   💰 $95/unit | MOQ: 150
   📝 Digital signage Android wall panel...
```

**What to Look For:**
- ✅ Vendors mention "wall mount", "smart display", "digital signage"
- ✅ NO mentions of "portable tablet", "battery powered"
- ✅ Scores 70+ for relevant products
- ✅ Emails sent to high-scoring vendors

---

## 🔍 MONITORING DURING THE RUN

### **Check Live Logs:**
1. Click on the running workflow
2. Click on `smart-vendor-discovery` job
3. Expand steps to see:
   - "Run AI Sourcing Agent (1 hour runtime)" ← Main action here

### **What You'll See in Logs:**

**Good Signs:**
```
🌐 STEP 4: Intelligent Web Scraping
[1/10] '15.6 inch wall mount Android touch screen smart display'
  📥 Scraped 3 vendors
  🔄 Processing: Shenzhen HYY Technology
  ✅ Saved (Score: 85/100)

[2/10] 'Android digital signage 15.6 inch wall mount'
  📥 Scraped 2 vendors
  🔄 Processing: Smart Display Co.
  ✅ Saved (Score: 78/100)
```

**Expected Rejections (This is GOOD!):**
```
  🔄 Processing: Android Tablet Store
  ⚠️  Status: validation_failed
  Reason: CRITICAL: Product has battery (we need wall-powered displays only)
```

---

## ✅ SUCCESS CRITERIA

### **The Fix is Working If:**

1. **Vendor Names Include:**
   - "HYY Technology", "Digital Signage", "Smart Display"
   - "Wall Mount", "Advertising Display", "Menu Board"

2. **Product Descriptions Mention:**
   - "wall mount", "wall-powered", "DC adapter"
   - "digital signage", "smart display", "advertising screen"
   - "12V power", "VESA mount"

3. **NO Mentions Of:**
   - "portable", "battery", "tablet PC"
   - "gaming", "education tablet", "iPad alternative"

4. **Scores:**
   - High scores (70+): Wall-mounted smart screens
   - Low scores (<50): Portable tablets (auto-rejected)

5. **Emails Sent:**
   - Should be > 0 if high-scoring vendors found
   - Previously was 0 because nothing was relevant

---

## 📊 COMPARISON

### **Yesterday (Before Fix):**
```
🔍 Vendors: 8
📧 Emails: 0 ❌
Vendors: Shenzhen HYY (66), Windro (54) ⚠️
Issue: Finding tablets, not smart screens
```

### **Today (After Fix):**
```
🔍 Vendors: 5-12
📧 Emails: 3-8 ✅
Vendors: HYY Smart Display (85+), Digital Signage (75+)
Result: Wall-mounted smart screens only! ✅
```

---

## 🛠️ IF SOMETHING GOES WRONG

### **Workflow Fails?**
- Check the "Run AI Sourcing Agent" step logs
- Look for errors in migration or scraping
- Common issue: Playwright browser install (usually auto-fixes)

### **Still Finding Tablets?**
- Check the extraction logs - look for `wall_mount: false` or `has_battery: true`
- These should trigger auto-rejection in validation

### **No Vendors Found?**
- Made-in-China might be blocking (try different platform)
- Keywords might be too specific (check logs)
- This is better than finding wrong vendors!

### **Telegram Not Working?**
- Check if `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set in GitHub Secrets
- Workflow will continue and save results anyway

---

## 📝 AFTER THE RUN

### **Review Results:**

1. **Check Telegram Message** - Primary results notification
2. **Download Artifacts:**
   - Go to workflow run
   - Scroll to bottom → "Artifacts"
   - Download `sourcing-reports-XXX`
   - Check `daily_report_*.txt`

3. **Check Database:**
   - Artifacts include `vendors.db`
   - Download and open with SQLite browser
   - Query: `SELECT vendor_name, score, wall_mount, has_battery, product_type FROM vendors ORDER BY score DESC;`

---

## 🎯 EXPECTED TIMELINE

| Time | Status |
|------|--------|
| 0:00 | Workflow triggered |
| 0:05 | Ollama installing |
| 0:10 | Migration running ✅ |
| 0:15 | **Scraping started** ⭐ |
| 0:30 | Processing vendors |
| 0:45 | Validation & scoring |
| 1:00 | Email outreach |
| 1:05 | **Telegram report sent** 📱 |
| 1:10 | Complete! |

---

## 🚨 CRITICAL DIFFERENCES TO LOOK FOR

### **Database Schema:**
New run will have these columns populated:
- `wall_mount` = TRUE for smart screens
- `has_battery` = FALSE for wall-powered
- `product_type` = "smart screen" or "digital signage"

### **Validation Logs:**
You should see rejections like:
```
✗ Layer 3: Constraint Check: CRITICAL: Product has battery
✗ Layer 3: Constraint Check: CRITICAL: Product is portable/tablet
```

---

## ✅ YOU'RE READY!

**The workflow is now running (or about to run).**

**What to do:**
1. ☕ **Take a break** - It takes ~60 minutes
2. 📱 **Watch Telegram** - Report arrives automatically
3. 📊 **Review results** - Check if vendors are relevant
4. 🎉 **Celebrate** - If you see wall-mounted smart screens!

---

**Expected Result:** Relevant vendors with emails sent! 🎯

Good luck! Check your Telegram in ~60 minutes! 🚀
