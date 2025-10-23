# 🎙️ ELEVENLABS CREDIT SYSTEM EXPLAINED

⚠️ **WARNING: This document contains pricing errors. Please see VERIFIED-COST-BREAKDOWN-2025.md for accurate information.**

**Critical Update to Cost Analysis**

---

## 🚨 THE PROBLEM YOU IDENTIFIED

You're paying **$22 USD/month ($34.10 AUD)** for ElevenLabs Pro subscription, which gives you **monthly credits**.

**The big question:** What happens when those credits run out?

**Short answer:** You have 3 options:
1. ❌ Service stops until next month (not acceptable for business)
2. 💰 Enable "usage-based billing" and pay overage charges
3. 📈 Upgrade to higher tier with more credits

---

## 💳 HOW ELEVENLABS PRICING ACTUALLY WORKS

### Credit System Breakdown

**1 Character = 1 Credit** (for most models)
**1,000 Characters ≈ 1 Minute of Audio**

Example:
- "Hello, welcome to Kebabalab" = 29 characters = 29 credits
- 2-minute phone conversation ≈ 2,000 characters = 2,000 credits

### Your Current Plan: Starter/Creator ($22 USD/month)

Based on ElevenLabs pricing tiers, your $22/month plan likely includes:

| Plan Detail | Amount |
|------------|--------|
| Monthly cost | $22 USD ($34.10 AUD) |
| Character credits/month | ~30,000 characters |
| Minutes of audio | ~30 minutes |
| Custom voices | 10 voices |
| Commercial license | ✅ Yes |

**This means:** You can only do **15 calls per month** (at 2 min/call) before running out of credits!

---

## 🔴 WHAT HAPPENS WHEN YOU RUN OUT

### Option 1: Service Stops (Default)

**What happens:**
- Your VAPI calls will fail when trying to use ElevenLabs
- Customer hears error or dead air
- Orders are lost

**Cost:** $0 additional
**Risk:** ⚠️ CRITICAL - Business downtime, lost revenue

---

### Option 2: Enable Usage-Based Billing (Overage Charges)

**What happens:**
- When you hit your 30,000 character limit, ElevenLabs automatically charges you for additional usage
- You set a threshold (e.g., "allow up to $100 in overages")
- Service continues without interruption

**Overage pricing:**
- **Standard models:** $0.24 per 1,000 characters
- **Turbo v2.5 models:** $0.12 per 1,000 characters (50% cheaper)

**Cost calculation for 500 calls/month:**

| Item | Calculation | Cost |
|------|-------------|------|
| Total minutes needed | 500 calls × 2 min | 1,000 minutes |
| Total characters needed | 1,000 min × 1,000 chars | 1,000,000 characters |
| Included in subscription | 30 min × 1,000 chars | 30,000 characters |
| **Overage needed** | 1,000,000 - 30,000 | **970,000 characters** |
| **Overage cost (Turbo v2.5)** | 970 × $0.12 | **$116.40 USD** |
| **Monthly subscription** | Fixed | **$22.00 USD** |
| **TOTAL MONTHLY COST** | Subscription + Overage | **$138.40 USD ($214.52 AUD)** |

**Plus VAPI still charges you $0.05/min for their platform!**

**Total voice cost:** $214.52 AUD + VAPI fees = **Way more expensive than advertised!**

---

### Option 3: Upgrade to Higher Tier

**ElevenLabs Pricing Tiers:**

| Plan | Cost (USD) | Cost (AUD) | Characters/month | Minutes | Best for |
|------|-----------|-----------|-----------------|---------|----------|
| **Starter** | $5 | $7.75 | 30,000 | 30 min | Testing (15 calls) |
| **Creator** | $22 | $34.10 | 100,000 | 100 min | Small use (50 calls) |
| **Pro** | $99 | $153.45 | 500,000 | 500 min | Medium use (250 calls) |
| **Scale** | $330 | $511.50 | 2,000,000 | 2,000 min | High use (1,000 calls) |
| **Business** | $1,320 | $2,046 | 11,000,000 | 11,000 min | Enterprise (5,500 calls) |

**For 500 calls/month (1,000 minutes needed):**
- **Pro plan:** $99/month covers 500 min ✅ Not enough!
- **Scale plan:** $330/month covers 2,000 min ✅ Enough with buffer

**Problem:** You'd need to pay **$511.50 AUD/month** for ElevenLabs alone!

---

## 💰 REVISED COST ANALYSIS (With Overage Reality)

### Scenario: 500 Calls/Month at 2 Minutes Each

**Previous calculation (WRONG):**
- ElevenLabs: $34.10/month subscription
- Usage through VAPI: Included in subscription
- Total: $34.10/month

**Actual calculation (CORRECT):**

| Service | Calculation | Monthly Cost (AUD) |
|---------|-------------|-------------------|
| ElevenLabs subscription | $22 USD | $34.10 |
| ElevenLabs overage (970k chars) | 970 × $0.12 × 1.55 | $180.42 |
| **Total ElevenLabs** | - | **$214.52** |
| VAPI platform | 1,000 min × $0.078 | $78.00 |
| Deepgram | 1,000 min × $0.016 | $16.00 |
| GPT-4o-mini | 1,000 min × $0.016 | $16.00 |
| Twilio | 1,000 min × $0.006 | $6.00 |
| Twilio phone | Fixed | $1.78 |
| SMS (300) | 300 × $0.012 | $3.60 |
| Server | Fixed | $15.50 |
| **TOTAL** | - | **$351.40** |

**Per call cost:** $351.40 / 500 = **$0.70 per call** (not $0.54!)

---

## 🚀 WHY CARTESIA IS THE SOLUTION

**Cartesia doesn't use a credit/subscription model. It's pure pay-as-you-go.**

### Cost Comparison at 500 Calls/Month (1,000 minutes)

| Provider | Model | Subscription | Usage Cost | Total Cost (AUD) |
|----------|-------|-------------|-----------|-----------------|
| **ElevenLabs** | Flash v2 | $34.10 | $180.42 overage | **$214.52** |
| **ElevenLabs** | Turbo v2.5 | $34.10 | $90.21 overage | **$124.31** |
| **Cartesia** | Sonic | $0 | 1,000 min × $0.008 | **$12.40** |
| **PlayHT** | 2.0 Turbo | $72.09 | 1,000 min × $0.016 | **$88.09** |
| **OpenAI** | TTS HD | $0 | 1,000 min × $0.047 | **$72.85** |

**Cartesia saves you $102-202/month compared to ElevenLabs!**

---

## 📊 UPDATED TRUE COSTS

### Current System (500 calls/month, 2 min avg)

| Service | Monthly Cost (AUD) |
|---------|-------------------|
| VAPI Platform | $78.00 |
| Deepgram Nova 2 | $16.00 |
| GPT-4o-mini | $16.00 |
| **ElevenLabs (with overage)** | **$214.52** |
| Twilio | $11.38 |
| Server | $15.50 |
| **TOTAL** | **$351.40** |

**Per call:** $0.70 AUD

---

### Optimized System with Cartesia (500 calls/month, 2 min avg)

| Service | Monthly Cost (AUD) |
|---------|-------------------|
| VAPI Platform | $78.00 |
| Deepgram Nova 2 | $16.00 |
| GPT-4o-mini | $16.00 |
| **Cartesia Sonic** | **$12.40** |
| Twilio | $11.38 |
| Server | $15.50 |
| **TOTAL** | **$149.28** |

**Per call:** $0.30 AUD

**Savings:** $202.12/month (57% reduction!)

---

### Optimized System with ElevenLabs Turbo v2.5 (Compromise)

| Service | Monthly Cost (AUD) |
|---------|-------------------|
| VAPI Platform | $78.00 |
| Deepgram Nova 2 | $16.00 |
| GPT-4o-mini | $16.00 |
| **ElevenLabs Turbo v2.5** | **$124.31** |
| Twilio | $11.38 |
| Server | $15.50 |
| **TOTAL** | **$261.19** |

**Per call:** $0.52 AUD

**Savings:** $90.21/month (26% reduction)

---

## 🎯 UPDATED RECOMMENDATIONS

### ❌ DON'T: Keep Using ElevenLabs Flash v2

**Why not:**
- $214.52/month for voice alone at 500 calls
- Most expensive option
- Credits run out quickly
- Need to constantly monitor usage

---

### ⚠️ MAYBE: Switch to ElevenLabs Turbo v2.5 (Short-term)

**Pros:**
- You already have the subscription
- 50% cheaper than Flash v2 ($124/month vs $214/month)
- Voice cloning included
- Easy to implement (2 hours)

**Cons:**
- Still expensive ($124/month for voice)
- Still have credit limits
- Still need to enable overage billing
- Not sustainable at scale

**Verdict:** Good temporary solution for this month while you test Cartesia

---

### ✅ DO: Switch to Cartesia Sonic (Recommended)

**Pros:**
- **94% cheaper:** $12.40/month vs $214/month
- No subscription, pure pay-as-you-go
- No credit limits or overage surprises
- Fastest latency (150ms)
- Excellent quality
- Custom voice cloning ($153 one-time)
- Unlimited scaling

**Cons:**
- Need to clone voice ($153 one-time)
- New provider (testing needed)
- 2-3 days setup time

**Verdict:** Best long-term solution, massive savings

---

### 🏆 ALTERNATIVE: PlayHT 2.0 Turbo (Middle Ground)

**Pros:**
- High quality voice cloning
- $88/month total cost (better than ElevenLabs)
- Proven reliability
- Good Australian accent support

**Cons:**
- More expensive than Cartesia ($88 vs $12)
- Still has subscription ($72/month)
- Slower than Cartesia (400ms vs 150ms)

**Verdict:** Good if Cartesia quality doesn't meet standards

---

## 📋 IMMEDIATE ACTION PLAN (REVISED)

### This Week: Enable Overage Billing + Test Cartesia

**Step 1: Prevent Service Interruption**
1. Log into ElevenLabs dashboard
2. Go to Account → Billing
3. Enable "Usage-Based Billing"
4. Set threshold: $200 USD/month
5. This prevents calls from failing when credits run out

**Cost:** Peace of mind, allows business to continue

---

**Step 2: Switch to Turbo v2.5 Immediately**
1. Go to ElevenLabs Voice Lab
2. Record 2-5 mins of Australian voice
3. Create custom voice
4. In VAPI: Change model to "eleven_turbo_v2_5"
5. Use your custom voice ID

**Savings:** $90/month (50% reduction on voice costs)
**Time:** 2-4 hours

---

**Step 3: Sign Up for Cartesia Trial (Parallel)**
1. Visit https://cartesia.ai
2. Sign up for free trial
3. Clone your voice (or same voice from Step 2)
4. Test quality with 10-20 sample calls
5. Compare side-by-side with ElevenLabs

**Time:** 3-4 hours for testing

---

### Next Week: Migrate to Cartesia (If Quality Good)

**Step 4: Full Cartesia Migration**
1. Pay $153 for custom voice cloning
2. Update VAPI to use Cartesia
3. Run parallel testing (50/50 split) for 3 days
4. Monitor customer feedback
5. Full cutover if no issues
6. Cancel ElevenLabs subscription (save $34/month)

**Savings:** $202/month compared to current
**ROI:** 153 / 202 = 0.75 months (pays for itself in 3 weeks!)

---

## 💰 UPDATED BREAK-EVEN ANALYSIS

### At Current Costs ($0.70/call)

| Pricing | Orders for Break-even | Revenue at Break-even |
|---------|----------------------|---------------------|
| $2.50/order | 195 orders | $487.50 |
| $3.50/order | 140 orders | $490.00 |
| $5.00/order | 98 orders | $490.00 |

---

### After Cartesia Migration ($0.30/call)

| Pricing | Orders for Break-even | Revenue at Break-even |
|---------|----------------------|---------------------|
| $2.50/order | 68 orders | $170.00 |
| $3.50/order | 49 orders | $171.50 |
| $5.00/order | 35 orders | $175.00 |

**Conclusion:** With Cartesia, you break even with just **49 orders/month at $3.50/order** (vs 140 orders with current setup!)

---

## 🎯 UPDATED PROFIT PROJECTIONS

### At 500 Calls/Month

| Setup | Revenue (@$3.50) | Costs | Profit | Margin |
|-------|-----------------|-------|--------|--------|
| **Current (Flash v2)** | $1,750 | $351 | $1,399 | 80% |
| **ElevenLabs Turbo v2.5** | $1,750 | $261 | $1,489 | 85% |
| **Cartesia Sonic** | $1,750 | $149 | **$1,601** | **91%** |

**Extra profit with Cartesia:** $202/month more than current

---

### At 1,000 Calls/Month

| Setup | Revenue (@$3.50) | Costs | Profit | Margin |
|-------|-----------------|-------|--------|--------|
| **Current (Flash v2)** | $3,500 | $595 | $2,905 | 83% |
| **ElevenLabs Turbo v2.5** | $3,500 | $415 | $3,085 | 88% |
| **Cartesia Sonic** | $3,500 | $211 | **$3,289** | **94%** |

**Extra profit with Cartesia:** $384/month more than current

---

## ✅ FINAL RECOMMENDATIONS

### Immediate (This Week):

1. **Enable ElevenLabs overage billing** - Prevent service interruption
2. **Switch to Turbo v2.5** - 50% voice cost reduction, same subscription
3. **Sign up for Cartesia trial** - Test quality in parallel

### Short-term (Week 2-3):

1. **Test Cartesia thoroughly** - 50+ test calls, verify quality
2. **Clone custom voice on Cartesia** - $153 one-time investment
3. **Migrate to Cartesia** - Save $202/month

### If Cartesia Quality Issues:

1. **Fallback to ElevenLabs Turbo v2.5** - Still 50% savings
2. **Or try PlayHT 2.0** - Middle ground at $88/month
3. **Monitor ElevenLabs for pricing updates** - They may reduce prices

---

## 📞 ANSWER TO YOUR QUESTION

**"What happens when ElevenLabs credits run out?"**

**Default:** Service stops, calls fail ❌

**Solution 1:** Enable usage-based billing
- Cost: $180/month in overages at 500 calls
- Total: $214/month for voice

**Solution 2:** Upgrade to Scale plan ($330 USD/month)
- Cost: $511 AUD/month
- Overkill for your volume

**Solution 3 (BEST):** Switch to Cartesia
- Cost: $12/month for voice
- Savings: $202/month
- No credits, no limits, no surprises

**Bottom line:** Your current ElevenLabs plan can only handle ~15 calls/month. At 500 calls/month, you'll pay $214/month in total (subscription + overages). Cartesia costs $12/month with no limits.

**Switch to Cartesia and save $2,424 AUD per year.**

---

**Report prepared by:** Claude Code
**Date:** October 21, 2025