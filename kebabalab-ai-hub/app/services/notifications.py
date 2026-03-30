"""
Notification service — sends SMS and WhatsApp confirmations via Twilio.
"""

import logging
from typing import Optional

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def get_twilio_client():
    try:
        from twilio.rest import Client
        return Client(settings.twilio_account_sid, settings.twilio_auth_token)
    except Exception as e:
        logger.error(f"Failed to create Twilio client: {e}")
        return None


def format_order_confirmation(order: dict) -> str:
    """Format a nice SMS/WhatsApp confirmation message."""
    lines = [
        f"✅ KebabaLab Order #{order.get('order_number', '???')} Confirmed!",
        "",
    ]

    items = order.get("items", [])
    for item in items:
        name = item.get("name", "Item")
        size = item.get("size", "")
        protein = item.get("protein", "")
        qty = item.get("quantity", 1)
        price = item.get("price", 0) * qty

        desc = f"• {name}"
        if size:
            desc += f" ({size})"
        if protein:
            desc += f" - {protein}"
        if qty > 1:
            desc += f" x{qty}"
        desc += f" ${price:.2f}"
        lines.append(desc)

    lines.extend([
        "",
        f"💰 Total: ${order.get('total', 0):.2f}",
        f"⏰ Ready: {order.get('estimated_ready', 'ASAP')}",
        "",
        "See you soon! 🌯",
    ])

    return "\n".join(lines)


async def send_sms_confirmation(phone_number: str, order: dict) -> bool:
    """Send SMS order confirmation via Twilio."""
    client = get_twilio_client()
    if not client:
        logger.warning("Twilio not configured, skipping SMS")
        return False

    message_body = format_order_confirmation(order)

    try:
        message = client.messages.create(
            body=message_body,
            from_=settings.twilio_phone_number,
            to=phone_number,
        )
        logger.info(f"SMS sent: {message.sid}")
        return True
    except Exception as e:
        logger.error(f"Failed to send SMS: {e}")
        return False


async def send_whatsapp_confirmation(phone_number: str, order: dict) -> bool:
    """Send WhatsApp order confirmation via Twilio."""
    client = get_twilio_client()
    if not client:
        logger.warning("Twilio not configured, skipping WhatsApp")
        return False

    message_body = format_order_confirmation(order)

    # Ensure WhatsApp format
    to_number = phone_number if phone_number.startswith("whatsapp:") else f"whatsapp:{phone_number}"

    try:
        message = client.messages.create(
            body=message_body,
            from_=settings.twilio_whatsapp_number,
            to=to_number,
        )
        logger.info(f"WhatsApp sent: {message.sid}")
        return True
    except Exception as e:
        logger.error(f"Failed to send WhatsApp: {e}")
        return False


async def send_confirmation(phone_number: str, order: dict, channel: str = "sms") -> bool:
    if channel == "whatsapp":
        return await send_whatsapp_confirmation(phone_number, order)
    return await send_sms_confirmation(phone_number, order)
