# ⚡ Stuffed Lamb - Quick Start Guide

**Get up and running in under 10 minutes!**

---

## 🎯 **What You Need to Populate**

### **1. Twilio Credentials** (Required for SMS)

**Get from:** https://console.twilio.com/ (free trial available)

**Add to `.env` file:**
```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_FROM=+61412345678        # Your Twilio phone number
SHOP_ORDER_TO=+61398765432      # Shop phone for notifications
```

### **2. Shop Phone Number** (Optional but recommended)

**File:** `data/business.json` (line 5)

**Change:**
```json
"phone": "+61 3 XXXX XXXX",  ← Update this
```

**To:**
```json
"phone": "+61394621234",     ← Your actual number
```

---

## 🚀 **Installation (3 Steps)**

### **Step 1: Install Dependencies**
```bash
cd /home/user/Claude/stuffed-lamb
pip install -r requirements.txt
```

### **Step 2: Configure Environment**
```bash
# Copy template
cp .env.example .env

# Edit with your Twilio credentials
nano .env  # or vim, or any editor
```

### **Step 3: Run the Server**

**Option 1: Use Startup Scripts (Recommended)**

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
./start.sh
```

**Option 2: Direct Run**
```bash
python run.py
```

**Done!** Server is now running on http://localhost:8000

💡 **Tip:** The startup scripts automatically check dependencies and .env configuration!

---

## ✅ **Verify Everything Works**

### **Setup Verification (Recommended):**
```bash
./verify_setup.sh        # Linux/Mac
```
**Checks:** Python version, .env file, dependencies, data files, Redis, port availability

### **Health Check:**
```bash
python healthcheck.py --url http://localhost:8000 --full
```
**Verifies:** Server is running and endpoints are accessible

### **Run Tests:**
```bash
pytest tests/test_stuffed_lamb_system.py -v
```
**Expected:** 28/28 tests passing ✅

### **Test API Call:**
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

**Expected:** JSON response with shop status

---

## 📋 **What's Already Configured** ✅

You don't need to change these - they're ready to go:

- ✅ **Menu:** 3 main dishes, drinks, extras (all priced)
- ✅ **Hours:** Mon-Tue closed, Wed-Fri 1pm-9pm, Sat-Sun 1pm-10pm
- ✅ **Business:** Name, address, timezone
- ✅ **VAPI:** 18 tools configured
- ✅ **Tests:** 28 comprehensive tests
- ✅ **Database:** Auto-creates on first run

---

## 🎯 **What Happens When You Run It**

1. **Server starts** on port 8000 (or your custom port)
2. **Menu loads** from `data/menu.json`
3. **Database initializes** (SQLite in `data/orders.db`)
4. **18 tools register** for VAPI integration
5. **Session manager starts** (Redis or in-memory fallback)
6. **Ready to accept orders!** 🎉

---

## 🔌 **Connect to VAPI (Optional)**

See `config/VAPI_SETUP.md` for full instructions.

**Quick version:**
1. Go to VAPI dashboard
2. Create new assistant
3. Copy `config/system-prompt.md` → System Prompt
4. Import `config/vapi-tools.json` → Custom Tools
5. Set webhook: `https://your-domain.com/vapi/webhook`

---

## 🐛 **Common Issues**

### **"Redis connection failed"**
- **This is normal!** System falls back to in-memory sessions
- For production, install Redis: `sudo apt-get install redis-server`

### **"Module not found"**
- Run: `pip install -r requirements.txt`

### **Tests failing**
- Check you're in the right directory: `cd /home/user/Claude/stuffed-lamb`
- Verify Python 3.8+: `python --version`

### **Port already in use**
- Use custom port: `python run.py --port 5000`

---

## 🚀 **Production Deployment**

### **Quick Deploy with Docker:**
```bash
# Create .env file first, then:
docker-compose up -d
```

### **For Full Production Deployment:**
See **[PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md)** for:
- Linux server deployment (systemd)
- Docker deployment
- Windows server setup
- Cloud platforms (Heroku, Railway, AWS, etc.)
- Monitoring and maintenance
- Security best practices

---

## 📚 **Full Documentation**

| File | What's Inside |
|------|---------------|
| **PRODUCTION_DEPLOYMENT.md** | 🚀 Production deployment guide |
| **SETUP_CHECKLIST.md** | Complete step-by-step setup |
| **SYSTEM_STATUS_REPORT.md** | Full system status and configuration |
| **ENV_SETUP_GUIDE.md** | Environment variables explained |
| **README.md** | General system overview |
| **config/VAPI_SETUP.md** | VAPI integration guide |

---

## 🎉 **You're Done!**

Once you:
1. ✅ Install dependencies (`pip install -r requirements.txt`)
2. ✅ Configure `.env` with Twilio credentials
3. ✅ Run `python run.py`

**Your system is LIVE and ready to take orders!**

**Test it:** Run `pytest tests/ -v` to verify everything works.

---

**Need help?** Check `SYSTEM_STATUS_REPORT.md` for complete system overview!
