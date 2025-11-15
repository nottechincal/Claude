# 🚀 Stuffed Lamb System - Complete Setup Checklist

This checklist tells you **EXACTLY** what you need to configure before running the system.

---

## ✅ **STEP 1: Install Dependencies**

```bash
cd /home/user/Claude/stuffed-lamb

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

**Required packages:**
- ✅ flask (web framework)
- ✅ flask-cors (CORS support)
- ✅ pytz (timezone support)
- ✅ rapidfuzz (fuzzy matching for voice orders)
- ✅ redis (session storage - optional but recommended)
- ✅ twilio (SMS notifications)
- ✅ pytest (testing)

---

## ✅ **STEP 2: Configure Environment Variables (.env)**

### **Action Required: Create and populate .env file**

```bash
# Copy the template
cp .env.example .env

# Edit with your actual values
nano .env  # or vim .env, or use any text editor
```

### **YOU MUST POPULATE THESE VALUES:**

#### **1. Twilio Credentials (REQUIRED for SMS notifications)**

Get these from https://console.twilio.com/

```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_actual_auth_token_here
```

#### **2. Phone Numbers (REQUIRED - E.164 format)**

```bash
# Your Twilio phone number (the one you purchased from Twilio)
TWILIO_FROM=+61412345678

# Shop's phone number (where order notifications are sent)
SHOP_ORDER_TO=+61398765432
```

**Important:**
- Phone numbers MUST start with `+61` (Australia)
- No spaces or dashes: `+61412345678` ✅ NOT `+61 412 345 678` ❌
- Must be valid E.164 format

#### **3. Optional but Recommended**

```bash
# Port (default is 8000)
PORT=8000

# Redis (for production - install Redis first)
REDIS_HOST=localhost
REDIS_PORT=6379
# REDIS_PASSWORD=your_password_if_needed
```

### **What's Already Configured (NO ACTION NEEDED):**

✅ SHOP_NAME=Stuffed Lamb
✅ SHOP_ADDRESS=210 Broadway, Reservoir VIC 3073
✅ SHOP_TIMEZONE=Australia/Melbourne
✅ GST_RATE=0.10
✅ SESSION_TTL=1800 (30 minutes)
✅ MENU_LINK_URL=https://stuffed-lamb.tuckerfox.com.au/

---

## ✅ **STEP 3: Verify Data Files (Pre-configured)**

These files are **already configured** - you can review them but don't need to change them:

### **data/menu.json** ✅ Complete
- 3 main dishes (Mansaf $33, Lamb Mandi $28, Chicken Mandi $23)
- Soup of the Day ($7)
- Drinks (Soft Drinks $3, Water $2)
- All extras and modifiers configured
- Synonyms for voice recognition

### **data/hours.json** ✅ Complete
- Monday: CLOSED
- Tuesday: CLOSED
- Wed-Fri: 1pm-9pm
- Sat-Sun: 1pm-10pm

### **data/business.json** ⚠️ Needs Phone Update
- Business name: Stuffed Lamb
- Address: 210 Broadway, Reservoir VIC 3073
- **Phone number has placeholder** - You should update line 5:

```json
"phone": "+61 3 9462 XXXX",  ← CHANGE THIS to actual phone
```

Edit `data/business.json` and replace the phone number.

### **data/rules.json** ✅ Complete
- No combos (unlike Kebabalab)
- 10% dine-in service charge
- Allergen information
- Escalation keywords

---

## ✅ **STEP 4: VAPI Configuration (For Voice AI)**

If you're using VAPI for voice ordering:

### **Files Already Configured:**

✅ `config/system-prompt.md` - Voice AI instructions
✅ `config/vapi-tools.json` - All 18 tool definitions
✅ `config/VAPI_SETUP.md` - Complete setup guide

### **Action Required:**

1. Go to your VAPI dashboard
2. Create a new assistant
3. Copy content from `config/system-prompt.md` → VAPI system prompt
4. Import `config/vapi-tools.json` → VAPI custom tools
5. Set webhook URL to: `https://your-domain.com/vapi/webhook`

See `config/VAPI_SETUP.md` for detailed instructions.

---

## ✅ **STEP 5: Test the System**

### **Run Tests First (No .env needed)**

```bash
pytest tests/test_stuffed_lamb_system.py -v
```

**Expected result:** ✅ 28/28 tests passing

If tests fail, check:
- Menu data is valid (`data/menu.json`)
- Python packages installed correctly

### **Start the Server**

```bash
# Simple way (recommended)
python run.py

# Or direct module run
python -m stuffed_lamb.server

# Or with custom port
python run.py --port 5000
```

**Expected output:**
```
==================================================
Kebabalab VAPI Server - SIMPLIFIED
==================================================
Database initialized with performance indexes
Menu loaded: 3 categories, 6 items from /home/user/Claude/stuffed-lamb/data/menu.json
Loaded 18 tools:
  1. checkOpen
  2. getCallerSmartContext
  ... (18 tools total)
Starting server on port 8000
```

### **Test a Webhook Call**

```bash
curl -X POST http://localhost:8000/vapi/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "type": "tool-calls",
      "toolCalls": [{
        "id": "test123",
        "type": "function",
        "function": {
          "name": "checkOpen",
          "arguments": "{\"phone\":\"+61412345678\"}"
        }
      }]
    }
  }'
```

**Expected:** JSON response with shop hours/status

---

## 📋 **FINAL CHECKLIST - What You MUST Do**

Before running the system, ensure:

- [ ] **Dependencies installed** (`pip install -r requirements.txt`)
- [ ] **.env file created** (`cp .env.example .env`)
- [ ] **TWILIO_ACCOUNT_SID configured** (from Twilio console)
- [ ] **TWILIO_AUTH_TOKEN configured** (from Twilio console)
- [ ] **TWILIO_FROM set** (your Twilio phone number in +61... format)
- [ ] **SHOP_ORDER_TO set** (shop phone number in +61... format)
- [ ] **Phone in data/business.json updated** (remove XXX placeholder)
- [ ] **Tests pass** (`pytest tests/ -v`)
- [ ] **Server starts** (`python run.py`)

---

## 🔧 **Optional Production Setup**

For production deployment:

### **1. Install Redis (Recommended)**

```bash
# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis
sudo systemctl enable redis

# Verify
redis-cli ping  # Should return "PONG"
```

Then uncomment Redis settings in `.env` if needed.

### **2. Use Production WSGI Server**

```bash
# Install gunicorn
pip install gunicorn

# Run with 4 workers
gunicorn -w 4 -b 0.0.0.0:8000 stuffed_lamb.server:app
```

### **3. Enable HTTPS**

Use nginx or similar reverse proxy with SSL certificate.

---

## 🐛 **Troubleshooting**

### **"Redis connection failed"**
- **Normal if Redis not installed** - system falls back to in-memory sessions
- For production, install Redis (see above)

### **"TWILIO_* not set" errors**
- Check `.env` file exists
- Check variable names are correct (not TWILIO_FROM_NUMBER, use TWILIO_FROM)
- Check no extra spaces around values

### **Tests failing**
```bash
# Make sure you're in the right directory
cd /home/user/Claude/stuffed-lamb

# Check Python can find the module
python -c "from stuffed_lamb.server import load_menu; load_menu()"

# Run tests with verbose output
pytest tests/ -v -s
```

### **Server won't start**
```bash
# Check port is available
lsof -i :8000

# Try different port
python run.py --port 5000

# Check logs
cat logs/stuffed_lamb.log
```

---

## 📞 **Support Files**

- **README.md** - General system overview
- **ENV_SETUP_GUIDE.md** - Detailed environment variable guide
- **config/VAPI_SETUP.md** - VAPI integration guide
- **logs/stuffed_lamb.log** - Server logs (created when server runs)

---

## ✨ **Once Everything is Configured**

Your system will:
- ✅ Accept voice/webhook orders via VAPI
- ✅ Process menu items with fuzzy matching (handles typos)
- ✅ Calculate prices with GST included
- ✅ Send SMS receipts via Twilio
- ✅ Store orders in SQLite database
- ✅ Respect operating hours (closed Mon-Tue)
- ✅ Handle all 18 VAPI tools correctly

**You'll be ready to take orders!** 🎉

---

**Need help?** Check the logs at `logs/stuffed_lamb.log` or run tests with `pytest tests/ -v`
