"""
Order service — creates, retrieves, and manages orders in PostgreSQL.
"""

import logging
import uuid
from datetime import datetime
from typing import Optional

import pytz
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.order import Order
from app.services.cart import get_cart_summary, clear_cart
from app.redis_client import redis_get, redis_set, redis_publish

logger = logging.getLogger(__name__)
settings = get_settings()
TZ = pytz.timezone(settings.shop_timezone)


async def create_order(
    session_id: str,
    db: AsyncSession,
    phone_number: str,
    channel: str = "voice",
    customer_name: Optional[str] = None,
    pickup_time: str = "asap",
) -> dict:
    """
    Create a confirmed order from the current cart.
    Saves to PostgreSQL and publishes real-time event.
    """
    summary = await get_cart_summary(session_id)

    if summary["item_count"] == 0:
        return {"error": "Cart is empty. Add items before placing an order."}

    now = datetime.now(TZ)
    estimated_ready = _estimate_ready_time(now, summary["item_count"])

    order = Order(
        id=str(uuid.uuid4()),
        customer_phone=phone_number,
        customer_name=customer_name,
        channel=channel,
        items=summary["items"],
        subtotal=summary["subtotal"],
        gst=summary["gst"],
        total=summary["total"],
        status="confirmed",
        pickup_time=pickup_time,
        estimated_ready=estimated_ready,
        session_id=session_id,
    )

    db.add(order)
    await db.commit()
    await db.refresh(order)

    # Clear the cart
    await clear_cart(session_id)

    # Store in customer history
    await _update_customer_history(phone_number, order.to_dict())

    # Publish real-time event to dashboard
    await redis_publish("orders:new", order.to_dict())

    return {
        "order_id": order.id,
        "order_number": order.order_number,
        "total": float(order.total),
        "estimated_ready": estimated_ready,
        "status": "confirmed",
    }


async def get_order(order_id: str, db: AsyncSession) -> Optional[dict]:
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    return order.to_dict() if order else None


async def get_recent_orders(db: AsyncSession, limit: int = 50) -> list[dict]:
    result = await db.execute(
        select(Order).order_by(desc(Order.created_at)).limit(limit)
    )
    orders = result.scalars().all()
    return [o.to_dict() for o in orders]


async def update_order_status(order_id: str, status: str, db: AsyncSession) -> dict:
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        return {"error": "Order not found"}

    order.status = status
    await db.commit()

    # Publish status update
    await redis_publish("orders:update", {"id": order_id, "status": status})

    return {"order_id": order_id, "status": status}


async def get_customer_history(phone_number: str) -> dict:
    """Get a customer's order history from Redis cache."""
    key = f"customer:{phone_number}:history"
    data = await redis_get(key)
    return data or {"orders": [], "total_orders": 0}


async def _update_customer_history(phone_number: str, order: dict) -> None:
    key = f"customer:{phone_number}:history"
    history = await redis_get(key) or {"orders": [], "total_orders": 0}

    # Keep last 10 orders
    history["orders"].insert(0, {
        "id": order["id"],
        "items": order["items"],
        "total": order["total"],
        "created_at": order["created_at"],
    })
    history["orders"] = history["orders"][:10]
    history["total_orders"] = history.get("total_orders", 0) + 1

    # Cache for 90 days
    await redis_set(key, history, ttl=90 * 24 * 3600)


def _estimate_ready_time(now: datetime, item_count: int) -> str:
    """Estimate when an order will be ready — Cranny Boys Pizza takes about 22 minutes."""
    # Base 22 min + 3 min per item over 2, capped at 35 min
    minutes = min(22 + max(0, (item_count - 2) * 3), 35)
    from datetime import timedelta
    ready = now + timedelta(minutes=minutes)
    return ready.strftime("%-I:%M %p")
