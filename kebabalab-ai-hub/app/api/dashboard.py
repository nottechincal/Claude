"""
Dashboard API — Server-Sent Events for real-time order updates.
The shop owner sees orders appear in real-time.
"""

import asyncio
import json
import logging
from typing import AsyncIterator

import redis.asyncio as redis
from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse, StreamingResponse

from app.config import get_settings
from app.redis_client import get_redis

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Serve the real-time kitchen dashboard."""
    with open("app/templates/dashboard.html") as f:
        return HTMLResponse(f.read())


@router.get("/api/events")
async def event_stream(request: Request):
    """
    Server-Sent Events endpoint.
    Streams real-time order updates to the dashboard.
    """
    async def generate() -> AsyncIterator[str]:
        # Subscribe to Redis pub/sub
        r = get_redis()
        pubsub = r.pubsub()
        await pubsub.subscribe("orders:new", "orders:update")

        # Send initial connection event
        yield "data: {\"type\": \"connected\"}\n\n"

        try:
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break

                # Poll for messages
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message["type"] == "message":
                    channel = message["channel"]
                    data = message["data"]
                    event_type = "new_order" if channel == "orders:new" else "order_update"

                    payload = json.dumps({"type": event_type, "data": json.loads(data)})
                    yield f"data: {payload}\n\n"
                else:
                    # Heartbeat every second to keep connection alive
                    yield "data: {\"type\": \"heartbeat\"}\n\n"
                    await asyncio.sleep(1)

        except asyncio.CancelledError:
            pass
        finally:
            await pubsub.unsubscribe("orders:new", "orders:update")
            await pubsub.close()

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
