# 📚 Stuffed Lamb Documentation

Complete documentation for the Stuffed Lamb automated ordering system.

---

## 🚀 Getting Started

### **New Users - Start Here:**

1. **[QUICK_START.md](QUICK_START.md)** - Get up and running in 10 minutes
   - Installation steps
   - Basic configuration
   - First run

2. **[STARTUP_GUIDE.md](STARTUP_GUIDE.md)** - All startup options explained
   - Startup scripts comparison
   - ngrok setup and configuration
   - Redis installation
   - Service management

---

## 🔧 Configuration & Setup

3. **[ENV_SETUP_GUIDE.md](ENV_SETUP_GUIDE.md)** - Environment variables explained
   - All environment variables
   - Required vs optional
   - Common mistakes
   - Variable reference

4. **[SETUP_CHECKLIST.md](SETUP_CHECKLIST.md)** - Complete setup checklist
   - Step-by-step setup process
   - Dependencies installation
   - Configuration steps
   - Verification

---

## 🚀 Deployment

5. **[PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md)** - Production deployment guide
   - Linux server (systemd)
   - Docker deployment
   - Windows server
   - Cloud platforms (Heroku, Railway, AWS, DigitalOcean)
   - Nginx reverse proxy
   - SSL/TLS setup
   - Monitoring and maintenance
   - Security best practices

---

## 📊 System Information

6. **[SYSTEM_STATUS_REPORT.md](SYSTEM_STATUS_REPORT.md)** - Complete system overview
   - System architecture
   - Feature list
   - Configuration details
   - Testing information

7. **[ACTION_REQUIRED.md](ACTION_REQUIRED.md)** - Setup action items
   - Required configuration steps
   - Pre-launch checklist

---

## 📖 Additional Resources

- **[../README.md](../README.md)** - Main project README
- **[../config/VAPI_SETUP.md](../config/VAPI_SETUP.md)** - VAPI integration guide

---

## 🎯 Quick Reference

### Starting the System

**Windows:**
```powershell
# Full startup (with ngrok for VAPI)
..\start.bat

# Or directly:
..\scripts\start-with-ngrok.bat
```

**Linux/Mac:**
```bash
# Full startup (with ngrok for VAPI)
../start.sh

# Or directly:
../scripts/start-complete.sh
```

### Common Tasks

- **Verify setup:** `../scripts/verify_setup.sh`
- **Health check:** `python ../scripts/healthcheck.py`
- **Run tests:** `pytest ../tests/ -v`
- **Stop services:** `../scripts/stop.sh` (Linux) or `../scripts/stop.bat` (Windows)

---

## 💡 Navigation Tips

- All scripts are in `../scripts/`
- All configuration data is in `../data/`
- VAPI configuration is in `../config/`
- Docker files are at root: `../Dockerfile`, `../docker-compose.yml`

---

**Need help?** Start with [QUICK_START.md](QUICK_START.md) for the fastest path to getting running!
