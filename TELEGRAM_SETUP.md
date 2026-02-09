# 📱 TELEGRAM SETUP - Quick & Easy (3 Minutes)

## Why Telegram > Email?
- ✅ All messages saved in your Telegram chat
- ✅ Instant notifications on your phone
- ✅ No spam folder issues
- ✅ Easier to read and access
- ✅ Works on all devices

---

## 🚀 Step 1: Create Telegram Bot (2 minutes)

### 1.1 Open Telegram and find @BotFather
- Open Telegram app or web (https://web.telegram.org)
- Search for: `@BotFather`
- Start chat with BotFather (the official bot creator)

### 1.2 Create your bot
Send this command to BotFather:
```
/newbot
```

BotFather will ask:
- **Bot name:** `AI Sourcing Agent` (or any name you like)
- **Bot username:** `your_sourcing_bot` (must end with "bot")

### 1.3 Get your Bot Token
BotFather will reply with:
```
Done! Your token is: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

**Copy this token!** You'll need it in Step 3.

### 1.4 Find your bot and start a chat
- Search for your bot username in Telegram
- Click "Start" to begin chat with your bot

---

## 🔑 Step 2: Get Your Chat ID (1 minute)

### Option A: Use this bot (easiest)
1. Search for `@userinfobot` in Telegram
2. Start chat and it will instantly show your Chat ID
3. Copy the number (e.g., `123456789`)

### Option B: Use web method
1. Send any message to your bot (e.g., "hello")
2. Open this URL in browser (replace YOUR_BOT_TOKEN):
```
https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
```
3. Look for `"chat":{"id":123456789}` in the response
4. Copy that number

**Example:**
If response shows: `"chat":{"id":987654321}`
Your Chat ID is: `987654321`

---

## ⚙️ Step 3: Add to GitHub Secrets (1 minute)

1. **Go to your repository settings:**
   https://github.com/avinash1166/ai-sourcing-agent/settings/secrets/actions

2. **Add TELEGRAM_BOT_TOKEN:**
   - Click "New repository secret"
   - Name: `TELEGRAM_BOT_TOKEN`
   - Value: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz` (your token from Step 1.3)
   - Click "Add secret"

3. **Add TELEGRAM_CHAT_ID:**
   - Click "New repository secret"
   - Name: `TELEGRAM_CHAT_ID`
   - Value: `123456789` (your Chat ID from Step 2)
   - Click "Add secret"

4. **Keep existing email secrets** (for vendor conversations):
   - `USER_EMAIL` = `avinashlingamop123@gmail.com`
   - `EMAIL_PASSWORD` = [Your Gmail app password]
   
   **Note:** Email is still used to TALK TO VENDORS. Telegram is for YOUR reports!

---

## ✅ Step 4: Test It! (30 seconds)

1. Go to Actions: https://github.com/avinash1166/ai-sourcing-agent/actions
2. Click "AI Sourcing Agent - Self-Learning Mode"
3. Click "Run workflow" → "Run workflow"
4. Wait 10-15 minutes
5. **Check your Telegram!** You'll get a message! 📱

---

## 📱 What You'll Receive on Telegram

### Daily Report (Every day at ~10 AM UTC):
```
🤖 AI Sourcing Agent - Daily Report
📅 February 9, 2026

━━━━━━━━━━━━━━━━━━━━━━━━
📊 TODAY'S SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━

🔍 Vendors Discovered: 15
📧 Emails Sent: 8
💬 Replies Received: 3

━━━━━━━━━━━━━━━━━━━━━━━━
⭐ HIGH-PRIORITY VENDORS (Score ≥ 70)
━━━━━━━━━━━━━━━━━━━━━━━━

✅ Shenzhen Display Tech - Score: 85/100
   📧 contact@sdtech.com
   💰 $125/unit | MOQ: 150
   📝 15.6" Android tablet, customizable...

━━━━━━━━━━━━━━━━━━━━━━━━
💬 VENDOR RESPONSES
━━━━━━━━━━━━━━━━━━━━━━━━

💬 TechVision Co
   ⏱️ Responded in 3.2 hours
   💰 Price: $135 | MOQ: 200
   📄 "Thank you for your inquiry..."
```

### Instant Alerts (Real-time):
```
🚨 HIGH-SCORE VENDOR FOUND!

⭐ XYZ Electronics
📊 Score: 92/100
📧 sales@xyz.com
💰 $128/unit
📦 MOQ: 120

⏰ 14:23 UTC
```

---

## 🔒 Security Notes

- ✅ Bot token is encrypted in GitHub Secrets
- ✅ Only your bot can send to your chat ID
- ✅ Only GitHub Actions can access the token
- ✅ Revoke token anytime via @BotFather

---

## 🆘 Troubleshooting

### Not receiving messages?

**Check 1: Verify secrets are set correctly**
- Go to: Settings → Secrets and variables → Actions
- Should see: `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`

**Check 2: Test your bot manually**
- Send a message to your bot in Telegram
- It should appear in the chat (bot won't reply, that's normal)

**Check 3: Verify Chat ID**
- Use @userinfobot again to confirm your Chat ID
- Make sure it's just numbers (e.g., `123456789`)
- NO quotes, NO spaces

**Check 4: Check GitHub Actions logs**
- Actions tab → Latest run → Check for errors
- Look for "Telegram" messages in logs

### Bot not responding?

**Normal!** Your bot doesn't need to respond to your messages. It only SENDS you reports from GitHub Actions.

---

## 📝 Quick Reference

**What you need:**
1. Bot Token (from @BotFather): `1234567890:ABC...`
2. Chat ID (from @userinfobot): `123456789`

**Where to add them:**
- GitHub repo → Settings → Secrets and variables → Actions

**Two secrets needed:**
- `TELEGRAM_BOT_TOKEN` = Your bot token
- `TELEGRAM_CHAT_ID` = Your chat ID

**Email still needed for:**
- `USER_EMAIL` = Your Gmail (to talk to vendors)
- `EMAIL_PASSWORD` = Gmail app password (to talk to vendors)

---

## 🎉 All Done!

Your agent will now send reports to **Telegram** instead of email!

**Benefits:**
- 📱 Check on phone anytime
- 💾 All messages saved in Telegram
- 🚀 Instant notifications
- 📊 Easy to scroll through history
- ✅ No spam folder problems

**Next:** Just wait for your first Telegram report! 🤖
