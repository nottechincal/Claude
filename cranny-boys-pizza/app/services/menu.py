"""
Menu service — loads and searches the Cranny Boys Pizza menu.
Uses RapidFuzz for typo-tolerant matching.
"""

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Optional

from rapidfuzz import fuzz, process

logger = logging.getLogger(__name__)

PIZZA_SIZES = ["small", "medium", "large", "family", "jumbo"]

PASTA_TYPE_OPTIONS = ["spaghetti", "penne", "fettuccine", "rigatoni"]
PASTA_TYPE_DEFAULT = "spaghetti"

WINGS_SAUCE_OPTIONS = ["garlic butter", "honey mustard", "BBQ", "buffalo", "sweet chilli", "hot & spicy"]


@lru_cache(maxsize=1)
def load_menu() -> dict:
    data_dir = Path("data")
    with open(data_dir / "menu.json") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_hours() -> dict:
    data_dir = Path("data")
    with open(data_dir / "hours.json") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_business() -> dict:
    data_dir = Path("data")
    with open(data_dir / "business.json") as f:
        return json.load(f)


def get_all_items() -> list[dict]:
    """Flatten all menu items into a single list."""
    menu = load_menu()
    items = []
    for category, category_items in menu.get("categories", {}).items():
        for item in category_items:
            items.append({**item, "category": category})
    return items


def get_available_items() -> list[dict]:
    """Return only available (not sold out) items."""
    return [item for item in get_all_items() if item.get("available", True)]


def search_menu(query: str, limit: int = 5) -> list[dict]:
    """
    Fuzzy-search the menu for items matching the query.
    Returns ranked list of matches (available items only).
    """
    items = get_available_items()
    item_names = [item.get("name", "") for item in items]

    # Fuzzy match
    matches = process.extract(
        query,
        item_names,
        scorer=fuzz.WRatio,
        limit=limit,
        score_cutoff=50,
    )

    results = []
    for name, score, idx in matches:
        item = items[idx].copy()
        item["match_score"] = score
        results.append(item)

    return results


def get_item_by_name(name: str) -> Optional[dict]:
    """Get exact or best-match menu item (available items only)."""
    items = get_available_items()
    item_names = [item.get("name", "") for item in items]

    match = process.extractOne(name, item_names, scorer=fuzz.WRatio, score_cutoff=60)
    if match:
        _, _, idx = match
        return items[idx]
    return None


def calculate_item_price(item: dict, size: Optional[str] = None) -> float:
    """
    Calculate base price for an item with given size.
    Pizzas use 'sizes' dict (small/medium/large/family/jumbo).
    Pastas, parmas, entrees etc. use flat 'price'.
    """
    sizes = item.get("sizes", {})
    if size and size in sizes:
        return float(sizes[size])
    if sizes:
        # Default to first available size
        return float(next(iter(sizes.values())))
    if "price" in item:
        return float(item["price"])
    return 0.0


def calculate_half_half_price(half1_name: str, half2_name: str, size: str) -> float:
    """
    Calculate price for a half/half pizza.
    Price is the higher of the two halves' prices at the given size.
    """
    item1 = get_item_by_name(half1_name)
    item2 = get_item_by_name(half2_name)

    price1 = calculate_item_price(item1, size) if item1 else 0.0
    price2 = calculate_item_price(item2, size) if item2 else 0.0

    return max(price1, price2)


def format_cart_for_display(cart: list) -> str:
    """Format cart items into a human-readable string."""
    if not cart:
        return "Your cart is empty."

    lines = []
    total = 0.0

    for i, item in enumerate(cart, 1):
        desc_parts = [item.get("name", "Item")]

        if item.get("half_half"):
            h1 = item.get("half1", "?")
            h2 = item.get("half2", "?")
            desc_parts = [f"Half/Half ({h1} | {h2})"]

        if item.get("size"):
            desc_parts.append(item["size"])
        if item.get("pasta_type") and item.get("category") == "pastas":
            desc_parts.append(f"({item['pasta_type']})")
        if item.get("sauce"):
            desc_parts.append(f"sauce: {item['sauce']}")

        price = item.get("price", 0)
        qty = item.get("quantity", 1)
        line_total = price * qty
        total += line_total

        qty_str = f"x{qty} " if qty > 1 else ""
        lines.append(f"{i}. {qty_str}{' '.join(desc_parts)} — ${line_total:.2f}")

    gst = total / 11  # GST-inclusive pricing
    lines.append(f"\nTotal: ${total:.2f} (incl. ${gst:.2f} GST)")
    return "\n".join(lines)
