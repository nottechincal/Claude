# KebabaLab AI Hub — Setup Guide

## What This Is

A completely rebuilt, multi-channel AI ordering system for KebabaLab.

**The old system** used VAPI (a third-party voice AI platform) and Flask.
**This new system** uses Claude directly (smarter, cheaper, more control) and FastAPI.

### Channels
| Channel | How | Status |
|---------|-----|--------|
| 📞 Phone (Voice) | Twilio Voice + Claude | Full |
| 💬 WhatsApp | Twilio WhatsApp + Claude | Full |
| 📱 SMS | Twilio SMS + Claude | Full |
| 🌐 Web Chat | WebSocket + Claude streaming | Full |

### Key Tech
- **AI**: Claude claude-opus-4-6 (ordering) + claude-haiku-4-5 (voice streaming for speed)
- **Framework**: FastAPI (async, 3x faster than Flask)
- **Database**: PostgreSQL (production-grade)
- **Cache/Sessions**: Redis
- **Communications**: Twilio (all channels)
- **Dashboard**: Real-time kitchen display via SSE

---

## Quick Start (Docker)

```bash
# 1. Clone and configure
cp .env.example .env
nano .env   # Fill in API keys

# 2. Start everything
make prod

# 3. View dashboard
open http://localhost:8000/dashboard

# 4. Test the chat
open http://localhost:8000
```

---

## Configuration

### Required API Keys

```env
# Anthropic (Claude AI)
ANTHROPIC_API_KEY=sk-ant-...

# Twilio (Voice, SMS, WhatsApp)
TWILIO_ACCOUNT_SID=ACxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxx
TWILIO_PHONE_NUMBER=+61xxxxxxxxx   # Your Twilio number
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# Public URL (ngrok for dev, your domain for prod)
BASE_URL=https://xxxx.ngrok.io
```

### Twilio Webhook Setup

After getting your public URL (ngrok or domain), configure Twilio:

**Voice calls:**
```
Webhook URL: https://your-url/voice/inbound
Method: POST
Status Callback: https://your-url/voice/status
```

**SMS:**
```
Webhook URL: https://your-url/sms/inbound
Method: POST
```

**WhatsApp (Sandbox):**
```
When a message comes in: https://your-url/whatsapp/inbound
Method: POST
```

---

## Local Development

```bash
# Start Redis and Postgres
docker compose up -d postgres redis

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your keys

# Run with auto-reload
uvicorn app.main:app --reload --port 8000

# Start ngrok for webhooks
ngrok http 8000
```

---

## Architecture

```
Customer calls/texts/chats
         │
         ▼
┌─────────────────────────────────────┐
│         KebabaLab AI Hub            │
│                                     │
│  Channels:                          │
│  📞 /voice/inbound  → Twilio Voice  │
│  💬 /whatsapp/inbound → WA Bot      │
│  📱 /sms/inbound → SMS Bot          │
│  🌐 /chat/ws → WebSocket            │
│                                     │
│  AI Brain:                          │
│  Claude claude-opus-4-6 (main)            │
│  Claude claude-haiku-4-5 (voice stream)   │
│         │                           │
│         ▼ Tool calls                │
│  Services:                          │
│  • CartService (Redis)              │
│  • MenuService (JSON + fuzzy)       │
│  • OrderService (PostgreSQL)        │
│  • NotificationService (Twilio)     │
│         │                           │
│         ▼                           │
│  📊 Dashboard (SSE real-time)       │
└─────────────────────────────────────┘
         │
         ▼
   PostgreSQL + Redis
```

---

## Why This Is Better Than The Old System

| Feature | Old (VAPI) | New (Claude Direct) |
|---------|-----------|-------------------|
| AI | VAPI's generic AI | Claude claude-opus-4-6 (much smarter) |
| Channels | Voice only | Voice + WhatsApp + SMS + Web |
| Speed | Flask (sync) | FastAPI (async, 3x faster) |
| Database | SQLite | PostgreSQL (production) |
| Real-time | None | SSE dashboard + WebSocket |
| Deployment | Manual | Docker Compose (one command) |
| Tool loop | 20+ calls for simple edit | 1 call (fixed) |
| AI cost | VAPI pricing | Direct Anthropic (cheaper) |

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web chat UI |
| `/dashboard` | GET | Kitchen display |
| `/api/events` | GET (SSE) | Real-time order stream |
| `/api/orders` | GET | List orders |
| `/api/orders/{id}` | GET | Get order |
| `/api/orders/{id}/status` | PATCH | Update status |
| `/voice/inbound` | POST | Twilio Voice webhook |
| `/voice/process` | POST | Speech processing |
| `/whatsapp/inbound` | POST | WhatsApp webhook |
| `/sms/inbound` | POST | SMS webhook |
| `/chat/ws` | WebSocket | Web chat |
| `/health` | GET | Health check |
| `/api/docs` | GET | Swagger UI |
