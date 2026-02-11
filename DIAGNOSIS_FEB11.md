# DIAGNOSIS: Feb 11, 2026 - Dead Product Links & Missing Emails

## Problem Reported by User

Telegram feedback shows vendor "Shenzhen Hopestar Sci-Tech Co., Ltd." with:
- Product link leads to "information not available" on Made-in-China
- No email found
- Suspicious price detected ($125.5)
- System asking "is this relevant?"

## Root Cause Analysis

### 1. **Dead Product Links** ❌
- Scraper is extracting product URLs correctly
- BUT Made-in-China URLs may be:
  - Session-based (expire quickly)
  - Geo-locked (different results in different regions)
  - Product deleted/moved
  
**Evidence from logs:**
```
✓ Real product URL: https://cnhopestar.en.made-in-china.com/product/rYXRKulPqGhE...
```

The URL exists but leads to "information not available" when visited.

### 2. **Missing Emails** ❌
- Alternative contact finder IS trying:
  - Google search
  - Made-in-China vendor profile scraping
  - Website contact page scraping
- BUT not finding any emails

**Evidence from logs:**
```
🔍 Searching for contact email: Shenzhen Hopestar Sci-Tech Co., Ltd.
  → Checking vendor profile: https://cnhopestar.en.made-in-china.com/company-profile.html...
⚠️  No email found through alternative methods
```

**Why?**
- Made-in-China hides emails on free profiles (forces inquiry system)
- Google may not index Made-in-China vendor contacts
- Vendors may only show emails to logged-in buyers

### 3. **Placeholder Price Detection** ⚠️
- LLM keeps outputting $125.5 as example price
- Anti-hallucination system correctly detects it as suspicious
- Results in quality score drop (0.70 → 0.50)

**Evidence from logs:**
```
⚠️  Suspicious placeholder price: $125.5
⚠️  -3 points: MINOR hallucination detected (Total: 97)
❌ DATA QUALITY CHECK FAILED (confidence: 0.50)
```

### 4. **Low Success Rate** 📉
- GitHub Action run: 20 keywords searched
- Only 2 vendors saved (10% success rate)
- 13 vendors rejected for: missing email + fake price

## Immediate User Question

**"Should I mark as RELEVANT or IRRELEVANT?"**

### **ANSWER: Mark as ❌ IRRELEVANT**

**Reasons:**
1. ❌ No email = Cannot contact vendor (dealbreaker)
2. ❌ Dead product link = Cannot verify specs (red flag)
3. ⚠️ Suspicious price = Data quality poor
4. ⚠️ Score 88/100 is misleading (should be lower with missing email)

**What This Teaches The System:**
- Vendors without emails are NOT useful
- System will lower scoring for no-email vendors in future
- Feedback patterns will learn to prioritize findable contacts

## Fixes Applied

### Fix #1: Telegram URL Display
**BEFORE:**
```
• Product URL: https://cnhopestar.en.made-in-china.com/product/rY...
```
(Truncated to 50 chars, user can't click)

**AFTER:**
```
• Product: <a href="FULL_URL">View product</a>
```
(Clickable HTML link with full URL, no truncation)

**File:** `telegram_feedback.py` line 99

### Fix #2: Longer Description Preview
**BEFORE:** Description truncated to 150 chars
**AFTER:** Description truncated to 200 chars

More context for user to make informed decision.

## Recommended Next Steps

### Option A: Lower Threshold for Saving (NOT RECOMMENDED)
- Save vendors even without emails
- Pro: More data collected
- Con: Useless data (can't contact them)

### Option B: Improve Email Discovery (RECOMMENDED)
1. Add more search methods:
   - LinkedIn company page scraping
   - Crunchbase/similar databases
   - DNS MX record lookup + common email patterns (sales@domain, info@domain)
   
2. Use Made-in-China inquiry system:
   - Create "Send Inquiry" automation
   - Track responses via scraping platform inbox
   
3. Accept phone numbers as alternative contact:
   - Extract phone/WhatsApp from profiles
   - User can manually message them

### Option C: Focus on Different Platforms (RECOMMENDED)
- AliExpress (sellers often show WhatsApp/WeChat)
- DHgate (more contact visibility)
- Direct manufacturer websites (better email disclosure)
- LinkedIn prospecting (find sales managers)

### Option D: Better Price Validation (EASY WIN)
Fix the LLM prompt to stop hallucinating $125.5:

**Current prompt issue:**
```json
{"price_per_unit":125.5,...}
```
The example shows 125.5, so LLM copies it!

**Fix:**
```json
{"price_per_unit":null,...}  // or show range: {"price_per_unit":68.9,...}
```

## User Action Required

1. **Click ❌ IRRELEVANT** in Telegram for this vendor
2. **Wait for next GitHub Action run** to see if fix #1 (clickable links) works
3. **Decide on strategy:**
   - Stick with Made-in-China (low email success rate ~10%)
   - Expand to other platforms (AliExpress, direct websites)
   - Accept inquiry system instead of direct emails

## Success Metrics to Track

- **Email Discovery Rate:** Currently ~10%, target 50%+
- **Link Validity Rate:** Currently unknown (many dead), target 90%+
- **Price Accuracy:** Currently poor (LLM hallucination), target 80%+
- **Overall Save Rate:** Currently 10% (2/20), target 40%+

## Code Changes Summary

**Files Modified:**
1. `telegram_feedback.py` - Fixed URL truncation, now shows clickable link

**Files To Modify Next:**
1. `oem_search.py` - Fix price example in prompt (line 181)
2. `alternative_contact.py` - Add LinkedIn/website scraping
3. `scraper.py` - Add AliExpress/DHgate support

---
*Diagnosis completed: 2026-02-11*
*Status: ONE FIX APPLIED (Telegram URL), MORE FIXES NEEDED*
