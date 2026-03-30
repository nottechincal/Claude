"""
Tool Executor — dispatches Claude's tool calls to the appropriate services.
This is the bridge between the AI and the real world.
"""

import json
import logging
from datetime import datetime
from typing import Any

import pytz
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.services import cart, menu, order as order_service, notifications

logger = logging.getLogger(__name__)
settings = get_settings()
TZ = pytz.timezone(settings.shop_timezone)


async def execute_tool(
    tool_name: str,
    tool_input: dict,
    session_id: str,
    phone_number: str,
    db: AsyncSession = None,
    channel: str = "voice",
) -> Any:
    """
    Main dispatcher. Claude calls a tool → we execute it → return result.
    """
    logger.info(f"Executing tool: {tool_name} | session: {session_id}")

    try:
        match tool_name:

            case "check_shop_open":
                return await _check_shop_open()

            case "get_caller_context":
                return await _get_caller_context(phone_number)

            case "search_menu":
                query = tool_input.get("query", "")
                results = menu.search_menu(query, limit=5)
                if not results:
                    return {"found": False, "message": f"Nothing found for '{query}'"}
                return {
                    "found": True,
                    "items": [
                        {
                            "name": item["name"],
                            "category": item.get("category"),
                            "sizes": item.get("sizes", {}),
                            "price": item.get("price"),
                            "description": item.get("description", ""),
                            "pizza_type": item.get("pizza_type"),
                            "pasta_type_options": item.get("pasta_type_options"),
                            "sauce_options": item.get("sauce_options"),
                            "available": item.get("available", True),
                        }
                        for item in results[:3]
                    ],
                }

            case "add_to_cart":
                items_to_add = tool_input.get("items", [])
                return await cart.add_items_to_cart(session_id, items_to_add)

            case "view_cart":
                summary = await cart.get_cart_summary(session_id)
                return summary

            case "edit_cart_item":
                item_index = tool_input.get("item_index", 0)
                changes = tool_input.get("changes", {})
                return await cart.edit_cart_item(session_id, item_index, changes)

            case "remove_from_cart":
                item_index = tool_input.get("item_index", 0)
                return await cart.remove_from_cart(session_id, item_index)

            case "clear_cart":
                await cart.clear_cart(session_id)
                return {"cleared": True}

            case "get_order_summary":
                return await cart.get_cart_summary(session_id)

            case "set_pickup_time":
                pickup_time = tool_input.get("pickup_time", "asap")
                from app.redis_client import redis_set
                await redis_set(f"session:{session_id}:pickup_time", pickup_time)
                return {"pickup_time_set": pickup_time}

            case "create_order":
                if db is None:
                    return {"error": "Database not available"}

                # Get stored pickup time
                from app.redis_client import redis_get
                pickup_time = await redis_get(f"session:{session_id}:pickup_time") or "asap"
                customer_name = tool_input.get("customer_name")

                result = await order_service.create_order(
                    session_id=session_id,
                    db=db,
                    phone_number=phone_number,
                    channel=channel,
                    customer_name=customer_name,
                    pickup_time=pickup_time,
                )

                if "error" not in result:
                    # Auto-send confirmation
                    order_data = await order_service.get_order(result["order_id"], db)
                    if order_data and channel in ("sms", "whatsapp", "voice"):
                        notif_channel = "whatsapp" if channel == "whatsapp" else "sms"
                        await notifications.send_confirmation(phone_number, order_data, notif_channel)

                return result

            case "repeat_last_order":
                pn = tool_input.get("phone_number", phone_number)
                history = await order_service.get_customer_history(pn)
                orders = history.get("orders", [])
                if not orders:
                    return {"found": False, "message": "No previous orders found"}

                last_order = orders[0]
                items = last_order.get("items", [])

                # Re-add items to cart
                await cart.clear_cart(session_id)
                for item in items:
                    await cart.add_items_to_cart(session_id, [item])

                summary = await cart.get_cart_summary(session_id)
                return {
                    "found": True,
                    "loaded": True,
                    "order_date": last_order.get("created_at", ""),
                    "cart": summary,
                }

            case "send_confirmation":
                if db is None:
                    return {"error": "Database not available"}
                order_id = tool_input.get("order_id")
                notif_channel = tool_input.get("channel", "sms")
                order_data = await order_service.get_order(order_id, db)
                if not order_data:
                    return {"error": "Order not found"}
                success = await notifications.send_confirmation(phone_number, order_data, notif_channel)
                return {"sent": success}

            case _:
                logger.warning(f"Unknown tool: {tool_name}")
                return {"error": f"Unknown tool: {tool_name}"}

    except Exception as e:
        logger.exception(f"Tool execution error — {tool_name}: {e}")
        return {"error": str(e)}


async def _check_shop_open() -> dict:
    """Check if shop is currently open."""
    hours_data = menu.load_hours()
    now = datetime.now(TZ)
    day_name = now.strftime("%A").lower()

    # hours.json stores each day as a list of time windows: [{"open": "17:00", "close": "22:00"}]
    day_windows = hours_data.get(day_name, [])

    if not day_windows:
        return {
            "is_open": False,
            "message": f"Sorry, we're closed today ({now.strftime('%A')}). Check our hours!",
        }

    now_minutes = now.hour * 60 + now.minute

    for window in day_windows:
        open_time = window.get("open", "17:00")
        close_time = window.get("close", "22:00")

        open_h, open_m = map(int, open_time.split(":"))
        close_h, close_m = map(int, close_time.split(":"))

        open_minutes = open_h * 60 + open_m
        close_minutes = close_h * 60 + close_m

        # Handle midnight crossover
        if close_minutes < open_minutes:
            is_open = now_minutes >= open_minutes or now_minutes < close_minutes
        else:
            is_open = open_minutes <= now_minutes < close_minutes

        if is_open:
            return {
                "is_open": True,
                "current_time": now.strftime("%-I:%M %p"),
                "opens": open_time,
                "closes": close_time,
                "message": f"We're open! Kitchen closes at {close_time}.",
            }

    # Not in any open window
    first_window = day_windows[0]
    return {
        "is_open": False,
        "current_time": now.strftime("%-I:%M %p"),
        "opens": first_window.get("open", "17:00"),
        "closes": first_window.get("close", "22:00"),
        "message": f"We're currently closed. We open at {first_window.get('open', '17:00')}.",
    }


async def _get_caller_context(phone_number: str) -> dict:
    """Get customer history and personalisation data."""
    history = await order_service.get_customer_history(phone_number)
    orders = history.get("orders", [])
    total_orders = history.get("total_orders", 0)

    result = {
        "is_returning_customer": total_orders > 0,
        "total_orders": total_orders,
        "phone_number": phone_number,
    }

    if orders:
        last = orders[0]
        item_names = [item.get("name", "") for item in last.get("items", [])]
        result["last_order"] = {
            "items": item_names,
            "total": last.get("total"),
            "date": last.get("created_at", ""),
        }

        # Find most frequently ordered items
        from collections import Counter
        all_items = []
        for o in orders:
            all_items.extend([i.get("name", "") for i in o.get("items", [])])
        counter = Counter(all_items)
        result["favourites"] = [item for item, _ in counter.most_common(3)]

    return result
