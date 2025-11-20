# 🚀 Stuffed Lamb - Production Deployment Guide

This guide covers deploying Stuffed Lamb to production using various methods.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Deployment Options](#deployment-options)
3. [Linux Server (Systemd)](#linux-server-systemd)
4. [Docker Deployment](#docker-deployment)
5. [Windows Server](#windows-server)
6. [Cloud Platforms](#cloud-platforms)
7. [Post-Deployment](#post-deployment)
8. [Monitoring & Maintenance](#monitoring--maintenance)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### ✅ Before You Deploy

- [ ] Python 3.8 or higher
- [ ] Valid Twilio account with credentials
- [ ] Twilio phone number configured
- [ ] Shop phone number for notifications
- [ ] Domain name (optional but recommended)
- [ ] SSL certificate (for HTTPS)
- [ ] Redis installed (recommended for production)

### 🔒 Security Checklist

- [ ] `.env` file is NOT committed to git
- [ ] Firewall configured (allow ports 80, 443, 8000)
- [ ] SSH key authentication enabled (disable password auth)
- [ ] Regular security updates scheduled
- [ ] Backups configured

---

## Deployment Options

### 1. **Linux Server with Systemd** (Recommended for VPS/Dedicated Servers)
- Best for: VPS, dedicated servers, cloud VMs
- Pros: Full control, efficient, auto-restart
- Cons: Requires server management

### 2. **Docker** (Recommended for Containers)
- Best for: Container platforms, easy scaling
- Pros: Portable, isolated, easy updates
- Cons: Slight overhead

### 3. **Windows Server**
- Best for: Windows environments
- Pros: Native Windows support
- Cons: Less common for production

### 4. **Cloud Platforms** (PaaS)
- Best for: Managed hosting
- Pros: Minimal management, auto-scaling
- Cons: Can be expensive

---

## Linux Server (Systemd)

### Step 1: Prepare the Server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip python3-venv redis-server nginx

# Create application user
sudo useradd -m -s /bin/bash stuffedlamb

# Create application directory
sudo mkdir -p /opt/stuffed-lamb
sudo chown stuffedlamb:stuffedlamb /opt/stuffed-lamb
```

### Step 2: Deploy Application

```bash
# Switch to application user
sudo su - stuffedlamb

# Clone or copy application
cd /opt/stuffed-lamb
# (Upload your files here via git, scp, rsync, etc.)

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
nano .env  # Edit with your credentials
```

### Step 3: Configure Systemd Service

```bash
# Exit application user
exit

# Copy service file
sudo cp /opt/stuffed-lamb/deployment/stuffed-lamb.service /etc/systemd/system/

# Edit service file if needed
sudo nano /etc/systemd/system/stuffed-lamb.service

# Reload systemd
sudo systemctl daemon-reload

# Enable and start service
sudo systemctl enable stuffed-lamb
sudo systemctl start stuffed-lamb

# Check status
sudo systemctl status stuffed-lamb
```

### Step 4: Configure Nginx Reverse Proxy

```bash
# Create Nginx config
sudo nano /etc/nginx/sites-available/stuffed-lamb
```

Add this configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/stuffed-lamb /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Step 5: Setup SSL with Let's Encrypt

```bash
# Install certbot
sudo apt install -y certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is configured automatically
```

---

## Docker Deployment

### Step 1: Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install -y docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
```

### Step 2: Prepare Environment

```bash
# Create .env file
cp .env.example .env
nano .env  # Edit with your credentials
```

### Step 3: Build and Run

```bash
# Build and start containers
docker-compose up -d

# Check logs
docker-compose logs -f stuffed-lamb

# Check status
docker-compose ps
```

### Step 4: Verify Deployment

```bash
# Health check
curl http://localhost:8000/health

# Should return: {"status": "healthy"}
```

### Docker Commands

```bash
# Stop containers
docker-compose down

# Restart
docker-compose restart

# View logs
docker-compose logs -f

# Update application
docker-compose down
git pull  # or update files
docker-compose up -d --build

# Backup data
docker-compose exec stuffed-lamb tar czf /tmp/backup.tar.gz /app/data
docker cp stuffed-lamb:/tmp/backup.tar.gz ./backup-$(date +%Y%m%d).tar.gz
```

---

## Windows Server

### Step 1: Install Dependencies

1. Install Python 3.8+ from https://python.org
2. Install Redis for Windows (optional)
3. Install Git (optional)

### Step 2: Setup Application

```powershell
# Navigate to application directory
cd C:\stuffed-lamb

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
copy .env.example .env
notepad .env  # Edit with your credentials
```

### Step 3: Run as Windows Service

Use **NSSM** (Non-Sucking Service Manager):

```powershell
# Download NSSM from https://nssm.cc/download

# Install service
nssm install StuffedLamb "C:\stuffed-lamb\venv\Scripts\python.exe" "C:\stuffed-lamb\run.py"
nssm set StuffedLamb AppDirectory "C:\stuffed-lamb"
nssm set StuffedLamb DisplayName "Stuffed Lamb VAPI System"
nssm set StuffedLamb Description "Automated ordering system for Stuffed Lamb"
nssm set StuffedLamb Start SERVICE_AUTO_START

# Start service
nssm start StuffedLamb

# Check status
nssm status StuffedLamb
```

Or use Task Scheduler to run `start.bat` at system startup.

---

## Cloud Platforms

### Heroku

```bash
# Install Heroku CLI
# Create Procfile
echo "web: python run.py" > Procfile

# Create heroku app
heroku create stuffed-lamb

# Set environment variables
heroku config:set $(cat .env | xargs)

# Deploy
git push heroku main
```

### Railway.app

1. Connect GitHub repository
2. Add environment variables from `.env`
3. Deploy automatically on push

### DigitalOcean App Platform

1. Connect GitHub repository
2. Add environment variables
3. Configure:
   - Build Command: `pip install -r requirements.txt`
   - Run Command: `python run.py`
   - Port: 8000

### AWS EC2

Same as **Linux Server (Systemd)** above.

---

## Post-Deployment

### 1. Verify System

```bash
# Run verification script
./verify_setup.sh

# Health check
python healthcheck.py --url http://your-domain.com --full

# Test SMS notifications
curl -X POST http://your-domain.com/vapi/webhook \
  -H "Content-Type: application/json" \
  -d @tests/sample_order.json
```

### 2. Test VAPI Integration

1. Login to VAPI dashboard
2. Update webhook URL: `https://your-domain.com/vapi/webhook`
3. Make a test call
4. Verify order appears in database

### 3. Setup Monitoring

**Basic monitoring:**

```bash
# Create monitoring script
cat > /opt/stuffed-lamb/monitor.sh << 'EOF'
#!/bin/bash
if ! curl -sf http://localhost:8000/health > /dev/null; then
    echo "Stuffed Lamb is DOWN!" | mail -s "ALERT: Service Down" admin@example.com
    systemctl restart stuffed-lamb
fi
EOF

# Add to crontab
chmod +x /opt/stuffed-lamb/monitor.sh
crontab -e
# Add: */5 * * * * /opt/stuffed-lamb/monitor.sh
```

**Production monitoring tools:**
- Uptime monitoring: UptimeRobot, Pingdom
- Application monitoring: New Relic, Datadog
- Log aggregation: Papertrail, Loggly

---

## Monitoring & Maintenance

### Log Locations

- **Systemd**: `journalctl -u stuffed-lamb -f`
- **Docker**: `docker-compose logs -f stuffed-lamb`
- **Application**: `logs/stuffed_lamb.log` (JSON structured logs)
- Logs are emitted in JSON, so forward them to your log aggregation stack (Datadog, ELK, etc.) for searching on `tool`, `correlation_id`, or `session_id` fields.

### Metrics & Telemetry

- The server exposes Prometheus-compatible counters at `GET /metrics`.
- Scrape endpoint example (Prometheus):

```yaml
scrape_configs:
  - job_name: stuffed-lamb
    metrics_path: /metrics
    static_configs:
      - targets: ['localhost:8000']
```

- Key metrics:
  - `quick_add_requests_total`, `quick_add_success_total`, `quick_add_failure_total`
  - `menu_miss_total` – watch for spikes caused by new accents or menu items
  - `sms_success_total`, `sms_failure_total`, `notification_queue_retries_total`
  - `webhook_auth_failures_total` – indicates unauthorized traffic hitting `/webhook`
- Alert if failures increase or if metrics endpoint becomes unavailable.

### Accent & Pronunciation Dictionary

- Accent variants live in `data/pronunciations.json`.
- When the menu changes or new modifiers are introduced, add phonetic spellings under the appropriate `items` or `modifiers` entry.
- After editing `pronunciations.json`, restart the service so `build_menu_indexes()` reloads the new variants.
- Keep this file under version control so the NLP pipeline evolves with your callers.

### Database Backups

```bash
# Create backup script
cat > /opt/stuffed-lamb/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR=/opt/stuffed-lamb/backups
mkdir -p $BACKUP_DIR
DATE=$(date +%Y%m%d_%H%M%S)
cp /opt/stuffed-lamb/data/orders.db $BACKUP_DIR/orders_$DATE.db
find $BACKUP_DIR -name "orders_*.db" -mtime +30 -delete
EOF

chmod +x /opt/stuffed-lamb/backup.sh

# Run daily at 2 AM
crontab -e
# Add: 0 2 * * * /opt/stuffed-lamb/backup.sh
```

### Update Application

**Systemd:**

```bash
sudo su - stuffedlamb
cd /opt/stuffed-lamb
git pull  # or update files
source venv/bin/activate
pip install -r requirements.txt --upgrade
exit
sudo systemctl restart stuffed-lamb
```

**Docker:**

```bash
docker-compose down
git pull
docker-compose up -d --build
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check logs
sudo journalctl -u stuffed-lamb -n 50 --no-pager

# Check permissions
ls -la /opt/stuffed-lamb

# Check .env file
sudo -u stuffedlamb cat /opt/stuffed-lamb/.env

# Test manually
sudo su - stuffedlamb
cd /opt/stuffed-lamb
source venv/bin/activate
python run.py
```

### Database Issues

```bash
# Check database file
ls -la /opt/stuffed-lamb/data/orders.db

# Recreate database
rm /opt/stuffed-lamb/data/orders.db
# Restart service (will auto-create)
```

### Redis Connection Failed

```bash
# Check Redis status
sudo systemctl status redis

# Start Redis
sudo systemctl start redis

# Test connection
redis-cli ping
```

### Port Already in Use

```bash
# Find what's using port 8000
sudo netstat -tulpn | grep 8000
# or
sudo ss -tulpn | grep 8000

# Kill the process or change PORT in .env
```

---

## Security Best Practices

1. **Keep .env secure**: Never commit, use proper file permissions (600)
2. **Use HTTPS**: Always use SSL/TLS in production
3. **Regular updates**: Keep system and dependencies updated
4. **Firewall**: Only allow necessary ports (80, 443, 22)
5. **Monitoring**: Setup alerts for downtime
6. **Backups**: Regular automated backups
7. **Rate limiting**: Consider adding Nginx rate limiting
8. **DDoS protection**: Use Cloudflare or similar

---

## Need Help?

- 📖 Documentation: See README.md and QUICK_START.md
- 🐛 Issues: Check logs and verify_setup.sh
- 💬 Support: Contact your system administrator

---

**System Status Check:**

```bash
# Quick status check
./verify_setup.sh
python healthcheck.py --url http://localhost:8000 --full
sudo systemctl status stuffed-lamb
```

**System is production-ready!** 🚀
