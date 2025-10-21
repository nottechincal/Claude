# 🔧 Troubleshooting Guide

## Issue: Assistant Calling Old Tools

### Symptoms
- Assistant says "Hold on a sec" repeatedly
- Calls `validateItem`, `validateMenuItems`, etc. (OLD tools)
- Doesn't call `startItemConfiguration`, `setItemProperty`, etc. (NEW tools)
- Doesn't follow the order flow properly

### Root Cause
Your assistant still has old tools attached and/or new tools haven't been created yet.

---

## 🚀 Quick Fix (Recommended)

### Step 1: Run Diagnostic Script

```powershell
cd "Claude Latest"
./vapi-diagnostic.ps1
```

This will show you:
- ✓/✗ Which new tools exist
- ✓/✗ Which new tools are attached
- ⚠ Which old tools need removal

**Screenshot the output and check what it says.**

### Step 2: Run Setup Script

```powershell
./vapi-setup-tools.ps1
```

This will:
- Create all 10 new tools
- Optionally delete old tools
- Attach new tools to your assistant

**Answer "y" when it asks to delete old tools.**

### Step 3: Update System Prompt

1. Go to https://dashboard.vapi.ai/assistants
2. Open your assistant
3. Go to **System Message** or **Instructions** section
4. **Delete everything**
5. Open `system-prompt.md` from this folder
6. **Copy ALL contents** (Ctrl+A, Ctrl+C)
7. **Paste** into VAPI (Ctrl+V)
8. **Save**

### Step 4: Verify Server & Ngrok

```bash
# Terminal 1: Server running?
python server_v2.py

# Terminal 2: Ngrok running?
ngrok http 8000

# Check ngrok URL matches tools:
# Should be: https://surveyable-natisha-unsacred.ngrok-free.dev
```

### Step 5: Test

Call your assistant and say:
```
"Small chicken kebab"
```

Expected behavior:
- ✓ Should ask: "What salads would you like?"
- ✓ Should call `startItemConfiguration`
- ✓ Should call `setItemProperty` multiple times
- ✗ Should NOT call `validateItem`

---

## 📋 Manual Fix (If Scripts Don't Work)

### 1. Check Tools in VAPI Dashboard

Go to: https://dashboard.vapi.ai/tools

**You should see these NEW tools:**
- ✅ checkOpen
- ✅ getCallerInfo
- ✅ startItemConfiguration ⭐
- ✅ setItemProperty ⭐
- ✅ addItemToCart ⭐
- ✅ getCartState
- ✅ priceCart
- ✅ estimateReadyTime
- ✅ createOrder
- ✅ endCall

**Delete these OLD tools if present:**
- ❌ validateItem
- ❌ validateMenuItems
- ❌ priceOrder (old version)
- ❌ notifyShop
- ❌ sendReceipt
- ❌ sendMenuLink
- ❌ validateSauceRequest
- ❌ testConnection
- ❌ detectCombos

### 2. Check Assistant Tools

Go to: https://dashboard.vapi.ai/assistants

Open your assistant → **Tools** section

**Should have ONLY these 10 tools:**
1. checkOpen
2. getCallerInfo
3. startItemConfiguration
4. setItemProperty
5. addItemToCart
6. getCartState
7. priceCart
8. estimateReadyTime
9. createOrder
10. endCall

**If you see old tools** → Remove them!

### 3. Create Missing Tools Manually

If any new tools are missing, create them using the VAPI API:

```powershell
# Use vapi-setup-tools.ps1 - it's easier!
./vapi-setup-tools.ps1
```

Or create manually in dashboard using `vapi-tools-definitions.json` as reference.

---

## 🔍 Detailed Diagnostics

### Check Server Logs

```bash
# If server is running, check logs:
tail -f kebabalab_server.log

# You should see tool calls like:
# "Calling tool: startItemConfiguration"
# "Calling tool: setItemProperty"
```

### Test Server Directly

```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "toolCalls": [{
        "function": {
          "name": "checkOpen",
          "arguments": "{}"
        },
        "id": "test123"
      }]
    }
  }'
```

Expected response:
```json
{
  "results": [{
    "toolCallId": "test123",
    "result": {
      "ok": true,
      "isOpen": true,
      ...
    }
  }]
}
```

### Check Ngrok

```bash
# Visit ngrok web interface:
http://localhost:4040

# Check requests are coming through
# Should see POST requests to /webhook
```

### Check VAPI Assistant Config

```powershell
# Use diagnostic script:
./vapi-diagnostic.ps1

# Or check manually:
$ApiKey = "4000447a-37e5-4aa6-b7b3-e692bec2706f"
$AssistantId = "320f76b1-140a-412c-b95f-252032911ca3"

Invoke-RestMethod -Method Get `
  -Uri "https://api.vapi.ai/assistant/$AssistantId" `
  -Headers @{
    "Authorization" = "Bearer $ApiKey"
    "Content-Type" = "application/json"
  }
```

---

## ❌ Common Issues & Fixes

### Issue: "validateItem not found"
**Fix:** Old tools still attached. Run `vapi-setup-tools.ps1` and delete old tools.

### Issue: "startItemConfiguration not found"
**Fix:** New tools not created. Run `vapi-setup-tools.ps1` to create them.

### Issue: Assistant says "Hold on a sec" repeatedly
**Fix:** Tools not responding or wrong webhook URL. Check:
1. Server is running
2. Ngrok is running
3. Webhook URL in tools matches ngrok URL

### Issue: Assistant doesn't ask for salads/sauces
**Fix:** System prompt not updated. Copy `system-prompt.md` to VAPI.

### Issue: Webhook returns 404
**Fix:**
1. Check server is running: `python server_v2.py`
2. Check ngrok is forwarding to port 8000
3. Check URL in tools is correct

### Issue: Tools return "ok: false"
**Fix:** Check server logs for actual error:
```bash
tail -f kebabalab_server.log | grep ERROR
```

---

## ✅ Verification Checklist

After fixing, verify:

- [ ] All 10 new tools exist in VAPI
- [ ] All 10 new tools attached to assistant
- [ ] No old tools attached
- [ ] System prompt updated (from system-prompt.md)
- [ ] Server running (`python server_v2.py`)
- [ ] Ngrok running and URL matches
- [ ] Test call works:
  - [ ] Asks for salads
  - [ ] Asks for sauces
  - [ ] Calls `startItemConfiguration`
  - [ ] Calls `setItemProperty`
  - [ ] Calls `addItemToCart`

---

## 🆘 Still Not Working?

### 1. Share Diagnostic Output

Run and share:
```powershell
./vapi-diagnostic.ps1 > diagnostic-output.txt
```

### 2. Share Server Logs

```bash
tail -100 kebabalab_server.log > server-log.txt
```

### 3. Share Call Transcript

From VAPI dashboard → Call logs → Copy transcript

### 4. Check These

- ✅ Python server running on port 8000?
- ✅ Ngrok forwarding to port 8000?
- ✅ Ngrok URL matches tools webhook URL?
- ✅ System prompt is from `system-prompt.md`?
- ✅ VAPI assistant ID is `320f76b1-140a-412c-b95f-252032911ca3`?

---

## 🎯 Expected Behavior

When working correctly:

**Customer:** "Small chicken kebab"

**Assistant Flow:**
1. Calls `startItemConfiguration { category: "kebabs" }`
2. Calls `setItemProperty { field: "size", value: "small" }`
3. Calls `setItemProperty { field: "protein", value: "chicken" }`
4. **Asks:** "What salads would you like?"
5. Customer answers
6. Calls `setItemProperty { field: "salads", value: [...] }`
7. **Asks:** "Which sauces?"
8. Customer answers
9. Calls `setItemProperty { field: "sauces", value: [...] }`
10. **Asks:** "Any extras?"
11. Customer answers
12. Calls `addItemToCart {}`
13. **Says:** "Got it! Anything else?"

**No "Hold on a sec", no `validateItem`, no errors.**

---

## 📞 Quick Commands Reference

```bash
# Start server
python server_v2.py

# Start ngrok
ngrok http 8000

# Check server health
curl http://localhost:8000/health

# Run diagnostic
./vapi-diagnostic.ps1

# Setup tools
./vapi-setup-tools.ps1

# View logs
tail -f kebabalab_server.log
```

---

**Follow the Quick Fix steps above and you should be good to go!** 🚀
