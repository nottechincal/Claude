# 🔴 Environment Variable Issues Found

## Critical Issues with Current .env

Your `.env` file has **wrong variable names** that the server doesn't recognize!

### ❌ WRONG Variables (Server Ignores These)

```bash
SESSION_TTL_SECONDS=3600    # ❌ Server looks for SESSION_TTL
MENU_LINK=https://...       # ❌ Server looks for MENU_LINK_URL
LOG_LEVEL=INFO              # ❌ Not used (server hardcodes logging.INFO)
APP_VERSION=2.1.0           # ❌ Not used
SERVER_BASE_URL=...         # ❌ Not used
DB_PATH=...                 # ❌ Server uses hardcoded 'data/orders.db'
MENU_JSON_PATH=...          # ❌ Server uses hardcoded 'data/menu.json'
RULES_JSON_PATH=...         # ❌ Not used
BUSINESS_JSON_PATH=...      # ❌ Not used
HOURS_JSON_PATH=...         # ❌ Not used
SQUARE_*=...                # ❌ Not implemented
ADMIN_TOKEN=...             # ❌ Not used
DISABLE_TWILIO_...=...      # ❌ Not used
```

### ✅ CORRECT Variables (What Server Actually Needs)

```bash
# Core Settings
PORT=8000                                    ✓ Correct
GST_RATE=0.10                               ✓ Correct
SESSION_TTL=1800                            ✓ FIX: Was SESSION_TTL_SECONDS

# Business Details (MISSING - using defaults!)
SHOP_NAME=Kebabalab                         ✗ MISSING
SHOP_ADDRESS=1/99 Carlisle St, St Kilda     ✗ MISSING
SHOP_TIMEZONE=Australia/Melbourne           ✗ MISSING

# Twilio
TWILIO_ACCOUNT_SID=AC2d65f829...            ✓ Correct
TWILIO_AUTH_TOKEN=0d819f3b76...             ✓ Correct
TWILIO_FROM=+61468033229                    ✓ Correct
SHOP_ORDER_TO=+61423680596                  ✓ Correct

# Menu Link
MENU_LINK_URL=https://kebabalab.com.au/menu ✓ FIX: Was MENU_LINK

# Redis (MISSING - using in-memory fallback)
REDIS_HOST=localhost                        ✗ MISSING
REDIS_PORT=6379                            ✗ MISSING
REDIS_DB=0                                 ✗ MISSING

# Session Management
MAX_SESSIONS=1000                          ✗ MISSING
```

## What Happens with Current .env

### Variables That Work:
- ✅ Server runs on PORT 8000
- ✅ GST calculations correct (0.10)
- ✅ Twilio SMS works
- ✅ Shop notifications work

### Variables That Don't Work:
- ❌ Session timeout defaults to 1800s (not your 3600)
- ❌ Menu link defaults to hardcoded URL (not your MENU_LINK)
- ❌ Business details use hardcoded defaults
- ❌ Redis not configured (using in-memory sessions)
- ❌ Max sessions defaults to 1000 (not configurable)

## Impact Assessment

### 🔴 Critical (Fix Now)
1. **MENU_LINK** → Should be **MENU_LINK_URL**
   - Impact: Wrong URL might be sent in SMS
   - Fix: Rename variable

2. **SESSION_TTL_SECONDS** → Should be **SESSION_TTL**
   - Impact: Sessions expire at default 30 min, not your 60 min
   - Fix: Rename variable

### 🟡 Important (Fix Soon)
3. **Missing SHOP_NAME, SHOP_ADDRESS, SHOP_TIMEZONE**
   - Impact: Using hardcoded defaults instead of your .env values
   - Fix: Add these variables

4. **Missing REDIS_* variables**
   - Impact: Using in-memory sessions (not production-ready)
   - Fix: Install Redis and configure

### 🟢 Low Priority (Clean Up)
5. **Unused variables** (LOG_LEVEL, APP_VERSION, etc.)
   - Impact: None (server ignores them)
   - Fix: Remove to avoid confusion

## Quick Fix

Replace your `.env` with the contents of `.env.CORRECTED` file:

```bash
cd "Claude Latest"
cp .env .env.backup        # Backup current
cp .env.CORRECTED .env     # Use corrected version
```

## Verification

After fixing, verify with:

```bash
# Check session timeout
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(f'SESSION_TTL={os.getenv(\"SESSION_TTL\")}')"

# Check menu link
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(f'MENU_LINK_URL={os.getenv(\"MENU_LINK_URL\")}')"

# Check business details
python -c "from kebabalab.server import SHOP_NAME, SHOP_ADDRESS, SHOP_TIMEZONE; print(f'Name: {SHOP_NAME}\\nAddress: {SHOP_ADDRESS}\\nTimezone: {SHOP_TIMEZONE}')"
```

## Files Provided

1. **`.env.CORRECTED`** - Your .env with fixes applied
2. **`.env.example`** - Updated template with correct variable names
3. **This file** - Explanation of issues

## Action Items

- [ ] Review `.env.CORRECTED`
- [ ] Backup current `.env`: `cp .env .env.backup`
- [ ] Replace with corrected version: `cp .env.CORRECTED .env`
- [ ] Verify server picks up new values
- [ ] Consider installing Redis for production
- [ ] Remove unused variables for clarity

---

**TL;DR:** Your .env has wrong variable names. Server is using defaults instead of your values. Use `.env.CORRECTED` to fix.
