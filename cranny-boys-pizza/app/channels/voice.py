"""
Twilio Voice Channel
Handles inbound phone calls with Claude AI.

Flow:
1. Customer calls → Twilio → POST /voice/inbound
2. We return TwiML <Gather> to capture speech
3. Customer speaks → Twilio → POST /voice/process
4. Speech text → Claude → response text
5. Return TwiML <Say> to speak the response
6. Repeat until order complete
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

router = APIRouter(prefix="/voice", tags=["voice"])

TWIML_HEADER = '<?xml version="1.0" encoding="UTF-8"?>'


def twiml_say(text: str, voice: str = "Polly.Nicole") -> str:
    """Generate TwiML <Say> response."""
    # Nicole is an Australian voice from Amazon Polly — sounds native
    safe_text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f"""{TWIML_HEADER}
<Response>
    <Say voice="{voice}">{safe_text}</Say>
    <Gather input="speech" timeout="5" speechTimeout="auto" action="{settings.base_url}/voice/process" method="POST">
        <Say voice="{voice}">Go ahead.</Say>
    </Gather>
    <Redirect>{settings.base_url}/voice/process</Redirect>
</Response>"""


def twiml_gather(prompt: str, voice: str = "Polly.Nicole") -> str:
    """Generate TwiML with Gather for speech input."""
    safe_prompt = prompt.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f"""{TWIML_HEADER}
<Response>
    <Gather input="speech" timeout="5" speechTimeout="auto" action="{settings.base_url}/voice/process" method="POST">
        <Say voice="{voice}">{safe_prompt}</Say>
    </Gather>
    <Redirect>{settings.base_url}/voice/process</Redirect>
</Response>"""


def twiml_end(message: str, voice: str = "Polly.Nicole") -> str:
    """Generate TwiML to end the call."""
    safe_msg = message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f"""{TWIML_HEADER}
<Response>
    <Say voice="{voice}">{safe_msg}</Say>
    <Hangup/>
</Response>"""


def get_session_id(call_sid: str) -> str:
    """Derive a stable session ID from Twilio's CallSid."""
    return f"voice_{call_sid}"


@router.post("/inbound")
async def inbound_call(
    CallSid: str = Form(""),
    From: str = Form(""),
    To: str = Form(""),
):
    """
    Entry point for new inbound calls.
    Creates a session and starts the ordering conversation.
    """
    logger.info(f"Inbound call: {CallSid} from {From}")
    session_id = get_session_id(CallSid)

    agent = OrderingAgent(session_id=session_id, phone_number=From, channel="voice")

    async with AsyncSessionLocal() as db:
        tool_fn = partial(execute_tool, db=db, channel="voice")
        response_text = await agent.chat(
            f"A customer is calling from {From}. Greet them and check if we're open.",
            tool_fn,
        )

    twiml = twiml_gather(response_text)
    return Response(content=twiml, media_type="application/xml")


@router.post("/process")
async def process_speech(
    CallSid: str = Form(""),
    From: str = Form(""),
    SpeechResult: str = Form(""),
    Confidence: str = Form("0"),
):
    """
    Process speech input from the customer.
    Called by Twilio with the transcribed speech.
    """
    logger.info(f"Speech [{CallSid}]: '{SpeechResult}' (confidence: {Confidence})")

    if not SpeechResult.strip():
        twiml = twiml_gather("Sorry, I didn't catch that. What would you like to order?")
        return Response(content=twiml, media_type="application/xml")

    session_id = get_session_id(CallSid)
    agent = OrderingAgent(session_id=session_id, phone_number=From, channel="voice")

    async with AsyncSessionLocal() as db:
        tool_fn = partial(execute_tool, db=db, channel="voice")
        response_text = await agent.chat(SpeechResult, tool_fn)

    # Check if the response signals end of call
    end_phrases = ["goodbye", "bye", "see you soon", "call ended", "hangup"]
    if any(phrase in response_text.lower() for phrase in end_phrases):
        twiml = twiml_end(response_text)
    else:
        twiml = twiml_gather(response_text)

    return Response(content=twiml, media_type="application/xml")


@router.post("/status")
async def call_status(
    CallSid: str = Form(""),
    CallStatus: str = Form(""),
):
    """Twilio status callback — cleanup on call end."""
    logger.info(f"Call status: {CallSid} → {CallStatus}")
    if CallStatus in ("completed", "failed", "busy", "no-answer"):
        session_id = get_session_id(CallSid)
        # Clean up session (optional — let TTL handle it)
    return Response(content="ok", media_type="text/plain")
