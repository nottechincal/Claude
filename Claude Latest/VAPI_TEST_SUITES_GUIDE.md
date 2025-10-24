# VAPI Test Suites - Implementation Guide

This guide explains how to use the test suites defined in `VAPI_TEST_SUITES.json` with your VAPI assistant.

---

## 📋 Overview

**File:** `VAPI_TEST_SUITES.json`
**Format:** VAPI-compliant test suite definitions
**Total Tests:** 14 comprehensive scenarios
**Coverage:** All critical functionality and bug fixes

---

## 🎯 Test Suite Structure

Each test suite contains:

```json
{
  "name": "Test name",
  "description": "What this tests",
  "type": "voice" or "chat",
  "attempts": 1,
  "script": "Detailed instructions for the AI tester...",
  "rubric": "Success criteria for LLM evaluation..."
}
```

### Components Explained:

**Script:** Tells the AI tester exactly what to say and do during the test call. Think of this as the "customer behavior simulator."

**Rubric:** Lists specific criteria an LLM will use to evaluate if the test passed. This is where you define success conditions.

**Type:**
- `"chat"` - Text-based testing (faster, recommended for initial testing)
- `"voice"` - Actual voice call (slower but tests real voice experience)

**Attempts:** Number of times to run this test (1-5). Use 1 for most tests, use 3-5 for flaky scenarios.

---

## 🚀 How to Use in VAPI

### Method 1: VAPI Dashboard (Recommended)

1. **Go to VAPI Dashboard** → Test Suites
2. **Click "Create Test Suite"**
3. **Copy one test from** `VAPI_TEST_SUITES.json`
4. **Fill in the fields:**
   - Name: Copy the `name` field
   - Description: Copy the `description` field
   - Type: Select "Voice" or "Chat"
   - Script: Copy the entire `script` field
   - Rubric: Copy the entire `rubric` field
   - Attempts: Set to 1 (or higher for repeated testing)
5. **Select your assistant** from the dropdown
6. **Click "Run Test"**

### Method 2: VAPI API

```bash
curl --request POST \
  --url https://api.vapi.ai/test-suite-run \
  --header 'Authorization: Bearer <YOUR_API_KEY>' \
  --header 'Content-Type: application/json' \
  --data '{
    "assistantId": "your-assistant-id",
    "name": "Test 1: Basic Order with Exclusions",
    "type": "voice",
    "script": "...",
    "rubric": "...",
    "attempts": 1
  }'
```

---

## 📊 Test Priority Levels

### 🔴 **CRITICAL - Run These First**

These tests verify the bugs we fixed in your live testing:

1. **Test 1: Basic Order with Exclusions** ⭐
   - Verifies "no onion" exclusion works
   - Bug fix from Round 1

2. **Test 2: HSP with No Cheese** ⭐⭐
   - Verifies "no cheese" exclusion works
   - Bug fix from Round 2 (#1)

3. **Test 4: Meal Conversion** ⭐
   - Verifies duplicate drinks removed
   - Bug fix from Round 1
   - Should show $34 NOT $41

4. **Test 7: HSP Combo Size Change** ⭐⭐⭐
   - Verifies HSP combo pricing updates
   - Bug fix from Round 2 (#2)
   - MUST show $17 → $22 when changing small to large

**Priority:** Run these 4 tests FIRST to verify all bug fixes work.

### 🟡 **HIGH PRIORITY - Core Functionality**

5. **Test 3: Multiple Items with Quantities**
   - Basic quantity parsing

6. **Test 6: Edit Cart - Change Size**
   - Basic editing functionality

7. **Test 11: Size Confirmation**
   - Never defaults to size

8. **Test 13: Complete Checkout Flow**
   - End-to-end order completion

**Priority:** Run after critical tests pass.

### 🟢 **MEDIUM PRIORITY - Advanced Features**

9. **Test 5: Complex Order with Multiple Customizations**
10. **Test 8: Remove Cart Item**
11. **Test 9: Edit Customizations**
12. **Test 10: Complex Real-World Order**

**Priority:** Run when basic functionality is solid.

### ⚪ **LOW PRIORITY - Edge Cases**

13. **Test 12: Multiple Sequential Edits**
    - Stress test
14. **Test 14: Cancel and Start Fresh**
    - Cart clearing

**Priority:** Run last to verify system stability.

---

## 💰 Cost Estimation

### Voice Tests:
- **Per test:** ~2-4 minutes of call time
- **Cost per test:** ~$0.20 - $0.50
- **All 14 tests:** ~$3-7 total

### Chat Tests (Recommended First):
- **Per test:** ~30 seconds - 1 minute
- **Cost per test:** ~$0.05 - $0.15
- **All 14 tests:** ~$1-2 total

### Recommended Approach:
1. **Start with Chat type** for all 14 tests (~$1-2)
2. **Fix any failures** found
3. **Re-run failed tests** as Voice to verify (~$1-2)
4. **Run critical tests** as Voice for final validation (~$1-2)

**Total estimated cost:** $3-6 (well within $10 free credits)

---

## 📈 Interpreting Results

After running a test, VAPI will show:

### ✅ **Test Passed**
- All rubric criteria met
- Transcript shows expected behavior
- System working correctly

**Action:** Move to next test

### ❌ **Test Failed**
VAPI will show which rubric criteria failed.

**Example Failure:**
```
Rubric Question 3: Did the assistant EXCLUDE onion from the order?
Result: NO - Transcript shows onion was included
```

**Actions:**
1. **Check server logs** for that time period
2. **Review webhook calls** to see what went wrong
3. **Fix the bug** in server.py
4. **Re-run the test** to verify fix

### ⚠️ **Partial Pass**
Some criteria passed, others failed.

**Action:** Review failed criteria and investigate.

---

## 🐛 Debugging Failed Tests

When a test fails:

### Step 1: Review the Transcript
VAPI provides full conversation transcript. Look for:
- What the customer said
- What your assistant responded
- Where the breakdown occurred

### Step 2: Check Server Logs
Look at your webhook server logs during the test time:

```bash
# View recent logs
tail -n 100 kebabalab/server.log

# Search for specific order
grep "quickAddItem" kebabalab/server.log
grep "ERROR" kebabalab/server.log
```

### Step 3: Check Specific Tool Calls
The VAPI dashboard shows all tool calls made during the test:
- Parameters sent
- Response received
- Errors (if any)

### Step 4: Reproduce Locally
Use our Python test suite to reproduce:

```bash
cd "/home/user/Claude/Claude Latest"
python test_all_scenarios.py
python test_bug_fixes.py
```

### Step 5: Fix and Re-test
1. Fix the bug in `server.py`
2. Test locally first
3. Deploy to server
4. Re-run the VAPI test

---

## 📋 Test Execution Checklist

### Before Running Tests:

- [ ] Webhook server is running and accessible
- [ ] VAPI assistant is configured with correct webhook URL
- [ ] All tools are properly defined in VAPI dashboard
- [ ] You have VAPI credits available
- [ ] Server logs are accessible for debugging

### Running Tests:

- [ ] Start with "chat" type for faster/cheaper testing
- [ ] Run critical tests first (Tests 1, 2, 4, 7)
- [ ] Document any failures immediately
- [ ] Check server logs after each failed test
- [ ] Take screenshots of VAPI results

### After Tests:

- [ ] Review all test results in VAPI dashboard
- [ ] Check pass rate (target: 100%)
- [ ] Document any bugs found
- [ ] Fix critical issues first
- [ ] Re-run failed tests after fixes
- [ ] Verify all fixes with voice tests

---

## 🎯 Success Criteria

Your system is ready for production when:

```
✅ 14/14 tests pass (100% pass rate)
✅ All critical bug fixes verified:
   - "No onion" exclusion works
   - "No cheese" exclusion works
   - Duplicate drinks removed in meal conversion
   - HSP combo size changes update price ($17→$22)
   - Speech output natural (no "vertical bar")
✅ Pricing calculations correct
✅ Cart editing works smoothly
✅ Checkout flow completes successfully
✅ No errors in server logs
```

---

## 🔄 Continuous Testing

### After Code Changes:

**Always run at minimum:**
1. Test 1 (Basic exclusions)
2. Test 2 (HSP no cheese)
3. Test 4 (Meal conversion)
4. Test 7 (HSP combo pricing)

These 4 tests cover all the critical bugs we fixed.

### Before Production Deploy:

**Run all 14 tests** to ensure no regressions.

### Ongoing Monitoring:

**Run weekly or after major changes:**
- All 14 tests as "chat" type (~$1-2)
- Critical tests as "voice" type (~$1-2)

---

## 📝 Example: Running Test 7 (Critical)

This is the most important test - it verifies Bug #2 fix from Round 2.

### In VAPI Dashboard:

1. **Create New Test Suite**
2. **Copy from VAPI_TEST_SUITES.json:**

```json
{
  "name": "Test 7: HSP Combo Size Change with Price Recalculation",
  "type": "voice",
  "script": "You are ordering an HSP, converting to combo, then changing size:

1. When greeted, say: 'Hi there'
2. When asked what you'd like, say: 'Small chicken HSP please'
3. Wait for confirmation (should be $15.00)
4. Then say: 'Can I make that a combo with Coke?'
5. Wait for confirmation (should be $17.00)
6. Then say: 'Actually, change that HSP to large please'
7. Listen VERY carefully to the price update - it should change to $22.00
8. If price is $22.00, say: 'Perfect'
9. If price stayed at $17.00, say: 'Wait, what's the price now?'
10. If asked about checkout, say: 'Cancel the order'",

  "rubric": "Evaluate this CRITICAL bug fix:

1. Did the assistant initially create a small chicken HSP at $15.00?
2. When converted to combo, did the price become $17.00?
3. When the size was changed to large, did the price UPDATE to $22.00? (CRITICAL)
4. Did the assistant explicitly mention the new price of $22.00?
5. Did the size change from small to large?

The test PASSES if:
- Initial small HSP: $15.00 ✓
- Small HSP combo: $17.00 ✓
- Large HSP combo: $22.00 ✓ (MUST UPDATE)

The test FAILS if:
- Price stays at $17.00 after changing to large (CRITICAL BUG #2)
- Price is any value other than $22.00
- Size doesn't change"
}
```

3. **Select your assistant**
4. **Click "Run Test"**
5. **Wait for results** (~3-5 minutes)
6. **Review transcript and evaluation**

### Expected Result:

```
✅ Test PASSED
All rubric criteria met:
- Small HSP: $15.00 ✓
- Combo: $17.00 ✓
- Large: $22.00 ✓
```

### If Failed:

```
❌ Test FAILED
Failed criteria:
- "Did the price UPDATE to $22.00?" → NO (stayed at $17.00)

Action needed: Check editCartItem() in server.py lines 1584-1591
```

---

## 🎉 Quick Start

**Want to start testing right now?**

1. **Go to VAPI Dashboard** → https://dashboard.vapi.ai
2. **Click "Test Suites"** → "Create Test Suite"
3. **Open** `VAPI_TEST_SUITES.json` in this repo
4. **Copy Test 1** (the first test in the JSON array)
5. **Paste the script and rubric** into VAPI
6. **Set type to "chat"** (faster and cheaper)
7. **Click "Run Test"**
8. **Wait 30-60 seconds** for results

If Test 1 passes, continue with Tests 2, 4, and 7. These are your critical tests.

---

## 📚 Additional Resources

- **VAPI Test Suites Docs:** https://docs.vapi.ai/test/test-suites
- **Server Code:** `kebabalab/server.py`
- **Local Tests:** `test_all_scenarios.py`, `test_bug_fixes.py`
- **Bug Fixes Documentation:** `CRITICAL_FIXES_ROUND_2.md`

---

## 🆘 Troubleshooting

### "Test timed out"
- Increase timeout in VAPI settings
- Check if webhook server is accessible
- Verify server isn't overloaded

### "Tool call failed"
- Check server logs for errors
- Verify tool definitions in VAPI match your webhook
- Test tool locally with Python scripts

### "LLM evaluation unclear"
- Rubric might be too vague
- Check transcript manually
- Adjust rubric for clarity

### "Test keeps failing but works manually"
- Check script for ambiguous wording
- Test exact script phrases manually
- Review speech recognition in transcript

---

**You now have 14 production-ready test suites!** 🚀

Start with the critical tests (1, 2, 4, 7) and expand from there.
