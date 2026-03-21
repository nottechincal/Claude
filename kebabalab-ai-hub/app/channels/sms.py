"""
SMS Channel via Twilio
Handles SMS ordering with Claude AI.
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

router = APIRouter(prefix="/sms", tags=["sms"])


def get_session_id(phone: str) -> str:
    clean = phone.replace("+", "").replace(" ", "")
    return f"sms_{clean}"


def sms_response(message: str) -> Response:
    safe_msg = message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{safe_msg}</Message>
</Response>"""
    return Response(content=twiml, media_type="application/xml")


@router.post("/inbound")
async def inbound_sms(
    From: str = Form(""),
    Body: str = Form(""),
):
    """Handle inbound SMS messages."""
    logger.info(f"SMS from {From}: {Body[:100]}")

    message = Body.strip()
    if not message:
        return sms_response("Hi! Text us your order and we'll get it sorted. Type MENU for the menu.")

    # Quick commands
    if message.upper() == "MENU":
        return sms_response(
            "KebabaLab Menu:\n"
            "🌯 Kebab Small $10 / Large $15 (Lamb/Chicken/Mixed/Falafel)\n"
            "🥙 HSP (Halal Snack Pack) from $14\n"
            "🍟 Chips Small $4 / Large $6\n"
            "🥤 Cans $2.50 / Bottles $4\n\n"
            "Just text your order! e.g. 'Large chicken kebab with garlic sauce'"
        )

    session_id = get_session_id(From)
    agent = OrderingAgent(session_id=session_id, phone_number=From, channel="sms")

    async with AsyncSessionLocal() as db:
        tool_fn = partial(execute_tool, db=db, channel="sms")
        response_text = await agent.chat(message, tool_fn)

    # SMS has 160 char limit — truncate gracefully if needed
    if len(response_text) > 1600:
        response_text = response_text[:1597] + "..."

    return sms_response(response_text)
