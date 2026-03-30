"""
Cart service — manages customer carts via Redis.
Supports pizza sizes, half/half pizzas, pasta types, and wing sauces.
"""

import logging
from typing import Optional

from app.redis_client import redis_delete, redis_get, redis_set
from app.services.menu import (
    calculate_item_price,
    calculate_half_half_price,
    get_item_by_name,
    format_cart_for_display,
    PASTA_TYPE_DEFAULT,
)
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
    Supports half/half pizzas, pasta types, and wing sauces.
    """
    cart = await get_cart(session_id)
    added = []
    errors = []

    for item_request in items:
        name = item_request.get("name", "")
        half_half = item_request.get("half_half", False)
        half1 = item_request.get("half1", "")
        half2 = item_request.get("half2", "")

        # Handle half/half pizzas
        if half_half and half1 and half2:
            size = item_request.get("size") or "large"
            price = calculate_half_half_price(half1, half2, size)

            cart_item = {
                "name": f"Half/Half Pizza",
                "category": "traditional_pizzas",
                "half_half": True,
                "half1": half1,
                "half2": half2,
                "size": size,
                "quantity": max(1, int(item_request.get("quantity", 1))),
                "price": price,
                "notes": item_request.get("notes"),
            }
            cart.append(cart_item)
            added.append(f"Half/Half ({half1} | {half2})")
            continue

        # Regular item
        menu_item = get_item_by_name(name)

        if not menu_item:
            errors.append(f"Could not find '{name}' on the menu")
            continue

        # Check availability
        if not menu_item.get("available", True):
            errors.append(f"'{menu_item['name']}' is currently sold out")
            continue

        size = item_request.get("size") or _default_size(menu_item)
        price = calculate_item_price(menu_item, size)

        cart_item = {
            "name": menu_item["name"],
            "category": menu_item.get("category", ""),
            "size": size,
            "half_half": False,
            "half1": None,
            "half2": None,
            "pasta_type": _resolve_pasta_type(menu_item, item_request),
            "sauce": item_request.get("sauce"),
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
    Edit a specific cart item. Updates price if size or half/half status changes.
    """
    cart = await get_cart(session_id)

    if item_index < 0 or item_index >= len(cart):
        return {"error": f"No item at index {item_index}. Cart has {len(cart)} items."}

    item = cart[item_index]

    # Apply changes
    for key, value in changes.items():
        if key in ("size", "half_half", "half1", "half2", "pasta_type", "sauce", "quantity", "notes"):
            item[key] = value

    # Recalculate price if size or half/half changed
    if "size" in changes or "half1" in changes or "half2" in changes or "half_half" in changes:
        if item.get("half_half") and item.get("half1") and item.get("half2"):
            item["price"] = calculate_half_half_price(item["half1"], item["half2"], item.get("size", "large"))
        else:
            menu_item = get_item_by_name(item["name"])
            if menu_item:
                item["price"] = calculate_item_price(menu_item, item.get("size"))

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
    """Return sensible default size for a pizza item."""
    sizes = menu_item.get("sizes", {})
    if "large" in sizes:
        return "large"
    if sizes:
        return next(iter(sizes))
    return None


def _resolve_pasta_type(menu_item: dict, item_request: dict) -> Optional[str]:
    """Resolve pasta type for pasta dishes. Returns None for non-pasta items."""
    category = menu_item.get("category", "")
    if category != "pastas":
        return None

    # Lasagna doesn't have a pasta type
    if not menu_item.get("pasta_type_options", True):
        return None

    return item_request.get("pasta_type") or PASTA_TYPE_DEFAULT
