# VAPI Dashboard Fixes Required
**Date:** October 23, 2025
**Priority:** URGENT - These fixes are required for the system to work properly

---

## Summary

I've fixed **all the server-side bugs** that I could fix in code:
- ✅ Menu file path fixed
- ✅ Size defaulting removed (now asks customer)
- ✅ editCartItem corruption bug fixed with validation
- ✅ Pricing calculation protected

However, several issues **CANNOT be fixed in the server code** - they require changes to your VAPI dashboard configuration. Here's exactly what you need to fix:

---

## ISSUE 1: "Give me a moment" Spam 🔴 CRITICAL

### Problem
The AI says "give me a moment", "hold on a sec", "just a sec" constantly throughout the call (10+ times). This makes the experience robotic and annoying.

### Root Cause
VAPI's "thinking messages" feature is enabled and firing on every tool call.

### Fix Required (VAPI Dashboard)
1. Go to your VAPI Assistant settings
2. Find "Server Messages" or "Thinking Messages" section
3. **Option A: Disable them completely** (recommended)
   - Turn off "thinking messages"

4. **Option B: Customize them** (if you want to keep some)
   - Change the generic messages to more natural phrases:
     - "Let me check that for you"
     - "One moment while I prepare your order"
     - "Almost done"
   - Set them to trigger less frequently (not on every tool call)

### Alternative Solution
For each tool, you can set custom response messages:
- `quickAddItem` → "Adding that to your order"
- `editCartItem` → "I'll change that for you"
- `priceCart` → (no message needed, just return the total)
- `createOrder` → (no message needed, confirmation is in the response)

---

## ISSUE 2: sendReceipt Sends Menu Link 🔴 CRITICAL

### Problem
When customer says "send me the receipt", the AI calls `sendMenuLink` multiple times instead of calling `sendReceipt`.

### Root Cause
The AI is choosing the wrong tool based on the system prompt or tool descriptions.

### Fix Required (VAPI Dashboard)

#### Part 1: Check Tool Descriptions
1. Go to your tools list
2. Check the description for `sendReceipt`:
   ```
   Should say: "Send order receipt via SMS to customer's phone"
   ```
3. Check the description for `sendMenuLink`:
   ```
   Should say: "Send restaurant menu link via SMS"
   ```
4. Make sure they're clearly different!

#### Part 2: Update System Prompt
Add this to your system prompt:

```
IMPORTANT - Tool Selection:
- When customer asks for "receipt", "confirmation", or "order details" → use sendReceipt
- When customer asks for "menu", "what do you have", or "see options" → use sendMenuLink
- NEVER send menu link when customer wants a receipt!
```

#### Part 3: Test with Explicit Instruction
Try updating the prompt to be more explicit:

```
If the customer says any of these phrases, call sendReceipt:
- "send me the receipt"
- "text me the receipt"
- "send confirmation"
- "send order details"
```

---

## ISSUE 3: Pickup Time Auto-Estimation 🟡 MEDIUM

### Problem
The system automatically estimates pickup time without asking the customer when they want to pick up.

### Root Cause
The AI is calling `estimateReadyTime` on its own instead of first asking the customer.

### Fix Required (VAPI Dashboard)

Update your system prompt with this section:

```
PICKUP TIME PROTOCOL:

1. ALWAYS ask the customer: "When would you like to pick this up?"

2. Wait for customer response:
   - If they say "as soon as possible", "ASAP", "now", or "right away" → call estimateReadyTime
   - If they give a specific time (e.g., "6:30 PM", "in 20 minutes") → call setPickupTime

3. NEVER call estimateReadyTime without asking first
4. Minimum pickup time is 10 minutes from now
5. If customer says less than 10 minutes, tell them: "We need at least 10 minutes to prepare your order"

PHRASING:
- If customer says "in X minutes" → respond: "Perfect, see you in X minutes"
- If customer says specific time like "6:30" → respond: "Great, see you at six thirty"
- If customer says "ASAP" → call estimateReadyTime, then say: "Your order will be ready in about X minutes"
```

---

## ISSUE 4: Call Not Ending 🟡 MEDIUM

### Problem
After `endCall` tool is executed, the AI continues talking and calling more tools instead of ending the conversation.

### Root Cause
The `endCall` tool doesn't have the "end call" action enabled in VAPI.

### Fix Required (VAPI Dashboard)

1. Go to your tools list
2. Find the `endCall` tool
3. Look for "Server Message" or "End Call Action" settings
4. **Enable "End Call After Execution"** or similar option
5. The response message should be: "Thank you for calling Kebabalab. Have a great day!"

### Alternative
If the above setting doesn't exist, update your system prompt:

```
ENDING CALLS:

When you call the endCall tool, you MUST stop all conversation immediately.
Do NOT call any other tools after endCall.
Do NOT say anything else after calling endCall.
The server will handle the goodbye message.
```

---

## ISSUE 5: Better Time Phrasing 🟢 LOW PRIORITY

### Current Behavior
System says exact time like "5:45 PM" which sounds robotic.

### Desired Behavior
More natural phrasing:
- "See you in 15 minutes"
- "Ready at half past six"
- "Your order will be ready in about 20 minutes"

### Fix Required (VAPI Dashboard)

Update system prompt with natural phrasing guidelines:

```
NATURAL TIME PHRASING:

When telling pickup time:
- For minutes: "See you in 15 minutes" or "Ready in about 20 minutes"
- For specific times: "See you at six thirty" or "Ready at quarter past five"
- Avoid robotic times like "17:45" or "5:45 PM"

Examples:
- Customer: "I'll pick it up in 20 minutes" → You: "Perfect! See you in 20 minutes"
- Customer: "I'll be there at 6:30" → You: "Great! See you at six thirty"
- Customer: "As soon as possible" → You: "Your order will be ready in about 15 minutes"
```

---

## Testing Checklist

After making these VAPI dashboard changes, test the following:

### Test 1: Thinking Messages
- [ ] Make an order
- [ ] Count how many times AI says "give me a moment" or similar
- [ ] Should be 0-2 times max (not 10+)

### Test 2: Receipt vs Menu
- [ ] Complete an order
- [ ] Say "send me the receipt"
- [ ] Verify you receive RECEIPT SMS (not menu link)
- [ ] Verify you only get ONE SMS (not multiple)

### Test 3: Pickup Time
- [ ] Start an order
- [ ] AI should ASK "When would you like to pick this up?"
- [ ] AI should NOT auto-estimate without asking

### Test 4: Call Ending
- [ ] Complete an order
- [ ] After confirmation, call should end cleanly
- [ ] AI should NOT continue calling tools after endCall

### Test 5: Size Confirmation
- [ ] Say "I want a chicken kebab"
- [ ] AI should ASK "Would you like small or large?"
- [ ] AI should NOT assume large

### Test 6: Pricing
- [ ] Order 2 small chicken kebabs
- [ ] Total should be $20 (not $35)
- [ ] Change one to large → total should be $25

---

## Summary of What I Fixed (Server-Side)

✅ **Menu path** - Server can now find menu.json correctly
✅ **Size defaulting** - Server now returns error if size not specified (forces AI to ask)
✅ **editCartItem corruption** - Added validation to prevent salads/sauces mixing
✅ **Pricing calculation** - Protected against corruption, always recalculates
✅ **Detailed logging** - Added before/after logs for debugging

---

## What YOU Need to Fix (VAPI Dashboard)

🔴 **Critical - Fix These First:**
1. Disable or customize "thinking messages" to stop "give me a moment" spam
2. Fix tool selection so sendReceipt is called instead of sendMenuLink
3. Update system prompt to ask for pickup time before estimating

🟡 **Medium Priority:**
4. Enable "end call action" on endCall tool
5. Add better tool descriptions to help AI choose correctly

🟢 **Nice to Have:**
6. Natural time phrasing in system prompt

---

## Need Help?

If you need help with any of these VAPI dashboard changes:
1. Check VAPI documentation for your specific dashboard version
2. Look for "Server Messages", "Tool Settings", or "System Prompt" sections
3. Test one change at a time to isolate any issues

---

**All server-side fixes have been committed and pushed.**
**Branch:** `claude/review-system-011CUPtj8Diq4MicfKFmxmei`
**Ready for deployment after VAPI dashboard fixes.**
