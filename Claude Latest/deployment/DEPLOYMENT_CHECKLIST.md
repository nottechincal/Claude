# Production Deployment Checklist

Quick reference checklist for deploying the simplified system.

## Pre-Deployment

- [ ] Backup current database: `cp data/orders.db data/orders.db.backup-$(date +%Y%m%d)`
- [ ] Screenshot current VAPI configuration
- [ ] Note current VAPI tool count: **22 tools**
- [ ] Confirm you have VAPI API key
- [ ] Confirm you have production server URL or ngrok

## Local Testing

- [ ] Run test suite: `python test_chip_upgrade.py`
  - Expected: ALL TESTS PASSED!
- [ ] Start local server: `python server_simplified.py`
- [ ] Test health endpoint: `curl http://localhost:8000/health`
  - Expected: `{"status": "healthy", "tools": 15}`

## Server Setup

- [ ] Install dependencies: `pip install flask flask-cors python-dotenv`
- [ ] Create production config: `cp .env.production.example .env.production`
- [ ] Edit `.env.production` with your values
- [ ] Test startup script: `./start_production.sh`

## Expose Server

Choose one:

### Option A: ngrok (Testing)
- [ ] Run: `ngrok http 8000`
- [ ] Note URL: `https://________.ngrok-free.app`

### Option B: Production Server
- [ ] Deploy to your hosting (AWS, Railway, etc.)
- [ ] Note URL: `https://__________.com`

## VAPI Configuration

- [ ] Get your webhook URL: `https://________/webhook`
- [ ] Upload tools to VAPI:
  ```bash
  python upload_tools_to_vapi.py YOUR_VAPI_KEY YOUR_WEBHOOK_URL
  ```
  - Expected: 15 tools created ✓

- [ ] Go to https://dashboard.vapi.ai
- [ ] Open your assistant
- [ ] Delete all 22 old tools
- [ ] Add all 15 new tools (from upload script)
- [ ] Copy `config/system-prompt-simplified.md`
- [ ] Paste into assistant system prompt
- [ ] Save assistant

## Testing

### Test 1: Simple Order
- [ ] Call VAPI number
- [ ] Order: "Large chicken kebab with garlic sauce"
- [ ] Expected: Item added in ~5 seconds

### Test 2: Meal Conversion
- [ ] Order: "Chicken kebab"
- [ ] Say: "Make it a meal with Coke"
- [ ] Expected: Converted to meal, price announced

### Test 3: CRITICAL - Chip Upgrade
- [ ] Order: "Chicken kebab meal with Coke"
- [ ] Say: "Can you make the chips large?"
- [ ] Expected:
  - [ ] Response within 5 seconds
  - [ ] Price updates to $25
  - [ ] NO long pause
  - [ ] NO multiple "hold on" messages

### Test 4: Complete Order
- [ ] Complete full order flow
- [ ] Confirm order created in database:
  ```bash
  sqlite3 data/orders.db "SELECT * FROM orders ORDER BY created_at DESC LIMIT 1;"
  ```

## Monitoring

- [ ] Watch logs: `tail -f logs/kebabalab_production.log`
- [ ] Check for errors
- [ ] Verify tool call counts (should be 8-12 per order)
- [ ] No editCartItem loops

## Success Criteria

All must pass:

- [x] Test suite passes locally
- [x] Health endpoint returns 200
- [x] 15 tools created in VAPI
- [x] System prompt updated
- [x] Simple order works
- [x] Meal conversion works
- [x] **Chip upgrade works in 1 call (CRITICAL)**
- [x] Order saved to database
- [x] Logs show no errors

## If Something Goes Wrong

### Quick Rollback

1. **Stop new server:**
   ```bash
   pkill -f server_simplified.py
   ```

2. **Start old server:**
   ```bash
   python server_v2.py
   ```

3. **Restore VAPI:**
   - Delete 15 new tools
   - Re-add 22 old tools
   - Restore old system prompt

4. **Restore database (if needed):**
   ```bash
   cp data/orders.db.backup-XXXXXX data/orders.db
   ```

## Post-Deployment

- [ ] Monitor first 10 real orders
- [ ] Check average tool calls per order
- [ ] Verify no customer complaints about wait time
- [ ] Document any issues

## Final Sign-Off

Deployment is complete when:

- [ ] All tests pass
- [ ] Real orders processed successfully
- [ ] No critical errors in logs
- [ ] Team trained on new system
- [ ] Rollback plan documented

---

**Deployment Date:** __________
**Deployed By:** __________
**Server URL:** __________
**Status:** ⬜ In Progress  ⬜ Complete  ⬜ Rolled Back

---

## Quick Reference

**Test Command:**
```bash
python test_chip_upgrade.py
```

**Start Server:**
```bash
./start_production.sh
# or
python server_simplified.py
```

**Upload Tools:**
```bash
python upload_tools_to_vapi.py YOUR_API_KEY YOUR_URL
```

**Check Health:**
```bash
curl http://localhost:8000/health
```

**View Logs:**
```bash
tail -f logs/kebabalab_production.log
```

**Check Database:**
```bash
sqlite3 data/orders.db "SELECT COUNT(*) FROM orders;"
```

---

**Need Help?**
See: DEPLOYMENT_PRODUCTION.md for detailed instructions
