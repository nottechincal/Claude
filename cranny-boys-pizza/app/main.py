"""
Cranny Boys Pizza AI Hub — Main FastAPI Application

Multi-channel AI ordering system powered by Claude.
Channels: Voice (Twilio), WhatsApp, SMS, Web Chat
Brain: Claude claude-opus-4-6 with tool use
"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from app.config import get_settings
from app.database import init_db

# ─── Logging ──────────────────────────────────────────────────────────────────

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


# ─── Lifespan ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🍕 Cranny Boys Pizza AI Hub starting up...")
    await init_db()
    logger.info("✅ Database initialised")
    logger.info(f"📡 Base URL: {settings.base_url}")
    logger.info("🤖 Claude AI: claude-opus-4-6 (ordering) / claude-haiku-4-5 (voice streaming)")
    yield
    logger.info("👋 Cranny Boys Pizza AI Hub shutting down")


# ─── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Cranny Boys Pizza AI Hub",
    description="Multi-channel AI ordering system powered by Claude",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Routers ──────────────────────────────────────────────────────────────────

from app.channels.voice import router as voice_router
from app.channels.whatsapp import router as whatsapp_router
from app.channels.sms import router as sms_router
from app.channels.webchat import router as webchat_router
from app.api.orders import router as orders_router
from app.api.dashboard import router as dashboard_router

app.include_router(voice_router)
app.include_router(whatsapp_router)
app.include_router(sms_router)
app.include_router(webchat_router)
app.include_router(orders_router)
app.include_router(dashboard_router)


# ─── Core Routes ──────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the web chat interface."""
    with open("app/templates/chat.html") as f:
        return HTMLResponse(f.read())


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Cranny Boys Pizza AI Hub",
        "version": "1.0.0",
        "channels": ["voice", "whatsapp", "sms", "web"],
        "ai": "claude-opus-4-6",
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error on {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
