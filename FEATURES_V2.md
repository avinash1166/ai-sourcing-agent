# AI Sourcing Agent V2 - Self-Learning Features

## 🚀 New Features Added

### 1. **Dynamic Keyword Learning** ✅
The agent now learns from successful vendor discoveries and generates new search keywords automatically.

**How it works:**
- Analyzes vendors that scored 70+ points
- Extracts common patterns from their descriptions
- Uses AI to generate variations of successful keywords
- Avoids keywords that led to poor vendors

**Example:**
```
Day 1: Uses base keywords → Finds 5 good vendors
Day 2: Learns from those vendors → Generates 10 new keywords
Day 3: Uses 17 total keywords (7 base + 10 learned)
```

**Files:**
- `learning_engine.py` - Core learning logic
- `main_v2.py` - Integrated workflow


### 2. **Multi-Turn Email Conversations** ✅
The agent now monitors your inbox and automatically responds to vendor replies.

**Capabilities:**
- Checks Gmail inbox for vendor responses
- Extracts key information (price, MOQ, customization)
- Generates intelligent follow-up emails
- Tracks conversation history in database
- Knows when to stop contacting (learned behavior)

**Example Flow:**
```
Day 1: Agent sends inquiry → Vendor replies
Day 2: Agent reads reply → Extracts price/MOQ → Sends follow-up
Day 3: Vendor provides specs → Agent confirms interest
```

**Files:**
- `email_conversation.py` - Email conversation manager
- Updates `vendors` table with response data

**Required Setup:**
```bash
# Set GitHub secrets:
USER_EMAIL=your_email@gmail.com
EMAIL_PASSWORD=your_app_password  # Gmail App Password
```


### 3. **Daily Email Reports** ✅
You receive a beautiful HTML email every day summarizing all activities.

**Report Includes:**
- 📊 Total vendors discovered
- ⭐ High-scoring vendors (≥70)
- 📋 Medium-scoring vendors (50-69)
- 💬 Vendor responses with prices/MOQ
- 🔍 Keywords used
- ⏱️ Response times

**Example:**
Every day at ~10 AM UTC, you get an email:
```
Subject: AI Sourcing Report - Feb 9, 2026 - 15 Vendors Found

High-Priority Vendors:
✅ Shenzhen Display Tech - Score: 85/100
   Email: contact@sdtech.com
   $125/unit, MOQ: 150

Responses Received:
💬 TechVision Co responded in 3.2 hours
   Price: $135, MOQ: 200
```

**Files:**
- `daily_email_report.py` - Email report generator


### 4. **Self-Learning System** ✅
The agent learns from every interaction and improves over time.

**What it learns:**
- Which keywords find good vendors
- Which vendors to avoid contacting again
- Optimal response patterns
- Price ranges that work
- MOQ patterns

**Learning Metrics:**
- Success rate (vendors that respond positively)
- Keyword effectiveness
- Red flag patterns
- Optimal contact timing

**Database Enhancement:**
New fields added to track learning:
```sql
discovered_date, keywords_used, validation_status, 
rejection_reason, email_sent_count, last_email_date,
email_response, price_quoted, moq_quoted,
customization_confirmed, response_time_hours
```


### 5. **1-Hour Daily Runtime** ✅
GitHub Actions now runs for a full hour to maximize vendor discovery.

**Runtime Breakdown:**
```
00:00 - 00:05  Learning analysis
00:05 - 00:10  Keyword generation
00:10 - 00:15  Email conversation processing
00:15 - 00:55  Intelligent web scraping (time-boxed)
00:55 - 01:00  Reporting & email
```

**Smart Time Management:**
- Automatically stops at 1 hour
- Prioritizes high-value keywords first
- Skips vendors it learned to avoid
- Maximizes vendor processing within time limit


## 📋 Updated Configuration

### GitHub Secrets Required:
```bash
# Go to: Settings → Secrets and variables → Actions → New secret

USER_EMAIL = avinashlingamop123@gmail.com
EMAIL_PASSWORD = your_gmail_app_password
```

### Generate Gmail App Password:
1. Go to Google Account → Security
2. Enable 2-Factor Authentication
3. Search for "App Passwords"
4. Create new app password for "Mail"
5. Copy the 16-character password
6. Add to GitHub secrets


## 🎯 How to Use

### First Time Setup:
```bash
# 1. Push code to GitHub (already done)
git push origin main

# 2. Add GitHub secrets
# Go to repo Settings → Secrets → Add USER_EMAIL and EMAIL_PASSWORD

# 3. Enable GitHub Actions
# Go to Actions tab → Enable workflows

# 4. Test manually
# Actions → AI Sourcing Agent → Run workflow
```

### Daily Operation:
- **Automatic:** Runs every day at 9 AM UTC (1 hour)
- **Manual:** Click "Run workflow" in Actions tab anytime
- **Check results:** 
  - Email report sent to your inbox
  - Reports in GitHub artifacts
  - Database committed to repo


## 📊 Performance Improvements

| Feature | Before | After V2 |
|---------|--------|----------|
| Keywords | 7 static | 7 base + 10 learned = 17 |
| Email | One-time | Multi-turn conversations |
| Learning | None | Continuous improvement |
| Reports | File only | File + Email |
| Runtime | ~15 min | 1 hour (optimized) |
| Vendor quality | Random | Improves over time |


## 🧠 Learning Examples

### Week 1:
```
Keywords: 7 base keywords
Vendors found: 20
High-quality: 3 (15%)
Learning data: Insufficient
```

### Week 4:
```
Keywords: 7 base + 12 learned = 19 keywords
Vendors found: 35
High-quality: 12 (34%)
Learning insights:
  ✓ Keywords with "customizable" work better
  ✓ Avoid vendors mentioning "loop player"
  ✓ Shenzhen region vendors respond faster
```

### Month 3:
```
Keywords: 7 base + 18 learned = 25 keywords
Vendors found: 50
High-quality: 28 (56%)
Learning insights:
  ✓ Optimal price range identified: $120-140
  ✓ Best keywords: "Android kiosk customizable"
  ✓ Response rate: 45% (up from 15%)
```


## 🔧 Technical Stack

**New Dependencies:**
- `learning_engine.py` - Machine learning logic
- `email_conversation.py` - Email management (IMAP/SMTP)
- `daily_email_report.py` - HTML email reports
- `main_v2.py` - Enhanced orchestrator

**Updated Files:**
- `oem_search.py` - Enhanced database schema
- `.github/workflows/` - 1-hour runtime config


## 🎉 What You Get

### Every Day:
1. ✅ **Email in your inbox** with full report
2. ✅ **Database updated** with new vendors
3. ✅ **Conversations managed** automatically
4. ✅ **Learning improved** from every run
5. ✅ **Keywords optimized** based on success

### Over Time:
- 📈 **Increasing quality** of vendor discoveries
- 🎯 **Better targeting** through learned keywords
- ⚡ **Faster responses** to promising vendors
- 💡 **Smarter decisions** on who to contact
- 🚀 **Continuous improvement** without manual intervention


## 📝 Monitoring

### Check Status:
```bash
# GitHub Actions tab shows:
- Last run time
- Success/failure status
- Vendors processed
- Artifacts (reports)

# Your email shows:
- Daily summary
- High-priority vendors
- Vendor responses
- Keywords used
```

### View Learning Progress:
```bash
# Run locally to see learning report
python main_v2.py test

# Check database
sqlite3 data/vendors.db
SELECT COUNT(*), AVG(score) FROM vendors WHERE discovered_date >= date('now', '-7 days');
```


## 🆘 Troubleshooting

### No email received?
- Check GitHub secrets (USER_EMAIL, EMAIL_PASSWORD)
- Verify Gmail App Password is correct
- Check spam folder

### Learning not improving?
- Need minimum 5 successful vendors (score ≥70)
- Runs daily, give it 1-2 weeks
- Check `data/vendors.db` for historical data

### Conversations not working?
- Gmail App Password must be set
- IMAP must be enabled in Gmail settings
- Check Actions log for errors


## 🚀 Next Steps

Your agent is now fully autonomous and self-improving! Just:
1. Add GitHub secrets (email credentials)
2. Enable GitHub Actions
3. Let it run daily
4. Check your email for reports
5. Watch it get smarter over time

**No manual intervention needed!** 🎉
