"""
WhatsApp Channel via Twilio
Handles WhatsApp messages with Claude AI.

Flow:
1. Customer messages → Twilio → POST /whatsapp/inbound
2. Message → Claude (with conversation history) → response
3. Response → Twilio → customer
"""

import logging
from functools import partial

from fastapi import APIRouter, Form, Response

from app.ai.agent import OrderingAgent
from app.config import get_settings
from app.database import AsyncSessionLocal
from app.services.tool_executor import execute_tool

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])


def get_session_id(phone: str) -> str:
    """Derive session ID from phone number."""
    clean = phone.replace("whatsapp:", "").replace("+", "").replace(" ", "")
    return f"wa_{clean}"


def twilio_response(message: str) -> Response:
    """Return a TwiML MessagingResponse."""
    safe_msg = message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{safe_msg}</Message>
</Response>"""
    return Response(content=twiml, media_type="application/xml")


@router.post("/inbound")
async def inbound_message(
    From: str = Form(""),
    Body: str = Form(""),
    NumMedia: str = Form("0"),
    MediaUrl0: str = Form(""),
):
    """
    Handle inbound WhatsApp messages.
    """
    logger.info(f"WhatsApp from {From}: {Body[:100]}")

    # Extract phone (remove whatsapp: prefix for processing, keep for session)
    phone_number = From.replace("whatsapp:", "")
    session_id = get_session_id(From)

    # Handle media (image of menu etc)
    message = Body.strip()
    if not message and int(NumMedia) > 0:
        message = "I sent you an image"
    if not message:
        return twilio_response("Hey! What can I get ya? 🌯")

    agent = OrderingAgent(session_id=session_id, phone_number=phone_number, channel="whatsapp")

    async with AsyncSessionLocal() as db:
        tool_fn = partial(execute_tool, db=db, channel="whatsapp")
        response_text = await agent.chat(message, tool_fn)

    return twilio_response(response_text)
