# Production Deployment Guide - Simplified System

This guide walks you through deploying the simplified 15-tool system to production.

## Pre-Deployment Checklist

Before you begin, ensure you have:

- [ ] VAPI account and API key
- [ ] Production server (or ngrok for testing)
- [ ] Access to update VAPI assistant configuration
- [ ] Backup of current system (just in case)
- [ ] 30-60 minutes for deployment

---

## Step 1: Backup Current System

### A. Backup Current Database

```bash
cd "Claude Latest/data"
cp orders.db orders.db.backup-$(date +%Y%m%d-%H%M%S)
```

### B. Document Current VAPI Configuration

1. Go to https://dashboard.vapi.ai
2. Open your assistant
3. Take screenshots of:
   - Tool list
   - System prompt
   - Voice settings
4. Export tool configurations if possible

---

## Step 2: Prepare Production Environment

### A. Install Dependencies

```bash
cd "Claude Latest"
pip install flask flask-cors python-dotenv --quiet
```

### B. Create Production Environment File

```bash
cp .env.example .env.production
```

Edit `.env.production`:

```env
# Server Configuration
PORT=8000
ENVIRONMENT=production
DEBUG=false

# Database
DB_PATH=data/orders.db

# VAPI Configuration (optional - for webhook verification)
VAPI_API_KEY=your_vapi_api_key_here
VAPI_PHONE_NUMBER=your_vapi_phone_number

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/kebabalab_production.log

# Security (add if needed)
WEBHOOK_SECRET=your_webhook_secret_here
```

### C. Create Required Directories

```bash
mkdir -p logs
mkdir -p data
mkdir -p backups
```

---

## Step 3: Test Server Locally

### A. Run the Test Suite

```bash
python test_chip_upgrade.py
```

Expected output:
```
✓ TEST PASSED - Chip upgrade works in 1 call!
✓ QuickAddItem tests complete
ALL TESTS PASSED!
```

### B. Start the Server

```bash
python server_simplified.py
```

Expected output:
```
==================================================
Kebabalab VAPI Server - SIMPLIFIED
==================================================
Database initialized
Menu loaded successfully
Loaded 15 tools:
  1. checkOpen
  2. getCallerSmartContext
  ... (etc)
Starting server on port 8000
```

### C. Test Health Endpoint

In another terminal:

```bash
curl http://localhost:8000/health
```

Expected:
```json
{
  "status": "healthy",
  "server": "kebabalab-simplified",
  "tools": 15,
  "sessions": 0
}
```

If all tests pass, proceed to Step 4.

---

## Step 4: Expose Server to Internet

### Option A: Using ngrok (Testing/Development)

```bash
# In a new terminal
ngrok http 8000
```

You'll get a URL like: `https://abc123.ngrok-free.app`

**Note:** ngrok URLs change each time. For production, use Option B.

### Option B: Production Server (Recommended)

Deploy to your production server (e.g., AWS, DigitalOcean, Railway, etc.)

**Example using Railway:**

1. Install Railway CLI
2. `railway login`
3. `railway init`
4. `railway up`
5. Note your production URL

**Example using Docker:**

```bash
# Create Dockerfile (see Step 5B)
docker build -t kebabalab-vapi .
docker run -p 8000:8000 kebabalab-vapi
```

---

## Step 5: Production Server Setup (Optional)

### A. Create Production Start Script

Create `start_production.sh`:

```bash
#!/bin/bash

echo "Starting Kebabalab VAPI Server (Production)..."

# Load production environment
export ENVIRONMENT=production

# Start server with gunicorn (production-grade)
gunicorn -w 4 -b 0.0.0.0:8000 --timeout 120 --log-level info server_simplified:app
```

Make executable:
```bash
chmod +x start_production.sh
```

### B. Create Dockerfile (Optional)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn

# Copy application
COPY . .

# Create necessary directories
RUN mkdir -p logs data backups

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run server
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "--timeout", "120", "server_simplified:app"]
```

### C. Update requirements.txt

Add to `requirements.txt`:

```
flask==3.0.0
flask-cors==4.0.0
python-dotenv==1.0.0
gunicorn==21.2.0
```

---

## Step 6: Update VAPI Configuration

### A. Get Your Webhook URL

Your webhook URL will be one of:
- ngrok: `https://abc123.ngrok-free.app/webhook`
- Production: `https://your-domain.com/webhook`

**Important:** Note this URL - you'll need it for all 15 tools.

### B. Prepare Tool Definitions

Edit `config/vapi-tools-simplified.json` and replace all instances of `YOUR_WEBHOOK_URL` with your actual webhook URL.

You can use this command:

```bash
# Replace with your webhook URL
WEBHOOK_URL="https://your-domain.com"

sed "s|YOUR_WEBHOOK_URL|$WEBHOOK_URL|g" \
  config/vapi-tools-simplified.json > \
  config/vapi-tools-production.json
```

### C. Upload Tools to VAPI

**Option 1: Manual Upload (Safest for first time)**

1. Go to https://dashboard.vapi.ai
2. Navigate to "Tools" section
3. **Delete all 22 old tools** (after confirming backup)
4. For each tool in `config/vapi-tools-production.json`:
   - Click "Create Tool"
   - Select "Function"
   - Copy the tool definition
   - Paste into VAPI
   - Save

**Option 2: API Upload (Faster)**

Use the script in Step 7.

### D. Update Assistant System Prompt

1. Go to your VAPI assistant
2. Click "Edit"
3. Scroll to "System Prompt"
4. **Copy entire contents** of `config/system-prompt-simplified.md`
5. Paste into VAPI system prompt field
6. Save

### E. Attach Tools to Assistant

1. In your VAPI assistant settings
2. Go to "Tools" section
3. **Remove all old tools**
4. **Add all 15 new tools:**
   - checkOpen
   - getCallerSmartContext
   - quickAddItem
   - addMultipleItemsToCart
   - getCartState
   - removeCartItem
   - editCartItem
   - priceCart
   - convertItemsToMeals
   - getOrderSummary
   - setPickupTime
   - estimateReadyTime
   - createOrder
   - repeatLastOrder
   - endCall
5. Save assistant

---

## Step 7: VAPI Tool Upload Script

Create `upload_tools_to_vapi.py`:

```python
"""
Upload simplified tools to VAPI via API

Usage:
  python upload_tools_to_vapi.py YOUR_VAPI_API_KEY YOUR_WEBHOOK_URL
"""

import json
import requests
import sys

def upload_tools(api_key, webhook_url):
    """Upload all tools to VAPI"""

    # Load tool definitions
    with open('config/vapi-tools-simplified.json', 'r') as f:
        config = json.load(f)

    tools = config['tools']

    print(f"Uploading {len(tools)} tools to VAPI...")
    print(f"Webhook URL: {webhook_url}")
    print()

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    created_tools = []

    for tool in tools:
        tool_name = tool['function']['name']

        # Update webhook URL
        tool['server']['url'] = f"{webhook_url}/webhook"

        print(f"Creating tool: {tool_name}...", end=" ")

        # Create tool via VAPI API
        response = requests.post(
            'https://api.vapi.ai/tool',
            headers=headers,
            json=tool
        )

        if response.status_code in [200, 201]:
            tool_id = response.json().get('id')
            created_tools.append({
                'name': tool_name,
                'id': tool_id
            })
            print(f"✓ (ID: {tool_id})")
        else:
            print(f"✗ Error: {response.status_code}")
            print(f"   {response.text}")

    print()
    print(f"Successfully created {len(created_tools)} tools")
    print()
    print("Tool IDs:")
    for tool in created_tools:
        print(f"  {tool['name']}: {tool['id']}")

    print()
    print("Next steps:")
    print("1. Go to https://dashboard.vapi.ai")
    print("2. Open your assistant")
    print("3. Add these tools to your assistant")

    return created_tools

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python upload_tools_to_vapi.py YOUR_VAPI_API_KEY YOUR_WEBHOOK_URL")
        print()
        print("Example:")
        print("  python upload_tools_to_vapi.py sk_... https://your-domain.com")
        sys.exit(1)

    api_key = sys.argv[1]
    webhook_url = sys.argv[2].rstrip('/')

    upload_tools(api_key, webhook_url)
```

**Usage:**

```bash
python upload_tools_to_vapi.py YOUR_VAPI_API_KEY https://your-domain.com
```

---

## Step 8: Test the Deployment

### A. Make a Test Call

Call your VAPI phone number and test:

**Test 1: Simple Order**
```
You: "Hi"
AI: "Welcome to Kebabalab! What can I get for you?"
You: "Large chicken kebab with lettuce, tomato, and garlic sauce"
AI: [Adds item] "Got it! Anything else?"
You: "No thanks"
AI: [Confirms order and total]
```

**Test 2: Meal Conversion**
```
You: "Can I get a chicken kebab?"
AI: "Small or large?"
You: "Large"
AI: [Asks for salads/sauces]
You: "Lettuce, tomato, garlic"
AI: [Adds item]
You: "Can you make that a meal with a Coke?"
AI: [Converts to meal] "Sure, I've made that a Large Kebab Meal for you!"
```

**Test 3: THE CRITICAL TEST - Chip Upgrade**
```
You: "Is that with small chips or large chips?"
AI: "Small chips"
You: "Can you make it large chips?"
AI: [editCartItem in 1 call] "Done! That's now $25 total"
```

**Expected behavior:**
- ✅ Response within 5 seconds
- ✅ Price updates correctly
- ✅ NO long pauses
- ✅ NO looping

### B. Check Server Logs

```bash
tail -f logs/kebabalab_production.log
```

Look for:
- No errors
- Tool calls executing correctly
- Chip upgrade: ONE editCartItem call (not 20+)

### C. Verify Database

```bash
sqlite3 data/orders.db "SELECT * FROM orders ORDER BY created_at DESC LIMIT 1;"
```

Should show your test order saved correctly.

---

## Step 9: Monitor First Real Orders

### A. Watch Logs in Real-Time

```bash
tail -f logs/kebabalab_production.log | grep -E "Tool call|Error|WARNING"
```

### B. Key Metrics to Monitor

- **Tool call count per order:** Should be 8-12 (was 25-30)
- **editCartItem loops:** Should NEVER happen
- **Customer wait time:** Should be <30 seconds total
- **Error rate:** Should be <1%

### C. Common Issues and Fixes

**Issue: "Tool not found" error**
- Fix: Verify all 15 tools are created in VAPI
- Fix: Check webhook URL is correct

**Issue: "Invalid itemIndex" error**
- Fix: Check getCartState is being called before editCartItem
- Fix: Verify index is 0-based

**Issue: Slow responses**
- Fix: Check server CPU/memory
- Fix: Verify webhook URL is reachable
- Fix: Check internet connection

---

## Step 10: Rollback Plan (If Needed)

If something goes wrong, you can quickly rollback:

### A. Rollback Server

```bash
# Stop simplified server
pkill -f server_simplified.py

# Start old server
python server_v2.py
```

### B. Rollback VAPI

1. Go to VAPI dashboard
2. Delete 15 new tools
3. Re-create 22 old tools from backup
4. Restore old system prompt
5. Attach old tools to assistant

### C. Rollback Database (if needed)

```bash
cd data
cp orders.db orders.db.failed-deployment
cp orders.db.backup-XXXXXXXX orders.db
```

---

## Production Checklist

Before declaring deployment complete:

- [ ] Server is running and accessible
- [ ] Health check returns 200 OK
- [ ] All 15 tools created in VAPI
- [ ] System prompt updated
- [ ] Tools attached to assistant
- [ ] Test call completed successfully
- [ ] Chip upgrade works in 1 call
- [ ] Database saving orders correctly
- [ ] Logs show no errors
- [ ] Monitoring set up
- [ ] Team notified of changes
- [ ] Rollback plan documented
- [ ] Backup confirmed working

---

## Success Criteria

Your deployment is successful when:

✅ **Test calls work perfectly**
- Simple orders: <10 tool calls
- Meal conversions: 1 call
- Chip upgrades: 1 call (not 20+)

✅ **Performance improved**
- Order completion time: <1 minute (was 2+ minutes)
- No customer hang-ups
- No infinite loops

✅ **All features working**
- Order history
- Repeat orders
- Meal conversions
- Custom pickup times
- Order confirmation

---

## Post-Deployment

### Week 1: Close Monitoring

- Check logs daily
- Review any error reports
- Monitor customer feedback
- Track order completion rates

### Week 2-4: Optimization

- Analyze tool usage patterns
- Optimize frequently-used tools
- Add logging for edge cases
- Consider additional improvements

### Ongoing: Maintenance

- Regular database backups
- Log rotation
- Performance monitoring
- Feature additions (following the 15-tool principle)

---

## Support

If you encounter issues:

1. **Check logs first:** `tail -f logs/kebabalab_production.log`
2. **Test health endpoint:** `curl http://your-server/health`
3. **Review this guide:** Look for similar issues
4. **Test locally:** Run `python test_chip_upgrade.py`
5. **Rollback if critical:** Follow rollback plan

---

## Summary

**Deployment Steps:**
1. ✅ Backup current system
2. ✅ Install dependencies
3. ✅ Test server locally
4. ✅ Expose server to internet
5. ✅ Update VAPI tools (delete 22, add 15)
6. ✅ Update system prompt
7. ✅ Make test calls
8. ✅ Monitor first real orders
9. ✅ Celebrate success 🎉

**Expected Results:**
- 70% faster orders
- Zero chip upgrade loops
- Happy customers
- Clean logs
- Maintainable codebase

**You're ready to go live!**

---

Created: October 23, 2025
Status: Production-Ready ✅
