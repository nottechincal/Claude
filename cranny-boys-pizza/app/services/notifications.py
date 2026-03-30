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
        f"✅ Cranny Boys Pizza Order #{order.get('order_number', '???')} Confirmed!",
        "",
    ]

    items = order.get("items", [])
    for item in items:
        qty = item.get("quantity", 1)
        price = item.get("price", 0) * qty

        if item.get("half_half"):
            h1 = item.get("half1", "?")
            h2 = item.get("half2", "?")
            size = item.get("size", "")
            desc = f"• Half/Half ({h1} | {h2})"
            if size:
                desc += f" ({size})"
        else:
            name = item.get("name", "Item")
            size = item.get("size", "")
            pasta_type = item.get("pasta_type", "")
            sauce = item.get("sauce", "")

            desc = f"• {name}"
            if size:
                desc += f" ({size})"
            if pasta_type:
                desc += f" - {pasta_type}"
            if sauce:
                desc += f" - {sauce} sauce"

        if qty > 1:
            desc += f" x{qty}"
        desc += f" ${price:.2f}"
        lines.append(desc)

    lines.extend([
        "",
        f"💰 Total: ${order.get('total', 0):.2f}",
        f"⏰ Ready in approx: {order.get('estimated_ready', 'ASAP')}",
        f"📍 Shop 8/21 Strathlea Dr, Cranbourne West",
        "",
        "Thanks! See you soon 🍕",
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
