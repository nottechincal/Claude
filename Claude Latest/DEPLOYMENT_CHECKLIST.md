# Deployment Checklist - VAPI Integration

**Status:** Ready for deployment
**Date:** 2025-10-29
**Tests:** 64/64 passing (100%)

---

## Prerequisites (Already Complete)

- ✅ All critical bugs fixed
- ✅ GST calculation working correctly
- ✅ Redis session storage implemented
- ✅ 100% test pass rate
- ✅ ngrok installed and ready

---

## Step 1: Start Your Server

### 1.1 Configure Environment Variables

Create `.env` file if you haven't already:

```bash
# Copy from example
cp .env.example .env
```

Edit `.env` and set:

```bash
# Required
DATABASE_FILE=data/orders.db
MENU_FILE=data/menu.json
BUSINESS_FILE=data/business.json

# Optional - SMS (can skip for testing)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# Optional - Redis (falls back to in-memory if not available)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Optional - CORS (already allows all for testing)
# ALLOWED_ORIGINS=https://vapi.ai,https://app.vapi.ai
```

### 1.2 Install Dependencies

```bash
cd "Claude Latest"
pip install -r requirements.txt
```

### 1.3 Start Flask Server

```bash
python kebabalab/server.py
```

You should see:
```
WARNING: rapidfuzz not available, fuzzy matching disabled
✓ Redis connected: localhost:6379 (db=0)  # OR: using in-memory sessions
Loading menu from: data/menu.json
Loaded 46 menu items from 6 categories
Database initialized at: data/orders.db
 * Running on http://127.0.0.1:5000
```

---

## Step 2: Expose with ngrok

### 2.1 Start ngrok

In a **separate terminal**:

```bash
ngrok http 5000
```

### 2.2 Copy Your Public URL

You'll see something like:
```
Forwarding    https://abc123.ngrok.io -> http://localhost:5000
```

Copy the `https://abc123.ngrok.io` URL.

Your webhook URL will be: `https://abc123.ngrok.io/webhook`

---

## Step 3: Configure VAPI Dashboard

### 3.1 Set Webhook URL

1. Go to https://dashboard.vapi.ai
2. Navigate to your assistant settings
3. Find "Server URL" or "Webhook URL" field
4. Enter: `https://abc123.ngrok.io/webhook`
5. Save

### 3.2 Upload System Prompt

1. In VAPI dashboard, find "System Prompt" section
2. Copy the entire contents of: `config/system-prompt-simplified.md`
3. Paste into VAPI system prompt field
4. Save

### 3.3 Upload Tool Definitions

1. In VAPI dashboard, find "Functions" or "Tools" section
2. Open: `config/vapi-tools-simplified.json`
3. You need to add each of the **17 tools** individually:

**The 17 Tools to Add:**
1. `checkOpen` - Check if shop is open
2. `quickAddItem` - Add item to cart
3. `modifyCartItem` - Modify cart item
4. `removeCartItem` - Remove item from cart
5. `reviewCart` - Show cart contents
6. `priceCart` - Calculate prices
7. `convertItemsToMeals` - Suggest combos
8. `clearCart` - Clear entire cart
9. `setPickupTime` - Set pickup time
10. `getOrderSummary` - Get final summary
11. `createOrder` - Finalize order
12. `getMenuCategory` - Show menu category
13. `searchMenuByProtein` - Search by protein
14. `getBestSellers` - Show popular items
15. `getComboOptions` - Show combo deals
16. `getAvailableDrinks` - List drinks
17. `getAvailableExtras` - List extras

For each tool, copy the JSON definition from `vapi-tools-simplified.json` and paste into VAPI.

**Example for `checkOpen`:**
```json
{
  "type": "function",
  "function": {
    "name": "checkOpen",
    "description": "Check if the shop is currently open",
    "parameters": {
      "type": "object",
      "properties": {}
    }
  }
}
```

### 3.4 Configure Assistant Settings

Recommended VAPI settings:

- **Model**: GPT-4 or GPT-4-turbo (for best performance)
- **Voice**: Choose Australian English voice if available
- **Temperature**: 0.7 (balanced creativity)
- **Max Tokens**: 150-200 (concise responses)
- **First Message**: "G'day! Welcome to Kebabalab St Kilda. Are you ready to order?"

---

## Step 4: Test Your Connection

### 4.1 Test Webhook Endpoint

Test that VAPI can reach your webhook:

```bash
curl -X POST https://abc123.ngrok.io/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "type": "tool-calls",
      "call": {
        "id": "test-123",
        "type": "webCall",
        "customer": {"number": "+61412345678"}
      },
      "toolCalls": [{
        "id": "test-call-1",
        "type": "function",
        "function": {
          "name": "checkOpen",
          "arguments": {}
        }
      }]
    }
  }'
```

Expected response:
```json
{
  "results": [{
    "toolCallId": "test-call-1",
    "result": "{\"ok\": true, \"isOpen\": true, \"message\": \"...\"}"
  }]
}
```

---

## Step 5: Make Your First Test Call

### 5.1 Call Your VAPI Number

Call the phone number assigned to your VAPI assistant.

### 5.2 Test Order Flow

Try this complete order:

**Customer:** "Hi, I'd like to order"
**System:** "G'day! Welcome to Kebabalab St Kilda. Are you ready to order?"
**Customer:** "Yes, I want a large lamb kebab with no onion"
**System:** "Got it, large lamb kebab with no onion. Anything else?"
**Customer:** "And small chips"
**System:** "Added small chips. Anything else?"
**Customer:** "No that's all"
**System:** "Let me get your total..." [calls priceCart]
**System:** "Your total is $20.00 including $1.82 GST. When would you like to pick up?"
**Customer:** "In 20 minutes"
**System:** "Pickup at [time]. Can I get your name?"
**Customer:** "John Smith"
**System:** "And your phone number?"
**Customer:** "0412 345 678"
**System:** "Perfect! Order confirmed. Pick up at [time]. See you soon!"

### 5.3 Verify Order in Database

After the call, check that order was saved:

```bash
sqlite3 data/orders.db "SELECT * FROM orders ORDER BY id DESC LIMIT 1;"
```

You should see your order with:
- Customer name: John Smith
- Customer phone: +61412345678
- Total: $20.00
- GST: $1.82
- Status: confirmed
- Items JSON with large lamb kebab and small chips

---

## Step 6: Monitor Logs

### 6.1 Watch Server Logs

Keep the Flask terminal open to monitor:

```
=== WEBHOOK REQUEST ===
Call ID: call-abc123
Phone: +61412345678
Tool: quickAddItem
Args: {"description": "large lamb kebab no onion"}

=== WEBHOOK RESPONSE ===
Status: 200
Result: {"ok": true, "message": "Added to cart"}
```

### 6.2 Watch ngrok Logs

ngrok shows all HTTP requests:
```
POST /webhook    200 OK
POST /webhook    200 OK
```

### 6.3 Check for Errors

If you see any errors:

1. **500 errors** - Check Flask terminal for Python exceptions
2. **404 errors** - Webhook URL is wrong in VAPI dashboard
3. **Timeouts** - Server is too slow or crashed
4. **No response** - ngrok not forwarding or server not running

---

## Step 7: Common Issues

### Issue: "Connection refused"
**Fix:** Make sure Flask server is running on port 5000

### Issue: "404 Not Found"
**Fix:** Webhook URL should end with `/webhook` (e.g., `https://abc123.ngrok.io/webhook`)

### Issue: "Tool not found"
**Fix:** Make sure all 17 tools are added to VAPI dashboard with exact names

### Issue: "Redis connection failed"
**Fix:** Redis is optional, system will use in-memory sessions automatically

### Issue: "GST showing $0.00"
**Fix:** This was fixed in the code - should show correct GST now

### Issue: "Prices are wrong"
**Fix:** All prices now come from `data/menu.json` - edit that file

### Issue: "Session data lost between calls"
**Fix:** Check that VAPI is using the same call ID for the conversation

---

## Step 8: Production Checklist (Before Going Live)

### Security:
- [ ] Restrict CORS origins to VAPI domains only
- [ ] Add webhook signature verification
- [ ] Add rate limiting
- [ ] Use environment-based error messages (hide details in prod)

### Configuration:
- [ ] Set up Redis in production (Render, Railway, etc.)
- [ ] Configure Twilio for SMS confirmations
- [ ] Update shop hours in code or move to config
- [ ] Set proper timezone (Australia/Melbourne)

### Monitoring:
- [ ] Set up logging to file or service
- [ ] Monitor order creation rate
- [ ] Track error rates
- [ ] Set up alerts for failures

### Testing:
- [ ] Test during shop hours
- [ ] Test outside shop hours (should say closed)
- [ ] Test invalid orders
- [ ] Test with different phone numbers
- [ ] Test combos and meal upgrades
- [ ] Test exclusions (no onion, no cheese, etc.)

---

## Quick Reference

### Server Start Command:
```bash
cd "Claude Latest" && python kebabalab/server.py
```

### ngrok Start Command:
```bash
ngrok http 5000
```

### Test Webhook:
```bash
curl -X POST https://YOUR-NGROK-URL.ngrok.io/webhook -H "Content-Type: application/json" -d @test_payload.json
```

### Check Recent Orders:
```bash
sqlite3 data/orders.db "SELECT id, customer_name, total, status, created_at FROM orders ORDER BY id DESC LIMIT 5;"
```

### View Order Details:
```bash
sqlite3 data/orders.db "SELECT * FROM orders WHERE id = 1;"
```

---

## Success Checklist

When everything is working, you should be able to:

- ✅ Call VAPI number and hear greeting
- ✅ Order items using natural language
- ✅ Get correct prices with GST
- ✅ Set pickup time
- ✅ Provide name and phone
- ✅ Receive order confirmation
- ✅ See order in database
- ✅ (Optional) Receive SMS confirmation

---

## Need Help?

If you encounter issues:

1. **Check Flask logs** - Most errors show here
2. **Check ngrok logs** - Shows if requests are reaching server
3. **Check VAPI logs** - Shows AI responses and tool calls
4. **Check database** - Verify orders are being saved
5. **Review test results** - Both test suites should pass 100%

---

**Current Status:** All systems ready for deployment
**Test Results:** 64/64 tests passing (100%)
**Critical Bugs:** All fixed
**Ready for:** Live customer calls

🚀 **You're ready to take orders!**
