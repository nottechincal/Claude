# Stuffed Lamb - Environment Setup Guide

## Quick Start

```bash
cd stuffed-lamb

# 1. Copy the example file
cp .env.example .env

# 2. Edit with your values
nano .env  # or use your preferred editor

# 3. Update these critical values:
#    - TWILIO_ACCOUNT_SID
#    - TWILIO_AUTH_TOKEN
#    - TWILIO_FROM
#    - SHOP_ORDER_TO
```

## Required Environment Variables

### ✅ Core Variables (Must Set)

```bash
# Server
PORT=8000                                # Port to run server on
HOST=0.0.0.0                            # Host binding (0.0.0.0 = all interfaces)

# Business
SHOP_NAME=Stuffed Lamb
SHOP_ADDRESS=210 Broadway, Reservoir VIC 3073
SHOP_TIMEZONE=Australia/Melbourne

# Tax
GST_RATE=0.10                           # 10% Australian GST

# Sessions
SESSION_TTL=1800                        # Session timeout in SECONDS (30 min)
MAX_SESSIONS=1000                       # Max concurrent sessions

# Menu Link
MENU_LINK_URL=https://stuffed-lamb.tuckerfox.com.au/
```

### 📱 Twilio Variables (Required for SMS)

```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxx    # From Twilio Console
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxx     # From Twilio Console
TWILIO_FROM=+61XXXXXXXXX                # Your Twilio phone number
SHOP_ORDER_TO=+61XXXXXXXXX              # Shop's phone for notifications
```

**How to get Twilio credentials:**
1. Go to https://console.twilio.com/
2. Sign up / Log in
3. Get Account SID and Auth Token from dashboard
4. Purchase a phone number (or use trial number for testing)

### 🗄️ Redis Variables (Optional but Recommended)

```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=                         # Leave empty if no password
```

**Why Redis?**
- Production-ready session storage
- Survives server restarts
- Better for multiple server instances
- Without Redis, uses in-memory storage (sessions lost on restart)

**Install Redis:**
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# Start Redis
redis-server
```

### 🌐 CORS Variables (Optional)

```bash
ALLOWED_ORIGINS=*                       # Use * for development

# Production (restrict to VAPI):
# ALLOWED_ORIGINS=https://api.vapi.ai,https://vapi.ai
```

## Common Variables That DON'T Exist

These are from Kebabalab and **don't apply** to Stuffed Lamb:

```bash
❌ SESSION_TTL_SECONDS     # Use SESSION_TTL instead!
❌ TWILIO_FROM_NUMBER      # Use TWILIO_FROM instead!
❌ MENU_LINK               # Use MENU_LINK_URL instead!
❌ LOG_LEVEL               # Not used (hardcoded in server)
❌ DB_PATH                 # Hardcoded to data/orders.db
❌ MENU_JSON_PATH          # Hardcoded to data/menu.json
```

## Variable Name Reference

| Correct Variable | ❌ Common Mistake | Server Reads |
|-----------------|-------------------|--------------|
| SESSION_TTL | SESSION_TTL_SECONDS | ✅ SESSION_TTL |
| TWILIO_FROM | TWILIO_FROM_NUMBER | ✅ TWILIO_FROM |
| MENU_LINK_URL | MENU_LINK | ✅ MENU_LINK_URL |
| SHOP_ORDER_TO | SHOP_NOTIFICATION_NUMBER | ✅ SHOP_ORDER_TO |

## Environment-Specific Configs

### Development (.env.development)

```bash
PORT=8000
DEBUG=true
ALLOWED_ORIGINS=*
# Use Twilio test credentials
# Use in-memory sessions (no Redis needed)
```

### Production (.env.production)

```bash
PORT=8000
DEBUG=false
ALLOWED_ORIGINS=https://api.vapi.ai,https://vapi.ai
# Use real Twilio credentials
# Use Redis for sessions
REDIS_HOST=localhost
REDIS_PORT=6379
```

## Testing Your Configuration

### 1. Verify Variables Load

```bash
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

print('PORT:', os.getenv('PORT'))
print('SHOP_NAME:', os.getenv('SHOP_NAME'))
print('SESSION_TTL:', os.getenv('SESSION_TTL'))
print('MENU_LINK_URL:', os.getenv('MENU_LINK_URL'))
print('TWILIO_FROM:', os.getenv('TWILIO_FROM'))
"
```

### 2. Test Server Startup

```bash
python -m stuffed_lamb.server
```

Expected output:
```
WARNING: Redis connection failed ... falling back to in-memory sessions
INFO - Menu loaded: 3 categories, 6 items from .../data/menu.json
INFO - Database initialized with performance indexes
INFO - Starting server on port 8000
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:8000
```

### 3. Test Twilio Connection

```bash
python3 -c "
from stuffed_lamb.server import get_twilio_client
client, from_number = get_twilio_client()
print('Twilio Client:', 'Connected' if client else 'Not configured')
print('From Number:', from_number)
"
```

### 4. Test Menu Loading

```bash
python3 -c "
from stuffed_lamb.server import load_menu, MENU
load_menu()
print('Menu Categories:', list(MENU.get('categories', {}).keys()))
print('Total Items:', sum(len(items) for items in MENU['categories'].values()))
"
```

## Troubleshooting

### Issue: "Server doesn't read my .env"

**Solution:**
```bash
# Install python-dotenv if not installed
pip install python-dotenv

# Make sure .env is in the same directory as server.py
ls -la .env

# Check for syntax errors in .env (no spaces around =)
# WRONG: PORT = 8000
# RIGHT: PORT=8000
```

### Issue: "Session timeout not working"

**Check:**
- Variable is `SESSION_TTL` not `SESSION_TTL_SECONDS`
- Value is in seconds (1800 = 30 minutes, 3600 = 1 hour)

### Issue: "Menu link wrong in SMS"

**Check:**
- Variable is `MENU_LINK_URL` not `MENU_LINK`
- URL includes https:// and trailing slash

### Issue: "Redis connection failed"

**This is OK for development!**
- Server falls back to in-memory sessions
- For production, install Redis:
  ```bash
  sudo apt-get install redis-server
  sudo systemctl start redis
  ```

### Issue: "Twilio SMS not sending"

**Check:**
1. TWILIO_ACCOUNT_SID is correct (starts with AC)
2. TWILIO_AUTH_TOKEN is correct
3. TWILIO_FROM is in E.164 format (+61...)
4. SHOP_ORDER_TO is in E.164 format (+61...)
5. Twilio account has funds/credits

## Security Best Practices

1. ✅ **Never commit .env to git**
   ```bash
   # Add to .gitignore
   echo ".env" >> .gitignore
   ```

2. ✅ **Use different credentials for dev/prod**
   - Development: Use Twilio test credentials
   - Production: Use real credentials

3. ✅ **Rotate credentials regularly**
   - Change Twilio auth token every 90 days
   - Update Redis password quarterly

4. ✅ **Restrict CORS in production**
   ```bash
   ALLOWED_ORIGINS=https://api.vapi.ai,https://vapi.ai
   ```

5. ✅ **Use environment-specific .env files**
   - .env.development
   - .env.production
   - .env.staging

## Files Provided

1. **`.env.example`** - Template with all variables
2. **`.env.CORRECTED`** - Ready-to-use template (update credentials)
3. **`ENV_SETUP_GUIDE.md`** - This file

## Quick Reference

```bash
# Copy template
cp .env.example .env

# Edit variables
nano .env

# Test configuration
python -m stuffed_lamb.server

# Run tests
pytest tests/

# Production deployment
gunicorn -w 4 -b 0.0.0.0:8000 stuffed_lamb.server:app
```

---

**Remember:** Update TWILIO_* credentials and phone numbers before going live!
