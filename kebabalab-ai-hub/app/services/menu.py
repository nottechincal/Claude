"""
Menu service — loads and searches the menu.
Uses RapidFuzz for typo-tolerant matching.
"""

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Optional

from rapidfuzz import fuzz, process

logger = logging.getLogger(__name__)

PROTEIN_ALIASES = {
    "lamb": "lamb",
    "chicken": "chicken",
    "mixed": "mixed",
    "falafel": "falafel",
    "chook": "chicken",
    "chic": "chicken",
}

SAUCE_ALIASES = {
    "garlic": "garlic",
    "chilli": "chilli",
    "chili": "chilli",
    "bbq": "bbq",
    "tomato": "tomato",
    "sweet chilli": "sweet chilli",
    "tahini": "tahini",
    "hummus": "hummus",
}

SALAD_OPTIONS = [
    "lettuce", "tomato", "onion", "cucumber", "capsicum",
    "cabbage", "carrot", "beetroot", "tabouli", "all",
]


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


def search_menu(query: str, limit: int = 5) -> list[dict]:
    """
    Fuzzy-search the menu for items matching the query.
    Returns ranked list of matches.
    """
    items = get_all_items()
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
    """Get exact or best-match menu item."""
    items = get_all_items()
    item_names = [item.get("name", "") for item in items]

    match = process.extractOne(name, item_names, scorer=fuzz.WRatio, score_cutoff=60)
    if match:
        _, _, idx = match
        return items[idx]
    return None


def calculate_item_price(item: dict, size: Optional[str] = None) -> float:
    """Calculate price for an item with given size."""
    prices = item.get("prices", {})
    if size and size in prices:
        return float(prices[size])
    if "price" in item:
        return float(item["price"])
    # Default to first price
    if prices:
        return float(next(iter(prices.values())))
    return 0.0


def format_cart_for_display(cart: list) -> str:
    """Format cart items into a human-readable string."""
    if not cart:
        return "Your cart is empty."

    lines = []
    total = 0.0

    for i, item in enumerate(cart, 1):
        desc_parts = [item.get("name", "Item")]
        if item.get("size"):
            desc_parts.append(item["size"])
        if item.get("protein"):
            desc_parts.append(f"({item['protein']})")
        if item.get("salads"):
            desc_parts.append(f"salads: {', '.join(item['salads'])}")
        if item.get("sauces"):
            desc_parts.append(f"sauces: {', '.join(item['sauces'])}")

        price = item.get("price", 0)
        qty = item.get("quantity", 1)
        line_total = price * qty
        total += line_total

        qty_str = f"x{qty} " if qty > 1 else ""
        lines.append(f"{i}. {qty_str}{' '.join(desc_parts)} — ${line_total:.2f}")

    gst = total / 11  # GST-inclusive pricing
    lines.append(f"\nTotal: ${total:.2f} (incl. ${gst:.2f} GST)")
    return "\n".join(lines)
