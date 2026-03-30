"""
Cart service — manages customer carts via Redis.
"""

import logging
from typing import Optional

from app.redis_client import redis_delete, redis_get, redis_set
from app.services.menu import calculate_item_price, get_item_by_name, format_cart_for_display
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

CART_KEY = "cart:{session_id}"


async def get_cart(session_id: str) -> list:
    data = await redis_get(CART_KEY.format(session_id=session_id))
    return data if isinstance(data, list) else []


async def save_cart(session_id: str, cart: list) -> None:
    await redis_set(CART_KEY.format(session_id=session_id), cart)


async def clear_cart(session_id: str) -> None:
    await redis_delete(CART_KEY.format(session_id=session_id))


async def add_items_to_cart(session_id: str, items: list[dict]) -> dict:
    """
    Add one or more items to the cart.
    Resolves menu items and calculates prices.
    """
    cart = await get_cart(session_id)
    added = []
    errors = []

    for item_request in items:
        name = item_request.get("name", "")
        menu_item = get_item_by_name(name)

        if not menu_item:
            errors.append(f"Could not find '{name}' on the menu")
            continue

        size = item_request.get("size") or _default_size(menu_item)
        price = calculate_item_price(menu_item, size)

        cart_item = {
            "name": menu_item["name"],
            "category": menu_item.get("category", ""),
            "size": size,
            "protein": item_request.get("protein") or _default_protein(menu_item),
            "salads": item_request.get("salads") or [],
            "sauces": item_request.get("sauces") or [],
            "extras": item_request.get("extras") or [],
            "quantity": max(1, int(item_request.get("quantity", 1))),
            "price": price,
            "notes": item_request.get("notes"),
        }
        cart.append(cart_item)
        added.append(cart_item["name"])

    await save_cart(session_id, cart)

    result = {"added": added, "cart_size": len(cart)}
    if errors:
        result["errors"] = errors
    return result


async def edit_cart_item(session_id: str, item_index: int, changes: dict) -> dict:
    """
    Edit a specific cart item. Updates price if size changes.
    This is the CRITICAL fix — one call handles all property changes.
    """
    cart = await get_cart(session_id)

    if item_index < 0 or item_index >= len(cart):
        return {"error": f"No item at index {item_index}. Cart has {len(cart)} items."}

    item = cart[item_index]

    # Apply changes
    for key, value in changes.items():
        if key in ("size", "protein", "salads", "sauces", "extras", "quantity", "notes"):
            item[key] = value

    # Recalculate price if size changed
    if "size" in changes:
        menu_item = get_item_by_name(item["name"])
        if menu_item:
            item["price"] = calculate_item_price(menu_item, item["size"])

    cart[item_index] = item
    await save_cart(session_id, cart)

    return {"updated": item, "item_index": item_index}


async def remove_from_cart(session_id: str, item_index: int) -> dict:
    cart = await get_cart(session_id)
    if item_index < 0 or item_index >= len(cart):
        return {"error": f"No item at index {item_index}"}

    removed = cart.pop(item_index)
    await save_cart(session_id, cart)
    return {"removed": removed["name"], "cart_size": len(cart)}


async def get_cart_summary(session_id: str) -> dict:
    """Calculate totals and return structured cart summary."""
    cart = await get_cart(session_id)
    subtotal = sum(item.get("price", 0) * item.get("quantity", 1) for item in cart)
    gst = subtotal / 11  # Australian GST-inclusive pricing
    return {
        "items": cart,
        "item_count": len(cart),
        "subtotal": round(subtotal, 2),
        "gst": round(gst, 2),
        "total": round(subtotal, 2),
        "display": format_cart_for_display(cart),
    }


def _default_size(menu_item: dict) -> Optional[str]:
    """Return sensible default size for a menu item."""
    prices = menu_item.get("prices", {})
    if "small" in prices:
        return "small"
    return None


def _default_protein(menu_item: dict) -> Optional[str]:
    """Return default protein if item has protein options."""
    category = menu_item.get("category", "")
    if category in ("kebabs", "hsp"):
        return "lamb"
    return None
