# VAPI Integration & Real-World Testing Guide

**Goal:** Integrate Claude with VAPI for real-world voice testing of the Stuffed Lamb system

---

## OPTION 1: Direct Webhook Testing (Fastest - 15 minutes)

I can send HTTP requests directly to your webhook endpoint to simulate VAPI calls. This tests all the logic without needing actual voice.

### Setup Steps:

1. **Start the Stuffed Lamb server locally**
2. **I'll send test webhook payloads** simulating VAPI
3. **Monitor responses and logs** in real-time

**Advantages:**
- ✅ Instant testing, no external setup
- ✅ Tests all tools and logic
- ✅ Can iterate quickly
- ✅ No VAPI account needed yet

**Limitations:**
- ❌ No actual voice testing
- ❌ Doesn't test speech-to-text accuracy

---

## OPTION 2: VAPI Web Dashboard Testing (30 minutes)

VAPI has a web-based testing interface where you can type messages and test the conversation flow.

### Setup Steps:

1. **Create VAPI account** (free trial available)
2. **Create VAPI assistant** with Stuffed Lamb config
3. **Use web chat interface** to test conversations
4. **I monitor webhook calls** and help optimize

**Advantages:**
- ✅ Tests actual VAPI integration
- ✅ No phone calls needed
- ✅ Fast iteration
- ✅ Can test conversation flow

**Limitations:**
- ❌ No actual voice (text only)
- ❌ Doesn't test pronunciation/accent handling

---

## OPTION 3: Real Voice Testing via VAPI Phone (1 hour)

Get a real phone number from VAPI and make actual voice calls to test the system end-to-end.

### Setup Steps:

1. **Create VAPI account**
2. **Get phone number** (costs ~$1-5/month)
3. **Configure VAPI assistant** with our tools
4. **Call the number** and have conversations
5. **I monitor logs** and analyze failures

**Advantages:**
- ✅ Real-world voice testing
- ✅ Tests accent handling
- ✅ Tests speech-to-text accuracy
- ✅ Most realistic scenario

**Limitations:**
- ⏱️ Takes longer to set up
- 💰 Requires VAPI paid plan (~$30/month + usage)

---

## OPTION 4: Automated Testing Suite (2-3 hours)

I create a comprehensive test suite that simulates various scenarios, accents, and edge cases.

### What I'll Build:

1. **Webhook simulator** - Sends test payloads
2. **Scenario library** - 50+ test cases
3. **Accent variants** - Tests pronunciation variants
4. **Performance monitoring** - Tracks success rates
5. **Automated reports** - Shows what works/fails

**Advantages:**
- ✅ Comprehensive testing
- ✅ Repeatable
- ✅ Can run anytime
- ✅ Documents all edge cases

---

## RECOMMENDED APPROACH: Hybrid Testing

**Phase 1: Webhook Testing (Today - 30 min)**
→ I test all tools via direct HTTP calls
→ Verify logic works correctly
→ Fix any bugs found

**Phase 2: VAPI Dashboard (Tomorrow - 1 hour)**
→ Set up VAPI assistant
→ Test conversation flow
→ Optimize prompts

**Phase 3: Real Voice (Week 1 - 2 hours)**
→ Get phone number
→ Real-world testing
→ Accent validation

---

## LET'S START: OPTION 1 (Webhook Testing)

I can start testing RIGHT NOW if you:

### Step 1: Start the Server

```bash
cd /home/user/Claude/stuffed-lamb
python run.py
```

This will start the server on `http://localhost:8000`

### Step 2: I'll Send Test Requests

I'll simulate VAPI webhook calls testing:
- ✅ quickAddItem with various pronunciations
- ✅ Complex orders (multiple items, quantities)
- ✅ Accent variants (Aussie, Middle Eastern)
- ✅ Edge cases (fast speech, errors)
- ✅ Full order flow (add → price → create)

### Step 3: Monitor Results

You'll see:
- Real-time logs of what's working
- Failed matches (items not recognized)
- Success rates per tool
- Recommendations for improvements

---

## OPTION 2 SETUP: VAPI Dashboard Testing

If you want to go with VAPI integration:

### 1. Create VAPI Account

```bash
# Go to: https://vapi.ai
# Sign up (free trial available)
# Get API key from dashboard
```

### 2. I'll Create the VAPI Assistant Config

I'll generate the exact JSON configuration for VAPI that includes:
- System prompt
- All 18 tools
- Webhook URL
- Voice settings

### 3. Configure in VAPI Dashboard

```
Dashboard → Assistants → Create New
→ Import our JSON config
→ Set webhook URL
→ Test in web interface
```

### 4. Test Flow

```
You type: "Hi, I'd like to order"
VAPI: Calls our webhook → getCallerSmartContext
Our server: Returns customer data
VAPI: "Welcome back! Want your usual order?"
You type: "Yes, and add a lamb mandi"
VAPI: Calls webhook → repeatLastOrder + quickAddItem
... etc
```

---

## OPTION 3 SETUP: Real Voice Testing

### 1. VAPI Account Setup

**Cost:** ~$30/month + usage
**Includes:** Phone number, voice calls, transcription

### 2. Get Phone Number

```
VAPI Dashboard → Phone Numbers → Buy Number
→ Choose Australian number (+61)
→ Assign to assistant
```

### 3. Configure Voice Settings

```json
{
  "voice": {
    "provider": "11labs",
    "voiceId": "australian-female",
    "model": "eleven_turbo_v2"
  },
  "transcriber": {
    "provider": "deepgram",
    "model": "nova-2",
    "language": "en-AU"  // Australian English
  }
}
```

### 4. Testing Protocol

**Test Scenarios:**
1. **New customer order**
   - Call number
   - Order lamb mandi with nuts
   - Complete checkout

2. **Returning customer**
   - Call with same number
   - Test "repeat last order"

3. **Complex order**
   - Multiple items
   - Different quantities
   - Extras and add-ons

4. **Accent testing**
   - Broad Australian accent
   - Middle Eastern accent
   - Fast speech
   - Background noise

5. **Error scenarios**
   - Invalid items
   - Unclear speech
   - Interruptions

---

## WHAT I NEED FROM YOU

To start testing, please provide:

### For Option 1 (Webhook Testing - Can start now):
```bash
# Just run:
cd /home/user/Claude/stuffed-lamb
python run.py

# That's it! I'll do the rest
```

### For Option 2 (VAPI Dashboard):
- VAPI account credentials (or I'll guide you through signup)
- I'll create the assistant config

### For Option 3 (Real Voice):
- VAPI paid account
- Phone number purchased
- I'll help with full setup

---

## TESTING SCRIPT I'LL CREATE

I'll build a Python script that simulates VAPI webhook calls:

```python
# stuffed-lamb/test_vapi_simulation.py

import requests
import json
import hmac
import hashlib

class VAPISimulator:
    def __init__(self, webhook_url, secret):
        self.url = webhook_url
        self.secret = secret

    def simulate_call(self, phone_number, message):
        """Simulate a VAPI webhook call"""

        # Create VAPI-style payload
        payload = {
            "message": {
                "type": "tool-calls",
                "toolCallList": [
                    {
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "quickAddItem",
                            "arguments": json.dumps({
                                "description": message
                            })
                        }
                    }
                ],
                "call": {
                    "customer": {
                        "number": phone_number
                    }
                }
            }
        }

        # Sign request
        signature = self.create_signature(payload)

        # Send to webhook
        response = requests.post(
            self.url,
            json=payload,
            headers={
                'X-Stuffed-Lamb-Signature': signature,
                'Content-Type': 'application/json'
            }
        )

        return response.json()

    def create_signature(self, payload):
        """Create HMAC signature like VAPI does"""
        body = json.dumps(payload)
        return hmac.new(
            self.secret.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()

# Test scenarios
scenarios = [
    # Basic orders
    ("lamb mandi", "Should match Lamb Mandi"),
    ("chicken mandi with nuts", "Chicken + addon"),
    ("mansaf with extra jameed", "Mansaf + extra"),

    # Accent variants
    ("mahn-sahf", "Australian accent - mansaf"),
    ("lam mandy", "Australian accent - lamb mandi"),
    ("chook mandi", "Aussie slang - chicken"),

    # Fast speech
    ("two lamb mandis with nuts and sultanas", "Multiple quantity + addons"),
    ("gimme a chicken", "Casual speech"),

    # Errors (should fail gracefully)
    ("burger", "Not on menu"),
    ("the thing with the yogurt", "Vague description"),
]

# Run tests
simulator = VAPISimulator(
    webhook_url="http://localhost:8000/webhook",
    secret="your-webhook-secret"
)

for message, description in scenarios:
    print(f"\n{'='*60}")
    print(f"TEST: {description}")
    print(f"INPUT: '{message}'")

    result = simulator.simulate_call("+61412345678", message)

    if result.get('ok'):
        print(f"✅ SUCCESS: {result.get('message')}")
    else:
        print(f"❌ FAILED: {result.get('error')}")
```

---

## MONITORING & ANALYTICS

While testing, I'll track:

### Success Metrics:
```
Order Success Rate: 75/100 tests = 75%
Item Match Rate: 85/100 = 85%
Accent Handling: 60/80 variants = 75%
Edge Cases: 12/20 handled = 60%
```

### Failure Analysis:
```
Top Failures:
1. "mahn-sahf" → Not matched (15 times)
2. "lam with nuts" → Partial match only (12 times)
3. "two chickens" → Quantity parsing failed (8 times)
4. "the lamb thing" → Too vague (5 times)
```

### Recommendations:
```
Add pronunciations:
- "mahn-sahf" → mansaf
- "lam" → lamb mandi
- "the lamb thing" → needs LLM fallback
```

---

## REAL-TIME COLLABORATION

While testing, we can:

1. **I run tests** → Find failures
2. **I suggest fixes** → Update pronunciations.json
3. **You approve** → I implement
4. **I re-test** → Verify improvements
5. **Repeat** → Until 95%+ success rate

This iterative process takes 2-3 hours and results in a **production-ready system**.

---

## ESTIMATED TIMELINE

**Option 1 (Webhook Testing):**
- Setup: 5 minutes (start server)
- Testing: 1-2 hours (100+ scenarios)
- Fixes: 1-2 hours (implement improvements)
- **Total: 3-4 hours** → 95%+ accuracy

**Option 2 (VAPI Dashboard):**
- Setup: 30 minutes (VAPI account + config)
- Testing: 2-3 hours (conversation flows)
- Optimization: 2-3 hours (prompt tuning)
- **Total: 5-6 hours** → Production-ready

**Option 3 (Real Voice):**
- Setup: 1 hour (VAPI account + phone)
- Testing: 3-4 hours (voice scenarios)
- Accent validation: 2-3 hours (multiple speakers)
- **Total: 6-8 hours** → Fully validated

---

## WHICH OPTION DO YOU PREFER?

**Quick answer:**
1. **"Let's start with webhook testing"** → I'll start now
2. **"Set up VAPI dashboard"** → I'll create the config
3. **"Go full voice testing"** → I'll guide you through VAPI setup
4. **"Do all three"** → We'll do phased testing

**Just tell me which option and I'll begin immediately!**

---

## BONUS: Self-Testing Mode

I can also create a **self-diagnostic tool** that runs automatically:

```bash
# Run this anytime to test the system
python test_suite.py --full

# Output:
# ✅ 47/50 basic orders successful (94%)
# ⚠️  3 accent variants failed
# ✅ All edge cases handled
# ✅ Payment flow works
# ⚠️  Order status tool missing
#
# Overall Score: 92/100
# Production Ready: YES (with noted improvements)
```

This gives you confidence before deploying!
