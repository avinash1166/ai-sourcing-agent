# 📧 Email Setup Guide - Quick Start

## 🎯 Goal
Enable your AI agent to send you daily reports and manage vendor conversations automatically.

## ⚡ Quick Setup (5 minutes)

### Step 1: Generate Gmail App Password

1. **Go to Google Account Settings**
   - Visit: https://myaccount.google.com/security
   
2. **Enable 2-Factor Authentication** (if not already enabled)
   - Click "2-Step Verification"
   - Follow the setup wizard
   - Required for App Passwords

3. **Create App Password**
   - Search for "App Passwords" in the search bar
   - Click "App passwords"
   - Select:
     - App: Mail
     - Device: Other (enter "AI Sourcing Agent")
   - Click "Generate"
   - **Copy the 16-character password** (e.g., `abcd efgh ijkl mnop`)
   - Keep this safe - you'll only see it once!

### Step 2: Add GitHub Secrets

1. **Go to your repository**
   - https://github.com/avinash1166/ai-sourcing-agent

2. **Navigate to Settings**
   - Click "Settings" tab (top right)
   - Click "Secrets and variables" → "Actions"

3. **Add USER_EMAIL secret**
   - Click "New repository secret"
   - Name: `USER_EMAIL`
   - Value: `avinashlingamop123@gmail.com`
   - Click "Add secret"

4. **Add EMAIL_PASSWORD secret**
   - Click "New repository secret"
   - Name: `EMAIL_PASSWORD`
   - Value: [Paste the 16-character app password from Step 1]
   - **Important:** Remove spaces (e.g., `abcdefghijklmnop`)
   - Click "Add secret"

### Step 3: Verify Setup

1. **Go to Actions tab**
   - https://github.com/avinash1166/ai-sourcing-agent/actions

2. **Enable workflows** (if prompted)
   - Click "I understand my workflows, go ahead and enable them"

3. **Test manually**
   - Click "AI Sourcing Agent - Self-Learning Mode"
   - Click "Run workflow" dropdown
   - Click green "Run workflow" button
   - Wait ~10 minutes
   - Check your email inbox!

## ✅ What You'll Receive

### Daily Email (Every day at ~10 AM UTC):
```
Subject: AI Sourcing Report - Feb 9, 2026 - 15 Vendors Found

📊 Today's Summary
- Vendors Discovered: 15
- Emails Sent: 8
- Replies Received: 3

⭐ High-Priority Vendors (Score ≥ 70)
✅ Shenzhen Display Tech - Score: 85/100
   Email: contact@sdtech.com
   Description: 15.6" Android tablet, customizable...

💬 Vendor Responses Received
💬 TechVision Co responded in 3.2 hours
   Price: $135, MOQ: 200
   Response: "Thank you for your inquiry..."
```

## 🔒 Security Notes

- ✅ App Passwords are safer than your real Gmail password
- ✅ GitHub Secrets are encrypted and hidden
- ✅ Only GitHub Actions can access them
- ✅ Revoke anytime from Google Account settings

## 🆘 Troubleshooting

### Not receiving emails?

**Check 1: Verify secrets are set**
- Go to repo Settings → Secrets and variables → Actions
- You should see: `USER_EMAIL` and `EMAIL_PASSWORD`

**Check 2: Verify email address**
- Make sure `USER_EMAIL` = `avinashlingamop123@gmail.com`

**Check 3: Verify app password**
- Remove all spaces from the 16-character password
- Should be: `abcdefghijklmnop` (no spaces)

**Check 4: Check spam folder**
- Emails might go to spam first time
- Mark as "Not Spam" to receive future emails

**Check 5: Enable IMAP in Gmail**
- Gmail Settings → Forwarding and POP/IMAP
- Enable IMAP
- Save changes

### Actions failing?

**Check workflow logs:**
- Actions tab → Latest run → Click on the job
- Look for error messages
- Common issues:
  - "Authentication failed" = Wrong app password
  - "No such module" = Dependencies not installed (shouldn't happen)
  - "Timeout" = Ollama taking too long (normal first time)

## 📱 Gmail App Password Reminder

**Your credentials:**
- Email: `avinashlingamop123@gmail.com`
- App Password: Generate at https://myaccount.google.com/apppasswords

**Format:**
- ❌ Wrong: `abcd efgh ijkl mnop` (has spaces)
- ✅ Correct: `abcdefghijklmnop` (no spaces)

## 🎉 You're All Set!

Once configured:
1. ✅ Agent runs daily at 9 AM UTC (1 hour)
2. ✅ You get email report after each run
3. ✅ Vendor conversations handled automatically
4. ✅ Learning improves over time
5. ✅ No manual work needed!

**Next manual trigger:** Go to Actions tab → Run workflow

**Check status:** https://github.com/avinash1166/ai-sourcing-agent/actions

---

**Need help?** Check the Actions logs for detailed error messages.
