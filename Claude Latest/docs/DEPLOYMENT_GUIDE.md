# 🚀 Kebabalab VAPI System - Deployment Guide

## Overview

This is an enterprise-grade phone ordering system for Kebabalab with:
- Step-by-step order configuration
- Automatic combo/meal detection
- Robust state management
- Production-ready error handling

---

## Prerequisites

1. **Python 3.8+** installed
2. **VAPI Account** with API access
3. **Ngrok** or similar tunnel service (for development)
4. **Domain with HTTPS** (for production)

---

## Step 1: Server Setup

### Install Dependencies

```bash
pip install fastapi uvicorn python-dotenv twilio pytz
```

### Configure Environment

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Edit `.env` with your settings:
```env
DB_PATH=orders.db
GST_RATE=0.10
SHOP_TIMEZONE=Australia/Melbourne
```

### Test Server Locally

```bash
python server_v2.py
```

Server should start on `http://localhost:8000`

Test health endpoint:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy", "version": "2.0"}
```

---

## Step 2: Expose Server (Development)

### Using Ngrok

1. Install ngrok: https://ngrok.com/download

2. Start tunnel:
```bash
ngrok http 8000
```

3. Note the HTTPS URL (e.g., `https://abc123.ngrok-free.app`)

4. Update webhook URL in VAPI tools

### Using Other Tunnels

- **Cloudflare Tunnel**: `cloudflared tunnel --url http://localhost:8000`
- **LocalTunnel**: `lt --port 8000`
- **serveo.net**: `ssh -R 80:localhost:8000 serveo.net`

---

## Step 3: VAPI Configuration

### Create VAPI Assistant

1. Go to https://dashboard.vapi.ai
2. Click "Create Assistant"
3. Configure:
   - **Name**: Kebabalab Order Assistant
   - **Voice**: Australian English female (recommended: Nova or Shimmer)
   - **Model**: GPT-4 or GPT-4-turbo
   - **System Prompt**: Copy entire contents of `system-prompt.md`

### Add Tools to VAPI

You need to create each tool in VAPI. Use the definitions from `vapi-tools-definitions.json`.

**IMPORTANT**: Replace `YOUR_WEBHOOK_URL_HERE` with your actual webhook URL!

#### Method 1: Using VAPI Dashboard

For each tool in `vapi-tools-definitions.json`:

1. Go to Tools section
2. Click "Create Tool"
3. Choose "Function"
4. Copy the function definition
5. Set server URL to `https://your-domain.com/webhook`
6. Save

#### Method 2: Using VAPI API (Recommended)

Create a script to bulk-create tools:

```python
import requests
import json

VAPI_API_KEY = "your_vapi_api_key_here"
WEBHOOK_URL = "https://your-domain.com/webhook"

with open("vapi-tools-definitions.json") as f:
    tools_config = json.load(f)

headers = {
    "Authorization": f"Bearer {VAPI_API_KEY}",
    "Content-Type": "application/json"
}

for tool in tools_config["tools"]:
    # Update webhook URL
    tool["server"]["url"] = WEBHOOK_URL

    # Create tool
    response = requests.post(
        "https://api.vapi.ai/tool",
        headers=headers,
        json=tool
    )

    if response.status_code == 201:
        print(f"✅ Created tool: {tool['function']['name']}")
    else:
        print(f"❌ Failed to create {tool['function']['name']}: {response.text}")
```

### Attach Tools to Assistant

1. In VAPI Dashboard, go to your assistant
2. In "Tools" section, add all created tools
3. Save assistant

---

## Step 4: Testing

### Test Tool Calls

Use VAPI's test interface or create a test call:

```bash
curl -X POST https://api.vapi.ai/call \
  -H "Authorization: Bearer YOUR_VAPI_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "assistantId": "your_assistant_id",
    "customer": {
      "number": "+61426499209"
    }
  }'
```

### Test Complete Order Flow

Simulate a complete order:

1. **Call starts** → System runs `getCallerInfo` and `checkOpen`
2. **Order kebab** → `startItemConfiguration` → `setItemProperty` for each field → `addItemToCart`
3. **Add chips** → `startItemConfiguration` → `setItemProperty` → `addItemToCart`
4. **Add can** → `startItemConfiguration` → `setItemProperty` → `addItemToCart` (**combo detected!**)
5. **Checkout** → `priceCart` → `estimateReadyTime` → `createOrder` → `endCall`

### Check Logs

Monitor server logs:
```bash
tail -f kebabalab_server.log
```

### Check Database

```bash
sqlite3 orders.db "SELECT * FROM orders ORDER BY created_at DESC LIMIT 5;"
```

---

## Step 5: Production Deployment

### Option A: VPS (DigitalOcean, Linode, etc.)

1. **Provision server** (Ubuntu 22.04 recommended)

2. **Install Python and dependencies**:
```bash
sudo apt update
sudo apt install python3 python3-pip nginx certbot python3-certbot-nginx
pip3 install fastapi uvicorn python-dotenv twilio pytz
```

3. **Copy files to server**:
```bash
scp -r . user@your-server:/home/user/kebabalab/
```

4. **Create systemd service** (`/etc/systemd/system/kebabalab.service`):
```ini
[Unit]
Description=Kebabalab VAPI Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/home/user/kebabalab
Environment="PATH=/usr/bin"
ExecStart=/usr/bin/python3 server_v2.py
Restart=always

[Install]
WantedBy=multi-user.target
```

5. **Enable and start**:
```bash
sudo systemctl enable kebabalab
sudo systemctl start kebabalab
```

6. **Configure Nginx** (`/etc/nginx/sites-available/kebabalab`):
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

7. **Enable HTTPS with Let's Encrypt**:
```bash
sudo ln -s /etc/nginx/sites-available/kebabalab /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d your-domain.com
```

### Option B: Cloud Platform (Heroku, Railway, Render)

#### Render.com (Recommended for simplicity)

1. Create `render.yaml`:
```yaml
services:
  - type: web
    name: kebabalab-vapi
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python server_v2.py
    envVars:
      - key: DB_PATH
        value: orders.db
      - key: GST_RATE
        value: "0.10"
```

2. Create `requirements.txt`:
```
fastapi
uvicorn
python-dotenv
twilio
pytz
```

3. Push to GitHub and connect to Render

#### Railway

1. Install Railway CLI
2. Run `railway init`
3. Run `railway up`
4. Set environment variables in dashboard

### Option C: Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "server_v2.py"]
```

Build and run:
```bash
docker build -t kebabalab-vapi .
docker run -p 8000:8000 --env-file .env kebabalab-vapi
```

---

## Step 6: Monitoring & Maintenance

### Monitor Logs

```bash
# Live logs
tail -f kebabalab_server.log

# Search for errors
grep ERROR kebabalab_server.log

# Check specific order
grep "order_id" kebabalab_server.log | grep "20251021-001"
```

### Database Backups

```bash
# Backup database daily
sqlite3 orders.db ".backup orders_backup_$(date +%Y%m%d).db"

# Automate with cron
0 2 * * * /usr/bin/sqlite3 /home/user/kebabalab/orders.db ".backup /backups/orders_$(date +\%Y\%m\%d).db"
```

### Health Checks

Set up monitoring with UptimeRobot or similar:
- URL: `https://your-domain.com/health`
- Interval: 5 minutes
- Alert if down

---

## Troubleshooting

### Tool calls failing

1. Check webhook URL is correct and accessible
2. Verify server is running: `curl https://your-domain.com/health`
3. Check server logs for errors
4. Test tool manually:
```bash
curl -X POST https://your-domain.com/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "toolCalls": [{
        "function": {"name": "checkOpen", "arguments": "{}"},
        "id": "test123"
      }]
    }
  }'
```

### Combos not detecting

1. Check server logs for `detect_combo_opportunity` calls
2. Verify cart contents with `getCartState`
3. Ensure items have correct `category` and `size` fields

### Orders not saving

1. Check database permissions
2. Verify DB_PATH in .env
3. Check database manually:
```bash
sqlite3 orders.db ".schema"
```

---

## Support

For issues:
1. Check logs first
2. Verify VAPI configuration
3. Test each tool individually
4. Contact VAPI support if needed

---

## Next Steps

✅ Server deployed and running
✅ VAPI assistant configured
✅ Tools created and attached
✅ Testing complete

**You're ready to take live orders!** 🎉

Monitor the first few orders closely and make adjustments as needed.
