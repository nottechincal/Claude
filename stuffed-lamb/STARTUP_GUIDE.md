# 🚀 Stuffed Lamb Startup Scripts Guide

This guide explains the different startup scripts and what each one does.

---

## 📋 Available Startup Scripts

### **Windows**

| Script | What It Starts | When to Use |
|--------|---------------|-------------|
| `start.bat` | Just the application | Development without VAPI |
| `start-with-ngrok.bat` | Application + ngrok + Redis (optional) | **VAPI integration & testing** |
| `stop.bat` | Stops all services | Cleanup |

### **Linux/Mac**

| Script | What It Starts | When to Use |
|--------|---------------|-------------|
| `start.sh` | Just the application | Development without VAPI |
| `start-complete.sh` | Application + ngrok + Redis (optional) | **VAPI integration & testing** |
| `stop.sh` | Stops all services | Cleanup |

---

## 🎯 Which Script Should You Use?

### **For VAPI Integration (Recommended):**

**Windows:**
```powershell
.\start-with-ngrok.bat
```

**Linux/Mac:**
```bash
./start-complete.sh
```

**What it does:**
1. ✅ Checks .env configuration
2. ✅ Installs Python dependencies
3. ✅ Starts Redis (if available, optional)
4. ✅ Starts the application server on port 8000
5. ✅ Starts ngrok tunnel to expose webhook
6. ✅ Shows you the public URL for VAPI

### **For Simple Testing (No VAPI):**

**Windows:**
```powershell
.\start.bat
```

**Linux/Mac:**
```bash
./start.sh
```

**What it does:**
1. ✅ Checks .env configuration
2. ✅ Installs Python dependencies
3. ✅ Starts the application server on port 8000
4. ❌ Does NOT start ngrok
5. ❌ Does NOT start Redis

---

## 🔧 What Each Service Does

### **1. Application Server (Required)**
- **Port:** 8000
- **Purpose:** The main Stuffed Lamb ordering system
- **Access:** http://localhost:8000
- **Health Check:** http://localhost:8000/health

### **2. ngrok (Required for VAPI)**
- **Port:** Forwards to 8000
- **Purpose:** Creates a public URL so VAPI can reach your webhook
- **Dashboard:** http://localhost:4040
- **Public URL:** https://xxxx-xx-xxx.ngrok-free.app (changes each time)

**Why you need it:**
- VAPI needs to send HTTP requests to your `/vapi/webhook` endpoint
- Your local server is not accessible from the internet
- ngrok creates a tunnel: Internet → ngrok → localhost:8000

### **3. Redis (Optional but Recommended)**
- **Port:** 6379
- **Purpose:** Session storage for user conversations
- **Fallback:** If not available, uses in-memory storage
- **Production:** Should always use Redis

---

## 📦 Required Software

### **For Basic Development:**
- ✅ Python 3.8+
- ✅ pip

### **For VAPI Integration:**
- ✅ Python 3.8+
- ✅ pip
- ✅ **ngrok** - [Download here](https://ngrok.com/download)
- ⭐ Redis (optional) - [Windows](https://github.com/microsoftarchive/redis/releases) | [Mac](https://formulae.brew.sh/formula/redis)

---

## 🛠️ Installation Guide

### **1. Install ngrok (Required for VAPI)**

**Windows:**
1. Download from https://ngrok.com/download
2. Extract `ngrok.exe` to a folder
3. Add to PATH or place in project folder
4. Run `ngrok authtoken YOUR_AUTH_TOKEN` (get token from ngrok.com)

**Mac:**
```bash
brew install ngrok/ngrok/ngrok
ngrok authtoken YOUR_AUTH_TOKEN
```

**Linux:**
```bash
# Download and install
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | \
  sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null && \
  echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | \
  sudo tee /etc/apt/sources.list.d/ngrok.list && \
  sudo apt update && sudo apt install ngrok

# Authenticate
ngrok authtoken YOUR_AUTH_TOKEN
```

### **2. Install Redis (Optional but Recommended)**

**Windows:**
- Download from: https://github.com/microsoftarchive/redis/releases
- Or use Docker: `docker run -d -p 6379:6379 redis:alpine`

**Mac:**
```bash
brew install redis
brew services start redis
```

**Linux:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis
```

---

## 🚀 Complete Startup Process

### **Step 1: First Time Setup**

```powershell
# Windows
cd stuffed-lamb
pip install -r requirements.txt
copy .env.example .env
notepad .env  # Add your credentials
```

```bash
# Linux/Mac
cd stuffed-lamb
pip install -r requirements.txt
cp .env.example .env
nano .env  # Add your credentials
```

### **Step 2: Start Everything**

**Windows:**
```powershell
.\start-with-ngrok.bat
```

**Linux/Mac:**
```bash
./start-complete.sh
```

### **Step 3: Get Your Public URL**

After starting, you'll see output like:
```
============================================
SUCCESS! All services started
============================================

Application:  http://localhost:8000
Health Check: http://localhost:8000/health

NGROK TUNNEL:
Public URL:   https://a1b2-c3d4.ngrok-free.app
VAPI Webhook: https://a1b2-c3d4.ngrok-free.app/vapi/webhook

Ngrok Dashboard: http://localhost:4040
```

### **Step 4: Configure VAPI**

1. Copy the VAPI Webhook URL: `https://YOUR-NGROK-URL/vapi/webhook`
2. Go to VAPI dashboard
3. Update your assistant's webhook URL
4. Test by making a call!

---

## 🛑 Stopping Services

**Windows:**
```powershell
.\stop.bat
```

**Linux/Mac:**
```bash
./stop.sh
```

This stops:
- Application server
- ngrok tunnel
- Redis (optional)

---

## 🐛 Troubleshooting

### **"ngrok not found"**
- Install ngrok from https://ngrok.com/download
- Add to PATH or run from ngrok folder
- Authenticate with `ngrok authtoken YOUR_TOKEN`

### **"Redis connection failed"**
- This is OK! System will use in-memory sessions
- For production, install Redis (see above)

### **"Port 8000 already in use"**
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill
```

### **ngrok URL changes every time**
- Free ngrok gives you a random URL each time
- Upgrade to ngrok paid plan for static domains
- Or deploy to production for permanent URL

### **VAPI webhook not working**
1. Check server is running: `curl http://localhost:8000/health`
2. Check ngrok is running: Open http://localhost:4040
3. Verify webhook URL in VAPI matches ngrok URL
4. Check logs in ngrok dashboard for incoming requests

---

## 📊 Service Logs

### **Application Logs**

**Windows:**
- Check the "Stuffed Lamb Server" window

**Linux/Mac:**
```bash
tail -f /tmp/stuffed-lamb.log
```

### **ngrok Logs**

**Windows:**
- Check the "Stuffed Lamb ngrok" window

**Linux/Mac:**
```bash
tail -f /tmp/stuffed-lamb-ngrok.log
```

**Or use ngrok dashboard:**
- http://localhost:4040

---

## 🎯 Quick Reference

### **Start with VAPI support:**
```bash
# Windows
.\start-with-ngrok.bat

# Linux/Mac
./start-complete.sh
```

### **Start simple (no VAPI):**
```bash
# Windows
.\start.bat

# Linux/Mac
./start.sh
```

### **Stop everything:**
```bash
# Windows
.\stop.bat

# Linux/Mac
./stop.sh
```

### **Check status:**
```bash
# Health check
curl http://localhost:8000/health

# ngrok dashboard
# Open: http://localhost:4040
```

---

## 🚀 Production Deployment

For production, you don't need ngrok! Deploy to:
- Docker (see docker-compose.yml)
- Cloud platforms (Heroku, Railway, AWS)
- Linux server with systemd

See **[PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md)** for complete guide.

---

## 💡 Tips

1. **Keep ngrok running** - Don't close the window while testing
2. **Save your ngrok URL** - It changes each time you restart
3. **Use ngrok dashboard** - http://localhost:4040 shows all requests
4. **Test locally first** - Use http://localhost:8000 before connecting VAPI
5. **Check health endpoint** - http://localhost:8000/health should return `{"status": "healthy"}`

---

**Need help?** Check logs, verify .env file, or see PRODUCTION_DEPLOYMENT.md!
